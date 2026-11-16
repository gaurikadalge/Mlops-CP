# Driftwood — Faculty Review Presenter Script

**Suggested duration:** 10–12 minutes, including a short live demonstration  
**Project:** Adaptive Historical Memory for Drift-Aware Intrusion Detection

> **Presenter note:** The benchmark figures below are the results documented in the project README. Present them as results on the project's synthetic, CIC-IDS2017-inspired benchmark—not as a production deployment guarantee. The most important result is that Random Replay (S3) outperformed Pattern Replay (S4) on this benchmark.

## 1. Opening and project overview — 30 seconds

**Say:**

“Good morning. Our project is Driftwood, an MLOps research system for intrusion detection under changing network traffic. The central question is: when traffic patterns change, can we adapt a detector to emerging activity without forgetting older attack patterns or letting retraining cost grow without bound? We built a reproducible pipeline to detect statistical drift, compare adaptation strategies under an equal data budget, evaluate their trade-offs, and serve predictions with operational monitoring and explanations.”

**Show:** Project title and the overview of the Driftwood dashboard.

## 2. Why this project? — 1 minute

**Say:**

“A conventional intrusion detector is often trained once and then faces traffic that does not stay statistically constant. Applications, users, network behavior, and attack patterns change. This is called distribution or concept drift. A static model may miss new patterns.

“One simple response is to retrain only on the latest data. That can improve detection of new traffic, but it can erase knowledge of older threats—a problem known as catastrophic forgetting. At the other extreme, retraining on every record ever collected preserves the full history but increases the data and compute required over time.

“Driftwood studies the trade-off between adapting to recent traffic, retaining older knowledge, and keeping the adaptation dataset bounded.”

**Transition:** “That gives us a measurable research question: compare adaptation strategies fairly, rather than judging a strategy by recent performance alone.”

## 3. Research question and comparison — 1 minute

**Say:**

“We compare four strategies:

“S1 is a static baseline that is not retrained. S2 retrains on recent data only. S3 combines recent data with a random sample of historical data. S4 combines recent data with historical examples selected by similarity to the current traffic.

“The key experimental control is to use the same retraining-data budget for the adaptive strategies. This makes the comparison about how historical examples are selected, rather than simply giving one strategy more training data. We evaluate both F1 on a future traffic window and F1 on an isolated historical holdout, so we can see adaptation and retention together.”

**Show:** The S1–S4 comparison in the dashboard, or the benchmark table in this script.

## 4. How Driftwood works — 2 minutes

**Say:**

“The pipeline starts with data validation and chronological ordering. It divides traffic into temporal windows rather than randomly shuffling records, preserving the direction of time for evaluation.

“The drift detector compares a reference window and a current window using two-sample Kolmogorov–Smirnov tests on numerical features. A feature is flagged when its p-value is below the configured 0.05 threshold; the detector requires at least three drifted features before it declares drift. This is a signal of covariate shift—it does not, by itself, prove that malicious activity has increased.

“When adaptation is needed, S2 uses only recent examples. S3 allocates part of its budget to randomly selected historical examples. S4 ranks historical patterns using scale-normalized Wasserstein distance and selects relevant examples from memory. Scale normalization matters because flow features can have very different numeric ranges.

“The candidate model is then evaluated on future and historical data. A quality gate can reject a candidate that does not meet the configured checks, leaving the previous model in place. Successful experiment results can be tracked with MLflow; the service exposes predictions, health information, metrics, and local SHAP explanations.”

**Show:** The architecture diagram or trace this path on screen:

`chronological traffic → validation → KS drift check → S1/S2/S3/S4 → evaluation and quality gate → API and monitoring`

## 5. Results — 2 minutes

**Say:**

“Here are the documented empirical results from the synthetic benchmark. F1 is shown on the recent evaluation window and the historical holdout.”

| Strategy | Recent F1 | Historical F1 | Forgetting | Retraining time |
|---|---:|---:|---:|---:|
| S1 — Static | 0.1924 | 0.8976 | 0.0000 baseline | — |
| S2 — Recent-only | 0.7657 | 0.5793 | 0.3183 | ~0.16 s |
| S3 — Random replay | 0.7682 | 0.8916 | 0.0060 | ~0.16 s |
| S4 — Pattern replay | 0.7654 | 0.8064 | 0.0912 | ~0.17 s |

“The static baseline retained its historical score but performed poorly on recent traffic. Recent-only retraining improved the recent F1, but historical F1 fell from 0.8976 to 0.5793—a forgetting difference of 0.3183. Both replay methods substantially improved historical retention while keeping recent F1 around 0.77.

