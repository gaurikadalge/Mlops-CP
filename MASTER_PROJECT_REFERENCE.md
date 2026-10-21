# Adaptive Historical Memory for Drift-Aware Intrusion Detection: Master Theoretical & Engineering Reference Manual

---

## Executive Summary

Traditional Machine Learning Intrusion Detection Systems (NIDS) deployed in enterprise networks suffer from statistical performance decay over time due to **Concept Drift** (adversarial mutation of exploit signatures, changing network topologies, and evolving background traffic). Conventional remediation strategies fall into two problematic extremes:
1. **Recent-Only Retraining ($S2$):** Updates the classifier exclusively on recent traffic logs. While fast ($O(1)$ relative to window size), it induces severe **Catastrophic Forgetting** ($F1$ on historical attacks collapses from $\sim 0.90$ down to $\sim 0.05 - 0.58$).
2. **Full-History Retraining:** Appends incoming traffic to an ever-expanding historical log and retrains from scratch. This introduces unbounded $O(N)$ computational complexity, saturates memory buffers, and dilutes emerging low-volume threats within millions of benign background packets.

This project introduces **Pattern-Aware Historical Replay ($S4$)**, an applied Continual Learning architecture governed by a **strictly enforced equal retraining budget** ($B_{total} = 4,000$ records). By combining multi-feature non-parametric drift detection (Kolmogorov-Smirnov Test), compact statistical attack memory banks, and scale-normalized Wasserstein distance retrieval, our system retrieves the most mathematically relevant historical threat signatures to balance the **Stability-Plasticity Dilemma**. The entire system is engineered as an enterprise-grade MLOps ecosystem satisfying all six units of the graduate MLOps curriculum.

---

## 1. Theoretical Framework & Mathematical Formulations

```
Streaming Window (W_t) ───► KS Drift Test (D_stat, p < 0.05) ───► Wasserstein Memory Match ───► Budget Allocation (50/50)
                                                                                                        │
                                                                                                        ▼
Production Model ◄─── Quality Gate (FPR < 5%) ◄─── Forward Eval + Holdout (Forgetting Metric) ◄─── XGBoost Retrain
```

### 1.1 Concept Drift & The Kolmogorov-Smirnov (KS) Test
Concept drift occurs when the joint probability distribution of network features $X$ and labels $y$ changes over time:
$$P_t(X, y) \neq P_{t+1}(X, y)$$

In streaming network flows, true labels $y$ are not available instantaneously. Therefore, we detect **Virtual Drift** (covariate shift $P_t(X) \neq P_{t+1}(X)$) across continuous flow features using the two-sample **Kolmogorov-Smirnov (KS) Test**.

Let $F_{ref}(x)$ and $F_{curr}(x)$ be the empirical cumulative distribution functions (ECDF) of a network feature computed over the reference baseline and the incoming streaming window:
$$F_n(x) = \frac{1}{n} \sum_{i=1}^n \mathbf{1}_{(-\infty, x]}(X_i)$$

The Kolmogorov-Smirnov statistic $D$ is the supremum of the absolute distance between the two distributions:
$$D = \sup_x \left| F_{ref}(x) - F_{curr}(x) \right|$$

Under the null hypothesis $H_0: F_{ref} = F_{curr}$, the scaled statistic converges to the Kolmogorov distribution:
$$\sqrt{\frac{n_{ref} n_{curr}}{n_{ref} + n_{curr}}} D \xrightarrow{d} K$$

A drift alert is triggered when the asymptotic p-value drops below significance across multiple monitored features:
$$\text{Drift Alert} \iff \exists f \in \text{Features} : p_f < \alpha \quad (\alpha = 0.05)$$

---

### 1.2 Mathematical Memory Retrieval: Scale-Normalized Wasserstein Distance
When drift occurs, the system must identify which historical attacks in the memory bank share statistical similarity with the drifted traffic.

Traditional Euclidean distance fails in tabular network telemetry because features possess wildly disparate scales (e.g., `Flow Duration` ranges up to $10^8$ microseconds, whereas `SYN Flag Count` is binary $0/1$). Furthermore, Euclidean distance between mean vectors ignores variance, skewness, and multimodal distributions.

