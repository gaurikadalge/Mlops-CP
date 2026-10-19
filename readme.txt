Absolutely. Below is a **complete implementation-spec Markdown file** you can give directly to your team. It assumes the **CIC-IDS2017 dataset is already prepared** and focuses on building the actual system.

# Adaptive Historical Memory for Drift-Aware Intrusion Detection

## 1. Project Overview

### Project Title

**Adaptive Historical Memory for Drift-Aware Intrusion Detection**

### Project Type

Machine Learning + MLOps + Cybersecurity

### Primary Application

**Intrusion Detection System (IDS) under evolving network traffic patterns**

---

# 2. Problem Description

Traditional machine-learning-based Intrusion Detection Systems are trained using historical network traffic. Their performance can degrade when the statistical distribution of incoming network traffic changes over time.

This is a **data drift** problem.

For example, an IDS may initially learn traffic patterns associated with:

* DoS attacks
* Port scans
* Botnet activity
* Brute-force attacks
* Web attacks

As the network environment changes, new traffic patterns may appear.

The deployed model can then become stale.

```text
Historical Network Traffic
          ↓
       XGBoost
          ↓
      IDS Model
          ↓
   New Network Traffic
          ↓
 Distribution Changes
          ↓
     Model Degradation
```

The conventional response is to retrain the model.

However, there are three competing approaches:

### Approach 1 — Recent-only retraining

Train only on the latest data.

```text
Recent Data
     ↓
  XGBoost
```

Advantages:

* Low computational cost
* Quickly adapts to new traffic

Problem:

* Can forget previously learned attack patterns

---

### Approach 2 — Full historical retraining

Train using all historical data plus recent data.

```text
All Historical Data
        +
    Recent Data
        ↓
      XGBoost
```

Advantages:

* Better historical knowledge retention

Problems:

* Increasing computational cost
* Large training dataset
* Much historical data may be irrelevant to the current drift

---

### Approach 3 — Random historical replay

Select a fixed amount of historical data randomly.

```text
Historical Data
      ↓
Random Sampling
      +
Recent Data
      ↓
XGBoost
```

This reduces the training cost but does not consider whether the selected historical data is relevant to the current drift.

---

# 3. Proposed Approach

The proposed system investigates:

> **Can historical samples be selected according to their relevance to the currently observed drift, rather than randomly, while keeping the same retraining-data budget?**

The system maintains a compact **Historical Pattern Memory**.

When drift is detected:

```text
Incoming Traffic
       ↓
Drift Detection
       ↓
Current Drift Distribution
       ↓
Compare with Historical Memory
       ↓
Retrieve Relevant Patterns
       ↓
Recent Data
       +
Relevant Historical Data
       ↓
XGBoost Retraining
       ↓
Validation
       ↓
Accept / Reject Model
```

---

# 4. Important Positioning

The project is **not claiming to invent**:

* drift detection
* automated retraining
* XGBoost
* replay
* continual learning
* MLOps

Existing MLOps platforms already provide drift monitoring and automated workflow integration.

Similarly, replay-based continual-learning approaches already exist.

The project focuses on a narrower research question:

> **At an equivalent retraining-data budget, does selecting historical samples according to their relevance to the observed drift preserve more historical knowledge than random historical replay while maintaining recent-threat detection?**

---

# 5. Research Question

### Primary Research Question

> **At an equivalent retraining-data budget, does pattern-aware historical replay preserve more historical intrusion-detection knowledge than random historical replay while maintaining performance on recent traffic?**

### Secondary Questions

1. Does pattern-aware replay reduce forgetting?
2. Can comparable detection performance be achieved with fewer historical samples?
3. How does historical-memory size affect performance?
4. Does bias-controlled sampling improve the result?
5. What is the computational cost of each adaptation strategy?

---

# 6. Hypotheses

### H1

Pattern-aware historical replay will provide better historical-attack retention than random historical replay under the same retraining-data budget.

