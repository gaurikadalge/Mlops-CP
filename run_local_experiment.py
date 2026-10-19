import pandas as pd
import numpy as np
import warnings
import time
import os
import mlflow
import mlflow.xgboost

warnings.filterwarnings('ignore')
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"

from src.preprocessing.loader import create_temporal_windows, split_temporal_window
from src.models.train import train_xgboost
from src.models.predict import predict_xgboost
from src.evaluation.metrics import evaluate_performance
from src.evaluation.forgetting import evaluate_historical_retention
from src.evaluation.comparison import create_strategy_result, build_comparison_dataframe, validate_budget_equality
from src.drift.ks_detector import detect_drift
from src.memory.build_memory import build_historical_memory
from src.adaptation.recent_only import adapt_recent_only
from src.adaptation.random_replay import adapt_random_replay
from src.adaptation.pattern_replay import adapt_pattern_replay


def main(data_path: str = None):
    # Setup MLflow tracking experiment with resilient fallback
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        import urllib.request
        try:
            with urllib.request.urlopen("http://localhost:5001/", timeout=1) as resp:
                tracking_uri = "http://localhost:5001"
        except Exception:
            tracking_uri = "file:///" + os.path.abspath("mlruns")
            
    mlflow.set_tracking_uri(tracking_uri)
    try:
        exp = mlflow.get_experiment_by_name("Adaptive_IDS_Experiment")
        if not exp:
            mlflow.create_experiment(
                "Adaptive_IDS_Experiment",
                artifact_location=os.path.abspath("mlruns")
            )
        mlflow.set_experiment("Adaptive_IDS_Experiment")
    except Exception:
        fallback_uri = "file:///" + os.path.abspath("mlruns")
        mlflow.set_tracking_uri(fallback_uri)
        mlflow.set_experiment("Adaptive_IDS_Experiment")
    
    print("Loading dataset...")
    # Preserve user's robust dataset path resolution
    if data_path is None:
        data_path = "dataset/cic_ids2017_inspired_synthetic.csv"
        if not os.path.exists(data_path):
            data_path = "cic_ids2017_inspired_synthetic.csv"
        if not os.path.exists(data_path):
            data_path = "../cic_ids2017_inspired_synthetic.csv"
    df = pd.read_csv(data_path)
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values(by='Timestamp').reset_index(drop=True)
    
    # 20% of data is 'Historical'
    hist_size = int(len(df) * 0.2)
    hist_df = df.iloc[:hist_size].copy()
    stream_df = df.iloc[hist_size:].copy()
    
    # Separate historical holdout (20% of historical data) for leak-free retention/forgetting measurement
    split_hist = int(len(hist_df) * 0.8)
    hist_train = hist_df.iloc[:split_hist].copy()
    hist_test = hist_df.iloc[split_hist:].copy()
    
    feature_cols = [c for c in hist_train.columns if c not in ['Timestamp', 'Label', 'Attack Type']]
    
    print(f"Historical Training Pool: {len(hist_train)} records")
    print(f"Historical Holdout Test:  {len(hist_test)} records (held out for forgetting evaluation)")
    print(f"Streaming Data Stream:    {len(stream_df)} records")
    
    print("\nBuilding Historical Pattern Memory (with empirical feature distributions)...")
    memory_patterns, memory_data_map = build_historical_memory(
        hist_train, feature_cols, attack_column='Attack Type', label_column='Label', min_samples=50
    )
    historical_pool = hist_train[feature_cols + ['Label']]
    print(f"Stored {len(memory_patterns)} historical attack patterns: {[p['pattern_id'] for p in memory_patterns]}")
    
    print("\nTraining Initial Baseline Model (S1)...")
    X_init = hist_train[feature_cols]
    y_init = hist_train['Label']
    baseline_model = train_xgboost(X_init, y_init)
    
    # Compute baseline historical performance on holdout
    baseline_hist_res = evaluate_historical_retention(
        baseline_model, hist_test[feature_cols], hist_test['Label'], baseline_hist_f1=1.0
    )
    baseline_hist_f1 = baseline_hist_res["historical_f1"]
    print(f"[Baseline IDS] Historical Holdout F1: {baseline_hist_f1:.4f}, FPR: {baseline_hist_res['historical_fpr']:.4f}")
    
    print("\nSimulating Data Stream with Leakage-Free Chronological Evaluation...")
    stream_df_clean = stream_df.drop(columns=['Attack Type'])
    windows = create_temporal_windows(stream_df_clean, window_size=5000, label_column='Label', timestamp_column='Timestamp')
    
    reference_window_df = X_init.tail(5000)
    total_budget = 2000  # Controlled identical budget for S2, S3, S4
    
    all_window_results = []
    
    for i, window in enumerate(windows):
        print(f"\n=======================================================")
        print(f"--- Window {window.id} Arrives ({window.timestamp_start} to {window.timestamp_end}) ---")
        print(f"=======================================================")
        
        # Leakage-free chronological forward split:
        # 60% of window (earlier timestamps) used strictly for adaptation if drift occurs
        # 40% of window (later timestamps) reserved strictly for untouched forward evaluation
        adapt_window, eval_window = split_temporal_window(window, train_ratio=0.6)
        print(f"Temporal Split: Adapt Split = {len(adapt_window.X)} records | Eval Split = {len(eval_window.X)} records")
        
        # S1 Static Evaluation on unseen eval window
        s1_eval_pred = predict_xgboost(baseline_model, eval_window.X)
        s1_metrics = evaluate_performance(eval_window.y, s1_eval_pred)
        s1_hist = evaluate_historical_retention(baseline_model, hist_test[feature_cols], hist_test['Label'], baseline_hist_f1)
        
        print(f"[S1 Baseline] Eval F1: {s1_metrics['f1_score']:.4f} | FPR: {s1_metrics['fpr']:.4f} | Hist F1: {s1_hist['historical_f1']:.4f} | Forgetting: 0.0000")
        
        with mlflow.start_run(run_name=f"{window.id}_S1_Static", nested=True):
            mlflow.log_params({"strategy": "S1_Static", "window_id": window.id})
            mlflow.log_metrics({
                "recent_f1": s1_metrics['f1_score'],
                "recent_fpr": s1_metrics['fpr'],
                "historical_f1": s1_hist['historical_f1'],
                "forgetting": 0.0
            })
            
        s1_row = create_strategy_result(
            "S1_Static", s1_metrics['f1_score'], s1_hist['historical_f1'], 0.0,
            s1_metrics['fpr'], 0, len(X_init), len(X_init), 0.0, window.id
        )
        
        # Detect Drift comparing reference distribution against incoming adapt window
        drift_result = detect_drift(reference_window_df, adapt_window.X)
        
        if drift_result["drift_detected"]:
            print(f" > [ALERT] Drift Detected! Drift Score: {drift_result['drift_score']:.4f}")
            print(f"   Drifted features: {drift_result['drifted_features']}")
            
            # ----------------------------------------------------
            # S2: Recent-Only Retraining (Budget = total_budget)
            # ----------------------------------------------------
            start_s2 = time.time()
            s2_model, s2_counts = adapt_recent_only(
                adapt_window, total_budget=total_budget, seed=42, return_counts=True
            )
            time_s2 = time.time() - start_s2
            s2_eval_pred = predict_xgboost(s2_model, eval_window.X)
            s2_metrics = evaluate_performance(eval_window.y, s2_eval_pred)
            s2_hist = evaluate_historical_retention(s2_model, hist_test[feature_cols], hist_test['Label'], baseline_hist_f1)
            
            # ----------------------------------------------------
            # S3: Random Historical Replay (Budget = total_budget)
            # ----------------------------------------------------
            start_s3 = time.time()
            s3_model, s3_counts = adapt_random_replay(
                adapt_window, historical_pool, total_budget=total_budget,
                recent_fraction=0.5, seed=42, return_counts=True
            )
            time_s3 = time.time() - start_s3
            s3_eval_pred = predict_xgboost(s3_model, eval_window.X)
            s3_metrics = evaluate_performance(eval_window.y, s3_eval_pred)
            s3_hist = evaluate_historical_retention(s3_model, hist_test[feature_cols], hist_test['Label'], baseline_hist_f1)
            
            # ----------------------------------------------------
            # S4: Pattern-Aware Replay with Wasserstein Retrieval
            # Unlabeled adapt_window.X used for retrieval
            # ----------------------------------------------------
            start_s4 = time.time()
            s4_model, s4_counts = adapt_pattern_replay(
                recent_data=adapt_window,
                current_profile=adapt_window.X,  # Unlabeled empirical data
                memory_patterns=memory_patterns,
                memory_data_map=memory_data_map,
                total_budget=total_budget,
                recent_fraction=0.5,
                top_k=2,
                seed=42,
                return_counts=True,
                historical_fallback_pool=historical_pool
            )
            time_s4 = time.time() - start_s4
            s4_eval_pred = predict_xgboost(s4_model, eval_window.X)
            s4_metrics = evaluate_performance(eval_window.y, s4_eval_pred)
            s4_hist = evaluate_historical_retention(s4_model, hist_test[feature_cols], hist_test['Label'], baseline_hist_f1)
            
            s2_row = create_strategy_result(
                "S2_RecentOnly", s2_metrics['f1_score'], s2_hist['historical_f1'], s2_hist['forgetting'],
                s2_metrics['fpr'], s2_counts['recent_count'], s2_counts['historical_count'], s2_counts['total_count'], time_s2, window.id
            )
            s3_row = create_strategy_result(
                "S3_RandomReplay", s3_metrics['f1_score'], s3_hist['historical_f1'], s3_hist['forgetting'],
                s3_metrics['fpr'], s3_counts['recent_count'], s3_counts['historical_count'], s3_counts['total_count'], time_s3, window.id
            )
            s4_row = create_strategy_result(
                "S4_PatternReplay", s4_metrics['f1_score'], s4_hist['historical_f1'], s4_hist['forgetting'],
                s4_metrics['fpr'], s4_counts['recent_count'], s4_counts['historical_count'], s4_counts['total_count'], time_s4, window.id
            )
            
            # Log S2, S3, S4 to MLflow
            for row, model, strat_name in [(s2_row, s2_model, "S2_RecentOnly"), (s3_row, s3_model, "S3_RandomReplay"), (s4_row, s4_model, "S4_PatternReplay")]:
                with mlflow.start_run(run_name=f"{window.id}_{strat_name}", nested=True):
                    mlflow.log_params({
                        "strategy": strat_name,
                        "window_id": window.id,
                        "total_budget": total_budget,
                        "recent_records": row["Recent Records"],
                        "hist_records": row["Hist Records"],
                        "total_records": row["Total Records"]
                    })
                    mlflow.log_metrics({
                        "recent_f1": row["Recent F1"],
                        "historical_f1": row["Historical F1"],
                        "forgetting": row["Forgetting"],
                        "fpr": row["FPR"],
                        "training_time": row["Training Time (s)"]
                    })
                    try:
                        mlflow.xgboost.log_model(model, "model")
                    except Exception as model_log_err:
                        print(f"Notice: Artifact storage not accessible locally ({model_log_err}). Metrics and parameters recorded.")
                    
            window_comparison = [s1_row, s2_row, s3_row, s4_row]
            # Verify strict budget equality between S2, S3, S4
            validate_budget_equality([s2_row, s3_row, s4_row], expected_budget=total_budget)
            all_window_results.extend(window_comparison)
            
            comp_df = build_comparison_dataframe(window_comparison)
            print("\nStrategy Comparison on Unseen Forward Evaluation Split:")
            print(comp_df.to_string(index=False))
            
            # Update reference window for future drift detection
            reference_window_df = adapt_window.X.copy()
        else:
            print(" > No significant drift detected.")
            all_window_results.append(s1_row)
            
    print("\n=======================================================")
    print("FINAL CONSOLIDATED EXPERIMENT REPORT (S1 vs S2 vs S3 vs S4)")
    print("=======================================================")
    final_df = build_comparison_dataframe(all_window_results)
    print(final_df.to_string(index=False))
    return final_df


run_pipeline = main


if __name__ == "__main__":
    main()