We formulate pattern matching using the **first Wasserstein Distance** ($L_1$ Earth Mover's Distance), scale-normalized by the standard deviation of each historical pattern feature:

Let $u$ represent the empirical 1D distribution of incoming feature $f$, and $v$ represent the stored historical attack distribution. The 1D Wasserstein distance is defined as:
$$W_1(u, v) = \int_{-\infty}^{\infty} |U(x) - V(x)| dx$$
where $U(x)$ and $V(x)$ are the continuous ECDFs of distributions $u$ and $v$.

To prevent high-magnitude features from dominating the metric, we normalize by the historical standard deviation $\sigma_v$ plus a numerical stability parameter $\epsilon = 10^{-6}$:
$$W_{\text{norm}}(u, v) = \frac{W_1(u, v)}{\sigma_v + \epsilon}$$

The composite similarity distance between current window $W_{curr}$ and historical attack pattern $P_k$ across all $M$ numerical features is:
$$\mathcal{D}(W_{curr}, P_k) = \frac{1}{M} \sum_{m=1}^M \frac{W_1(u_m, v_{k, m})}{\sigma_{k, m} + \epsilon}$$

The memory retrieval engine ranks all stored attack profiles and selects the **Top-$K$** patterns with minimal distance:
$$\text{Top-}K = \arg\min_{P_k \in \mathcal{M}}^{(K)} \mathcal{D}(W_{curr}, P_k)$$

---

### 1.3 The Stability-Plasticity Dilemma & Strict Budget Equality
Continual Learning in non-stationary network environments is governed by the **Stability-Plasticity Dilemma**:
* **Plasticity:** The ability of the neural/tree model to adapt to newly emerging threat distributions.
* **Stability:** The ability of the model to retain historical knowledge and resist catastrophic forgetting.

To ensure strict scientific rigor and computational bounded guarantees, all adaptation strategies operate under an **identical, fixed record budget** ($B_{total} = 4,000$ samples):

$$B_{total} = B_{recent} + B_{hist} = 4,000$$

| Strategy | Recent Budget ($B_{recent}$) | Historical Budget ($B_{hist}$) | Sample Selection Mechanism |
| :--- | :---: | :---: | :--- |
| **$S1$: Static Baseline** | $0$ | $4,000$ | Trained once on initial baseline; never retrained. |
| **$S2$: Recent-Only** | $4,000$ ($100\%$) | $0$ ($0\%$) | Uniform subsample from the incoming drifted window. |
| **$S3$: Random Replay** | $2,000$ ($50\%$) | $2,000$ ($50\%$) | $50\%$ recent + $50\%$ uniform random samples from entire historical memory pool. |
| **$S4$: Pattern-Aware** | $2,000$ ($50\%$) | $2,000$ ($50\%$) | $50\%$ recent + $50\%$ split equally among the Top-$K$ Wasserstein-retrieved attack patterns. |

---

### 1.4 Catastrophic Forgetting & Model Quality Gating

#### Catastrophic Forgetting Metric
To measure forgetting without data leakage, we maintain an **isolated historical holdout test set** ($\mathcal{D}_{hist}^{test}$) extracted from the baseline period, containing known attacks (`DoS Hulk`, `PortScan`, `Bot`, `BruteForce`) that are **never** used in retraining.

Let $F1_{base}(\mathcal{D}_{hist}^{test})$ be the initial macro $F1$-score of the baseline model, and $F1_{retrain}(\mathcal{D}_{hist}^{test})$ be the $F1$-score of the adapted model evaluated on that identical holdout:
$$\text{Forgetting} = F1_{base}(\mathcal{D}_{hist}^{test}) - F1_{retrain}(\mathcal{D}_{hist}^{test})$$

* $\text{Forgetting} \approx 0$: Complete retention of historical security knowledge.
* $\text{Forgetting} > 0.30$: Severe catastrophic forgetting (the IDS fails to recognize past exploits).
* $\text{Forgetting} < 0$: Positive backward transfer (retraining on new variations improved detection of older variants).

#### False Positive Rate ($FPR$) & Production Quality Gate
In high-throughput Network Intrusion Detection, a high False Positive Rate causes alert fatigue, overwhelms Security Operations Center (SOC) analysts, and interrupts legitimate business traffic.

$$FPR = \frac{FP}{FP + TN}$$

Before any retrained model candidate $M_{cand}$ is promoted to the MLflow Model Registry and FastAPI serving layer, it must pass a strict two-tier **Quality Gate**:
$$\text{Deploy}(M_{cand}) \iff \begin{cases} F1_{recent}(M_{cand}) \ge 0.70 \\ FPR_{recent}(M_{cand}) \le 0.05 \end{cases}$$

If $M_{cand}$ fails either condition (e.g., aggressive attack replay caused the decision tree to become overly paranoid on normal traffic), the candidate is rejected, an alert is logged in MLflow, and the active production model remains deployed.

---

## 2. Handling Class Imbalance, Dominance Bias & Replay Engineering

Network telemetry presents severe class imbalance: legitimate background traffic (`BENIGN`) typically constitutes $80\% - 99\%$ of raw NetFlow logs, while cyber attacks appear as sparse, bursty anomalies.

```
Raw Network Stream                    Replay Buffer Construction
┌─────────────────────────┐           ┌───────────────────────────────────────────┐
│ BENIGN (90%)            │           │ Recent Drift Window (50% = 2,000 records) │
│ ─────────────────────── │ ────────► ├───────────────────────────────────────────┤
│ Attack Mutations (10%)  │           │ Top-K Attack Signatures (50% = 2,000 rec) │
└─────────────────────────┘           │ (BENIGN strictly excluded from memory)    │
                                      └───────────────────────────────────────────┘
```

### 2.1 Implicit Minority Oversampling (Excluding BENIGN from Historical Memory)
In our architecture, the Historical Pattern Memory Bank stores profiles **exclusively for confirmed attack classes** (`DoS`, `PortScan`, `Bot`, `BruteForce`, `WebAttack`). `BENIGN` traffic is intentionally omitted from the historical memory pool.
* **Mechanism:** When the historical $50\%$ budget ($2,000$ samples) is drawn, it is filled $100\%$ with malicious attack signatures.
* **Impact:** When merged with the recent window (which is predominantly benign), the resulting retraining dataset automatically achieves a dense $\sim 50/50$ or $\sim 60/40$ attack-to-benign ratio. This functions as **Implicit Minority Oversampling** without synthesizing artificial points (like SMOTE), preserving genuine physical NetFlow packet correlations.

### 2.2 Eliminating Class Dominance Bias via Equal Top-$K$ Budget Splitting
Volumetric attacks (like UDP flood or SYN flood) generate millions of packets within seconds, whereas stealthy reconnaissance attacks (like Nmap stealth port scans or slow brute-force) generate only dozens of packets.
* **The Vulnerability in Random Replay ($S3$):** If historical samples are drawn randomly from an unweighted raw buffer, volumetric DoS attacks drown out stealthy port scans, causing the model to forget low-volume attacks.
* **The Solution in Pattern Replay ($S4$):** Once the Top-$K$ patterns are retrieved via Wasserstein distance, the historical budget $B_{hist}$ is allocated in **equal proportions**:
  $$B_{pattern} = \left\lfloor \frac{B_{hist}}{K} \right\rfloor$$
  For $B_{hist} = 2,000$ and $K = 2$, exactly $1,000$ samples are allocated to Pattern 1 and $1,000$ samples to Pattern 2, guaranteeing that low-volume attack classes maintain equal gradient representation in the XGBoost tree booster.

---

## 3. Computational Complexity, Resource Efficiency & Economic Impact

### 3.1 Algorithmic Complexity: $O(1)$ Fixed Budget vs $O(N)$ Unbounded Retraining

Let $N_t$ be the cumulative number of network packets observed up to time $t$, and let $B$ be our fixed retraining budget ($B = 4,000$). For XGBoost with $T$ trees, depth $d$, and $M$ features:

| Parameter | Unbounded Full-History Retraining | Our Budgeted Continual Learning ($S4$) |
| :--- | :---: | :---: |
| **Training Time Complexity** | $O(T \cdot d \cdot M \cdot N_t \log N_t)$ | $\mathcal{O}(T \cdot d \cdot M \cdot B \log B) = \mathbf{\mathcal{O}(1)}$ |
| **Memory Footprint** | Grows linearly with time: $O(N_t \cdot M)$ | Strictly bounded buffer: $\mathcal{O}(B \cdot M) = \mathbf{\mathcal{O}(1)}$ |
| **KS Drift Test Complexity** | — | $\mathcal{O}(M \cdot (n_{ref} \log n_{ref} + n_{curr} \log n_{curr}))$ |
| **Wasserstein Retrieval** | — | $\mathcal{O}(|\mathcal{M}| \cdot M \cdot n \log n)$ where $|\mathcal{M}| = 6$ patterns |

**Empirical Wall-Clock Measurements:**
* Retraining time for $S2$ (Recent-Only): $\mathbf{\sim 0.16\text{s}}$
* Retraining time for $S3$ (Random Replay): $\mathbf{\sim 0.16\text{s}}$
* Retraining time for $S4$ (Pattern Replay): $\mathbf{\sim 0.17\text{s}}$
* Full-History Retraining on million-row CIC-IDS2017: **$45 - 180\text{ minutes}$** per cycle.

### 3.2 Cloud Financial Optimization (AWS SageMaker Analysis)
In high-throughput cybersecurity environments, provisioning continuously running dedicated GPU/high-memory CPU instances ($ml.m5.2xlarge$ at $\$0.384/\text{hr}$) costs $\$276.48/\text{month}$ per inspection cluster.

Our architecture evaluates two distinct cloud serving profiles via [src/deployment/deploy_sagemaker.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/deployment/deploy_sagemaker.py):
1. **Serverless Inference Endpoint (Recommended):**
   * Memory Allocation: $2,048\text{ MB}$, Max Concurrency: $10$.
   * Cost: Billed per millisecond of execution. For bursty network traffic where packet bursts occur intermittently, idle compute cost is **$\$0.00$**.
2. **Real-Time Dedicated Endpoint ($ml.m5.large$):**
   * Base Cost: $\$0.115/\text{hr}$ ($\sim \$82.80/\text{month}$).
   * Configured with Target Tracking Auto-Scaling on metric `InvocationsPerInstance` to dynamically scale horizontally during active DDoS attacks and contract during off-peak hours.

---

## 4. Empirical Benchmark Findings & Scientific Rationale

### 4.1 Multi-Seed Robustness Evaluation (Mean $\pm$ Standard Deviation)
To ensure empirical findings are not an artifact of random seed selection, streaming forward evaluation was executed across 5 independent random seeds ($42, 100, 2023, 777, 999$) under identical $B_{total} = 2,000$ conditions:

| Window | Strategy | Recent $F1$ (Mean $\pm$ Std) | Historical $F1$ (Mean $\pm$ Std) | Catastrophic Forgetting | False Positive Rate ($FPR$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Window 2** | **$S2$: Recent-Only** | $0.7698 \pm 0.0000$ | $0.0558 \pm 0.0000$ | $0.8417 \pm 0.0000$ | $0.0424 \pm 0.0000$ |
| | **$S3$: Random Replay** | $0.7611 \pm 0.0168$ | $0.8862 \pm 0.0159$ | $0.0114 \pm 0.0159$ | $0.0560 \pm 0.0118$ |
| | **$S4$: Pattern Replay** | $0.7466 \pm 0.0158$ | $0.8894 \pm 0.0057$ | $0.0082 \pm 0.0057$ | $0.0643 \pm 0.0218$ |
| **Window 3** | **$S2$: Recent-Only** | $0.7692 \pm 0.0000$ | $0.5843 \pm 0.0000$ | $0.3132 \pm 0.0000$ | $0.0426 \pm 0.0000$ |
| | **$S3$: Random Replay** | $\mathbf{0.7668 \pm 0.0087}$ | $\mathbf{0.8986 \pm 0.0107}$ | $\mathbf{-0.0011 \pm 0.0107}$ | $0.0447 \pm 0.0039$ |
| | **$S4$: Pattern Replay** | $0.7655 \pm 0.0098$ | $0.8702 \pm 0.0088$ | $0.0273 \pm 0.0088$ | $0.0471 \pm 0.0024$ |
| **Window 4** | **$S2$: Recent-Only** | $0.7622 \pm 0.0000$ | $0.5799 \pm 0.0000$ | $0.3176 \pm 0.0000$ | $0.0464 \pm 0.0000$ |
| | **$S3$: Random Replay** | $0.7574 \pm 0.0065$ | $0.9027 \pm 0.0176$ | $-0.0051 \pm 0.0176$ | $0.0470 \pm 0.0034$ |
| | **$S4$: Pattern Replay** | $0.7565 \pm 0.0132$ | $0.8660 \pm 0.0121$ | $0.0316 \pm 0.0121$ | $0.0503 \pm 0.0041$ |

### 4.2 Scientific Analysis: Why Random Replay ($S3$) Competes with Pattern Replay ($S4$)
In scientific research, transparent analysis of empirical behavior is paramount. A key finding of this benchmark is that **$S3$ (Random Replay) slightly outperforms $S4$ (Pattern Replay) on multi-attack holdouts**:
1. **Multi-Attack Holdout Evaluation vs. Localized Boundary Formation:**
   The historical holdout contains diverse attack classes (`DoS`, `PortScan`, `Bot`). When drift is triggered by an influx of a specific mutated attack (e.g., PortScan), $S4$ computes minimal Wasserstein distance and retrieves historical PortScan variants. This constructs sharp decision boundaries around the active threat. However, non-drifting attacks (`DoS`) receive lower representation in that retraining cycle. When tested against a composite holdout evaluating *all* historical attacks, $S4$ exhibits minor retention degradation ($0.87$ vs $0.90$).
2. **Random Replay as a Global Regularizer:**
   Uniform random sampling across the historical buffer guarantees unbiased representation across the entire historical taxonomy. In lower-dimensional feature spaces, this broad historical coverage acts as a strong regularizer that prevents the tree booster from overfitting to the localized geometry of the drifted region.

---

## 5. Complete MLOps Ecosystem (Curriculum Alignment: Units I – VI)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 MLOps Lifecycle & Stack                                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Unit I:   Lifecycle & Invariants  │ GitHub Actions CI/CD (.github/workflows/), Pytest   │
│ Unit II:  Data Versioning & Tracking│ DVC (dvc.yaml, .dvc_remote), MLflow (mlflow.db)    │
│ Unit III: Pipeline Automation     │ Apache Airflow 10-Task DAG (dags/)                 │
│ Unit IV:  Deployment & Monitoring │ Docker Compose, FastAPI, Prometheus, Grafana       │
│ Unit V:   Responsible AI / XAI    │ SHAP TreeExplainer (/explain endpoint)             │
│ Unit VI:  Cloud MLOps             │ AWS SageMaker Container Contract (src/deployment/) │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Unit I: MLOps Lifecycle, Testing & Continuous Integration
* **File:** [.github/workflows/ml_pipeline.yml](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/.github/workflows/ml_pipeline.yml), [tests/](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/tests/)
* **Implementation:** A 30-test suite executed via `pytest` asserting:
  * Budget equality invariants in `test_replay.py`.
  * Zero temporal data leakage in `test_evaluation.py`.
  * Two-sample KS statistical sensitivity in `test_drift.py`.
  * SageMaker container handler contracts in `test_sagemaker.py`.

### Unit II: Data Management, Versioning & Experiment Tracking
* **Files:** [dvc.yaml](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/dvc.yaml), [mlflow.db](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/mlflow.db)
* **DVC Multi-Stage Pipeline:**
  1. `validate`: [src/pipeline/validate_data.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/pipeline/validate_data.py) checks feature non-negativity, missing values, and schema bounds.
  2. `preprocess`: [src/pipeline/preprocess_stage.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/pipeline/preprocess_stage.py) isolates baseline from streaming data and constructs historical memory JSON.
  3. `evaluate`: [src/pipeline/evaluate_stage.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/pipeline/evaluate_stage.py) computes forward evaluation and outputs [outputs/evaluation_metrics.json](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/outputs/evaluation_metrics.json).
* **MLflow Tracking:** Logs parameters (`strategy`, `window_id`, `budget`), metrics (`recent_f1`, `historical_f1`, `forgetting`, `fpr`), and registers model binaries (`model.ubj`).

### Unit III: Automated Pipeline Orchestration (Apache Airflow)
* **File:** [dags/adaptive_ids_workflow.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/dags/adaptive_ids_workflow.py)
* **Architecture:** 10 sequential and branching tasks:
  1. `select_traffic_window` $\rightarrow$ 2. `validate_schema` $\rightarrow$ 3. `detect_drift` $\rightarrow$ 4. `branch_on_drift`
  * If No Drift: $\rightarrow$ `skip_adaptation`
  * If Drift: $\rightarrow$ 5. `retrieve_historical_patterns` $\rightarrow$ 6. `adapt_and_train` $\rightarrow$ 7. `evaluate_forward_and_holdout` $\rightarrow$ 8. `apply_quality_gate` $\rightarrow$ 9. `log_to_mlflow` $\rightarrow$ 10. `update_memory`.

### Unit IV: Production Deployment, Telemetry & Observability
* **Files:** [src/pipeline/serve.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/pipeline/serve.py), [docker-compose.yml](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/docker-compose.yml)
* **Architecture:**
  * **FastAPI Service:** Exposes `/predict`, `/explain`, `/metrics`, `/health`, and `/memory/patterns`.
  * **Prometheus:** Scrapes `/metrics` every 5 seconds. Collects HTTP request rates, latency histograms, drift gauge (`ids_latest_drift_score`), and strategy performance gauges.
  * **Grafana Dashboard:** Visualizes live telemetry, throughput spikes, and research evaluation bars on `http://localhost:3002`.

### Unit V: Responsible AI & Explainability (SHAP)
* **Theory:** Traditional IDS classifiers operate as uninterpretable black boxes. Security analysts cannot distinguish between genuine malicious packet indicators and model bias.
* **Implementation:** Integrates **SHAP (SHapley Additive exPlanations)** based on cooperative game theory:
  $$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N| - |S| - 1)!}{|N|!} (v(S \cup \{i\}) - v(S))$$
  We utilize `shap.TreeExplainer` on the production XGBoost model to provide polynomial-time exact local feature attributions for every prediction via the `/explain` endpoint.