### H2

Pattern-aware replay will maintain competitive performance on recent attacks.

### H3

Selective historical replay will require less data and training computation than full-history retraining.

### H4

Bias-control mechanisms may improve performance when retrieved historical patterns are class-imbalanced.

These are **hypotheses**, not predetermined results.

---

# 7. System Scope

## Included

* CIC-IDS2017
* Chronological data processing
* XGBoost
* KS-based drift detection
* Historical pattern memory
* Pattern similarity
* Historical sample retrieval
* Fixed retraining-data budget
* Four experimental strategies
* Model validation
* MLflow experiment tracking
* Docker
* GitHub Actions
* Automated pipeline

## Initially excluded

* Transformers
* Deep reinforcement learning
* Online/incremental XGBoost
* Neural embeddings
* Knowledge graphs
* Complex semantic retrieval
* Ensemble IDS
* Multiple simultaneous drift detectors
* Meta-learning for predicting data allocation
* Automatic selection among completely different adaptation algorithms

Keep the first implementation narrow.

---

# 8. System Architecture

```text
                         ┌──────────────────┐
                         │  Network Traffic │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Preprocessing    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Drift Monitor    │
                         │ KS Test          │
                         └────────┬─────────┘
                                  │
                         ┌────────┴─────────┐
                         │                  │
                       No Drift           Drift
                         │                  │
                         ▼                  ▼
                    Prediction      Drift Characterization
                                            │
                                            ▼
                                   Historical Memory
                                            │
                                            ▼
                                   Pattern Similarity
                                            │
                                            ▼
                                  Relevant Historical
                                      Samples
                                            │
                                            ▼
                                  Fixed Data Budget
                                            │
                                            ▼
                                      XGBoost
                                            │
                                            ▼
                                   Model Validation
                                            │
                              ┌─────────────┴────────────┐
                              │                          │
                           Reject                     Accept
                              │                          │
                         Keep old model           Register model
                                                         │
                                                         ▼
                                                  Update Memory
```

---

# 9. Experimental Strategies

The project must implement four systems.

## S1 — Static Model

Train once.

```text
Initial Training
       ↓
    XGBoost
       ↓
Production
```

No adaptation occurs.

Purpose:

> Establish how performance changes without adaptation.

---

## S2 — Recent-only

When drift is detected:

```text
Recent Window
     ↓
XGBoost Retraining
```

Purpose:

> Measure the benefit and forgetting associated with purely recent adaptation.

---

## S3 — Random Historical Replay

```text
Historical Dataset
       ↓
Random Sampling
       ↓
Recent Data + Random Historical
       ↓
XGBoost
```

Purpose:

> Establish the baseline for historical replay.

---

## S4 — Pattern-aware Historical Replay

```text
Current Drift
     ↓
Compare with historical profiles
     ↓
Top-K relevant patterns
     ↓
Retrieve historical samples
     ↓
Recent + relevant historical
     ↓
XGBoost
```

Purpose:

> Test whether drift-relevant historical selection is better than random replay.

---

# 10. Critical Experimental Constraint

S3 and S4 **must use exactly the same retraining-data budget**.

For example:

```text
Total retraining budget = 100,000 records
```

### Random Replay

```text
50,000 recent
+
50,000 random historical
=
100,000
```

### Pattern-aware Replay

```text
50,000 recent
+
50,000 relevant historical
=
100,000
```

The difference is **only the historical selection mechanism**.

This is one of the most important controls in the project.

---

# 11. Dataset Assumption

The dataset is already prepared.

Expected format:

```text
data/
└── processed/
    ├── train.csv
    ├── ...
```

The processed data should contain:

* numerical network-flow features
* attack/benign label
* timestamp or preserved chronological order

Do not randomly shuffle the entire dataset before creating temporal windows.

---

# 12. Chronological Experiment Design

The system should simulate a continuously operating IDS.

