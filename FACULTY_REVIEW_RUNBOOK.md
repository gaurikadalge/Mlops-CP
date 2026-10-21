# Faculty Review & Demonstration Runbook
**Project:** Adaptive Historical Memory for Drift-Aware Intrusion Detection  
**Target Directory for All Commands:**  
`C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP`

---

## 0. Quick Setup & Environment

Before beginning the demo, open PowerShell as a regular user and ensure you are in the project folder:

```powershell
cd "C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP"
$env:PYTHONIOENCODING="utf-8"
```

---

## 1. Demonstration Roadmap (Overview for Faculty)

> **🚀 Flagship Enterprise React UI (Recommended for Review):**  
> Run `.\run_frontend.ps1` (or `npm run dev --prefix frontend`) to launch the full **SentinelFlow Enterprise React Dashboard** on `http://127.0.0.1:5173`. Built with modern React 19, Tailwind CSS, Lucide icons, and Recharts, it features real-time 5-Bucket cyber streaming controls, animated KS drift distributions, Wasserstein memory affinity ranking, 4,000-sample budget partitions, multi-window Catastrophic Forgetting line charts, an interactive SHAP Responsible AI Lab with flow sliders, and live Docker/Cloud microservice health indicators.

| Step | Topic & Syllabus Unit | Command to Run | What to Open / Show |
| :--- | :--- | :--- | :--- |
| **Flagship UI** | **Production React Frontend** | `.\run_frontend.ps1` | Browser: `http://127.0.0.1:5173` (SentinelFlow React Dashboard) |
| **Streamlit UI** | **Alternative Python UI** | `python -m streamlit run demo_dashboard.py` | Browser: `http://localhost:8501` (Streamlit Dashboard) |
| **Step 1** | **Unit I: Lifecycle & CI/CD** | `python -m pytest` | Terminal test summary (30 tests passing) |
| **Step 2** | **Unit II: Data Management** | `python -m dvc dag` | ASCII DAG in terminal + `outputs/data_validation_report.json` |
| **Step 3** | **Core Research Experiment** | `python run_terminal_demo.py` | Rich interactive terminal with drift alert, Wasserstein distances, budget allocation & F1 table |
| **Step 4** | **Units IV & V: Responsible AI** | `python -m uvicorn src.pipeline.serve:app --port 8000` | Browser: `http://127.0.0.1:8000/docs` + SHAP `/explain` output |
| **Step 5** | **Unit IV: Live Observability** | `docker compose up -d` | Browser: `http://localhost:3002` (Grafana) & `http://localhost:9090` (Prometheus) |
| **Step 6** | **Unit VI: Cloud MLOps** | `python src/deployment/deploy_sagemaker.py` | Terminal SageMaker deployment architecture & `build/sagemaker/model.tar.gz` |

---

## 2. Detailed Step-by-Step Instructions

### STEP 1: Verify Research Invariants & Run Test Suite
* **Syllabus Area:** Unit I (MLOps Lifecycle, Automation & Testing)
* **Directory:** `C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP`
* **Command:**
  ```powershell
  python -m pytest
  ```
* **What it Does:**
  Executes 30 automated unit and integration tests across all components.
* **What to Show Faculty:**
  * Point out that **all 30 tests pass**.
  * Highlight tests:
    * `test_replay.py`: Verifies strict budget equality ($B_{total} = 4,000$ across S2, S3, S4).
    * `test_evaluation.py`: Asserts zero temporal data leakage (chronological train/test split).
    * `test_airflow_dag.py`: Verifies the 10-task Airflow DAG dependency graph.
    * `test_sagemaker.py`: Tests the SageMaker container inference contract.

---

### STEP 2: Demonstrate DVC Data Versioning & Multi-Stage DAG
* **Syllabus Area:** Unit II (Data Management & Pipeline Lineage)
* **Directory:** `C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP`
* **Command:**
  ```powershell
  python -m dvc dag
  ```
* **What it Does:**
  Displays the directed acyclic graph tracking how raw network datasets flow through validation, preprocessing, and evaluation stages.
