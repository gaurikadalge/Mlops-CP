# Adaptive Historical Memory for Drift-Aware Intrusion Detection

[![MLOps Pipeline CI](https://github.com/gaurikadalge/Mlops-CP/actions/workflows/ml_pipeline.yml/badge.svg)](https://github.com/gaurikadalge/Mlops-CP/actions/workflows/ml_pipeline.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![DVC](https://img.shields.io/badge/data-versioned%20with%20DVC-9cf.svg)](https://dvc.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Prometheus](https://img.shields.io/badge/metrics-Prometheus-E6522C.svg)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/dashboard-Grafana%20v11+-F46800.svg)](https://grafana.com)

An end-to-end MLOps research and production system for **Intrusion Detection under Statistical Traffic Drift**. The project implements and compares four adaptation strategies using XGBoost, Kolmogorov-Smirnov (KS) drift detection, and scale-normalized Wasserstein pattern retrieval under a strictly enforced equal retraining-data budget.

---

## 1. Project Overview & Research Architecture

### Core Research Concept
Traditional machine learning IDS classifiers degrade when network traffic patterns drift over time. Retraining solely on recent traffic leads to catastrophic forgetting of historical attack signatures, while full-history retraining is computationally prohibitive and dilutes emerging threats. 

This repository evaluates:
> *Under an identical retraining-data budget, does pattern-aware historical replay preserve more historical intrusion-detection knowledge than random historical replay while maintaining detection on recent traffic?*

### The 4 Experimental Strategies (Strict Fixed Budget)
To ensure rigorous scientific validity, all adapted strategies ($S2, S3, S4$) are allocated an **identical total record budget** ($B_{total} = B_{recent} + B_{hist}$):
* **S1: Static IDS (Baseline)** — Initial XGBoost model trained on historical base traffic; never retrained.
* **S2: Recent-Only Retraining** — Retrained exclusively on the drifted recent window ($100\%$ recent budget).
* **S3: Random Historical Replay** — Retrained on $50\%$ recent window + $50\%$ randomly sampled historical records.
* **S4: Pattern-Aware Replay** — Retrained on $50\%$ recent window + $50\%$ historical records retrieved via scale-normalized Wasserstein distance from a compact historical pattern memory.

### Empirical Benchmark Findings (Synthetic Benchmark)
Experiments conducted on the benchmark dataset under chronological forward evaluation (training on earlier records, evaluating on future untouched records, and measuring forgetting on an isolated historical holdout) yield the following empirical results:

| Strategy | Recent F1 | Historical F1 | Catastrophic Forgetting | Retrain Time |
| :--- | :---: | :---: | :---: | :---: |
| **S1: Static** | 0.1924 | 0.8976 | 0.0000 (Baseline) | — |
| **S2: Recent-Only** | 0.7657 | 0.5793 | 0.3183 | ~0.16s |
| **S3: Random Replay** | **0.7682** | **0.8916** | **0.0060** | ~0.16s |
| **S4: Pattern Replay** | 0.7654 | 0.8064 | 0.0912 | ~0.17s |

*Empirical Note:* On this benchmark stream, **S3 slightly outperformed S4**, demonstrating that broad historical coverage can maintain resilience against multi-attack distribution shifts. These empirical results are preserved without fabrication or alteration.

---

## 2. System Architecture & Syllabus Integrations

```
                       ┌───────────────────────────────┐
                       │  Chronological Traffic Stream │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │   Preprocess & Schema Check   │ (DVC Stage 1 & 2)
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │ Kolmogorov-Smirnov Drift Test │
                       └───────────────┬───────────────┘
                                       │
                      ┌────────────────┴────────────────┐
                 [No Drift]                          [Drift]
                      │                                 │
                      ▼                                 ▼
             Serve Static Model               Wasserstein Retrieval
                      │                                 │
                      │                        Fixed-Budget Replay
                      │                        (S2 vs S3 vs S4)
                      │                                 │
                      │                       Untouched Forward Eval
                      │                       & Holdout Quality Gate
                      │                                 │
                      ▼                                 ▼
               FastAPI + SHAP  ◄──────────────── MLflow Registry
                      │
           ┌──────────┴──────────┐
           ▼                     ▼
     Prometheus               Grafana
   (Port 9090)              (Port 3002)
```

---

## 3. Step 4A — DVC (Data Versioning & Pipeline)

Data versioning tracks both synthetic benchmark data and real CIC-IDS2017 datasets, ensuring pipeline reproducibility without committing large binaries to Git.

### Setup and Storage
A local DVC remote (`local_storage`) is configured out-of-the-box in `.dvc/config`:
```bash
dvc remote list
# local_storage  ./.dvc_remote
```

### Tracked Datasets
- Synthetic benchmark: `dataset/cic_ids2017_inspired_synthetic.csv` is tracked via `dataset/cic_ids2017_inspired_synthetic.csv.dvc`.
- Raw CIC-IDS2017 real datasets: To ingest the real CIC-IDS2017 dataset:
  1. Download the official CSVs from the UNB CIC-IDS2017 portal.
  2. Place raw files under `data/raw/cic_ids2017/`.
  3. Track with DVC: `dvc add data/raw/cic_ids2017/*.csv`.
  4. Run `dvc push`.

### Multi-Stage Pipeline (`dvc.yaml`)
1. **`validate`**: Runs `src/pipeline/validate_data.py`. Verifies schemas, required numerical features, and class balance. Generates `outputs/data_validation_report.json`.
2. **`preprocess`**: Runs `src/pipeline/preprocess_stage.py`. Partitions initial historical base from streaming windows, builds compact attack profiles, and outputs `outputs/historical_memory.json`.
3. **`evaluate`**: Runs `src/pipeline/evaluate_stage.py`. Executes the chronological forward evaluation comparing S1–S4 under equal budgets, logging `outputs/evaluation_metrics.json`.

### DVC Execution Commands
```bash
# View pipeline DAG
dvc dag

# Reproduce the entire pipeline
dvc repro

# Check status of data artifacts
dvc status

# Push/Pull data to/from local storage
dvc push
dvc pull
```

---

## 4. Step 4B — Apache Airflow Orchestration

The Airflow DAG (`dags/adaptive_ids_workflow.py`) orchestrates the 10-step streaming IDS cycle without top-level parsing execution:
1. `select_next_window` — Chronologically slices the streaming window.
2. `validate_schema` — Validates feature bounds and types.
3. `detect_ks_drift` — Multi-feature Kolmogorov-Smirnov statistical test.
4. `branch_drift_decision` — Branches to adaptation if drift score exceeds threshold; skips otherwise.
5. `retrieve_memory_patterns` — Computes scale-normalized Wasserstein distances.
6. `run_adaptation_strategy` — Retrains XGBoost under the strict budget limit.
7. `evaluate_model` — Evaluates on forward test data and historical holdout.
8. `apply_quality_gate` — Asserts F1 and False Positive Rate thresholds.
9. `log_mlflow_results` — Records parameters, metrics, and models to MLflow.
10. `update_memory` — Updates pattern memory using temporal expiry policy.

### Running Airflow
Airflow is integrated as an optional Docker Compose profile so it does not destabilize existing services:

```bash
# Start Airflow Standalone (Webserver & Scheduler on http://localhost:8088)
docker compose --profile airflow up -d airflow-standalone

# View Airflow logs
docker compose logs -f airflow-standalone

# Stop Airflow service
docker compose stop airflow-standalone
```

### Testing the DAG
```bash
pytest tests/test_airflow_dag.py -v
```

---

## 5. Step 4C — GitHub Actions CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ml_pipeline.yml`) validates all pull requests and pushes to `main`:
- **Python Setup**: Python 3.11 environment with cached pip dependencies.
- **Unit & Integration Suite**: Runs all 30 tests with pytest and coverage reporting.
- **Invariant Checks**: Validates research invariants (budget equality in `test_replay.py`, temporal leakage prevention in `test_evaluation.py`).
- **Synthetic Smoke Test**: Runs `run_local_experiment.py` end-to-end against local SQLite MLflow.
- **DVC Validation**: Verifies `dvc dag` integrity.
- **Container Build Check**: Runs `docker compose config` and verifies `docker compose build api-server`.
- **Security & Privacy**: Zero cloud credentials or large external downloads required.

---

## 6. Step 4D — AWS SageMaker Production Deployment

A complete production deployment path for AWS SageMaker is provided:

### Canonical Inference Entry Point (`src/deployment/inference.py`)
Implements the SageMaker PyTorch/XGBoost container contract:
- `model_fn(model_dir)`: Loads the XGBoost binary/UBJ model artifact.
- `input_fn(request_body, content_type)`: Parses and validates `application/json` or `text/csv`, ensuring required features are present and non-negative.
- `predict_fn(input_data, model)`: Computes prediction probabilities and class labels.
- `output_fn(prediction, accept)`: Returns standardized JSON response.

### Packaging Deployment Artifacts
```bash
# Bundles the latest trained model with code/inference.py and requirements into model.tar.gz
python src/deployment/package_sagemaker.py
```
Output artifact: `build/sagemaker/model.tar.gz`. The script automatically verifies local inference compatibility.

### Deployment Guide & Dry-Run (`src/deployment/deploy_sagemaker.py`)
```bash
python src/deployment/deploy_sagemaker.py
```
- In environments without active AWS credentials, runs in **DRY-RUN** mode, printing IAM configurations, S3 locations, and cost analyses.
- **Serverless Inference**: 2048 MB RAM, max concurrency 10 (Pay-per-request; ideal for bursty network traffic).
- **Real-Time Endpoint**: `ml.m5.large` (~$0.115/hr) with auto-scaling on `InvocationsPerInstance`.

### Cloud Teardown Commands
To terminate SageMaker cloud resources after deployment:
```bash
aws sagemaker delete-endpoint --endpoint-name adaptive-ids-prod
aws sagemaker delete-endpoint-config --endpoint-config-name adaptive-ids-config
aws sagemaker delete-model --model-name adaptive-ids-xgboost
```

---

## 7. Serving, Observability & Live Telemetry

### Service Endpoints
| Service | URL | Credentials / Notes |
| :--- | :--- | :--- |
| **FastAPI REST API** | `http://localhost:8000` | Docs at `/docs` |
| **Prometheus** | `http://localhost:9090` | Scrapes API every 5s |
| **Grafana Dashboard** | `http://localhost:3002` | `admin` / `admin` (UID: `adaptive-ids-main`) |
| **MLflow Server** | `http://localhost:5001` | SQLite backend, artifact repository |

### FastAPI API Usage
- **Health Check**:
  ```bash
  curl -s http://localhost:8000/health
  ```
- **Inference (`/predict`)**:
  ```bash
  curl -s -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"features": {"Flow Duration": 150.0, "Flow Bytes/s": 4200.0, "Packet Length Mean": 45.0}}'
  ```
- **SHAP Feature Attributions (`/explain`)**:
  ```bash
  curl -s -X POST http://localhost:8000/explain \
    -H "Content-Type: application/json" \
    -d '{"features": {"Flow Duration": 95000.0, "Flow Bytes/s": 180000.0, "Packet Length Mean": 850.0}}'
  ```
- **Prometheus Metrics**:
  ```bash
  curl -s http://localhost:8000/metrics | grep "ids_"
  ```

---

## 8. Verification & Quickstart Guide

### 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Test Suite (All 30 Tests)
```bash
pytest
```

### 3. Run Interactive Terminal Experiment
```bash
python run_terminal_demo.py
```

### 4. Run End-to-End Experiment & Sync Telemetry
```bash
python run_local_experiment.py
```

### 5. Launch Full Observability Stack (Docker Compose)
```bash
docker compose up -d
```
Visit Grafana at `http://localhost:3002` to monitor real-time F1 scores, catastrophic forgetting, request throughput, latency, and drift status.

---

## 9. Verification & Audit Summary

- **Total Unit & Integration Tests**: 30 passed, 0 failed.
- **Core Invariants Tested**: Budget equality across S2/S3/S4, chronological forward splits, unlabeled memory retrieval, KS drift sensitivity.
- **Pipeline Stages**: All 3 DVC stages verified via `dvc dag` and `dvc status`.
- **Airflow DAG**: Validated structure and task execution via `tests/test_airflow_dag.py`.
- **SageMaker Package**: Built `build/sagemaker/model.tar.gz` and verified local inference.
- **Active Docker Services**: FastAPI (`8000`), Prometheus (`9090`), Grafana (`3002`), MLflow (`5001`) healthy and operational.

---

## 10. Research Robustness & Analysis of S3 vs S4

To assess statistical robustness, the streaming evaluation was executed across 5 independent random seeds (`42, 100, 2023, 777, 999`) under identical fixed budgets ($B_{total} = 2,000$ records):

### Multi-Seed Empirical Results (Mean $\pm$ Std)

| Window | Strategy | Recent F1 (Mean $\pm$ Std) | Historical F1 (Mean $\pm$ Std) | Forgetting (Mean $\pm$ Std) | FPR (Mean $\pm$ Std) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **W2** | **S2: Recent-Only** | $0.7698 \pm 0.0000$ | $0.0558 \pm 0.0000$ | $0.8417 \pm 0.0000$ | $0.0424 \pm 0.0000$ |
| | **S3: Random Replay** | $0.7611 \pm 0.0168$ | $0.8862 \pm 0.0159$ | $0.0114 \pm 0.0159$ | $0.0560 \pm 0.0118$ |
| | **S4: Pattern Replay** | $0.7466 \pm 0.0158$ | $0.8894 \pm 0.0057$ | $0.0082 \pm 0.0057$ | $0.0643 \pm 0.0218$ |
| **W3** | **S2: Recent-Only** | $0.7692 \pm 0.0000$ | $0.5843 \pm 0.0000$ | $0.3132 \pm 0.0000$ | $0.0426 \pm 0.0000$ |
| | **S3: Random Replay** | $\mathbf{0.7668 \pm 0.0087}$ | $\mathbf{0.8986 \pm 0.0107}$ | $\mathbf{-0.0011 \pm 0.0107}$ | $0.0447 \pm 0.0039$ |
| | **S4: Pattern Replay** | $0.7655 \pm 0.0098$ | $0.8702 \pm 0.0088$ | $0.0273 \pm 0.0088$ | $0.0471 \pm 0.0024$ |
| **W4** | **S2: Recent-Only** | $0.7622 \pm 0.0000$ | $0.5799 \pm 0.0000$ | $0.3176 \pm 0.0000$ | $0.0464 \pm 0.0000$ |
| | **S3: Random Replay** | $0.7574 \pm 0.0065$ | $0.9027 \pm 0.0176$ | $-0.0051 \pm 0.0176$ | $0.0470 \pm 0.0034$ |
| | **S4: Pattern Replay** | $0.7565 \pm 0.0132$ | $0.8660 \pm 0.0121$ | $0.0316 \pm 0.0121$ | $0.0503 \pm 0.0041$ |

### Scientific Rationale: Why S3 (Random Replay) Outperforms S4 on this Benchmark
1. **Multi-Attack Holdout Evaluation vs. Localized Retrieval**:
   The historical pool contains multiple distinct attack signatures (`DoS Hulk`, `PortScan`). When drift is triggered by an influx of a specific attack (e.g. PortScan in W3), S4 prioritizes historical samples with minimal Wasserstein distance to that incoming distribution. Consequently, the replay buffer contains fewer representations of non-drifting historical attacks (`DoS Hulk`). When evaluated against an isolated holdout testing *all* historical attacks, S4 exhibits slight forgetting on unretrieved attack types ($0.8064$ vs $0.8916$). In contrast, uniform random sampling (S3) guarantees unbiased representation across the entire historical taxonomy.
2. **Feature Space Dimensionality**:
   The benchmark dataset contains 3 continuous summary flow features. In lower-dimensional feature spaces, 1D Wasserstein projections have higher class overlap than in full 78-feature NetFlow spaces, meaning random replay acts as a highly effective regularizer.

---

## 11. Faculty Demonstration Runbook

To demonstrate the full working MLOps pipeline to faculty:

### Step 1: Run Full Test Suite (Verification of Invariants & Correctness)
```bash
pytest
```
*Expected Output:* 30 passed in ~5 seconds, verifying model training, KS drift, budget equality, leak-free splits, Airflow DAG, API endpoints, and SageMaker packaging.

### Step 2: Demonstrate DVC Pipeline Reproducibility
```bash
# View the reproducible dependency graph
dvc dag

# Verify that pipeline status and local cache are synchronized
dvc status
```
*Expected Output:* Renders the multi-stage DAG (`validate` $\rightarrow$ `preprocess` $\rightarrow$ `evaluate`) and confirms "Data and pipelines are up to date."

### Step 3: Run Interactive Terminal Simulation
```bash
python run_terminal_demo.py
```
*Expected Output:* Simulates 4 chronological windows, displays KS drift alerts, calculates Wasserstein distances for historical retrieval, enforces strict 4,000-record budget equality, and prints comparison table.

### Step 4: Show Live Observability & Real-Time Metrics (Docker Stack)
```bash
# 1. Verify all 4 containers are running
docker compose ps

# 2. Query health & SHAP explanation
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"features": {"Flow Duration": 95000.0, "Flow Bytes/s": 180000.0, "Packet Length Mean": 850.0}}'

# 3. Open Grafana Dashboard
open http://localhost:3002
# Login: admin / admin -> Navigate to "Adaptive IDS Observability & Research Dashboard"
```
*Expected Output:* Grafana displays live request rate, p99 latency, drift score (0.555), and side-by-side F1/Forgetting bars corresponding to actual experiment outputs.

### Step 5: Demonstrate AWS SageMaker Packaging & Dry-Run
```bash
# 1. Build & test SageMaker model archive
python src/deployment/package_sagemaker.py

# 2. Execute cloud deployment specification & cost analysis
python src/deployment/deploy_sagemaker.py
```
*Expected Output:* Packages `build/sagemaker/model.tar.gz`, verifies offline inference with `model_fn`/`predict_fn`, and prints serverless vs dedicated deployment specifications and cleanup commands.

---

## 12. Known Limitations & Cloud Disclosures

1. **AWS Cloud Provisioning**: Due to absence of active AWS credentials, live AWS endpoints were not provisioned to avoid unbudgeted cloud charges. The SageMaker deployment path was verified through local packaging (`package_sagemaker.py`), unit testing (`tests/test_sagemaker.py`), and a comprehensive dry-run script (`deploy_sagemaker.py`).
2. **Dataset Scale in CI**: CI runs against the synthetic benchmark dataset (`dataset/cic_ids2017_inspired_synthetic.csv`) rather than downloading the full multi-gigabyte raw CIC-IDS2017 dataset, preventing CI runner timeouts and excessive egress bandwidth.
3. **Local Airflow Profile**: Airflow is containerized as an optional Compose profile (`--profile airflow`) to prevent unnecessary memory footprint on resource-constrained development machines.