Conceptually:

```text
TIME ──────────────────────────────────────────────→

Initial Training
       │
       ▼
──────────────┬──────────────┬──────────────┬────────────
              │              │              │
           Window 1       Window 2       Window 3
              │              │              │
           Monitor        Monitor        Monitor
              │              │              │
            Drift?        Drift?        Drift?
```

The exact window sizes should be determined experimentally.

Do **not** artificially create a small number of drift points just to make the demo work.

Evaluate the feasible chronological windows and identify actual drift events.

---

# 13. Folder Structure

Use the following structure.

```text
adaptive-ids/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── windows/
│   └── memory/
│
├── configs/
│   ├── config.yaml
│   └── experiments.yaml
│
├── src/
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── validation.py
│   │
│   ├── drift/
│   │   ├── __init__.py
│   │   ├── ks_detector.py
│   │   └── drift_score.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── build_memory.py
│   │   ├── profile.py
│   │   └── retrieve.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── validate.py
│   │
│   ├── adaptation/
│   │   ├── __init__.py
│   │   ├── recent_only.py
│   │   ├── random_replay.py
│   │   └── pattern_replay.py
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── forgetting.py
│   │   └── comparison.py
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── run_cycle.py
│   │
│   └── utils/
│       ├── io.py
│       ├── logging.py
│       └── seed.py
│
├── experiments/
│   ├── baseline/
│   ├── replay/
│   ├── pattern_replay/
│   └── results/
│
├── models/
│   ├── checkpoints/
│   └── registry/
│
├── tests/
│   ├── test_drift.py
│   ├── test_memory.py
│   ├── test_replay.py
│   └── test_model.py
│
├── notebooks/
│   ├── 01_dataset_analysis.ipynb
│   ├── 02_drift_analysis.ipynb
│   └── 03_results_analysis.ipynb
│
├── .github/
│   └── workflows/
│       └── ml_pipeline.yml
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 14. Configuration

Keep experimental parameters outside the code.

Example:

```yaml
dataset:
  path: data/processed/dataset.csv
  label_column: Label
  timestamp_column: Timestamp

model:
  type: xgboost
  objective: binary:logistic
  eval_metric: logloss

drift:
  method: ks
  p_value: 0.05
  min_drifted_features: 3

memory:
  samples_per_pattern: 4000
  top_k: 2

adaptation:
  total_budget: 100000
  recent_fraction: 0.5
  historical_fraction: 0.5

mlflow:
  experiment_name: adaptive_ids
```

These values are **initial configuration values**, not claimed optimal values.

---

# 15. Module 1 — Data Pipeline

### File

```text
src/preprocessing/loader.py
```

Responsibilities:

1. Load prepared dataset.
2. Validate columns.
3. Remove invalid/infinite values.
4. Separate features and labels.
5. Preserve chronological order.
6. Generate windows.

Expected interface:

```python
dataset = load_dataset(path)

windows = create_temporal_windows(
    dataset,
    window_size=...
)
```

Output:

```python
Window(
    id,
    X,
    y,
    timestamp_start,
    timestamp_end
)
```

---

# 16. Module 2 — XGBoost Baseline

### File

```text
src/models/train.py
```

Implement:

```python
train_xgboost(X_train, y_train)
```

Initial model:

```text
Input
  ↓
XGBoost
  ↓
Binary classification

0 = Benign
1 = Attack
```

Do not introduce multiple model architectures.

The purpose is to keep the classifier fixed so that the experiment evaluates **adaptation strategy**, not model architecture.

---

# 17. Module 3 — Drift Detection

### File

```text
src/drift/ks_detector.py
```

Input:

```text
reference_window
current_window
```

For each selected numerical feature:

$$
D_{KS} =
\sup_x |F_{reference}(x)-F_{current}(x)|
$$

The implementation should return:

```python
{
    "drift_detected": True,
    "drift_score": 0.31,
    "drifted_features": [
        "Flow Bytes/s",
        "Packet Length Mean"
    ],
    "feature_statistics": {...}
}
```

---

# 18. Avoid Single-feature Drift Triggers

Do not implement:

```text
IF any feature drifts
→ retrain
```

This can cause excessive false triggers.

Instead:

```text
Feature-level KS results
        ↓
