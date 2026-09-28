import pandas as pd
import numpy as np
import warnings
import time
import os
import math

warnings.filterwarnings('ignore')

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import box

from src.preprocessing.loader import create_temporal_windows
from src.models.train import train_xgboost
from src.models.predict import predict_xgboost
from src.evaluation.metrics import evaluate_performance
from src.drift.ks_detector import detect_drift
from src.memory.profile import profile_pattern
from src.adaptation.recent_only import adapt_recent_only
from src.adaptation.random_replay import adapt_random_replay
from src.adaptation.pattern_replay import adapt_pattern_replay

console = Console()

def main():
    console.print(Panel.fit("[bold blue]Adaptive Historical Memory for Drift-Aware IDS[/bold blue]\n[italic]Executing Final Demonstration (Section 48)[/italic]", border_style="blue"))
    
    with console.status("[bold green]Loading dataset and setting up environments...") as status:
        data_path = "../cic_ids2017_inspired_synthetic.csv"
        df = pd.read_csv(data_path)
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values(by='Timestamp').reset_index(drop=True)
        
        hist_size = int(len(df) * 0.2)
        hist_df = df.iloc[:hist_size].copy()
        stream_df = df.iloc[hist_size:].copy()
        
        # Build Historical Test Set for Forgetting Metric (Hold out 20% of historical data)
        hist_train = hist_df.iloc[:int(len(hist_df)*0.8)].copy()
        hist_test = hist_df.iloc[int(len(hist_df)*0.8):].copy()
        
    console.print(f"[OK] Loaded {len(df)} total records (Historical: {len(hist_train)}, Stream: {len(stream_df)})")
    
    with console.status("[bold cyan]Building Historical Memory Patterns...") as status:
        memory_patterns = []
        memory_data_map = {}
        feature_cols = [c for c in hist_train.columns if c not in ['Timestamp', 'Label', 'Attack Type']]
        
        for attack_type in hist_train['Attack Type'].unique():
            if attack_type == 'BENIGN':
                continue
            pattern_data = hist_train[hist_train['Attack Type'] == attack_type][feature_cols]
            if len(pattern_data) > 50: 
                profile = profile_pattern(pattern_data, attack_type, feature_cols)
                memory_patterns.append(profile)
                
                pattern_full = hist_train[hist_train['Attack Type'] == attack_type][feature_cols + ['Label']]
                memory_data_map[attack_type] = pattern_full.sample(min(4000, len(pattern_full)), random_state=42)
                
        historical_pool = hist_train[feature_cols + ['Label']]
        
    console.print(f"[OK] Built memory for {len(memory_patterns)} attack patterns.")
    
    with console.status("[bold magenta]Training Initial Baseline Model (S1)...") as status:
        X_init = hist_train[feature_cols]
        y_init = hist_train['Label']
        baseline_model = train_xgboost(X_init, y_init)
        
        # Baseline historical F1
        baseline_hist_pred = predict_xgboost(baseline_model, hist_test[feature_cols])
        baseline_hist_f1 = evaluate_performance(hist_test['Label'], baseline_hist_pred)['f1_score']
        
    console.print(f"[OK] Initial IDS deployed. Baseline Historical F1: [bold]{baseline_hist_f1:.4f}[/bold]")
    console.print("\n[bold]Simulating Data Stream...[/bold]\n")
    
    stream_df_clean = stream_df.drop(columns=['Attack Type'])
    windows = create_temporal_windows(stream_df_clean, window_size=5000, label_column='Label', timestamp_column='Timestamp')
    
    reference_window_df = X_init.tail(5000)
    total_budget = 4000 
    
    for i, window in enumerate(windows):
        console.rule(f"[bold red]Window {i+1} Arrives ({window.timestamp_start} to {window.timestamp_end})")
        
        y_pred = predict_xgboost(baseline_model, window.X)
        metrics = evaluate_performance(window.y, y_pred)
        console.print(f"[dim]Current Static Model (S1) F1: {metrics['f1_score']:.4f}, FPR: {metrics['fpr']:.4f}[/dim]")
        
        drift_result = detect_drift(reference_window_df, window.X)
        if drift_result["drift_detected"]:
            console.print(f"[ALERT] [bold red]DRIFT DETECTED![/bold red] Score: {drift_result['drift_score']:.4f}")
            current_profile = profile_pattern(window.X, "current", feature_cols)
            
            # Show Pattern Similarity (Section 48 mockup)
            from src.memory.retrieve import retrieve_patterns
            all_patterns = retrieve_patterns(current_profile, memory_patterns, top_k=len(memory_patterns))
            
            sim_table = Table(title="Historical Pattern Similarity", box=box.SIMPLE)
            sim_table.add_column("Pattern", style="cyan")
            sim_table.add_column("Distance", style="magenta")
            
            for pat, dist in all_patterns:
                sim_table.add_row(pat, f"{dist:.4f}")
            console.print(sim_table)
            
            console.print(f"Top-K = 2")
            console.print(f"Recent:       2,000")
            console.print(f"Historical:   2,000")
            console.print(f"Total:        4,000\n")
            
            # S2: Recent Only
            s2_model = adapt_recent_only(window)
            s2_recent_pred = predict_xgboost(s2_model, window.X)
            s2_hist_pred = predict_xgboost(s2_model, hist_test[feature_cols])
            s2_metrics = {
                'Recent F1': evaluate_performance(window.y, s2_recent_pred)['f1_score'],
                'Historical F1': evaluate_performance(hist_test['Label'], s2_hist_pred)['f1_score'],
            }
            s2_metrics['Forgetting'] = baseline_hist_f1 - s2_metrics['Historical F1']
            
            # S3: Random Replay
            start_s3 = time.time()
            s3_model = adapt_random_replay(window, historical_pool, total_budget, 0.5)
            time_s3 = time.time() - start_s3
            s3_recent_pred = predict_xgboost(s3_model, window.X)
            s3_hist_pred = predict_xgboost(s3_model, hist_test[feature_cols])
            s3_metrics = {
                'Recent F1': evaluate_performance(window.y, s3_recent_pred)['f1_score'],
                'Historical F1': evaluate_performance(hist_test['Label'], s3_hist_pred)['f1_score'],
                'Training Time': time_s3
            }
            s3_metrics['Forgetting'] = baseline_hist_f1 - s3_metrics['Historical F1']
            
            # S4: Pattern Replay
            start_s4 = time.time()
            s4_model = adapt_pattern_replay(window, current_profile, memory_patterns, memory_data_map, total_budget, 0.5, top_k=2)
            time_s4 = time.time() - start_s4
            s4_recent_pred = predict_xgboost(s4_model, window.X)
            s4_hist_pred = predict_xgboost(s4_model, hist_test[feature_cols])
            s4_metrics = {
                'Recent F1': evaluate_performance(window.y, s4_recent_pred)['f1_score'],
                'Historical F1': evaluate_performance(hist_test['Label'], s4_hist_pred)['f1_score'],
                'Training Time': time_s4
            }
            s4_metrics['Forgetting'] = baseline_hist_f1 - s4_metrics['Historical F1']
            
            # Results Table
            res_table = Table(title="Retraining Results", box=box.ROUNDED)
            res_table.add_column("Strategy")
            res_table.add_column("Recent F1", justify="right")
            res_table.add_column("Historical F1", justify="right")
            res_table.add_column("Forgetting", justify="right")
            res_table.add_column("Time (s)", justify="right")
            
            res_table.add_row("Recent-Only (S2)", f"{s2_metrics['Recent F1']:.4f}", f"{s2_metrics['Historical F1']:.4f}", f"{s2_metrics['Forgetting']:.4f}", "-")
            res_table.add_row("Random Replay (S3)", f"{s3_metrics['Recent F1']:.4f}", f"{s3_metrics['Historical F1']:.4f}", f"{s3_metrics['Forgetting']:.4f}", f"{s3_metrics['Training Time']:.2f}")
            res_table.add_row("Pattern Replay (S4)", f"{s4_metrics['Recent F1']:.4f}", f"{s4_metrics['Historical F1']:.4f}", f"{s4_metrics['Forgetting']:.4f}", f"{s4_metrics['Training Time']:.2f}")
            
            console.print(res_table)
            
            # Stop after demonstrating one drift event for the demo
            break
            
        else:
            console.print("[OK] No significant drift detected.")
            
if __name__ == "__main__":
    main()
