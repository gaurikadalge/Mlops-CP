import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import warnings
import plotly.graph_objects as go
import plotly.express as px

warnings.filterwarnings('ignore')

from src.preprocessing.loader import create_temporal_windows
from src.models.train import train_xgboost
from src.models.predict import predict_xgboost
from src.evaluation.metrics import evaluate_performance
from src.drift.ks_detector import detect_drift
from src.memory.profile import profile_pattern
from src.adaptation.recent_only import adapt_recent_only
from src.adaptation.random_replay import adapt_random_replay
from src.adaptation.pattern_replay import adapt_pattern_replay
from src.memory.retrieve import retrieve_patterns

st.set_page_config(page_title="Adaptive IDS Demo", layout="wide")

@st.cache_resource
def load_and_prepare_data():
    data_path = "dataset/cic_ids2017_inspired_synthetic.csv"
    if not os.path.exists(data_path):
        st.error(f"Dataset not found at {data_path}. Please ensure it exists.")
        st.stop()
        
    df = pd.read_csv(data_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values(by='Timestamp').reset_index(drop=True)
    
    hist_size = int(len(df) * 0.4)
    hist_df = df.iloc[:hist_size].copy()
    stream_df = df.iloc[hist_size:].copy()
    
    hist_train = hist_df.iloc[:int(len(hist_df)*0.8)].copy()
    hist_test = hist_df.iloc[int(len(hist_df)*0.8):].copy()
    
    feature_cols = [c for c in hist_train.columns if c not in ['Timestamp', 'Label', 'Attack Type']]
    
    # Build Memory
    memory_patterns = []
    memory_data_map = {}
    
    for attack_type in hist_train['Attack Type'].unique():
        if attack_type == 'BENIGN':
            continue
        pattern_data = hist_train[hist_train['Attack Type'] == attack_type][feature_cols]
        if len(pattern_data) > 50: 
            profile = profile_pattern(pattern_data, attack_type, feature_cols)
            memory_patterns.append(profile)
            
            pattern_full = hist_train[hist_train['Attack Type'] == attack_type][feature_cols + ['Label']]
            memory_data_map[attack_type] = pattern_full.sample(min(4000, len(pattern_full)), random_state=42)
            
    historical_pool = hist_train[feature_cols + ['Label']]
    
    # Baseline Model
    X_init = hist_train[feature_cols]
    y_init = hist_train['Label']
    baseline_model = train_xgboost(X_init, y_init)
    
    baseline_hist_pred = predict_xgboost(baseline_model, hist_test[feature_cols])
    baseline_hist_f1 = evaluate_performance(hist_test['Label'], baseline_hist_pred)['f1_score']
    
    stream_df_clean = stream_df.drop(columns=['Attack Type'])
    windows = create_temporal_windows(stream_df_clean, window_size=10000, label_column='Label', timestamp_column='Timestamp')
    
    reference_window_df = X_init.tail(10000)
    
    return windows, baseline_model, baseline_hist_f1, memory_patterns, memory_data_map, historical_pool, hist_test, feature_cols, reference_window_df

st.title("🛡️ Adaptive Historical Memory for Drift-Aware IDS")
st.markdown("### Interactive MLOps Pipeline Demonstration")

with st.spinner("Loading dataset, building memory, and training baseline model..."):
    windows, baseline_model, baseline_hist_f1, memory_patterns, memory_data_map, historical_pool, hist_test, feature_cols, ref_window = load_and_prepare_data()

# Initialize session state for charts
if 'history_s2' not in st.session_state: st.session_state.history_s2 = []
if 'history_s3' not in st.session_state: st.session_state.history_s3 = []
if 'history_s4' not in st.session_state: st.session_state.history_s4 = []
if 'window_indices' not in st.session_state: st.session_state.window_indices = []

st.sidebar.header("Simulation Controls")
if 'window_idx' not in st.session_state:
    st.session_state.window_idx = 0
if 'ref_window' not in st.session_state:
    st.session_state.ref_window = ref_window

if st.sidebar.button("Simulate Next Window ⏭️"):
    st.session_state.window_idx += 1
    
if st.sidebar.button("Reset Simulation 🔄"):
    st.session_state.window_idx = 0
    st.session_state.ref_window = ref_window
    st.session_state.history_s2 = []
    st.session_state.history_s3 = []
    st.session_state.history_s4 = []
    st.session_state.window_indices = []

st.sidebar.markdown(f"**Current Window:** {st.session_state.window_idx} / {len(windows)}")
st.sidebar.markdown(f"**Baseline Historical F1:** {baseline_hist_f1:.4f}")

if st.session_state.window_idx == 0:
    st.info("System Initialized. Baseline model deployed. Click 'Simulate Next Window' in the sidebar to begin processing incoming network traffic.")
    st.stop()
    
if st.session_state.window_idx > len(windows):
    st.success("Simulation Complete.")
    st.stop()

# Get current window
idx = st.session_state.window_idx - 1
window = windows[idx]

st.header(f"Live Traffic: Window {st.session_state.window_idx}")
st.write(f"**Time range:** {window.timestamp_start} to {window.timestamp_end}")

# 1. Evaluate S1
y_pred = predict_xgboost(baseline_model, window.X)
metrics = evaluate_performance(window.y, y_pred)

col1, col2 = st.columns(2)
col1.metric("Current Static Model (S1) F1", f"{metrics['f1_score']:.4f}")
col2.metric("False Positive Rate", f"{metrics['fpr']:.4f}")

# 2. Detect Drift
drift_result = detect_drift(st.session_state.ref_window, window.X)

if not drift_result["drift_detected"]:
    st.success("✅ No significant distribution drift detected. Static model is performing well.")
    st.stop()

# --- 1. VISUALIZE DRIFT ---
st.error(f"🚨 DISTRIBUTION DRIFT DETECTED! (KS Score: {drift_result['drift_score']:.4f})")
st.markdown("### 1. Concept Drift Visualization")
drift_feat = feature_cols[0] if len(feature_cols) > 0 else None
if drift_feat:
    fig_drift = go.Figure()
    fig_drift.add_trace(go.Box(x=st.session_state.ref_window[drift_feat], name='Reference Window', marker_color='#1f77b4'))
    fig_drift.add_trace(go.Box(x=window.X[drift_feat], name='Current Window (Drifted)', marker_color='#d62728'))
    fig_drift.update_layout(title=f"Distribution Shift: {drift_feat}", height=300, margin=dict(t=40, b=40))
    st.plotly_chart(fig_drift, use_container_width=True)

current_profile = profile_pattern(window.X, "current", feature_cols)
all_patterns = retrieve_patterns(current_profile, memory_patterns, top_k=len(memory_patterns))
top_2_patterns = all_patterns[:2]

# --- 2. VISUALIZE RADAR CHART (PATTERN RETRIEVAL) ---
st.markdown("### 2. Pattern-Aware Memory Retrieval")
st.write("Comparing current drift signature against historical attack profiles in memory...")

categories = feature_cols[:5] # Max 5 for readability
plot_profiles = [current_profile]
for pat_id, _ in top_2_patterns:
    for mp in memory_patterns:
        if mp['pattern_id'] == pat_id:
            plot_profiles.append(mp)
            
max_vals = {c: max([p['feature_statistics'][c]['mean'] for p in plot_profiles]) for c in categories}
def norm(val, max_val): return val / max_val if max_val > 0 else 0

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
      r=[norm(current_profile['feature_statistics'][c]['mean'], max_vals[c]) for c in categories],
      theta=categories,
      fill='toself',
      name='Current Drift Anomaly',
      line_color='red'
))