Aggregate
        ↓
Drift score
        ↓
Threshold
```

Possible aggregation:

$$
DriftScore =
\frac{1}{N}\sum_i D_{KS,i}
$$

or:

$$
DriftScore =
\frac{\#\text{drifted features}}
{\#\text{monitored features}}
$$

Test the chosen method rather than claiming it is universally optimal.

---

# 19. Module 4 — Historical Memory

### File

```text
src/memory/build_memory.py
```

The memory contains compact representations of previously observed patterns.

For V1:

```text
Pattern = attack category
```

Example:

```text
DoS Hulk
PortScan
Botnet
SSH Patator
FTP Patator
```

---

# 20. Memory Structure

Example:

```json
{
  "pattern_id": "DoS_Hulk",
  "sample_count": 4000,
  "feature_statistics": {
    "Flow Duration": {
      "mean": 123.2,
      "std": 45.8
    }
  },
  "first_seen": "...",
  "last_seen": "..."
}
```

Store representative samples separately.

```text
data/
└── memory/
    ├── DoS_Hulk.csv
    ├── PortScan.csv
    ├── Botnet.csv
    └── ...
```

---

# 21. Representative Sampling

You should not simply store the entire historical dataset.

For each pattern:

```text
All historical samples
        ↓
Representative sampling
        ↓
Memory budget
```

Initial configuration:

```text
3,000–5,000 samples/pattern
```

The exact number should be treated as an experimental parameter.

Possible V1 sampling method:

```text
stratified/random representative sampling
```

Do not introduce clustering unless the basic method works first.

---

# 22. Module 5 — Pattern Profiling

### File

```text
src/memory/profile.py
```

For every historical pattern calculate:

* mean
* standard deviation
* selected distribution statistics
* sample count
* timestamp information

Example:

```python
profile_pattern(
    pattern_data,
    feature_columns
)
```

returns:

```python
{
    "pattern_id": "...",
    "mean": {...},
    "std": {...},
    "count": ...
}
```

---

# 23. Module 6 — Drift Pattern Characterization

When drift occurs:

```text
Current window
      ↓
Calculate feature statistics
      ↓
Current drift profile
```

For example:

```python
current_profile = {
    "Flow Duration": {
        "mean": ...,
        "std": ...
    },
    "Flow Bytes/s": {
        "mean": ...,
        "std": ...
    }
}
```

---

# 24. Module 7 — Pattern Similarity

### File

```text
src/memory/retrieve.py
```

Compare:

```text
Current drift profile
        vs
Historical pattern profile
```

Start with a simple statistical distance.

For example:

$$
d_i =
\frac{|\mu_{current,i}-\mu_{pattern,i}|}
{\sigma_{pattern,i}+\epsilon}
$$

Then:

$$
D(P,C)=
\frac{1}{N}\sum_i d_i
$$

Convert distance to a ranking/similarity score.

The exact similarity function should be configurable.

---

# 25. Retrieval Algorithm

Pseudo-code:

```python
def retrieve_patterns(current_profile, memory, top_k):

    scores = []

    for pattern in memory:

        distance = calculate_distance(
            current_profile,
            pattern.profile
        )

        scores.append(
            (pattern.id, distance)
        )

    scores.sort(
        key=lambda x: x[1]
    )

    return scores[:top_k]
```

Output:

```text
DoS Hulk      0.89
PortScan      0.77
Botnet        0.32
Web Attack    0.19
```

Select Top-K.

---

# 26. Important Online Constraint

The retrieval mechanism must **not use the true attack label of the incoming window**.

Incorrect:

```text
Current traffic = DoS Hulk
       ↓
