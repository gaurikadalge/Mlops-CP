"""
AEGIS Traffic Stream Simulator
Sends real-time network flow samples to the FastAPI REST API (port 8000).
This immediately triggers:
1. Live model inference and TreeSHAP explainability.
2. Prometheus counter & latency histogram metric updates (port 9090).
3. Real-time visual updates in Grafana dashboards (port 3002).
"""

import sys
import time
import random
import argparse
import urllib.request
import json

API_URL = "http://127.0.0.1:8000/predict"
EXPLAIN_URL = "http://127.0.0.1:8000/explain"

# Representative flow profiles
BENIGN_PROFILE = {
    "Flow Duration": (15000.0, 35000.0),
    "Total Fwd Packets": (5.0, 15.0),
    "Total Backward Packets": (4.0, 12.0),
    "Total Length of Fwd Packets": (400.0, 1200.0),
    "Total Length of Bwd Packets": (600.0, 2500.0),
    "Flow Bytes/s": (15000.0, 50000.0),
    "Flow Packets/s": (80.0, 220.0),
    "Packet Length Mean": (80.0, 220.0),
    "Packet Length Std": (30.0, 90.0),
    "SYN Flag Count": (0.0, 0.0),
    "ACK Flag Count": (1.0, 1.0),
}

ATTACK_DOS_PROFILE = {
    "Flow Duration": (80000.0, 140000.0),
    "Total Fwd Packets": (20.0, 60.0),
    "Total Backward Packets": (2.0, 8.0),
    "Total Length of Fwd Packets": (3000.0, 8000.0),
    "Total Length of Bwd Packets": (200.0, 800.0),
    "Flow Bytes/s": (140000.0, 260000.0),
    "Flow Packets/s": (300.0, 750.0),
    "Packet Length Mean": (650.0, 1100.0),
    "Packet Length Std": (200.0, 450.0),
    "SYN Flag Count": (1.0, 1.0),
    "ACK Flag Count": (0.0, 0.0),
}

def generate_sample(is_attack=False):
    profile = ATTACK_DOS_PROFILE if is_attack else BENIGN_PROFILE
    sample = {}
    for feat, (low, high) in profile.items():
        sample[feat] = round(random.uniform(low, high), 2)
    return sample

def send_sample(sample, explain=False):
    url = EXPLAIN_URL if explain else API_URL
    payload = json.dumps({"features": sample}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            elapsed_ms = (time.time() - start_t) * 1000
            data = json.loads(resp.read().decode("utf-8"))
            return True, data, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.time() - start_t) * 1000
        return False, str(e), elapsed_ms

def main():
    parser = argparse.ArgumentParser(description="Send network traffic samples to AEGIS API.")
    parser.add_argument("--count", type=int, default=20, help="Number of packets to send (default: 20)")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay in seconds between packets (default: 0.2s)")
    parser.add_argument("--explain", action="store_true", help="Also request SHAP explanations via /explain")
    parser.add_argument("--attack-ratio", type=float, default=0.4, help="Ratio of attack packets (0.0 to 1.0)")
    args = parser.parse_args()

    print("=" * 65)
    print("  AEGIS Live Traffic Stream Generator")
    print(f"  Target: {API_URL} | Packets: {args.count} | Delay: {args.delay}s")
    print(f"  Attack Ratio: {int(args.attack_ratio * 100)}% | SHAP Explain: {args.explain}")
    print("=" * 65)

    benign_cnt = 0
    attack_cnt = 0

    for i in range(1, args.count + 1):
        is_attack = random.random() < args.attack_ratio
        sample = generate_sample(is_attack=is_attack)
        
        ok, res, latency = send_sample(sample, explain=args.explain)
        
        if ok:
            label = res.get("label", "Unknown")
            prob = res.get("probability", 1.0)
            if label == "Attack":
                attack_cnt += 1
                flag = "[ALERT - ATTACK]"
            else:
                benign_cnt += 1
                flag = "[NORMAL - BENIGN]"
            
            print(f"[{i:03d}/{args.count:03d}] {flag:<17} | Prob: {prob*100:.1f}% | Latency: {latency:.1f}ms | Bytes/s: {sample['Flow Bytes/s']:>8.0f}")
        else:
            print(f"[{i:03d}/{args.count:03d}] [ERROR] {res}")

        if i < args.count:
            time.sleep(args.delay)

    print("-" * 65)
    print(f"Summary: Sent {args.count} flows -> {benign_cnt} Benign, {attack_cnt} Attacks classified.")
    print("Prometheus metrics updated at: http://localhost:9090")
    print("Grafana dashboard live at:     http://localhost:3002")
    print("=" * 65)

if __name__ == "__main__":
    main()
