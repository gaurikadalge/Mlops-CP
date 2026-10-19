"""
Preprocessing and memory bank construction stage for DVC pipeline.
Chronologically extracts baseline window and builds historical attack memory bank without data leakage.
"""
import os
import sys
import json
import argparse
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.loader import load_dataset, split_temporal_window
from src.memory.build_memory import build_historical_memory



def run_preprocess_stage(data_path: str, output_memory: str, output_meta: str):
    print(f"Running preprocessing stage on: {data_path}")
    df = load_dataset(data_path)
    
    # Feature columns (exclude Label, Attack Type, Timestamp)
    feature_cols = [c for c in df.columns if c not in ["Label", "Attack Type", "Timestamp"]]
    
    # Extract baseline window (earlier 30%)
    n = len(df)
    baseline_end = int(n * 0.30)
    baseline_df = df.iloc[:baseline_end].copy()
    
    # Build historical attack memory from historical attacks in baseline
    print("Building historical attack memory bank from baseline window...")
    memory_patterns, memory_data_map = build_historical_memory(baseline_df, feature_cols=feature_cols)
    
    os.makedirs(os.path.dirname(output_memory), exist_ok=True)
    os.makedirs(os.path.dirname(output_meta), exist_ok=True)
    
    # Save memory summary
    memory_summary = {
        "num_attack_types_stored": len(memory_patterns),
        "attack_types": [p["pattern_id"] for p in memory_patterns],
        "sample_counts_per_attack": {k: len(v) for k, v in memory_data_map.items()}
    }
    with open(output_memory, "w") as f:
        json.dump(memory_summary, f, indent=2)
        
    meta = {
        "dataset_path": data_path,
        "total_records": n,
        "baseline_size": len(baseline_df),
        "streaming_size": n - baseline_end,
        "memory_summary": memory_summary
    }
    with open(output_meta, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Preprocessing metadata saved to {output_meta} and memory to {output_memory}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess and build memory bank for DVC pipeline.")
    parser.add_argument("--data-path", default="dataset/cic_ids2017_inspired_synthetic.csv", help="Path to raw dataset")
    parser.add_argument("--output-memory", default="outputs/historical_memory.json", help="Path to memory bank summary")
    parser.add_argument("--output-meta", default="outputs/preprocessing_metadata.json", help="Path to metadata output")
    args = parser.parse_args()

    run_preprocess_stage(args.data_path, args.output_memory, args.output_meta)