retrieve DoS Hulk
```

Correct:

```text
Current traffic
      ↓
feature distribution
      ↓
similarity
      ↓
historical pattern retrieval
```

The ground-truth label is only used for offline evaluation.

---

# 27. Module 8 — Recent-only Adaptation

### File

```text
src/adaptation/recent_only.py
```

```python
def adapt_recent_only(
    recent_data,
    model_config
):
    return train_xgboost(
        recent_data.X,
        recent_data.y
    )
```

This establishes the adaptation baseline.

---

# 28. Module 9 — Random Replay

### File

```text
src/adaptation/random_replay.py
```

Inputs:

```text
recent data
historical data
total budget
```

Algorithm:

```text
total budget = B

recent budget = B × recent_fraction

historical budget =
B - recent budget
```

Then:

```python
historical_sample = historical.sample(
    n=historical_budget,
    random_state=seed
)
```

Combine:

```text
recent_sample
+
random_historical_sample
```

Train XGBoost.

---

# 29. Module 10 — Pattern-aware Replay

### File

```text
src/adaptation/pattern_replay.py
```

Flow:

```text
Drift
 ↓
Current profile
 ↓
Pattern retrieval
 ↓
Top-K patterns
 ↓
Retrieve historical samples
 ↓
Allocate historical budget
 ↓
Combine with recent data
 ↓
Train XGBoost
```

Example:

```python
patterns = retrieve_patterns(
    current_profile,
    memory,
    top_k=2
)
```

Then:

```text
Historical budget = 50,000

Pattern 1 → 25,000
Pattern 2 → 25,000
```

or use allocation proportional to similarity.

Keep the allocation method configurable.

---

# 30. Equal Budget Requirement

The function should enforce:

```python
assert len(training_data) == TOTAL_BUDGET
```

for S3 and S4.

Example:

```text
TOTAL_BUDGET = 100,000

Recent = 50,000
Historical = 50,000
```

If fewer relevant historical samples are available, define a deterministic fallback rather than silently violating the budget.

---

# 31. Bias-Control Ablation

Do not make arbitrary rules such as:

```text
maximum class = 40%
minimum class = 10%
```

part of the core method.

Instead test:

### S4a

```text
Pattern-aware retrieval
        ↓
Raw combined dataset
        ↓
XGBoost
```

### S4b

```text
Pattern-aware retrieval
        ↓
Class-balanced / reweighted dataset
        ↓
XGBoost
```

This lets you measure whether class imbalance affects the result.

---

# 32. Module 11 — Evaluation

### File

```text
src/evaluation/metrics.py
```

Calculate:

### Recent Attack F1

$$
F1_{recent}
$$

Measures adaptation to newly observed traffic.

---

### Historical Attack F1

$$
F1_{historical}
$$

Measures retention of previously learned attack patterns.

---

### Forgetting

$$
Forgetting =
F1_{historical}^{before}
-
F1_{historical}^{after}
$$

---

### False Positive Rate

$$
FPR =
\frac{FP}{FP+TN}
$$

Important because an IDS that labels large amounts of benign traffic as attacks is not useful.

---

# 33. Efficiency Metrics

Also record:

```text
training_records
historical_records
recent_records
training_time
memory_size
number_of_retraining_events
```

Optional:

```text
CPU usage
RAM usage
model size
```

---

# 34. Main Experimental Table

Eventually generate:

| Strategy             | Recent F1 | Historical F1 | Forgetting | FPR | Records | Training Time |
| -------------------- | --------: | ------------: | ---------: | --: | ------: | ------------: |
| Static               |           |               |            |     |         |               |
| Recent-only          |           |               |            |     |         |               |
| Random replay        |           |               |            |     |         |               |
| Pattern-aware replay |           |               |            |     |         |               |
| Full history         |           |               |            |     |         |               |

Do not fill these values beforehand.

---

# 35. Full-history Baseline

Although the main comparison is S3 vs S4, implement full-history retraining if computationally feasible.

```text
All historical
+
Recent
↓
XGBoost
```

This establishes the upper end of the data/computation trade-off.

If full-history training is too expensive, document that limitation and use a clearly defined sampled approximation only if scientifically justified.

---

# 36. Forgetting Experiment

For every adaptation event:

```text
Before adaptation
        ↓
