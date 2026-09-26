# MLOps & Integration Plan (Phase 9)

With the core machine learning logic (Phases 1-8) successfully implemented and validated locally, this document outlines the concrete steps required to complete Phase 9. The goal is to transform the local Python scripts into a reproducible, production-ready experimental MLOps pipeline.

## 1. MLflow Tracking Integration
**Objective:** Replace console prints with a centralized tracking server to record experiment parameters, metrics, and models.

**Implementation Steps:**
- **Instrumentation:** Update `src/pipeline/run_cycle.py` to use `mlflow.start_run()`.
- **Parameter Logging:** Log window IDs, adaptation strategies (S1, S3, S4), Top-K configurations, and total data budgets using `mlflow.log_params()`.
- **Metric Logging:** Log continuous metrics like Recent F1, Historical F1, Forgetting, FPR, Drift Score, and Retraining Time using `mlflow.log_metrics()`.
- **Model Registry:** Save the accepted candidate XGBoost models into the MLflow Model Registry using `mlflow.xgboost.log_model()`.

## 2. Containerization (Docker)
**Objective:** Ensure identical execution environments for all team members and eliminate "works on my machine" issues.

**Implementation Steps:**
- **Dockerfile:** Create a Docker image extending a base Python image. It will install all requirements (`xgboost`, `pandas`, `scipy`, `mlflow`) and copy the `src/` directory.
- **Docker Compose (`docker-compose.yml`):** Define a multi-container setup:
  - Service 1: **MLflow Tracking Server** (UI accessible on `localhost:5000`).
  - Service 2: **Experiment Runner** (Runs the `run_local_experiment.py` script and sends logs to the MLflow server).

## 3. Automated Unit Testing
**Objective:** Guarantee the reliability of the core algorithms before integrating them into a CI/CD loop.

**Implementation Steps:**
- **Test Framework:** Use `pytest` to execute tests in the `tests/` directory.
- **Drift Tests (`test_drift.py`):** Generate two synthetic arrays from the same distribution (assert no drift) and two from different distributions (assert drift detected).
- **Memory Tests (`test_memory.py`):** Mock a current profile and assert that the retrieval algorithm accurately returns the configured Top-K profiles based on calculated distances.
- **Budget Tests (`test_replay.py`):** Assert that `adapt_pattern_replay()` strictly outputs `len(X_train) == TOTAL_BUDGET` regardless of the Top-K similarities.

## 4. Continuous Integration / Continuous Deployment (CI/CD)
**Objective:** Automate code validation on every pull request to protect the main branch.

**Implementation Steps:**
- **GitHub Actions (`.github/workflows/ml_pipeline.yml`):**
  - **Trigger:** On push to `main` or pull requests.
  - **Jobs:**
    1. Set up Python environment.
    2. Run `pytest` to validate unit tests.
    3. Run a lightweight integration test (run the pipeline on a small 1,000-record dataset to ensure end-to-end execution doesn't crash).
  - *Note:* We will purposefully exclude the massive million-record dataset from GitHub Actions to prevent CI timeouts.

## 5. Final Demonstration Preparation
**Objective:** Provide a clear, teacher-facing visualization of the project's success.

**Implementation Steps:**
- Create `notebooks/03_results_analysis.ipynb`.
- Connect this notebook directly to the MLflow tracking server API.
- Pull the tracked runs for S3 (Random Replay) and S4 (Pattern Replay) operating on the same windows.
- Generate the final comparison table requested in the initial project spec:
  `| Strategy | Recent F1 | Historical F1 | Forgetting | FPR | Training Time |`