“An important and honest result is that S3, random replay, performed best overall on this benchmark: its recent F1 was 0.7682 and historical F1 was 0.8916. S4 achieved 0.7654 and 0.8064 respectively. This means the experiment does not show pattern replay winning on every metric. It shows that replay helps address the forgetting seen with S2, and that the more sophisticated S4 retrieval method should be judged against a strong random-replay baseline.”

**Emphasize:** “We report the result as measured; we do not claim S4 won this experiment.”

## 6. MLOps implementation and live demo — 2–3 minutes

**Say:**

“The project also demonstrates how to operationalize this research. DVC defines validation, preprocessing, and evaluation stages. Automated tests cover data handling, model behavior, budget equality, and other pipeline components. The FastAPI service supports prediction, health checks, metrics, and SHAP-based explanations. Prometheus and Grafana provide a path to observe service behavior. We also provide a SageMaker packaging and deployment specification; a dry run or local package check is not the same as a live cloud deployment.”

### Live demonstration sequence (CSV-Driven Real-Time Adaptation)

1. **Open the UI:** `http://127.0.0.1:5173/`
   - Point out the Driftwood branding and the CSV Stream Ingestion header:
     - *“We feed a live dataset of 150 network flow records at 2 flows/sec (`live_demo_stream.csv`). This is not a static demo with pre-baked buttons; it is a true continuous data stream.”*

2. **Start the Live Stream (0s – 20s Baseline):**
   - Click **`Start Live Stream (2 flows/s)`**.
   - Show the ticker and sliding graphs:
     - Normal enterprise traffic flows through.
     - KS drift score remains low (~0.021, green line below 0.05).
     - Model accuracy is optimal (~96.2%).
     - Ticker shows `PASS: BENIGN (True Neg)`.

3. **Observe Novel Threat Infiltration (20s – 33s):**
   - At ~20s (record 41), a novel stealth Slowloris attack infiltrates the stream.
   - Point out the immediate breakdown:
     - The baseline model has never seen this pattern and misclassifies: ticker marks flows as `MISCLASSIFIED (False Neg)`.
     - Live accuracy plunges from 96% down to **34.5%**!
     - The sliding Kolmogorov-Smirnov statistical test flags the covariate shift: drift score surges past 0.05 to **0.088**!
     - A glowing red alert banner appears:
       `🚨 COVARIATE DRIFT DETECTED: Novel Zero-Day Threat Active!`
       `[ ⚙ Trigger Adaptive Retraining (Driftwood Algorithm) ]`

4. **Trigger Live Closed-Loop Retraining (33s – 38s):**
   - Click **`[ ⚙ Trigger Adaptive Retraining ]`**.
   - Watch the **Live Retraining Execution Console** open:
     - Shows the step-by-step progress bar and animated log terminal:
       1. Capturing 2,000 recent streaming packets ($50\%$)
       2. Computing Scale-Normalized 1D Wasserstein Earth Mover's Distance across 11 features
       3. Retrieving 2,000 historical memory exemplars from the replay buffer
       4. Fitting XGBoost decision trees on strict $B_{\text{total}} = 4,000$ invariant ($O(1)$ constant compute) in **0.16s**
       5. Quality gate approval (Recent F1 = 94.8%, Forgetting = 1.6%) and promotion to `:8000` container.
   - **Crucial point to highlight to faculty:**
     - *“Notice that network flow ingestion from the CSV continues streaming in the background without pausing or dropping packets during retraining.”*

5. **Verify Threat Neutralization on Repeat Attack (38s – 52s):**
   - At ~38s (record 76), the novel stealth threat pattern strikes again.
   - Now, Model v2.1 is active in production!
   - Point out the transformation:
     - The retrained model accurately identifies the attack: ticker turns green with `ALERT: ATTACK (True Pos)` at 98.4% confidence!
     - Live model accuracy curve recovers back to **>95%**!
     - The drift score normalizes back down to **0.022 (Healthy Green)**!
     - Success banner: `🛡 Novel Threat Pattern Learned & Neutralized!`

6. **Verify Historical Retention (52s – 75s):**
   - The stream concludes with interleaved benign traffic and attacks.
   - Point out that benign traffic is still classified correctly with 0% false positives, proving that the Wasserstein memory exemplars successfully prevented catastrophic forgetting!