Historical evaluation
        ↓
Adapt model
        ↓
Historical evaluation
```

Calculate:

$$
F =
F1_{before}
-
F1_{after}
$$

Store:

```json
{
  "window": "W17",
  "strategy": "pattern_replay",
  "historical_f1_before": 0.89,
  "historical_f1_after": 0.87,
  "forgetting": 0.02
}
```

---

# 37. Model Validation Gate

### File

```text
src/models/validate.py
```

After retraining:

```text
Candidate Model
       ↓
Recent validation
       +
Historical validation
       +
Benign validation
       ↓
Quality Gate
```

The gate should prevent a clearly degraded candidate from automatically replacing the current model.

Conceptually:

```python
if acceptable(candidate_metrics):
    register_model()
else:
    reject_model()
```

Keep the criteria configurable.

---

# 38. MLflow

Every training run should log:

```text
strategy
window_id
drift_score

training_records
recent_records
historical_records

recent_f1
historical_f1
overall_f1
fpr
forgetting

training_time
memory_size

model_parameters
```

MLflow should allow you to compare:

```text
Random Replay
        vs
Pattern Replay
```

for the same window and budget.

---

# 39. Automated Pipeline

### File

```text
src/pipeline/run_cycle.py
```

Pseudo-code:

```python
def run_adaptation_cycle(
    reference_window,
    current_window,
    memory,
    current_model
):

    drift_result = detect_drift(
        reference_window,
        current_window
    )

    if not drift_result["drift_detected"]:
        return current_model

    current_profile = build_profile(
        current_window
    )

    relevant_patterns = retrieve_patterns(
        current_profile,
        memory
    )

    training_data = build_retraining_dataset(
        recent=current_window,
        historical=relevant_patterns
    )

    candidate_model = train_xgboost(
        training_data.X,
        training_data.y
    )

    metrics = evaluate_model(
        candidate_model
    )

    if quality_gate(metrics):
        register_model(candidate_model)

    update_memory(...)

    return candidate_model
```

---

# 40. Complete Automated Loop

The final application should behave like:

```text
START
  │
  ▼
Load reference data
  │
  ▼
Load model
  │
  ▼
Receive next traffic window
  │
  ▼
Detect drift
  │
  ├──────────── No ───────────→ Predict
  │
  ▼ Yes
Characterize drift
  │
  ▼
Retrieve relevant historical patterns
  │
  ▼
Construct fixed-budget dataset
  │
  ▼
Retrain XGBoost
  │
  ▼
Evaluate candidate
  │
  ├──── Reject ───→ Keep old model
  │
  ▼ Accept
Register new model
  │
  ▼
Update historical memory
  │
  ▼
Next traffic window
```

---

# 41. Docker

Create a reproducible environment.

### Dockerfile responsibilities

Install:

```text
Python
NumPy
Pandas
SciPy
Scikit-learn
XGBoost
MLflow
PyYAML
```

Then:

```text
Docker
 ↓
Run experiment
 ↓
Same environment for every team member
```

---

# 42. GitHub Actions

The CI pipeline should perform:

```text
Push / Pull Request
        ↓
Install dependencies
        ↓
Run unit tests
        ↓
Run data validation
        ↓
Run lightweight experiment
        ↓
Check metrics
        ↓
