"""
Driftwood Traffic Stream Simulator
Sends real-time network flow samples to the FastAPI REST API (port 8000).
This immediately triggers:
1. Live model inference and TreeSHAP explainability.
2. Prometheus counter & latency histogram metric updates (port 9090).
3. Real-time visual updates in Grafana dashboards (port 3002) and Web UI (port 5173).
"""

import sys
import time
import random
import argparse
import urllib.request
import json

API_URL = "http://127.0.0.1:8000/predict"
EXPLAIN_URL = "http://127.0.0.1:8000/explain"
DRIFT_SIMULATE_URL = "http://127.0.0.1:8000/simulate_drift"

# Representative flow profiles for 11 model features
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

ATTACK_PORTSCAN_PROFILE = {
    "Flow Duration": (1000.0, 8000.0),
    "Total Fwd Packets": (1.0, 4.0),
    "Total Backward Packets": (0.0, 1.0),
    "Total Length of Fwd Packets": (40.0, 240.0),
    "Total Length of Bwd Packets": (0.0, 60.0),
    "Flow Bytes/s": (5000.0, 25000.0),
    "Flow Packets/s": (350.0, 900.0),
    "Packet Length Mean": (40.0, 70.0),
    "Packet Length Std": (0.0, 20.0),
    "SYN Flag Count": (1.0, 1.0),
    "ACK Flag Count": (0.0, 0.0),
}

def generate_sample(attack_type=None):
    if attack_type == "dos":
        profile = ATTACK_DOS_PROFILE
    elif attack_type == "portscan":
        profile = ATTACK_PORTSCAN_PROFILE
    else:
        profile = BENIGN_PROFILE

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
    parser = argparse.ArgumentParser(description="Live traffic stream simulator for Driftwood NIDS.")
    parser.add_argument("--count", type=int, default=20, help="Number of packets to send (default: 20)")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay in seconds between packets (default: 0.2s)")
    parser.add_argument("--explain", action="store_true", help="Also request TreeSHAP explanations via /explain")
    parser.add_argument("--attack-ratio", type=float, default=0.4, help="Ratio of attack packets (0.0 to 1.0)")
    parser.add_argument("--continuous", action="store_true", help="Stream indefinitely in real time until Ctrl+C")
    parser.add_argument("--burst", action="store_true", help="Send a rapid 50-packet attack burst for live demo")
    parser.add_argument("--trigger-drift", action="store_true", help="Directly trigger a drift event and increment Grafana counter")
    args = parser.parse_args()

    if args.trigger_drift:
        print("[ACTION] Triggering live drift event at http://127.0.0.1:8000/simulate_drift...")
        try:
            req = urllib.request.Request(DRIFT_SIMULATE_URL, data=b"{}", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"[SUCCESS] Drift triggered! New score: {data.get('drift_score')}, retrained in {data.get('retraining_time')}")
                print("Check Grafana (http://localhost:3002) gauge and drift event counter.")
                return
        except Exception as e:
            print(f"[ERROR] Could not trigger drift on API: {e}")
            return

    if args.burst:
        args.count = 50
        args.delay = 0.05
        args.attack_ratio = 0.9

    mode_label = "CONTINUOUS REAL-TIME STREAM" if args.continuous else f"{args.count} PACKET BATCH"

    print("=" * 70)
    print("  DRIFTWOOD LIVE NETWORK TRAFFIC STREAM GENERATOR")
    print(f"  Target API:    {API_URL}")
    print(f"  Stream Mode:   {mode_label}")
    print(f"  Packet Delay:  {args.delay}s per flow | Attack Ratio: {int(args.attack_ratio * 100)}%")
    print(f"  TreeSHAP:      {args.explain}")
    print("=" * 70)
    print("  [Tip] Keep Grafana (http://localhost:3002) open to watch live graph shifts.")
    print("  [Tip] Press Ctrl+C at any time to halt continuous streaming.")
    print("=" * 70)

    benign_cnt = 0
    attack_cnt = 0
    pkt_index = 0

    try:
        while True:
            pkt_index += 1
            is_attack = random.random() < args.attack_ratio
            if is_attack:
                attack_variant = random.choice(["dos", "portscan"])
                sample = generate_sample(attack_type=attack_variant)
            else:
                sample = generate_sample(attack_type=None)

            ok, res, latency = send_sample(sample, explain=args.explain)

            if ok:
                label = res.get("label", "Unknown")
                prob = res.get("probability", 1.0)
                if label == "Attack":
                    attack_cnt += 1
                    flag = "\033[91m[ALERT - ATTACK]\033[0m" if sys.platform != "win32" else "[ALERT - ATTACK]"
                else:
                    benign_cnt += 1
                    flag = "\033[92m[NORMAL - BENIGN]\033[0m" if sys.platform != "win32" else "[NORMAL - BENIGN]"

                drift_score = res.get("drift_score", None)
                drift_str = f" | Drift: {drift_score:.3f}" if drift_score is not None else ""
                print(f"[{pkt_index:04d}] {flag:<17} | Prob: {prob*100:>5.1f}% | Latency: {latency:>5.1f}ms | B/s: {sample['Flow Bytes/s']:>8.0f}{drift_str}")
            else:
                print(f"[{pkt_index:04d}] [OFFLINE/SURROGATE] API not responding ({res}). Packets simulated.")

            if not args.continuous and pkt_index >= args.count:
                break

            time.sleep(args.delay)

    except KeyboardInterrupt:
        print("\n[INFO] Continuous streaming gracefully stopped by user.")

    print("-" * 70)
    print(f"Stream Summary: {pkt_index} total flows -> {benign_cnt} Benign, {attack_cnt} Attacks classified.")
    print("Prometheus Metrics: http://localhost:9090")
    print("Grafana Dashboard:  http://localhost:3002 (adaptive-ids-main)")
    print("Web Dashboard:      http://127.0.0.1:5173")
    print("=" * 70)

if __name__ == "__main__":
    main()
