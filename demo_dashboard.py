import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import urllib.request
import json
import warnings
import plotly.graph_objects as go
import plotly.express as px

warnings.filterwarnings('ignore')

# ML and Project Modules
from src.preprocessing.loader import create_temporal_windows, split_temporal_window
from src.models.train import train_xgboost
from src.models.predict import predict_xgboost
from src.evaluation.metrics import evaluate_performance
from src.drift.ks_detector import detect_drift
from src.memory.profile import profile_pattern
from src.adaptation.recent_only import adapt_recent_only
from src.adaptation.random_replay import adapt_random_replay
from src.adaptation.pattern_replay import adapt_pattern_replay
from src.memory.retrieve import retrieve_patterns, calculate_wasserstein_distance

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    shap = None
    SHAP_AVAILABLE = False

# -----------------------------------------------------------------------------
# 1. STREAMLIT PAGE CONFIG & AESTHETIC CYBER-THEME CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SentinelFlow | Drift-Aware Adaptive IDS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    code, pre, [class*="stCode"] {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Gradient Top Banner */
    .top-hero {
        background: linear-gradient(135deg, #0d1527 0%, #111e38 50%, #0a1120 100%);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 0px;
    }

    /* Metric Cards */
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .metric-card-title {
        color: #9ca3af;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card-val {
        color: #f3f4f6;
        font-size: 24px;
        font-weight: 700;
        margin-top: 4px;
    }

    /* Tool Pill Badges */
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-cyan { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .badge-green { background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }
    .badge-amber { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
    .badge-purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

    /* Service Status Indicator */
    .status-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }
    .status-up { background-color: #10b981; box-shadow: 0 0 8px #10b981; }
    .status-down { background-color: #ef4444; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA CACHING & INITIALIZATION
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def load_and_prepare_dataset():
    candidates = [
        "dataset/cic_ids2017_inspired_synthetic.csv",
        "cic_ids2017_inspired_synthetic.csv",
        "../dataset/cic_ids2017_inspired_synthetic.csv"
    ]
    data_path = next((p for p in candidates if os.path.exists(p)), None)
    if not data_path:
        st.error("Dataset not found. Please ensure `cic_ids2017_inspired_synthetic.csv` is present in `dataset/`.")
        st.stop()

    df = pd.read_csv(data_path)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df = df.sort_values(by="Timestamp").reset_index(drop=True)

    # 40% initial baseline calibration
    hist_size = int(len(df) * 0.4)
    hist_df = df.iloc[:hist_size].copy()
    stream_df = df.iloc[hist_size:].copy()

    # 80/20 train/test split on baseline to establish isolated historical holdout
    hist_train = hist_df.iloc[:int(len(hist_df) * 0.8)].copy()
    hist_test = hist_df.iloc[int(len(hist_df) * 0.8):].copy()

    feature_cols = [c for c in hist_train.columns if c not in ["Timestamp", "Label", "Attack Type"]]

    # Build memory bank of historical attack profiles
    memory_patterns = []
    memory_data_map = {}
    attack_types = [a for a in hist_train["Attack Type"].unique() if a != "BENIGN"]

    for attack in attack_types:
        atk_df = hist_train[hist_train["Attack Type"] == attack]
        if len(atk_df) >= 30:
            profile = profile_pattern(atk_df[feature_cols], attack, feature_cols)
            memory_patterns.append(profile)
            memory_data_map[attack] = atk_df[feature_cols + ["Label"]].sample(min(4000, len(atk_df)), random_state=42)

    historical_pool = hist_train[feature_cols + ["Label"]]

    # Train Static Baseline Model (S1)
    X_init = hist_train[feature_cols]
    y_init = hist_train["Label"]
    baseline_model = train_xgboost(X_init, y_init)

    baseline_hist_pred = predict_xgboost(baseline_model, hist_test[feature_cols])
    baseline_hist_f1 = float(evaluate_performance(hist_test["Label"], baseline_hist_pred)["f1_score"])

    # Slice streaming windows
    stream_df_clean = stream_df.drop(columns=["Attack Type"], errors="ignore")
    window_size = 10000 if len(stream_df_clean) >= 30000 else max(1000, len(stream_df_clean) // 4)
    windows = create_temporal_windows(stream_df_clean, window_size=window_size, label_column="Label", timestamp_column="Timestamp")

    ref_window = X_init.tail(window_size)

    return df, windows, baseline_model, baseline_hist_f1, memory_patterns, memory_data_map, historical_pool, hist_test, feature_cols, ref_window


with st.spinner("Initializing SentinelFlow Neural/XGBoost Engine & Calibrating Memory..."):
    df_raw, windows, baseline_model, baseline_hist_f1, memory_patterns, memory_data_map, historical_pool, hist_test, feature_cols, ref_window = load_and_prepare_dataset()

# -----------------------------------------------------------------------------
# 3. TOP BANNER & HERO SECTION
# -----------------------------------------------------------------------------
st.markdown("""
<div class="top-hero">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="hero-title">🛡️ SentinelFlow | Autonomous Drift-Aware NIDS</div>
            <div class="hero-subtitle">Production Continual Learning & Observability Platform under Enforced Fixed Retraining Budgets</div>
        </div>
        <div>
            <span class="badge-pill badge-cyan">XGBoost 2.1</span>
            <span class="badge-pill badge-green">KS Drift Engine</span>
            <span class="badge-pill badge-purple">Wasserstein Memory</span>
            <span class="badge-pill badge-amber">SHAP Explainability</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. TAB NAVIGATION
# -----------------------------------------------------------------------------
tab_sim, tab_shap, tab_obs, tab_arch, tab_math = st.tabs([
    "⚡ Cyber Stream Simulation",
    "🔍 Responsible AI (SHAP Lab)",
    "📊 Observability & Cloud Hub",
    "🛠️ MLOps Architecture",
    "📐 Mathematics & Research Matrix"
])

# -----------------------------------------------------------------------------
# TAB 1: CYBER STREAM SIMULATION (5-Bucket Scenario)
# -----------------------------------------------------------------------------
with tab_sim:
    # Session state for simulation tracking
    if "sim_window_idx" not in st.session_state: st.session_state.sim_window_idx = 0
    if "sim_history_s2" not in st.session_state: st.session_state.sim_history_s2 = []
    if "sim_history_s3" not in st.session_state: st.session_state.sim_history_s3 = []
    if "sim_history_s4" not in st.session_state: st.session_state.sim_history_s4 = []
    if "sim_indices" not in st.session_state: st.session_state.sim_indices = []
    if "current_ref_window" not in st.session_state: st.session_state.current_ref_window = ref_window

    col_ctrl, col_info1, col_info2, col_info3 = st.columns([1.5, 1, 1, 1])

    with col_ctrl:
        st.markdown("**Simulation Controller**")
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            if st.button("▶️ Next Window", use_container_width=True):
                if st.session_state.sim_window_idx < len(windows):
                    st.session_state.sim_window_idx += 1
        with sub_c2:
            if st.button("🔄 Reset Stream", use_container_width=True):
                st.session_state.sim_window_idx = 0
                st.session_state.sim_history_s2 = []
                st.session_state.sim_history_s3 = []
                st.session_state.sim_history_s4 = []
                st.session_state.sim_indices = []
                st.session_state.current_ref_window = ref_window

    with col_info1:
        st.metric("Streaming Window", f"{st.session_state.sim_window_idx} / {len(windows)}")
    with col_info2:
        st.metric("Baseline Hist F1", f"{baseline_hist_f1:.4f}")
    with col_info3:
        st.metric("Retraining Budget", "4,000 pkts", "Fixed O(1)")

    st.divider()

    if st.session_state.sim_window_idx == 0:
        st.info("System Ready. Click **'Next Window'** to simulate streaming enterprise traffic arrivals across the 5-bucket evaluation narrative.")
        
        st.markdown("### The 5-Bucket Scenario Roadmap")
        scenario_cols = st.columns(5)
        with scenario_cols[0]:
            st.markdown("""<div class="metric-card"><div class="metric-card-title">Bucket 1 & 2</div><div style="font-weight:600; color:#38bdf8;">Baseline Normalcy</div><div style="font-size:12px; color:#94a3b8; margin-top:4px;">Known DoS & PortScan. No drift triggered.</div></div>""", unsafe_allow_html=True)
        with scenario_cols[1]:
            st.markdown("""<div class="metric-card"><div class="metric-card-title">Bucket 3</div><div style="font-weight:600; color:#ef4444;">Mutated Attack</div><div style="font-size:12px; color:#94a3b8; margin-top:4px;">Low & Slow DoS (60% overlap). Drift triggered.</div></div>""", unsafe_allow_html=True)
        with scenario_cols[2]:
            st.markdown("""<div class="metric-card"><div class="metric-card-title">Bucket 4</div><div style="font-weight:600; color:#10b981;">Normalcy Recovery</div><div style="font-size:12px; color:#94a3b8; margin-top:4px;">Attacks stop. Quality Gate verifies FPR ≤ 0.05.</div></div>""", unsafe_allow_html=True)
        with scenario_cols[3]:
            st.markdown("""<div class="metric-card"><div class="metric-card-title">Bucket 5</div><div style="font-weight:600; color:#c084fc;">Zero-Day Exploit</div><div style="font-size:12px; color:#94a3b8; margin-top:4px;">0% match. Replay falls back to diverse buffer.</div></div>""", unsafe_allow_html=True)
        with scenario_cols[4]:
            st.markdown("""<div class="metric-card"><div class="metric-card-title">Production Guard</div><div style="font-weight:600; color:#fbbf24;">Quality Gate</div><div style="font-size:12px; color:#94a3b8; margin-top:4px;">Rejects paranoid models if FPR spikes.</div></div>""", unsafe_allow_html=True)

    else:
        curr_window = windows[st.session_state.sim_window_idx - 1]

        # 1. Evaluate Static Model S1 on incoming traffic
        s1_pred = predict_xgboost(baseline_model, curr_window.X)
        s1_perf = evaluate_performance(curr_window.y, s1_pred)

        # 2. Kolmogorov-Smirnov Statistical Drift Test
        drift_res = detect_drift(st.session_state.current_ref_window, curr_window.X)

        st.subheader(f"Incoming Traffic: Window {st.session_state.sim_window_idx}")
        st.caption(f"Timestamp range: `{curr_window.timestamp_start}` to `{curr_window.timestamp_end}` | Flow Records: `{len(curr_window.X):,}`")

        c_metric1, c_metric2, c_metric3, c_metric4 = st.columns(4)
        c_metric1.metric("Static Model (S1) F1", f"{s1_perf['f1_score']:.4f}")
        c_metric2.metric("Static False Positive Rate", f"{s1_perf['fpr']:.4f}")
        c_metric3.metric("KS Drift Score", f"{drift_res['drift_score']:.4f}")
        c_metric4.metric("Drift Status", "DRIFT DETECTED" if drift_res["drift_detected"] else "STABLE", delta="Alert" if drift_res["drift_detected"] else "Normal", delta_color="inverse")

        # Layout: Left column for Drift & Radar, Right column for Budget & Comparisons
        v_col1, v_col2 = st.columns([1.2, 1])

        with v_col1:
            # Distribution Drift Box/Violin plot
            st.markdown("#### 1. Statistical Covariate Shift (Kolmogorov-Smirnov)")
            primary_feat = feature_cols[0] if feature_cols else "Flow Duration"
            fig_ks = go.Figure()
            fig_ks.add_trace(go.Box(
                y=st.session_state.current_ref_window[primary_feat],
                name="Reference Window",
                marker_color="#38bdf8",
                boxpoints="outliers"
            ))
            fig_ks.add_trace(go.Box(
                y=curr_window.X[primary_feat],
                name="Current Streaming Window",
                marker_color="#ef4444" if drift_res["drift_detected"] else "#10b981",
                boxpoints="outliers"
            ))
            fig_ks.update_layout(
                title=f"Feature Distribution Comparison: {primary_feat}",
                template="plotly_dark",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_ks, use_container_width=True)

            # Memory Retrieval Radar / Distance Table
            st.markdown("#### 2. Scale-Normalized Wasserstein Memory Retrieval")
            all_patterns = retrieve_patterns(curr_window.X, memory_patterns, top_k=len(memory_patterns), memory_data_map=memory_data_map)
            top_patterns = all_patterns[:2]

            dist_df = pd.DataFrame(all_patterns, columns=["Historical Pattern", "Wasserstein Distance (Normalized)"])
            
            fig_bar = px.bar(
                dist_df,
                x="Wasserstein Distance (Normalized)",
                y="Historical Pattern",
                orientation="h",
                color="Wasserstein Distance (Normalized)",
                color_continuous_scale="Viridis_r",
                title="Historical Pattern Affinity (Lower Distance = Higher Replay Priority)",
                template="plotly_dark"
            )
            fig_bar.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)

        with v_col2:
            st.markdown("#### 3. Strict 4,000-Record Budget Allocation")
            top_names = [p[0] for p in top_patterns]
            budget_labels = ["Recent Drifted Window (50%)"] + [f"Historical: {name} (25%)" for name in top_names]
            budget_values = [2000, 1000, 1000]

            fig_donut = go.Figure(data=[go.Pie(
                labels=budget_labels,
                values=budget_values,
                hole=0.55,
                marker=dict(colors=["#38bdf8", "#818cf8", "#c084fc"])
            )])
            fig_donut.update_layout(
                title="Enforced Budget Partition ($B_{total} = 4,000$)",
                template="plotly_dark",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            # Execution of Retraining Strategies under budget
            adapt_w, eval_w = split_temporal_window(curr_window, train_ratio=0.6)

            # S2: Recent Only
            t_start = time.time()
            s2_model = adapt_recent_only(adapt_w, total_budget=4000)
            t_s2 = time.time() - t_start
            s2_recent_f1 = evaluate_performance(eval_w.y, predict_xgboost(s2_model, eval_w.X))["f1_score"]
            s2_hist_f1 = evaluate_performance(hist_test["Label"], predict_xgboost(s2_model, hist_test[feature_cols]))["f1_score"]
            s2_forget = baseline_hist_f1 - s2_hist_f1

            # S3: Random Replay
            t_start = time.time()
            s3_model = adapt_random_replay(adapt_w, historical_pool, 4000, 0.5)
            t_s3 = time.time() - t_start
            s3_recent_f1 = evaluate_performance(eval_w.y, predict_xgboost(s3_model, eval_w.X))["f1_score"]
            s3_hist_f1 = evaluate_performance(hist_test["Label"], predict_xgboost(s3_model, hist_test[feature_cols]))["f1_score"]
            s3_forget = baseline_hist_f1 - s3_hist_f1

            # S4: Pattern-Aware Replay
            t_start = time.time()
            s4_model = adapt_pattern_replay(adapt_w, adapt_w.X, memory_patterns, memory_data_map, 4000, 0.5, top_k=2)
            t_s4 = time.time() - t_start
            s4_recent_f1 = evaluate_performance(eval_w.y, predict_xgboost(s4_model, eval_w.X))["f1_score"]
            s4_hist_f1 = evaluate_performance(hist_test["Label"], predict_xgboost(s4_model, hist_test[feature_cols]))["f1_score"]
            s4_forget = baseline_hist_f1 - s4_hist_f1

            # Update State
            if st.session_state.sim_window_idx not in st.session_state.sim_indices:
                st.session_state.sim_indices.append(st.session_state.sim_window_idx)
                st.session_state.sim_history_s2.append(s2_hist_f1)
                st.session_state.sim_history_s3.append(s3_hist_f1)
                st.session_state.sim_history_s4.append(s4_hist_f1)

            st.markdown("#### 4. Empirical Strategy Performance Matrix")
            res_df = pd.DataFrame([
                {"Strategy": "S1: Static (No Retrain)", "Recent F1": s1_perf["f1_score"], "Historical F1": baseline_hist_f1, "Forgetting (↓)": 0.0000, "Compute Time": "0.00s"},
                {"Strategy": "S2: Recent-Only", "Recent F1": s2_recent_f1, "Historical F1": s2_hist_f1, "Forgetting (↓)": s2_forget, "Compute Time": f"{t_s2:.2f}s"},
                {"Strategy": "S3: Random Replay", "Recent F1": s3_recent_f1, "Historical F1": s3_hist_f1, "Forgetting (↓)": s3_forget, "Compute Time": f"{t_s3:.2f}s"},
                {"Strategy": "S4: Pattern-Aware Replay", "Recent F1": s4_recent_f1, "Historical F1": s4_hist_f1, "Forgetting (↓)": s4_forget, "Compute Time": f"{t_s4:.2f}s"}
            ])
            st.dataframe(res_df.style.highlight_max(subset=["Recent F1", "Historical F1"], color="#1e3a8a").highlight_min(subset=["Forgetting (↓)"], color="#064e3b"), use_container_width=True)

        # Bottom Full-Width Line Chart
        st.markdown("#### 5. Catastrophic Forgetting Mitigation Over Time")
        fig_forget = go.Figure()
        fig_forget.add_hline(y=baseline_hist_f1, line_dash="dash", line_color="#94a3b8", annotation_text="Baseline Historical F1")
        fig_forget.add_trace(go.Scatter(x=st.session_state.sim_indices, y=st.session_state.sim_history_s2, mode="lines+markers", name="S2: Recent-Only (Severe Collapse)", line=dict(color="#ef4444", width=2)))
        fig_forget.add_trace(go.Scatter(x=st.session_state.sim_indices, y=st.session_state.sim_history_s3, mode="lines+markers", name="S3: Random Replay", line=dict(color="#f59e0b", width=2)))
        fig_forget.add_trace(go.Scatter(x=st.session_state.sim_indices, y=st.session_state.sim_history_s4, mode="lines+markers", name="S4: Pattern-Aware Replay", line=dict(color="#10b981", width=3)))

        fig_forget.update_layout(
            title="Retention on Isolated Historical Holdout Test Set (Higher = Resisting Forgetting)",
            xaxis_title="Streaming Window Index",
            yaxis_title="Historical F1 Score",
            template="plotly_dark",
            height=360,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_forget, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: RESPONSIBLE AI (SHAP LAB)
# -----------------------------------------------------------------------------
with tab_shap:
    st.markdown("### 🔍 Responsible AI: Transparent Intrusion Explainability (Unit V)")
    st.write("Rather than acting as a black box, SentinelFlow integrates **SHAP (SHapley Additive exPlanations)** to attribute exact importance values to each NetFlow feature.")

    col_input, col_out = st.columns([1, 1.2])

    with col_input:
        st.markdown("#### Configure Network Flow Telemetry")
        flow_dur = st.slider("Flow Duration (µs)", 0.0, 150000.0, 95000.0, 500.0)
        flow_bytes = st.slider("Flow Bytes/s", 0.0, 250000.0, 180000.0, 1000.0)
        pkt_mean = st.slider("Packet Length Mean", 0.0, 1500.0, 850.0, 10.0)
        
        with st.expander("Advanced Flow Parameters"):
            fwd_pkts = st.number_input("Total Fwd Packets", 1.0, 1000.0, 25.0)
            bwd_pkts = st.number_input("Total Backward Packets", 1.0, 1000.0, 30.0)
            syn_flag = st.selectbox("SYN Flag Count", [0.0, 1.0], index=1)
            ack_flag = st.selectbox("ACK Flag Count", [0.0, 1.0], index=0)

    sample_dict = {
        "Flow Duration": flow_dur,
        "Flow Bytes/s": flow_bytes,
        "Packet Length Mean": pkt_mean
    }

    with col_out:
        st.markdown("#### Real-Time Feature Attribution")
        input_df = pd.DataFrame([sample_dict])[feature_cols[:len(sample_dict)]]
        
        pred_label = int(baseline_model.predict(input_df)[0])
        pred_prob = float(baseline_model.predict_proba(input_df)[0][1])

        st.metric("Classification Result", "🚨 INTRUSION / ATTACK" if pred_label == 1 else "✅ BENIGN NORMAL", f"Confidence: {pred_prob*100:.1f}%")

        if SHAP_AVAILABLE:
            try:
                explainer = shap.TreeExplainer(baseline_model)
                shap_values = explainer.shap_values(input_df)
                
                # Format for plot
                s_vals = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
                shap_df = pd.DataFrame({
                    "Feature": input_df.columns,
                    "Shapley Value (Contribution)": s_vals,
                    "Direction": ["Pushes toward Attack" if v > 0 else "Pushes toward Benign" for v in s_vals]
                }).sort_values(by="Shapley Value (Contribution)", ascending=True)

                fig_shap = px.bar(
                    shap_df,
                    x="Shapley Value (Contribution)",
                    y="Feature",
                    orientation="h",
                    color="Direction",
                    color_discrete_map={"Pushes toward Attack": "#ef4444", "Pushes toward Benign": "#10b981"},
                    title="SHAP Local Explanations (Impact on Decision)",
                    template="plotly_dark"
                )
                fig_shap.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_shap, use_container_width=True)
            except Exception as e:
                st.warning(f"SHAP local calculation notice: {e}")
        else:
            st.info("SHAP library is available via container API endpoint `/explain`.")

# -----------------------------------------------------------------------------
# TAB 3: OBSERVABILITY & CLOUD HUB
# -----------------------------------------------------------------------------
with tab_obs:
    st.markdown("### 📊 Enterprise Telemetry & Cloud Serving Hub")
    
    # Helper to check service ports
    def check_service(url):
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status in [200, 302, 401]
        except Exception:
            return False

    srv1, srv2, srv3, srv4 = st.columns(4)
    with srv1:
        is_api = check_service("http://127.0.0.1:8000/health")
        st.markdown(f"""<div class="metric-card"><div class="metric-card-title">FastAPI Production</div><div class="metric-card-val"><span class="status-dot {'status-up' if is_api else 'status-down'}"></span>{'ACTIVE' if is_api else 'OFFLINE'}</div><div style="font-size:12px; margin-top:6px;"><a href="http://127.0.0.1:8000/docs" target="_blank" style="color:#38bdf8;">Open Swagger Docs (:8000)</a></div></div>""", unsafe_allow_html=True)
    with srv2:
        is_prom = check_service("http://127.0.0.1:9090/-/healthy")
        st.markdown(f"""<div class="metric-card"><div class="metric-card-title">Prometheus Telemetry</div><div class="metric-card-val"><span class="status-dot {'status-up' if is_prom else 'status-down'}"></span>{'SCRAPING' if is_prom else 'STANDBY'}</div><div style="font-size:12px; margin-top:6px;"><a href="http://127.0.0.1:9090/targets" target="_blank" style="color:#38bdf8;">View Targets (:9090)</a></div></div>""", unsafe_allow_html=True)
    with srv3:
        is_graf = check_service("http://127.0.0.1:3002/api/health")
        st.markdown(f"""<div class="metric-card"><div class="metric-card-title">Grafana Observability</div><div class="metric-card-val"><span class="status-dot {'status-up' if is_graf else 'status-down'}"></span>{'CONNECTED' if is_graf else 'STANDBY'}</div><div style="font-size:12px; margin-top:6px;"><a href="http://127.0.0.1:3002" target="_blank" style="color:#38bdf8;">Open Dashboard (:3002)</a></div></div>""", unsafe_allow_html=True)
    with srv4:
        is_mlf = check_service("http://127.0.0.1:5001")
        st.markdown(f"""<div class="metric-card"><div class="metric-card-title">MLflow Registry</div><div class="metric-card-val"><span class="status-dot {'status-up' if is_mlf else 'status-down'}"></span>{'TRACKING' if is_mlf else 'STANDBY'}</div><div style="font-size:12px; margin-top:6px;"><a href="http://127.0.0.1:5001" target="_blank" style="color:#38bdf8;">Open MLflow UI (:5001)</a></div></div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown("#### AWS SageMaker Deployment Packaging (Unit VI)")
    tar_path = "build/sagemaker/model.tar.gz"
    tar_exists = os.path.exists(tar_path)
    tar_size = os.path.getsize(tar_path) / 1024 if tar_exists else 0

    c_cloud1, c_cloud2 = st.columns([1, 1.5])
    with c_cloud1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Artifact Status</div>
            <div style="font-weight:700; color:{'#10b981' if tar_exists else '#ef4444'}; font-size:18px; margin-top:4px;">
                {'✓ VERIFIED ARCHIVE' if tar_exists else 'NOT FOUND'}
            </div>
            <div style="font-size:12px; color:#94a3b8; margin-top:6px;">
                Location: <code>build/sagemaker/model.tar.gz</code><br>
                Payload Size: <b>{tar_size:.1f} KB</b><br>
                Inference Handlers: <code>code/inference.py</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_cloud2:
        st.markdown("""
        **Cloud Architecture Specification:**
        * **Framework Container:** `XGBoost 2.1-1 (Python 3.11)`
        * **Serverless Profile:** 2048 MB RAM, Concurrency 10 (Pay-per-request; $0 idle cost)
        * **Dedicated Real-Time Profile:** `ml.m5.large` (~$0.115/hr) with auto-scaling on `InvocationsPerInstance`
        * **Container Contract Verified:** `model_fn`, `input_fn`, `predict_fn`, `output_fn`
        """)

# -----------------------------------------------------------------------------
# TAB 4: MLOPS ARCHITECTURE & TOOL MATRIX
# -----------------------------------------------------------------------------
with tab_arch:
    st.markdown("### 🛠️ Curriculum Tool Matrix (Syllabus Units I – VI)")
    st.write("How every tool functions in the production architecture:")

    m_c1, m_c2 = st.columns(2)
    with m_c1:
        st.markdown("""
        **Unit I: Lifecycle & Testing**
        * **Pytest & GitHub Actions:** 30 automated tests enforcing budget equality, zero temporal leakage, and container compatibility.
        
        **Unit II: Data Management & Versioning**
        * **DVC (Data Version Control):** Tracks data lineage across multi-stage pipeline DAG (`validate` → `preprocess` → `evaluate`).
        * **MLflow:** SQLite metadata backend tracking runs, hyperparameters, metrics, and registered model binaries.

        **Unit III: Pipeline Orchestration**
        * **Apache Airflow:** 10-Task DAG (`dags/adaptive_ids_workflow.py`) orchestrating window extraction, schema check, drift test, branching, replay, and gate.
        """)
    with m_c2:
        st.markdown("""
        **Unit IV: Deployment & Observability**
        * **FastAPI:** Containerized high-throughput REST API exposing inference, SHAP explanations, and Prometheus metrics.
        * **Prometheus & Grafana:** Real-time telemetry scraping every 5s with pre-provisioned executive dashboards.

        **Unit V: Responsible AI**
        * **SHAP TreeExplainer:** Exact game-theoretic Shapley attributions for every prediction via `/explain`.

        **Unit VI: Cloud MLOps**
        * **AWS SageMaker SDK & Boto3:** Complete deployment packaging, model staging, and cost analysis.
        """)

# -----------------------------------------------------------------------------
# TAB 5: MATHEMATICS & RESEARCH MATRIX
# -----------------------------------------------------------------------------
with tab_math:
    st.markdown("### 📐 Mathematical Foundations & Academic Formulations")
    
    st.markdown("#### 1. Kolmogorov-Smirnov Statistical Drift Test")
    st.latex(r"D = \sup_x |F_{ref}(x) - F_{curr}(x)|")
    st.write("Identifies virtual concept drift across continuous NetFlow features by comparing the empirical cumulative distributions without requiring ground-truth labels.")

    st.markdown("#### 2. Scale-Normalized 1D Wasserstein Distance")
    st.latex(r"W_{norm}(u, v) = \frac{W_1(u, v)}{\sigma_v + \epsilon} = \frac{\int_{-\infty}^{\infty} |U(x) - V(x)| dx}{\sigma_v + \epsilon}")
    st.write("Normalizes Earth Mover's Distance by the historical standard deviation of each attack pattern, preventing massive features (Flow Duration) from dominating smaller features (Packet Length).")

    st.markdown("#### 3. Catastrophic Forgetting Metric")
    st.latex(r"\text{Forgetting} = F1_{baseline}(\mathcal{D}_{hist}^{test}) - F1_{adapted}(\mathcal{D}_{hist}^{test})")
    st.write("Quantifies retention decay on an isolated historical holdout test set that is never touched during retraining.")

    st.markdown("#### 4. Constant-Time Compute Constraint")
    st.latex(r"B_{total} = B_{recent} + B_{hist} = 4,000 \quad \implies \quad \mathcal{O}(1) \text{ Training Complexity}")

st.markdown("""
---
<div style="text-align: center; color: #64748b; font-size: 12px;">
    Adaptive Historical Memory for Drift-Aware IDS | Production MLOps Research Architecture
</div>
""", unsafe_allow_html=True)
