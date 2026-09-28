import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_data(num_samples=25000):
    np.random.seed(42)
    
    timestamps = [datetime(2023, 1, 1) + timedelta(minutes=i) for i in range(num_samples)]
    
    data = {
        'Timestamp': timestamps,
        'Flow Duration': np.random.normal(100, 20, num_samples),
        'Flow Bytes/s': np.random.normal(5000, 1000, num_samples),
        'Packet Length Mean': np.random.normal(50, 10, num_samples),
    }
    
    # Base is benign
    data['Label'] = np.zeros(num_samples, dtype=int)
    data['Attack Type'] = np.array(['BENIGN'] * num_samples, dtype=object)
    
    # Introduce some historical attacks (first 20% of data)
    hist_end = int(num_samples * 0.2)
    
    # Attack 1: DoS Hulk
    idx_dos = np.random.choice(range(0, hist_end), size=int(hist_end * 0.1), replace=False)
    data['Label'][idx_dos] = 1
    data['Attack Type'][idx_dos] = 'DoS Hulk'
    data['Flow Duration'][idx_dos] += 500
    
    # Attack 2: PortScan
    idx_port = np.random.choice(list(set(range(0, hist_end)) - set(idx_dos)), size=int(hist_end * 0.1), replace=False)
    data['Label'][idx_port] = 1
    data['Attack Type'][idx_port] = 'PortScan'
    data['Packet Length Mean'][idx_port] -= 30
    
    # Introduce drift in streaming data (after 50% mark)
    drift_start = int(num_samples * 0.5)
    
    # Shift features for all traffic after drift_start to simulate drift
    data['Flow Duration'][drift_start:] += 150
    data['Flow Bytes/s'][drift_start:] -= 2000
    
    # Introduce a new attack in the drifted region that resembles PortScan statistically but slightly different
    idx_new = np.random.choice(range(drift_start, num_samples), size=int(num_samples * 0.1), replace=False)
    data['Label'][idx_new] = 1
    data['Attack Type'][idx_new] = 'New Attack'
    data['Packet Length Mean'][idx_new] -= 25
    
    df = pd.DataFrame(data)
    df.to_csv('../cic_ids2017_inspired_synthetic.csv', index=False)
    print("Generated synthetic dataset at ../cic_ids2017_inspired_synthetic.csv")

if __name__ == "__main__":
    generate_synthetic_data()