* **What to Open:**
  Open file [outputs/data_validation_report.json](file:///C:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/outputs/data_validation_report.json) in your code editor.
* **What to Show Faculty:**
  * Explain: *"We use DVC to version datasets independently of Git. Large CSVs are never committed directly. Our `dvc.yaml` defines 3 stages: data validation, historical memory preprocessing, and forward evaluation."*
  * In the JSON report, show the schema checks: feature non-negativity, missing value counts, and class balance.

---

### STEP 3: Run Interactive Live Streaming IDS Simulation
* **Syllabus Area:** Core Research Demonstration
* **Directory:** `C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP`
* **Command:**
  ```powershell
  python run_terminal_demo.py
  ```
* **What it Does:**
  Simulates live streaming network traffic arriving in temporal windows.
* **What Appears on Screen & What to Explain:**
  1. **Baseline Initialization:** Loads initial baseline traffic and deploys Static Model (S1) with Historical F1 $\approx 0.9598$.
  2. **Window 1 Arrival & KS Drift Alert:**
     * The multi-feature **Kolmogorov-Smirnov statistical test** flags significant distribution drift: `[ALERT] DRIFT DETECTED!`.
  3. **Scale-Normalized Wasserstein Distance Table:**
     * The system calculates 1D Wasserstein distances normalized by feature standard deviation across 6 attack patterns (`BruteForce`, `WebAttack`, `Bot`, `DoS_Hulk`, `DoS_Slowloris`, `PortScan`).
  4. **Strict Retraining Budget Split:**
     * Recent Budget: 2,000 samples (50%)
     * Historical Budget: 2,000 samples (50%)
     * Total Retraining Budget: 4,000 samples (100%)
  5. **Final Comparison Table (S2 vs S3 vs S4):**
     * **S2 (Recent-Only):** Adapts to recent data ($F1 \approx 0.9559$) but has no memory mechanism.
     * **S3 (Random Replay) & S4 (Pattern Replay):** Retain high historical performance ($F1 \approx 0.94 - 0.96$) with catastrophic forgetting near zero.

---

### STEP 4: Demonstrate Responsible AI with SHAP & REST API
* **Syllabus Area:** Unit IV (Model Deployment) & Unit V (Responsible AI / Explainability)
* **Directory:** `C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP`

#### 1. Start the API Server in Terminal 1:
```powershell
python -m uvicorn src.pipeline.serve:app --host 127.0.0.1 --port 8000
```
*(Leave this running)*

#### 2. Open in Web Browser:
* **Interactive Swagger Documentation:** Open `http://127.0.0.1:8000/docs`
* Show the interactive endpoints: `/predict`, `/explain`, `/health`, `/metrics`, `/memory/patterns`.

#### 3. Test Live SHAP Attribution in Terminal 2 (PowerShell):
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/explain" -Method Post -ContentType "application/json" -Body '{"features": {"Flow Duration": 95000.0, "Total Fwd Packets": 25.0, "Total Backward Packets": 30.0, "Total Length of Fwd Packets": 4200.0, "Total Length of Bwd Packets": 5100.0, "Flow Bytes/s": 180000.0, "Flow Packets/s": 550.0, "Packet Length Mean": 850.0, "Packet Length Std": 120.0, "SYN Flag Count": 1.0, "ACK Flag Count": 0.0}}' | ConvertTo-Json -Depth 5
```
* **What to Show Faculty:**
  * Show the returned JSON response containing `prediction: 1` (`Attack`), `base_value`, and exact **Shapley feature attributions**.
  * Explain: *"To satisfy Responsible AI requirements, our system uses SHAP TreeExplainer. When an intrusion is detected, security operators see exactly which flow metrics (e.g. abnormal `Flow Bytes/s`) drove the classifier's decision."*

---

### STEP 5: Live Telemetry & Observability Stack (Docker, Prometheus, Grafana)
* **Syllabus Area:** Unit IV (Dynamic Monitoring & Observability)
* **Directory:** `C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP`

#### 1. Launch Containers (Requires Docker Desktop Running):
```powershell
docker compose up -d
```

#### 2. Open in Web Browser:
| Service | URL | Credentials / Navigation |
| :--- | :--- | :--- |
| **Grafana Dashboard** | `http://localhost:3002` | User: `admin` / Password: `admin`<br>Navigate to: **Dashboards** $\rightarrow$ **Adaptive IDS Observability & Research Dashboard** |
| **Prometheus Targets** | `http://localhost:9090/targets` | Shows `api-server` scrape endpoint in state `UP` |
| **MLflow Tracking UI** | `http://localhost:5001` | Displays tracked runs, parameters, metrics & model registry |

* **What to Show Faculty in Grafana:**
  * **Top Metrics Panel:** Current Model Strategy (`S4_PatternReplay`), Active Run ID, Latest Drift Score.
  * **Operational Health:** Live HTTP Request Throughput and Latency Histogram.
  * **Research Evaluation Bars:** Recent F1 vs Historical F1 vs Catastrophic Forgetting across S1–S4.

---

### STEP 6: AWS SageMaker Packaging & Cloud Architecture
* **Syllabus Area:** Unit VI (Cloud MLOps)
* **Directory:** `C:\Users\Utkarsh Ghom\Documents\VIT\ASSIGNMENTS\Mlops\CP\Mlops-CP`

#### 1. Test Package Creation:
```powershell
$env:PYTHONIOENCODING="utf-8"
python src/deployment/package_sagemaker.py
```
* **What it Does:**
  Bundles the latest trained model artifact (`model.ubj`) and the canonical SageMaker inference script (`code/inference.py`) into `build/sagemaker/model.tar.gz`. It then extracts the archive into a temporary directory and tests `model_fn`, `input_fn`, `predict_fn`, and `output_fn` locally.
* **What to Show Faculty:**
  Point out that local offline inference passed: `✓ model_fn`, `✓ input_fn`, `✓ predict_fn`, `✓ output_fn`.

#### 2. Run Deployment Specification & Cost Analysis:
```powershell
python src/deployment/deploy_sagemaker.py
```
* **What to Show Faculty:**
  * **Dry-Run Cloud Architecture:** Show the printed cloud specification:
    * Target S3 URI: `s3://my-mlops-ids-bucket/adaptive-ids/models/model.tar.gz`
    * Serverless Inference Configuration (2048 MB, Concurrency 10) for bursty traffic.
    * Dedicated Real-Time Endpoint Configuration (`ml.m5.large`, ~$0.115/hr) with auto-scaling.
    * Exact AWS CLI deployment and teardown commands.
  * Explain: *"We implemented the complete SageMaker SDK deployment pipeline and validated container compatibility locally to demonstrate cloud readiness without incurring unbudgeted live AWS charges."*

---

## 3. Anticipated Faculty Questions & Winning Answers

### Q1: "Why does Random Replay (S3) perform similarly or slightly better than Pattern Replay (S4) on this benchmark?"
> **Answer:**  
> *"Our historical memory contains multiple distinct attack types (DoS, PortScan, Botnet, WebAttack). When drift is triggered by an influx of a specific attack, Pattern Replay concentrates the historical budget on patterns mathematically closest (minimal Wasserstein distance) to that incoming traffic. This creates sharp decision boundaries around the active threat, but fewer historical samples of unrelated attacks are included in that specific retrain. Random Replay provides a uniform spread across all historical attack families, acting as a broad regularizer. In our multi-seed robustness analysis (documented in Section 10 of README.md), both methods successfully prevent catastrophic forgetting ($0.87 - 0.90$ retention vs $0.58$ for recent-only)."*

### Q2: "How is data leakage prevented between training and evaluation?"
> **Answer:**  
> *"We strictly enforce chronological forward splitting. In `src/preprocessing/loader.py`, incoming streaming windows are partitioned such that the first 60% of the window is used for adaptation, and the remaining 40% is reserved for future forward evaluation. The model never trains on future timestamps."*

### Q3: "How does the system prevent the retrained model from becoming overly aggressive or paranoid?"
> **Answer:**  
> *"Through the Model Quality Gate implemented in `src/models/validate.py` and integrated into Step 8 of the Airflow DAG. If retraining on attack data causes the False Positive Rate (FPR) on benign background traffic to exceed 5%, the candidate model is rejected and the previous production model remains deployed."*

### Q4: "How does this satisfy the Responsible AI requirement?"
> **Answer:**  
> *"In Unit V, rather than treating XGBoost as a black box, we integrated SHAP (SHapley Additive exPlanations) directly into the FastAPI serving layer (`/explain`). For every predicted packet, security analysts receive exact feature attributions explaining which metrics caused the alert."*
