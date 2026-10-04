# MLOps Comprehensive Architecture & Narrative Plan (Syllabus Aligned)

This document serves as the master blueprint for the **Adaptive Historical Memory for Drift-Aware IDS** project. It outlines our system architecture, the tools we use to meet the full MLOps course syllabus, the mathematical logic driving our novelty, and a concrete real-world simulation narrative to present to the jury.

---

## 1. System Components & Tooling Roles (Full MLOps Stack)

Our project implements a complete, production-ready MLOps pipeline covering every syllabus unit.

| Tool / Technology | Role in our Pipeline (Syllabus Unit) |
| :--- | :--- |
| **DVC (Data Version Control)** | Tracks data lineage and versions our massive network datasets, linking data states to git commits. *(Unit II: Data Management)* |
| **Great Expectations** | Validates incoming data streams to ensure schema integrity and feature bounds before models train on it. *(Unit II: Data Management)* |
| **Apache Airflow** | Orchestrates our entire adaptation pipeline (data extraction, training, drift detection, and deployment) as automated DAGs. *(Unit III: Pipeline Automation)* |
| **MLflow** | The centralized tracking server. Automatically logs experiment metrics and manages our Model Registry. *(Unit II: Data Management)* |
| **Prometheus & Grafana** | Replaces Streamlit as our enterprise-grade dynamic monitoring dashboard. Prometheus scrapes real-time metrics from our API, and Grafana visualizes the drift alerts, FPR, and Catastrophic Forgetting live. *(Unit IV: Deployment)* |
| **FastAPI & Docker** | Wraps our best MLflow-registered model in a REST API and containerizes the entire ecosystem for reproducible deployments. *(Unit IV: Deployment)* |
| **SHAP (SHapley Additive exPlanations)** | Provides Global and Local feature importance to explain exactly *why* our model flagged an intrusion. *(Unit V: Responsible AI)* |
| **AWS SageMaker** | Demonstrates cloud capabilities by deploying our Dockerized FastAPI containers to SageMaker Endpoints for scalable cloud inference. *(Unit VI: Cloud MLOps)* |

---

## 2. Core Logic: How Our Novelty Works

Standard adaptive models suffer from **Catastrophic Forgetting** (they learn new threats but forget old ones). We solve this using **Pattern-Aware Replay (Strategy 4)**.

1. **Drift Detection:** The KS-Test monitors data streams. If the p-value drops below 0.05, drift is mathematically declared.
2. **Statistical Profiling:** The new drifted window is converted into a mathematical fingerprint (mean and standard deviation).
3. **Targeted Memory Retrieval:** We compare the new fingerprint against our historical memory bank using **Z-Score Normalized Distance** to find the Top-K mathematically similar historical attacks.
4. **Budgeted Replay (Handling Imbalance & Bias):** We enforce a strict total compute budget (e.g., 4,000 samples):
   - **50% (Plasticity):** Current drifted data.
   - **50% (Stability):** Top-K historical attacks divided equally.
   *(This implicit minority oversampling solves severe network class imbalance).*
5. **Quality Gate:** Before Airflow allows the deployment of the newly trained model, it checks if the injected attack data caused a spike in False Positive Rate (FPR).

---

## 3. The Real-Life Simulation Narrative (Jury Demo via Grafana)

To clearly demonstrate our system to the jury, we will trigger our **Airflow DAG** to simulate a 5-bucket data stream. The jury will watch the system react in real-time on our **Grafana Dashboard**.

### Bucket 1 & 2: The Baseline (Normalcy)
*   **The Situation:** Normal traffic flows. 
*   **System Reaction:** Airflow processes the buckets. Grafana shows a flat, stable drift metric. SHAP plots show the model relies on standard port metrics to classify traffic.

### Bucket 3: The Mutated Threat (The 60% Similarity Event)
*   **The Situation:** A "Low and Slow" DoS attack hits, designed to evade detection.
*   **System Reaction:** 
    1. **Grafana Alert:** The KS-Test metric spikes on the Grafana dashboard. Drift is detected.
    2. **Retrieval & Retraining:** The Airflow DAG triggers the retraining loop. Memory retrieval finds a 50-60% similarity with an old, loud DoS attack. 
    3. **Result:** The model retrains on the 50/50 mix. Grafana shows accuracy on the new threat skyrocketing, while the line chart for "Historical F1" remains stable (proving no forgetting).

### Bucket 4: Return to Normalcy (The Stability Check)
*   **The Situation:** The attack stops. Normal traffic resumes.
*   **System Reaction:** We show the jury the **Grafana FPR (False Positive Rate) gauge**. The aggressive retraining in Bucket 3 didn't make the model paranoid—the FPR remains safely in the green zone.

### Bucket 5: The Zero-Day Exploit (The 0% Similarity Event)
*   **The Situation:** A completely novel attack (0% similarity) hits the network. 
*   **System Reaction:** 
    1. Grafana alerts a massive distribution shift.
    2. Because there is no strong pattern match, our logic pulls a *diverse* mix of historical attacks to fill the 50% budget.
    3. **SHAP Verification:** We pull up the SHAP UI. We prove to the jury that the newly trained model is looking at entirely new features (e.g., payload sizes) to identify this zero-day exploit, demonstrating Responsible AI explainability.

---

## 4. Current Status & Implementation Roadmap

We are currently pivoting our architecture to meet the strict syllabus requirements outlined in the course gap analysis. 

### Phase 1: Data Versioning & Validation (Unit II)
- [ ] Initialize **DVC** to track the `dataset/` directory.
- [ ] Integrate **Great Expectations** into `src/preprocessing/loader.py` to validate data schema and bounds before model consumption.

### Phase 2: Pipeline Orchestration with Airflow (Unit III)
- [ ] Create `dags/adaptive_ids_pipeline.py`.
- [ ] Refactor our `run_local_experiment.py` into distinct Airflow tasks (Extract/Validate -> Train Baseline -> Detect Drift/Adapt -> Register Model).

### Phase 3: Responsible AI & Explainability (Unit V)
- [ ] Implement `src/evaluation/explainability.py` using **SHAP**.
- [ ] Add an `/explain` endpoint to our FastAPI service to return live feature importance to the user.

### Phase 4: Dynamic Monitoring & Dashboards (Unit IV)
- [ ] **Deprecate Streamlit.**
- [ ] Instrument FastAPI with `prometheus-fastapi-instrumentator`.
- [ ] Add **Prometheus** and **Grafana** services to `docker-compose.yml` and build the live monitoring dashboard.

### Phase 5: Cloud MLOps (Unit VI)
- [ ] Write a deployment script using the **AWS SageMaker Python SDK**.
- [ ] Prepare documentation for pushing the Dockerized FastAPI app to Amazon ECR and serving it via SageMaker Endpoints.

### Phase 6: CI/CD Finalization (Units III & IV)
- [ ] Update GitHub Actions (`.github/workflows/ml_pipeline.yml`) to perform a `dvc pull` before running pytest.
- [ ] Add a CD step that triggers the SageMaker deployment on push to `main`.