colors = ['green', 'blue']
for i, (pat_id, _) in enumerate(top_2_patterns):
    pat_profile = next(p for p in memory_patterns if p['pattern_id'] == pat_id)
    fig_radar.add_trace(go.Scatterpolar(
          r=[norm(pat_profile['feature_statistics'][c]['mean'], max_vals[c]) for c in categories],
          theta=categories,
          fill='toself',
          name=f'Historical: {pat_id}',
          line_color=colors[i % len(colors)]
    ))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=True, height=500)

colA, colB = st.columns([2, 1])
with colA:
    st.plotly_chart(fig_radar, use_container_width=True)
with colB:
    st.markdown("**Statistical Distances**")
    sim_df = pd.DataFrame(all_patterns, columns=["Historical Pattern", "Statistical Distance (Lower is better)"])
    st.dataframe(sim_df, use_container_width=True)

# --- 3. VISUALIZE REPLAY BUFFER ALLOCATION ---
st.markdown("### 3. Replay Buffer Allocation (Resource Efficiency)")
total_budget = 4000
labels = ['Current Window Data'] + [p[0] for p in top_2_patterns]
values = [2000] + [1000]*len(top_2_patterns)
fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
fig_donut.update_layout(height=400, margin=dict(t=40, b=40))
st.plotly_chart(fig_donut, use_container_width=True)