Build Docker image
```

Do **not** run the complete million-record experiment on every GitHub push.

Use a small test dataset for CI.

Run full experiments separately.

---

# 43. Testing Strategy

Every module should have unit tests.

### Drift detector

Test:

```text
same distributions → no drift
different distributions → drift
```

### Memory

Test:

```text
memory size ≤ configured budget
```

### Retrieval

Test:

```text
Top-K returned correctly
```

### Replay

Test:

```text
training_records == configured budget
```

### Model

Test:

```text
model trains
prediction shape is correct
```

---

# 44. Experiment Reproducibility

Every experiment should record:

```text
random seed
dataset version
window IDs
model parameters
memory size
Top-K
data budget
drift threshold
sampling strategy
```

Use fixed random seeds for baseline comparisons.

---

# 45. Recommended Team Division

## Member 1 — Data + Drift

Own:

```text
src/preprocessing/
src/drift/
```

Deliver:

* chronological windows
* feature selection
* KS detector
* drift reports

---

## Member 2 — Historical Memory

Own:

```text
src/memory/
```

Deliver:

* pattern memory
* pattern profiles
* similarity
* Top-K retrieval

This is the most research-oriented module.

---

## Member 3 — ML + Experiments

Own:

```text
src/models/
src/adaptation/
src/evaluation/
```

Deliver:

* XGBoost
* S1
* S2
* S3
* S4
* metrics
* experiment comparison

This member owns the primary experimental results.

---

## Member 4 — MLOps + Integration

Own:

```text
src/pipeline/
.github/
Dockerfile
MLflow
```

Deliver:

* automated pipeline
* model validation gate
* MLflow
* Docker
* GitHub Actions
* final demo

---

# 46. Integration Contract

The four modules should communicate through simple objects/files.

### Drift module → Memory

```json
{
  "window_id": "W17",
  "drift_detected": true,
  "drift_score": 0.31,
  "drifted_features": [...]
}
```

### Memory → Adaptation

```json
{
  "window_id": "W17",
  "selected_patterns": [
    "DoS_Hulk",
    "PortScan"
  ],
  "similarity_scores": {
    "DoS_Hulk": 0.89,
    "PortScan": 0.77
  }
}
```

### Adaptation → MLOps

```json
{
  "strategy": "pattern_replay",
  "window_id": "W17",
  "training_records": 100000,
  "recent_records": 50000,
  "historical_records": 50000,
  "recent_f1": 0.91,
  "historical_f1": 0.87,
  "training_time": 42.3
}
```

---

# 47. Implementation Order

Do **not** develop all four strategies simultaneously.

Follow this order.

## Phase 1 — Baseline

```text
Dataset
 ↓
Temporal windows
 ↓
XGBoost
 ↓
S1 Static
```

**Goal:** establish a working IDS.

---

## Phase 2 — Drift

```text
Temporal windows
 ↓
KS detector
 ↓
Drift reports
```

**Goal:** reliably detect distribution changes.

---

## Phase 3 — Recent adaptation

```text
Drift
 ↓
Recent data
 ↓
XGBoost
```

**Goal:** establish S2.

---

## Phase 4 — Random replay

```text
Drift
 ↓
Recent + random historical
 ↓
XGBoost
```

**Goal:** establish S3.

---

## Phase 5 — Historical memory

```text
Historical data
 ↓
Pattern profiles
 ↓
Representative samples
```

**Goal:** build memory independently before connecting it to retraining.

---

## Phase 6 — Pattern retrieval

```text
Current drift
 ↓
Similarity
 ↓
Top-K patterns
```

**Goal:** verify retrieval separately.

---

## Phase 7 — Pattern-aware replay

```text
Drift
 ↓
Retrieve patterns
 ↓
Historical samples
 ↓
Recent + historical
 ↓
XGBoost
```

**Goal:** establish S4.

---

## Phase 8 — Evaluation

Run:

```text
S1
S2
S3
S4
```

on the same temporal experiment.

Generate:

* Recent F1
* Historical F1
* Forgetting
* FPR
* Training time
* Data volume
* Memory size

---

## Phase 9 — MLOps

Only after the ML experiment works:

```text
Python pipeline
 ↓
