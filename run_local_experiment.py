import pandas as pd
import numpy as np
import warnings
import time
import os
import mlflow
import mlflow.xgboost

warnings.filterwarnings('ignore')

from src.preprocessing.loader import create_temporal_windows
from src.models.train import train_xgboost
from src.models.predict import predict_xgboost
from src.evaluation.metrics import evaluate_performance
from src.drift.ks_detector import detect_drift
from src.memory.profile import profile_pattern
from src.adaptation.random_replay import adapt_random_replay
from src.adaptation.pattern_replay import adapt_pattern_replay

def main():
    # Setup MLflow tracking experiment
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("Adaptive_IDS_Experiment")
    
    print("Loading dataset...")
    data_path = "../cic_ids2017_inspired_synthetic.csv"
    df = pd.read_csv(data_path)
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values(by='Timestamp').reset_index(drop=True)
    
    # 20% of data is 'Historical'
    hist_size = int(len(df) * 0.2)
    hist_df = df.iloc[:hist_size].copy()
    stream_df = df.iloc[hist_size:].copy()
    
    print(f"Historical Data: {len(hist_df)} records")
    print(f"Streaming Data: {len(stream_df)} records")
    
    print("\nBuilding Historical Memory...")
    memory_patterns = []
    memory_data_map = {}
    feature_cols = [c for c in hist_df.columns if c not in ['Timestamp', 'Label', 'Attack Type']]
    
    for attack_type in hist_df['Attack Type'].unique():
        if attack_type == 'BENIGN':
            continue
        pattern_data = hist_df[hist_df['Attack Type'] == attack_type][feature_cols]
        if len(pattern_data) > 50: 
            profile = profile_pattern(pattern_data, attack_type, feature_cols)
            memory_patterns.append(profile)
            
            pattern_full = hist_df[hist_df['Attack Type'] == attack_type][feature_cols + ['Label']]
            memory_data_map[attack_type] = pattern_full.sample(min(4000, len(pattern_full)), random_state=42)
            
    historical_pool = hist_df[feature_cols + ['Label']]
    
    print("\nTraining Initial Baseline Model (S1)...")
    X_init = hist_df[feature_cols]
    y_init = hist_df['Label']
    baseline_model = train_xgboost(X_init, y_init)
    
    print("\nSimulating Data Stream with MLflow tracking...")
    stream_df_clean = stream_df.drop(columns=['Attack Type'])
    windows = create_temporal_windows(stream_df_clean, window_size=5000, label_column='Label', timestamp_column='Timestamp')
    
    reference_window_df = X_init.tail(5000)
    total_budget = 4000 
    
    for i, window in enumerate(windows):
        print(f"\n--- {window.id} ---")
        
        y_pred = predict_xgboost(baseline_model, window.X)
        metrics = evaluate_performance(window.y, y_pred)
        print(f"[S1 Baseline] F1: {metrics['f1_score']:.4f}, FPR: {metrics['fpr']:.4f}")
        
        # Log Baseline Metrics
        with mlflow.start_run(run_name=f"{window.id}_S1_Baseline", nested=True):
            mlflow.log_param("strategy", "S1_Static")
            mlflow.log_param("window_id", window.id)
            mlflow.log_metrics({"f1_score": metrics['f1_score'], "fpr": metrics['fpr']})
        
        drift_result = detect_drift(reference_window_df, window.X)
        if drift_result["drift_detected"]:
            print(f" > Drift Detected! Score: {drift_result['drift_score']:.4f}")
            current_profile = profile_pattern(window.X, "current", feature_cols)
            
            # S3: Random Replay
            start_s3 = time.time()
            s3_model = adapt_random_replay(window, historical_pool, total_budget, 0.5)
            time_s3 = time.time() - start_s3
            s3_metrics = evaluate_performance(window.y, predict_xgboost(s3_model, window.X))
            print(f"[S3 Random] F1: {s3_metrics['f1_score']:.4f}")
            
            with mlflow.start_run(run_name=f"{window.id}_S3_RandomReplay", nested=True):
                mlflow.log_param("strategy", "S3_RandomReplay")
                mlflow.log_param("window_id", window.id)
                mlflow.log_param("drift_score", drift_result['drift_score'])
                mlflow.log_param("total_budget", total_budget)
                mlflow.log_metrics({"f1_score": s3_metrics['f1_score'], "fpr": s3_metrics['fpr'], "training_time": time_s3})
                mlflow.xgboost.log_model(s3_model, "model")
            
            # S4: Pattern Replay
            start_s4 = time.time()
            s4_model = adapt_pattern_replay(window, current_profile, memory_patterns, memory_data_map, total_budget, 0.5, top_k=2)
            time_s4 = time.time() - start_s4
            s4_metrics = evaluate_performance(window.y, predict_xgboost(s4_model, window.X))
            print(f"[S4 Pattern] F1: {s4_metrics['f1_score']:.4f}")
            
            with mlflow.start_run(run_name=f"{window.id}_S4_PatternReplay", nested=True):
                mlflow.log_param("strategy", "S4_PatternReplay")
                mlflow.log_param("window_id", window.id)
                mlflow.log_param("drift_score", drift_result['drift_score'])
                mlflow.log_param("total_budget", total_budget)
                mlflow.log_metrics({"f1_score": s4_metrics['f1_score'], "fpr": s4_metrics['fpr'], "training_time": time_s4})
                mlflow.xgboost.log_model(s4_model, "model")
            
            # Update reference window
            reference_window_df = window.X.copy()
        else:
            print(" > No significant drift detected.")

if __name__ == "__main__":
    main()