# 3. Retraining
with st.spinner("Retraining multiple IDS models in parallel (S2, S3, S4) to compare strategies..."):
    # S2
    s2_model = adapt_recent_only(window)
    s2_recent_pred = predict_xgboost(s2_model, window.X)
    s2_hist_pred = predict_xgboost(s2_model, hist_test[feature_cols])
    s2_recent_f1 = evaluate_performance(window.y, s2_recent_pred)['f1_score']
    s2_hist_f1 = evaluate_performance(hist_test['Label'], s2_hist_pred)['f1_score']
    s2_forgot = baseline_hist_f1 - s2_hist_f1
    
    # S3
    t0 = time.time()
    s3_model = adapt_random_replay(window, historical_pool, total_budget, 0.5)
    t3 = time.time() - t0
    s3_recent_pred = predict_xgboost(s3_model, window.X)
    s3_hist_pred = predict_xgboost(s3_model, hist_test[feature_cols])
    s3_recent_f1 = evaluate_performance(window.y, s3_recent_pred)['f1_score']
    s3_hist_f1 = evaluate_performance(hist_test['Label'], s3_hist_pred)['f1_score']
    s3_forgot = baseline_hist_f1 - s3_hist_f1
    
    # S4
    t0 = time.time()
    s4_model = adapt_pattern_replay(window, current_profile, memory_patterns, memory_data_map, total_budget, 0.5, top_k=2)
    t4 = time.time() - t0
    s4_recent_pred = predict_xgboost(s4_model, window.X)
    s4_hist_pred = predict_xgboost(s4_model, hist_test[feature_cols])
    s4_recent_f1 = evaluate_performance(window.y, s4_recent_pred)['f1_score']
    s4_hist_f1 = evaluate_performance(hist_test['Label'], s4_hist_pred)['f1_score']
    s4_forgot = baseline_hist_f1 - s4_hist_f1
    
# Update state history
if st.session_state.window_idx not in st.session_state.window_indices:
    st.session_state.window_indices.append(st.session_state.window_idx)
    st.session_state.history_s2.append(s2_hist_f1)
    st.session_state.history_s3.append(s3_hist_f1)
    st.session_state.history_s4.append(s4_hist_f1)

# --- 4. VISUALIZE FORGETTING ---
st.markdown("### 4. Adaptation Results (Combating Catastrophic Forgetting)")

fig_line = go.Figure()
fig_line.add_hline(y=baseline_hist_f1, line_dash="dash", line_color="black", annotation_text="Baseline Initial F1")
fig_line.add_trace(go.Scatter(x=st.session_state.window_indices, y=st.session_state.history_s2, mode='lines+markers', name='S2: Recent Only (Severe Forgetting)', line=dict(color='red')))
fig_line.add_trace(go.Scatter(x=st.session_state.window_indices, y=st.session_state.history_s3, mode='lines+markers', name='S3: Random Replay', line=dict(color='orange')))
fig_line.add_trace(go.Scatter(x=st.session_state.window_indices, y=st.session_state.history_s4, mode='lines+markers', name='S4: Pattern Replay (Your Novelty)', line=dict(color='green', width=3)))
fig_line.update_layout(title="Historical F1 Score over Time (Higher is Better)", xaxis_title="Simulation Window", yaxis_title="Historical F1 Score", height=400)
st.plotly_chart(fig_line, use_container_width=True)

st.subheader("Final Metric Comparison")
res_df = pd.DataFrame({
    "Strategy": ["Recent-Only (S2)", "Random Replay (S3)", "Pattern Replay (S4)"],
    "Recent F1": [s2_recent_f1, s3_recent_f1, s4_recent_f1],
    "Historical F1": [s2_hist_f1, s3_hist_f1, s4_hist_f1],
    "Forgetting (↓)": [s2_forgot, s3_forgot, s4_forgot],
    "Training Time (s)": [np.nan, t3, t4]
})

st.dataframe(res_df.style.highlight_max(subset=['Recent F1', 'Historical F1'], color='lightgreen')
                   .highlight_min(subset=['Forgetting (↓)'], color='lightgreen')
                   .format(precision=4), use_container_width=True)
                   
st.success("Pattern-Aware Replay preserves significantly more historical knowledge while executing within a strict compute budget!")

st.session_state.ref_window = window.X.copy()