MLflow
 ↓
Docker
 ↓
GitHub Actions
```

This prevents the team from spending most of its time debugging infrastructure before knowing whether the algorithm works.

---

# 48. Final Demonstration

Your teacher-facing demonstration should follow:

```text
1. Initial IDS
       ↓
2. New traffic window arrives
       ↓
3. Drift detected
       ↓
4. Historical memory inspected
       ↓
5. Relevant patterns identified
       ↓
6. Fixed-budget retraining dataset constructed
       ↓
7. XGBoost retrained
       ↓
8. Candidate model evaluated
       ↓
9. Model accepted/rejected
       ↓
10. MLflow records experiment
       ↓
11. Compare against random replay
```

The key screen should show:

```text
CURRENT DRIFT
      ↓
┌───────────────────────────────┐
│ Historical Pattern Similarity │
├───────────────────────────────┤
│ DoS Hulk          0.89        │
│ PortScan          0.77        │
│ Botnet            0.32        │
│ Web Attack        0.19        │
└───────────────────────────────┘
      ↓
Top-K = 2
      ↓
Recent:       50,000
Historical:   50,000
Total:       100,000
      ↓
XGBoost
      ↓
Validation
```

Then immediately show:

```text
                  Random Replay    Pattern Replay

Recent F1             X.XX             X.XX
Historical F1         X.XX             X.XX
Forgetting            X.XX             X.XX
Training Time         X.XX             X.XX
```

Those values should be populated **only after running the experiments**.

---

# 49. Final Project Definition

### Problem

> **Network intrusion detection models can degrade as traffic distributions evolve. Recent-only retraining can cause historical knowledge loss, while full historical retraining becomes increasingly expensive.**

### Proposed solution

> **Maintain a compact historical memory of previously observed attack patterns. When distribution drift is detected, characterize the current traffic distribution and retrieve historically relevant samples based on statistical similarity. Combine those samples with recent traffic under a fixed retraining-data budget and retrain the XGBoost IDS.**

### Evaluation

> **Compare static, recent-only, random historical replay, and pattern-aware historical replay using recent-attack performance, historical retention, forgetting, false-positive rate, training cost, and data volume.**

### Core contribution

> **A reproducible, fixed-budget experimental framework for evaluating whether drift-relevant historical memory selection provides a better adaptation/retention trade-off than random replay in an evolving intrusion-detection environment.**

### Core research question

> **At an equivalent retraining-data budget, can drift-relevant historical replay preserve more historical intrusion-detection knowledge than random historical replay while maintaining performance on recent traffic?**

---

# 50. Definition of Done

The project should be considered complete only when all of these work:

```text
[ ] Dataset loads correctly
[ ] Chronological windows generated
[ ] XGBoost baseline works
[ ] Static baseline implemented
[ ] KS drift detector works
[ ] Recent-only adaptation works
[ ] Random replay works
[ ] Historical memory built
[ ] Pattern profiles generated
[ ] Similarity calculation works
[ ] Top-K retrieval works
[ ] Pattern-aware replay works
[ ] S3 and S4 use identical data budgets
[ ] Historical/recent evaluation implemented
[ ] Forgetting metric implemented
[ ] FPR implemented
[ ] Training-time measurement implemented
[ ] Memory-size measurement implemented
[ ] Model quality gate implemented
[ ] MLflow tracking works
[ ] Docker container works
[ ] Unit tests pass
[ ] Full temporal experiment runs
[ ] Results comparison generated
[ ] Demo pipeline works
[ ] Final architecture documented
```

**The implementation priority is:** **S1 → drift detection → S2 → S3 → memory → S4 → evaluation → MLOps.** This keeps the team from building infrastructure around an algorithm that hasn't yet been experimentally validated.