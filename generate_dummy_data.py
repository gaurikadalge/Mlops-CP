import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_data(num_samples_per_bucket=10000, num_buckets=5):
    np.random.seed(42)
    total_samples = num_samples_per_bucket * num_buckets
    timestamps = [datetime(2023, 1, 1) + timedelta(minutes=i) for i in range(total_samples)]
    
    # Base Benign Traffic
    data = {
        'Timestamp': timestamps,
        'Flow Duration': np.random.normal(100, 20, total_samples),
        'Flow Bytes/s': np.random.normal(5000, 1000, total_samples),
        'Packet Length Mean': np.random.normal(50, 10, total_samples),
        'Label': np.zeros(total_samples, dtype=int),
        'Attack Type': np.array(['BENIGN'] * total_samples, dtype=object)
    }
    
    # Helper to inject attacks
    def inject_attack(start_idx, end_idx, attack_name, duration_shift, bytes_shift, length_shift, ratio=0.1):
        idx = np.random.choice(range(start_idx, end_idx), size=int((end_idx - start_idx) * ratio), replace=False)
        data['Label'][idx] = 1
        data['Attack Type'][idx] = attack_name
        data['Flow Duration'][idx] += duration_shift
        data['Flow Bytes/s'][idx] += bytes_shift
        data['Packet Length Mean'][idx] += length_shift

    # -----------------------------------------------------
    # BUCKET 1 & 2: Baseline (Historical Memory)
    # -----------------------------------------------------
    b1_start, b2_end = 0, num_samples_per_bucket * 2
    inject_attack(b1_start, b2_end, 'Loud DoS', duration_shift=800, bytes_shift=10000, length_shift=0)
    inject_attack(b1_start, b2_end, 'PortScan', duration_shift=0, bytes_shift=0, length_shift=-30)

    # -----------------------------------------------------
    # BUCKET 3: Mutated Threat (60% similarity to Loud DoS)
    # -----------------------------------------------------
    b3_start, b3_end = num_samples_per_bucket * 2, num_samples_per_bucket * 3
    # "Low and Slow DoS" -> Duration shifted but not as extreme, bytes slightly increased
    inject_attack(b3_start, b3_end, 'Mutated DoS', duration_shift=400, bytes_shift=3000, length_shift=0)
    
    # -----------------------------------------------------
    # BUCKET 4: Return to Normalcy
    # -----------------------------------------------------
    b4_start, b4_end = num_samples_per_bucket * 3, num_samples_per_bucket * 4
    # Just normal background attacks
    inject_attack(b4_start, b4_end, 'Loud DoS', duration_shift=800, bytes_shift=10000, length_shift=0)

    # -----------------------------------------------------
    # BUCKET 5: Zero-Day Exploit (0% similarity)
    # -----------------------------------------------------
    b5_start, b5_end = num_samples_per_bucket * 4, total_samples
    # Completely bizarre metrics (e.g. Data Exfiltration)
    inject_attack(b5_start, b5_end, 'Zero-Day Exfiltration', duration_shift=-50, bytes_shift=-4000, length_shift=200)
    
    df = pd.DataFrame(data)
    # Ensure it writes to the correct dataset folder
    out_path = 'dataset/cic_ids2017_inspired_synthetic.csv'
    import os
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Generated 5-bucket synthetic dataset ({total_samples} rows) at {out_path}")

if __name__ == "__main__":
    generate_synthetic_data()
