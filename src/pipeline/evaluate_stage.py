"""
Evaluation and experiment stage for DVC pipeline.
Executes the fixed-budget 4-strategy benchmark and outputs tracked metrics JSON.
"""
import os
import sys
import json
import argparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from run_local_experiment import run_pipeline


def run_evaluation_stage(data_path: str, output_metrics: str):
    print(f"Running DVC evaluation stage using: {data_path}")
    results = run_pipeline(data_path=data_path)
    
    if hasattr(results, "to_dict"):
        records = results.to_dict(orient="records")
    elif isinstance(results, list):
        records = results
    else:
        records = [results]
        
    metrics_summary = {
        "dataset": data_path,
        "dataset_type": "synthetic_benchmark" if "synthetic" in data_path else "real_cic_ids2017",
        "strategies": records
    }
    
    os.makedirs(os.path.dirname(output_metrics), exist_ok=True)
    with open(output_metrics, "w") as f:
        json.dump(metrics_summary, f, indent=2)
        
    print(f"Evaluation metrics written to: {output_metrics}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate 4 IDS adaptation strategies for DVC.")
    parser.add_argument("--data-path", default="dataset/cic_ids2017_inspired_synthetic.csv", help="Path to raw dataset")
    parser.add_argument("--output-metrics", default="outputs/evaluation_metrics.json", help="Path to output metrics")
    args = parser.parse_args()

    run_evaluation_stage(args.data_path, args.output_metrics)