### Unit VI: Cloud MLOps & Production Staging (AWS SageMaker)
* **Files:** [src/deployment/package_sagemaker.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/deployment/package_sagemaker.py), [src/deployment/inference.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/deployment/inference.py), [src/deployment/deploy_sagemaker.py](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/src/deployment/deploy_sagemaker.py)
* **Implementation:** Implements the official AWS SageMaker PyTorch/XGBoost inference contract:
  * `model_fn(model_dir)`: Deserializes the XGBoost model binary.
  * `input_fn(request_body, content_type)`: Validates JSON/CSV against the 11-feature schema.
  * `predict_fn(input_data, model)`: Generates classification and probability scores.
  * `output_fn(prediction, accept)`: Formats standard JSON responses.
  * Packages all artifacts into [build/sagemaker/model.tar.gz](file:///c:/Users/Utkarsh%20Ghom/Documents/VIT/ASSIGNMENTS/Mlops/CP/Mlops-CP/build/sagemaker/model.tar.gz) and verifies local offline inference.

---

## 6. Real-World Simulation Narrative: The 5-Bucket Scenario

To demonstrate this system to a faculty panel or jury, we walk through a simulated chronological data stream of 5 distinct network traffic windows:

### Buckets 1 & 2: Baseline Calibration & Historical Memory Formation
* **Network Reality:** Standard enterprise traffic flowing with normal background `BENIGN` packets interspersed with loud, aggressive attacks (`Loud DoS`, `PortScan`).
* **System Action:** Baseline model $S1$ is trained. The memory bank profiles both attack classes. Historical $F1$ baseline is calibrated ($0.9598$). KS Test indicates no drift ($p > 0.05$).

### Bucket 3: The Mutated Exploit ("Low and Slow" DoS Drift)
* **Network Reality:** The attacker changes tactics to evade rate-limiting filters. Instead of flood spikes, they launch a "Low and Slow" DoS attack with moderate packet lengths and prolonged flow durations ($60\%$ statistical overlap with past DoS).
* **System Action:**
  1. KS Test detects drift: feature distributions diverge ($p < 0.001$).
  2. Memory retrieval computes Wasserstein distance: identifies historical `DoS_Hulk` as the closest mathematical match ($d = 1.0784$).
  3. The system builds a 4,000-sample budget: $2,000$ samples of the new "Low and Slow" traffic + $2,000$ retrieved samples of historical DoS.
  4. Retraining restores recent detection ($F1 \approx 0.9559$) while historical retention remains near baseline ($F1 \approx 0.9613$), yielding **zero catastrophic forgetting** ($\text{Forgetting} = -0.0015$).

### Bucket 4: Return to Normalcy & The False Positive Quality Gate
* **Network Reality:** Attack activity ceases; network logs return to normal benign operation.
* **System Action:** The system validates that the aggressive injection of attack signatures in Bucket 3 did not corrupt the model. The Quality Gate evaluates the False Positive Rate ($FPR = 0.0382 \le 0.05$). The model is proven not to have become paranoid on normal business traffic.

### Bucket 5: The Zero-Day Attack (0% Similarity)
* **Network Reality:** An entirely novel cyber threat (e.g., zero-day exfiltration) hits the network with anomalous packet ratios never before observed in enterprise history.
* **System Action:**
  1. KS Test triggers an emergency drift alert.
  2. Memory retrieval finds no close match (all Wasserstein distances $> 8.0$).
  3. The system gracefully falls back to a **diverse, balanced replay** of all historical attack classes.
  4. The model expands its decision surface to learn the zero-day exploit without collapsing previous defenses.
  5. Security analysts query `/explain` on FastAPI to inspect the SHAP attributions, identifying exactly which abnormal flow features characterize the zero-day exploit.

---

## 7. Faculty Defense & Viva Voce Q&A Cheat Sheet

### Q1: "Why did you choose Wasserstein Distance instead of Euclidean distance for memory retrieval?"
> **Answer:** *"Euclidean distance assumes orthogonal, independent features and measures point-to-point geometric distance between mean vectors, which completely ignores feature variance, multimodal distributions, and packet spread. Furthermore, NetFlow telemetry has features on drastically different scales (e.g., Flow Duration up to $10^8$ vs Flag Count $0/1$). Scale-Normalized Wasserstein Distance computes the true Earth Mover's Distance between 1D probability density functions and normalizes each feature by the historical standard deviation ($\sigma_v + \epsilon$), ensuring scale-invariant, distribution-aware pattern retrieval."*

### Q2: "Why does Random Replay ($S3$) perform so closely to Pattern Replay ($S4$) in your benchmark results?"
> **Answer:** *"This is one of the most interesting scientific insights of our research. When drift occurs due to one specific attack (e.g. PortScan), Pattern Replay concentrates the historical budget on samples closest to that specific attack. While this optimizes the local decision boundary around the active threat, it provides fewer historical samples of unretrieved attacks (like DoS). When evaluated against an isolated composite holdout testing all past attacks simultaneously, Pattern Replay shows slight retention trade-offs. Random Replay provides uniform representation across the entire historical taxonomy, acting as a global regularizer. Both methods, however, successfully prevent catastrophic forgetting compared to recent-only retraining ($F1 \sim 0.87 - 0.90$ vs $0.58$)."*

### Q3: "How does your system prevent temporal data leakage?"
> **Answer:** *"We enforce strict chronological forward evaluation in `src/preprocessing/loader.py`. Incoming streaming windows are sliced along the temporal index. The first 60% of the window is used for adaptation, while the remaining 40% is strictly reserved for unseen forward evaluation. The model never trains on records from future timestamps."*

### Q4: "Why did you use SHAP instead of LIME for the Responsible AI requirement?"
> **Answer:** *"LIME relies on local surrogate linear perturbations, which can be computationally expensive and non-deterministic on tabular data. SHAP (SHapley Additive exPlanations) is grounded in cooperative game theory and satisfies the four fundamental axioms of fairness: Efficiency, Symmetry, Dummy, and Additivity. Because our core classifier is XGBoost, we can use `shap.TreeExplainer`, which computes exact Shapley values in polynomial time rather than exponential sampling time."*

### Q5: "Why did you use a dry-run mode for AWS SageMaker deployment?"
> **Answer:** *"Our codebase implements the complete, production-ready AWS SageMaker Python SDK deployment specification in `src/deployment/deploy_sagemaker.py` and canonical container inference contracts in `src/deployment/inference.py`. Packaging is fully validated via `package_sagemaker.py` and automated unit tests (`test_sagemaker.py`). We utilize dry-run mode in local demonstration environments to eliminate unbudgeted hourly cloud provisioning charges while proving 100% cloud architectural readiness."*
