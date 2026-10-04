# MLOps Comprehensive Architecture & Narrative Plan

This document serves as the master blueprint for the **Adaptive Historical Memory for Drift-Aware IDS** project. It outlines our system architecture, the tools we use, the mathematical logic driving our novelty, and a concrete real-world simulation narrative to present to the jury.

---

## 1. System Components & Tooling Roles

Our project isn't just a machine learning script; it is a fully automated, production-ready MLOps pipeline.

| Tool / Technology | Role in our Pipeline |
| :--- | :--- |
| **XGBoost** | The core Machine Learning classifier used for detecting network intrusions. Chosen for its high performance on tabular data and fast retraining times. |
| **Kolmogorov-Smirnov (KS) Test** | Statistical engine running in `src/drift/`. Monitors streaming data and mathematically detects concept drift (distribution shifts) without relying on manual thresholds. |
| **MLflow** | The centralized tracking server. It automatically logs our experiment metrics (F1, FPR, Retraining Time) and manages the Model Registry (storing our retrained XGBoost models). |
| **Streamlit & Plotly** | Our frontend demonstration UI (`demo_dashboard.py`). Translates raw data into interactive visualizations (Radar Charts, Donut Charts, Time-Series) to make the ML mechanics visible to the jury. |
| **Docker & Docker Compose** | Containerization. Ensures that our MLflow server, FastAPI serving endpoint, and training pipelines run identically on any machine without setup issues. |
| **GitHub Actions & Pytest** | Our CI/CD loop. Automatically runs unit tests on every pull request to ensure our math (drift detection, data budgeting) doesn't break when we push new code. |
| **FastAPI / Uvicorn** | Model serving infrastructure. Wraps our best MLflow-registered model in a REST API so external applications can send network logs and receive real-time predictions. |

---

## 2. Core Logic: How Our Novelty Works

Standard adaptive models suffer from **Catastrophic Forgetting** (they learn new threats but forget old ones). We solve this using **Pattern-Aware Replay (Strategy 4)**.

1. **Drift Detection:** As network "windows" (buckets of traffic) stream in, the KS-Test compares the new data to historical data. If the p-value drops below 0.05 across multiple features, drift is declared.
2. **Statistical Profiling:** The new drifted window is converted into a mathematical fingerprint (mean and standard deviation).
3. **Targeted Memory Retrieval:** We compare the new fingerprint against our historical memory bank. Using **Z-Score Normalized Distance**, we find the Top-K mathematically similar historical attacks.
4. **Budgeted Replay (Handling Imbalance & Bias):** We enforce a strict total compute budget (e.g., 4,000 samples). 
   - **50% (Plasticity):** Current drifted data.
   - **50% (Stability):** Top-K historical attacks divided equally. By purposely excluding BENIGN traffic from the historical replay, we perform *implicit minority oversampling*, solving the severe class imbalance in network traffic. Dividing the historical budget equally among the Top-K attacks solves *class dominance bias* (ensuring huge volumetric attacks don't drown out stealthy attacks).
5. **Quality Gate:** Before deploying the newly trained model, we check if the injected attack data made the model too "paranoid" (causing a spike in False Positive Rate). If it fails the gate, the old model is kept.

---

## 3. The Real-Life Simulation Narrative (Jury Demo)

To clearly demonstrate our system to the jury, we will walk them through a simulated 5-bucket data stream.

### Bucket 1 & 2: The Baseline (Normalcy)
*   **The Situation:** Network traffic is flowing normally. We see standard `BENIGN` traffic mixed with known attacks (e.g., standard loud DoS attacks).
*   **System Reaction:** The baseline XGBoost model handles this easily. The KS-Test confirms the distributions match our training data. **No drift detected.** The model remains stable and fast.

### Bucket 3: The Mutated Threat (The 60% Similarity Event)
*   **The Situation:** The attacker realizes they are being blocked. They change tactics, launching a "Low and Slow" DoS attack. It evades standard rules.
*   **System Reaction:** 
    1. **Drift Detected:** The KS-Test immediately flags a distribution shift in feature `Flow Bytes/s`.
    2. **Retrieval:** The system profiles the new threat and checks memory. It finds a **50-60% similarity** with the historical loud DoS attack. 
    3. **Retraining:** The system dynamically builds a training dataset: 50% new "Low and Slow" data + 50% retrieved historical loud DoS data. 
    4. **Result:** The model's accuracy on the new threat skyrockets, *without forgetting the old loud DoS attack*, because we explicitly reinforced the boundary between them.

### Bucket 4: Return to Normalcy (The Stability Check)
*   **The Situation:** The attack stops. Normal `BENIGN` traffic resumes.
*   **System Reaction:** We prove to the jury that our aggressive retraining in Bucket 3 didn't ruin the model. The **Quality Gate** metrics show that the False Positive Rate (FPR) remains low. The model didn't become "paranoid" despite being injected with heavy attack data in Bucket 3.

### Bucket 5: The Zero-Day Exploit (The 0% Similarity Event)
*   **The Situation:** A completely novel, never-before-seen attack (e.g., a massive Botnet infiltration) hits the network. It shares **0% similarity** with anything in our memory bank.
*   **System Reaction:** 
    1. **Drift Detected:** Huge statistical divergence triggers the alarm.
    2. **Retrieval:** The memory bank returns low similarity scores across the board. 
    3. **Retraining:** Because there is no strong pattern match, the system pulls a *diverse* mix of random historical attacks to fill the 50% historical budget.
    4. **Result:** The model learns the new Zero-Day threat rapidly while keeping a broad, generalized defense against past threats. 

---

## 4. Current Status & Next Steps

### Where Are We Currently?
*   ✅ **Core ML Logic:** Drift detection, Memory Profiling, and Pattern-Aware Replay are fully implemented and functional.
*   ✅ **Visualization:** The Streamlit interactive dashboard (`demo_dashboard.py`) is complete, featuring Plotly visualizations for Concept Drift, Radar Charts for pattern matching, and Catastrophic Forgetting line charts.
*   ✅ **Containerization & API:** Docker-compose and FastAPI serving endpoints are integrated.
*   ✅ **Version Control:** Repository is cleaned up (legacy `adaptive-ids` folder removed) and successfully pushed to the main GitHub repository.

### What Needs to Be Done (Next Steps)?
1. **GitHub Actions CI/CD:** Ensure the `.github/workflows/ml_pipeline.yml` is active and successfully passing the `pytest` suite on the repository.
2. **Notebook Analysis:** Finalize `notebooks/03_results_analysis.ipynb` to pull MLflow logs and generate the final static comparison table requested by the grading rubric.
3. **Dry Run the Demo:** The team needs to practice running the simulation via `demo_dashboard.py` and reciting the "Bucket 1-5 Narrative" to ensure smooth handoffs during the presentation.