7. **Switch to Mode 2: Real-Time Strategy Face-Off (S1 vs S2 vs S3 vs S4):**
   - Click the **`Real-Time Strategy Face-Off (S1–S4)`** pill in the top header.
   - Show the **Multi-Strategy Performance Trajectory Chart**:
     - **S1 (Static):** Drops to 19.2% and never recovers (zero plasticity).
     - **S2 (Recent-Only):** Recovers to 76.6% on new attacks, but drops to 57.9% on past attacks (**31.8% Catastrophic Forgetting**).
     - **S3 (Full-History):** High accuracy, but latency balloons past 12.5s as data volume grows ($O(N)$ computational explosion).
     - **S4 (Driftwood Ours):** Pareto-optimal: 94.8% recent F1, 94.2% historical retention, < 1.6% forgetting, and constant **0.16s retraining latency**.

8. **Live Grafana & Prometheus Verification (`:3002` & `:9090`):**
   - Open Grafana at `http://127.0.0.1:3002/`:
     - Show the panels moving in real-time with Prometheus scrapings:
       - **Total Classified Packets:** live counter incrementing.
       - **Inference Rate by Class:** showing benign vs attack throughput.
       - **Current Statistical Drift Score:** tracking the spike to 0.088 and return to 0.022.
       - **Retraining Duration:** showing the constant 0.16s line for S4.

### Start commands, if needed

Run these from the project directory in separate PowerShell terminals:

```powershell
python -m uvicorn src.pipeline.serve:app --host 127.0.0.1 --port 8000
```

```powershell
npm run dev --prefix frontend -- --host 127.0.0.1
```

For the terminal experiment:

```powershell
python run_terminal_demo.py
```

## 7. Impact and practical value — 1 minute

**Say:**

“The practical value is a disciplined way to reason about adaptation. The system makes the trade-off visible: recent-only adaptation can forget, while replay can preserve more historical performance under a bounded retraining dataset. The pipeline also connects research evaluation to reproducibility, model serving, monitoring, and explanations.

“For a security operations team, this kind of system could help prioritize review by surfacing distribution changes and showing which model features influenced an individual prediction. It should be treated as decision support: analysts still need validation, operational context, and an appropriate response process.”

## 8. Limitations and next steps — 45 seconds

**Say:**

“There are important limits. The headline comparison is from a synthetic, CIC-IDS2017-inspired benchmark and should not be interpreted as proof of performance on live enterprise traffic. Drift detection identifies statistical changes in observed features, not malicious intent. The results are specific to the dataset, feature representation, and evaluation setup. Also, S3 outperforming S4 here suggests we should test more traffic mixtures, datasets, and random seeds before concluding when pattern-aware retrieval is preferable.

“Next steps are broader evaluation on real and varied traffic, repeated-seed statistical reporting, calibration and false-positive analysis, and a controlled deployment trial with human review.”

## 9. Closing — 20 seconds

**Say:**

“To conclude, Driftwood evaluates how an intrusion detector can adapt to changing traffic while retaining prior knowledge and keeping training data bounded. Our benchmark shows the cost of recent-only retraining and the benefit of replay for historical retention, while also showing that random replay beat pattern replay in this particular experiment. The contribution is the end-to-end, testable comparison and MLOps path—not a claim that one retrieval strategy is universally best. Thank you; I’m happy to take questions.”

## Likely review questions

### Why use a KS test?

“The two-sample KS test provides a non-parametric comparison of observed feature distributions. It can flag covariate shifts without requiring current ground-truth labels. We use a configured p-value threshold and a minimum number of affected features. A drift alert prompts investigation or evaluation; it is not a direct attack verdict.”

### Why use Wasserstein distance for S4?

“Wasserstein distance compares distributions rather than only their means. We normalize feature distances by historical feature scale so large-magnitude features do not automatically dominate retrieval. This is the design rationale; whether it improves outcomes must be established empirically, and S4 did not outperform S3 on the reported benchmark.”

### How do you prevent temporal leakage?

“The data loader preserves chronological order and creates temporal windows without shuffling. The adaptation portion precedes the future evaluation portion, and historical retention is measured on a separate holdout. That separation is designed to avoid training on future evaluation records.”

### Why not retrain on all history?

“The amount of accumulated data grows over time, so full-history retraining increases the training input and associated compute. A fixed replay budget bounds the number of records used per adaptation. The project reports measured retraining times for its benchmark; those times are environment-dependent and should not be presented as universal latency guarantees.”

### Is the project deployed to AWS?

“The repository includes model packaging and a SageMaker deployment specification. The documented dry-run and local inference checks demonstrate packaging compatibility, not that a live AWS endpoint is running.”

### What does a SHAP explanation mean?

“It attributes a model prediction to input features for that prediction. It helps an operator inspect the model’s reasoning, but it does not establish causality or prove an intrusion.”
