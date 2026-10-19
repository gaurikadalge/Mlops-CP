"""
Data validation stage for DVC pipeline.
Validates dataset integrity, feature presence, numeric validity, and class balance.
"""
import os
import sys
import json
import argparse
import pandas as pd
import numpy as np

CORE_SYNTHETIC_FEATURES = [
    "Flow Duration",
    "Flow Bytes/s",
    "Packet Length Mean"
]

FULL_CIC_FEATURES = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Packet Length Mean",
]

TARGET_COL = "Label"


def validate_dataset(data_path: str, output_path: str) -> bool:
    print(f"Validating dataset from: {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset file not found at: {data_path}")

    df = pd.read_csv(data_path)
    total_records = len(df)
    print(f"Loaded {total_records} records.")

    # Check for target column
    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' missing from dataset!")

    # Check whether dataset conforms to synthetic or real CIC-IDS2017 schema
    has_synthetic = all(col in df.columns for col in CORE_SYNTHETIC_FEATURES)
    has_full_cic = all(col in df.columns for col in FULL_CIC_FEATURES)

    if not (has_synthetic or has_full_cic):
        missing_syn = [c for c in CORE_SYNTHETIC_FEATURES if c not in df.columns]
        raise ValueError(f"Dataset is missing core features: {missing_syn}")

    dataset_type = "real_cic_ids2017" if has_full_cic else "synthetic_benchmark"

    # Check null / NaN counts
    null_counts = int(df.isnull().sum().sum())
    
    # Class distribution
    label_counts = df[TARGET_COL].value_counts().to_dict()
    # Normalize keys for JSON serialization
    label_dist = {str(k): int(v) for k, v in label_counts.items()}

    report = {
        "dataset_path": data_path,
        "dataset_type": dataset_type,
        "total_records": total_records,
        "total_columns": len(df.columns),
        "null_values_count": null_counts,
        "is_valid": null_counts == 0 and total_records > 0,
        "label_distribution": label_dist,
        "columns_checked": list(df.columns)
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Validation report successfully written to: {output_path}")
    return report["is_valid"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate dataset for DVC pipeline.")
    parser.add_argument("--data-path", default="dataset/cic_ids2017_inspired_synthetic.csv", help="Path to raw CSV dataset")
    parser.add_argument("--output", default="outputs/data_validation_report.json", help="Path to write validation report")
    args = parser.parse_args()

    is_valid = validate_dataset(args.data_path, args.output)
    if not is_valid:
        sys.exit(1)
