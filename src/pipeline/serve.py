import os
import glob
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np
import mlflow
import mlflow.xgboost
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

# Optional SHAP import
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    shap = None
    SHAP_AVAILABLE = False

# ---------------------------------------------------------
# Prometheus Metric Definitions (Bounded Labels Only)
# ---------------------------------------------------------
REQUEST_COUNT = Counter(
    "ids_http_requests_total",
    "Total HTTP requests handled",
    ["endpoint", "status"]
)

PREDICTION_COUNT = Counter(
    "ids_predictions_total",
    "Total IDS predictions classified",
    ["prediction_label", "strategy"]
)

PREDICTION_ERRORS = Counter(
    "ids_prediction_errors_total",
    "Total prediction or explanation errors",
    ["endpoint", "error_type"]
)

REQUEST_LATENCY = Histogram(
    "ids_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

MODEL_INFO = Gauge(
    "ids_model_info",
    "Information about currently deployed IDS model",
    ["strategy", "run_id"]
)

LATEST_DRIFT_SCORE = Gauge(
    "ids_latest_drift_score",
    "Latest statistical drift score recorded by detector"
)

DRIFT_EVENTS_TOTAL = Counter(
    "ids_drift_events_total",
    "Total drift events detected",
    ["strategy"]
)

RETRAINING_EVENTS_TOTAL = Counter(
    "ids_retraining_events_total",
    "Total retraining cycles completed",
    ["strategy"]
)

RETRAINING_DURATION_SECONDS = Gauge(
    "ids_retraining_duration_seconds",
    "Retraining time in seconds for latest adaptation event",
    ["strategy"]
)

# Research Metrics from Evaluated Strategies
STRATEGY_RECENT_F1 = Gauge(
    "ids_strategy_recent_f1",
    "Recent F1 score on forward evaluation split",
    ["strategy"]
)

STRATEGY_HISTORICAL_F1 = Gauge(
    "ids_strategy_historical_f1",
    "Historical F1 retention score on holdout test set",
    ["strategy"]
)

STRATEGY_FORGETTING = Gauge(
    "ids_strategy_forgetting",
    "Catastrophic forgetting metric (F1_baseline - F1_adapted)",
    ["strategy"]
)

STRATEGY_FPR = Gauge(
    "ids_strategy_fpr",
    "False Positive Rate on evaluation window",
    ["strategy"]
)

# ---------------------------------------------------------
# FastAPI App Initialization
# ---------------------------------------------------------
app = FastAPI(
    title="Adaptive IDS Inference & Observability API",
    description="Production inference endpoint with Prometheus monitoring and SHAP local explainability."
)

# Model state
model = None
explainer = None
model_metadata = {
    "strategy": "Unloaded",
    "run_id": "None",
    "feature_names": []
}


try:
    from pydantic import field_validator
    USE_FIELD_VALIDATOR = True
except ImportError:
    from pydantic import validator
    USE_FIELD_VALIDATOR = False


class NetworkTrafficFeature(BaseModel):
    """
    Input schema for network flow predictions.
    Validates that features dictionary is provided, non-empty, and contains numeric values.
    """
    features: Dict[str, float] = Field(
        ...,
        json_schema_extra={"example": {"Flow Duration": 150.0, "Flow Bytes/s": 4200.0, "Packet Length Mean": 45.0}}
    )

    if USE_FIELD_VALIDATOR:
        @field_validator("features")
        @classmethod
        def validate_features(cls, v):
            if not v:
                raise ValueError("Features dictionary cannot be empty.")
            for key, val in v.items():
                if not isinstance(val, (int, float)):
                    raise ValueError(f"Feature '{key}' must be numeric (int or float). Got: {type(val).__name__}")
                if np.isnan(val) or np.isinf(val):
                    raise ValueError(f"Feature '{key}' contains invalid NaN or Infinite value.")
            return v
    else:
        @validator("features")
        def validate_features_v1(cls, v):
            if not v:
                raise ValueError("Features dictionary cannot be empty.")
            for key, val in v.items():
                if not isinstance(val, (int, float)):
                    raise ValueError(f"Feature '{key}' must be numeric. Got: {type(val).__name__}")
                if np.isnan(val) or np.isinf(val):
                    raise ValueError(f"Feature '{key}' contains invalid NaN or Infinite value.")
            return v



class AttributionItem(BaseModel):
    feature: str
    feature_value: float
    attribution: float


class ExplanationResponse(BaseModel):
    prediction: int
    label: str
    base_value: float
    feature_attributions: List[AttributionItem]
    disclaimer: str


def sync_mlflow_metrics_to_prometheus():
    """
    Reads experiment metrics from MLflow backend (e.g. SQLite database)
    and synchronizes them to Prometheus Gauges for Grafana visualization.
    """
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(tracking_uri)
    try:
        experiment = mlflow.get_experiment_by_name("Adaptive_IDS_Experiment")
        if not experiment:
            return
        runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        if runs.empty:
            return

        # For each strategy, populate the latest metric values
        strategies = ["S1_Static", "S2_RecentOnly", "S3_RandomReplay", "S4_PatternReplay"]
        for strat in strategies:
            strat_runs = runs[runs["params.strategy"] == strat]
            if not strat_runs.empty:
                latest_run = strat_runs.sort_values(by="start_time", ascending=False).iloc[0]
                
                # Extract metrics if present
                if "metrics.recent_f1" in latest_run and not pd.isna(latest_run["metrics.recent_f1"]):
                    STRATEGY_RECENT_F1.labels(strategy=strat).set(float(latest_run["metrics.recent_f1"]))
                elif "metrics.f1_score" in latest_run and not pd.isna(latest_run["metrics.f1_score"]):
                    STRATEGY_RECENT_F1.labels(strategy=strat).set(float(latest_run["metrics.f1_score"]))

                if "metrics.historical_f1" in latest_run and not pd.isna(latest_run["metrics.historical_f1"]):
                    STRATEGY_HISTORICAL_F1.labels(strategy=strat).set(float(latest_run["metrics.historical_f1"]))

                if "metrics.forgetting" in latest_run and not pd.isna(latest_run["metrics.forgetting"]):
                    STRATEGY_FORGETTING.labels(strategy=strat).set(float(latest_run["metrics.forgetting"]))

                if "metrics.fpr" in latest_run and not pd.isna(latest_run["metrics.fpr"]):
                    STRATEGY_FPR.labels(strategy=strat).set(float(latest_run["metrics.fpr"]))
                elif "metrics.recent_fpr" in latest_run and not pd.isna(latest_run["metrics.recent_fpr"]):
                    STRATEGY_FPR.labels(strategy=strat).set(float(latest_run["metrics.recent_fpr"]))

                if "metrics.training_time" in latest_run and not pd.isna(latest_run["metrics.training_time"]):
                    RETRAINING_DURATION_SECONDS.labels(strategy=strat).set(float(latest_run["metrics.training_time"]))

        # Set latest drift score if available
        if "params.drift_score" in runs.columns:
            drift_scores = runs["params.drift_score"].dropna()
            if not drift_scores.empty:
                try:
                    LATEST_DRIFT_SCORE.set(float(drift_scores.iloc[0]))
                except (ValueError, TypeError):
                    pass

    except Exception as e:
        print(f"Warning: Failed to sync MLflow metrics to Prometheus: {e}")


@app.on_event("startup")
def startup_event():
    """
    On application startup, load the most recent model from MLflow,
    initialize the SHAP explainer, and sync Prometheus gauges.
    """
    global model, explainer, model_metadata
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(tracking_uri)
    
    try:
        experiment = mlflow.get_experiment_by_name("Adaptive_IDS_Experiment")
        loaded_model = None
        strategy_name = "Unknown_Strategy"
        run_id = "None"
        
        if experiment:
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["start_time DESC"],
                max_results=10
            )
            for _, run_row in runs.iterrows():
                cur_run_id = run_row.run_id
                model_uri = f"runs:/{cur_run_id}/model"
                try:
                    loaded_model = mlflow.xgboost.load_model(model_uri)
                    strategy_name = run_row.get("params.strategy", "Unknown_Strategy")
                    run_id = cur_run_id
                    break
                except Exception:
                    art_uri = str(run_row.get("artifact_uri", ""))
                    rel_candidates = []
                    if "Mlops_cp/" in art_uri:
                        sub = art_uri.split("Mlops_cp/")[-1]
                        rel_candidates.extend([sub, os.path.join("/app", sub), os.path.join(".", sub)])
                    for cand in rel_candidates:
                        for test_p in [os.path.join(cand, "model"), cand]:
                            if os.path.exists(test_p):
                                try:
                                    loaded_model = mlflow.xgboost.load_model(test_p)
                                    strategy_name = run_row.get("params.strategy", "Unknown_Strategy")
                                    run_id = cur_run_id
                                    break
                                except Exception:
                                    pass
                        if loaded_model is not None:
                            break
                    if loaded_model is not None:
                        break

        # Fallback: scan mlruns artifact directories if runs:/ resolution did not find model
        if loaded_model is None:
            artifact_dirs = glob.glob("adaptive-ids/mlruns/1/models/*/artifacts") + glob.glob("mlruns/1/models/*/artifacts")
            for art_dir in sorted(artifact_dirs, key=os.path.getmtime, reverse=True):
                try:
                    loaded_model = mlflow.xgboost.load_model(art_dir)
                    strategy_name = "S4_PatternReplay"
                    run_id = os.path.basename(os.path.dirname(art_dir))
                    break
                except Exception:
                    pass

        if loaded_model is not None:
            model = loaded_model
            model_metadata["strategy"] = str(strategy_name)
            model_metadata["run_id"] = str(run_id)
            feat_names = list(getattr(loaded_model, "feature_names_in_", []))
            model_metadata["feature_names"] = feat_names
            MODEL_INFO.labels(strategy=str(strategy_name), run_id=str(run_id)).set(1)

            if SHAP_AVAILABLE:
                try:
                    explainer = shap.TreeExplainer(model)
                except Exception as ex_err:
                    print(f"Warning: Could not initialize TreeExplainer: {ex_err}")
                    explainer = None
            print(f"IDS Model successfully loaded: strategy={strategy_name}, run_id={run_id}, features={feat_names}")

        # Sync operational experiment metrics into Prometheus gauges
        sync_mlflow_metrics_to_prometheus()

    except Exception as e:
        print(f"Notice: Model could not be loaded on startup ({e}). API remains healthy.")


@app.get("/health")
def health_check():
    """Health check endpoint indicating service status and model loading state."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "strategy": model_metadata["strategy"],
        "run_id": model_metadata["run_id"],
        "shap_available": SHAP_AVAILABLE and explainer is not None,
        "features": model_metadata.get("feature_names", [])
    }


@app.get("/metrics")
def metrics():
    """Exposes Prometheus time-series metrics."""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.post("/telemetry/sync")
def sync_telemetry():
    """Explicitly resyncs MLflow experiment metrics into Prometheus gauges."""
    sync_mlflow_metrics_to_prometheus()
    return {"status": "synchronized"}


@app.post("/predict")
def predict(traffic: NetworkTrafficFeature):
    """
    Accepts validated network traffic flow features and returns IDS classification.
    0 = Benign Traffic, 1 = Intrusion / Attack Traffic.
    """
    start_t = time.time()
    endpoint = "/predict"

    if model is None:
        PREDICTION_ERRORS.labels(endpoint=endpoint, error_type="model_not_loaded").inc()
        REQUEST_COUNT.labels(endpoint=endpoint, status="503").inc()
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Please train or register a model via MLflow first."
        )

    try:
        expected_features = model_metadata.get("feature_names", [])
        if expected_features:
            missing = [f for f in expected_features if f not in traffic.features]
            if missing:
                PREDICTION_ERRORS.labels(endpoint=endpoint, error_type="missing_features").inc()
                REQUEST_COUNT.labels(endpoint=endpoint, status="422").inc()
                raise HTTPException(status_code=422, detail=f"Missing required model features: {missing}")
            df = pd.DataFrame([traffic.features])[expected_features]
        else:
            df = pd.DataFrame([traffic.features])

        pred = int(model.predict(df)[0])
        label = "Attack" if pred == 1 else "Benign"

        # Extract probability if supported
        prob = 0.5
        try:
            prob_arr = model.predict_proba(df)[0]
            prob = float(prob_arr[1])
        except Exception:
            pass

        # Record metrics with bounded labels
        strat = model_metadata.get("strategy", "unknown")
        PREDICTION_COUNT.labels(prediction_label=label, strategy=strat).inc()
        REQUEST_COUNT.labels(endpoint=endpoint, status="200").inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_t)

        return {
            "prediction": pred,
            "label": label,
            "probability": round(prob, 4),
            "strategy": strat
        }

    except HTTPException:
        raise
    except Exception as e:
        PREDICTION_ERRORS.labels(endpoint=endpoint, error_type=type(e).__name__).inc()
        REQUEST_COUNT.labels(endpoint=endpoint, status="400").inc()
        raise HTTPException(status_code=400, detail=f"Inference error: {str(e)}")


@app.post("/explain", response_model=ExplanationResponse)
def explain(traffic: NetworkTrafficFeature):
    """
    Computes local feature attributions using SHAP for an individual network traffic packet.
    Returns feature attributions indicating each feature's contribution to the classification.
    """
    start_t = time.time()
    endpoint = "/explain"

    if model is None:
        PREDICTION_ERRORS.labels(endpoint=endpoint, error_type="model_not_loaded").inc()
        REQUEST_COUNT.labels(endpoint=endpoint, status="503").inc()
        raise HTTPException(status_code=503, detail="Model is not loaded. Train a model first.")

    if not SHAP_AVAILABLE or explainer is None:
        PREDICTION_ERRORS.labels(endpoint=endpoint, error_type="shap_unavailable").inc()
        REQUEST_COUNT.labels(endpoint=endpoint, status="501").inc()
        raise HTTPException(status_code=501, detail="SHAP explainer is unavailable in current runtime.")

    try:
        expected_features = model_metadata.get("feature_names", [])
        if expected_features:
            missing = [f for f in expected_features if f not in traffic.features]
            if missing:
                PREDICTION_ERRORS.labels(endpoint=endpoint, error_type="missing_features").inc()
                REQUEST_COUNT.labels(endpoint=endpoint, status="422").inc()
                raise HTTPException(status_code=422, detail=f"Missing required model features: {missing}")
            df = pd.DataFrame([traffic.features])[expected_features]
        else:
            df = pd.DataFrame([traffic.features])

        pred = int(model.predict(df)[0])
        label = "Attack" if pred == 1 else "Benign"

        shap_values = explainer(df)
        base_val = float(shap_values.base_values[0]) if hasattr(shap_values.base_values, "__getitem__") else float(shap_values.base_values)
        vals = shap_values.values[0]

        attributions = []
        for feat_name, attr_val in zip(df.columns, vals):
            attributions.append(AttributionItem(
                feature=feat_name,
                feature_value=float(traffic.features[feat_name]),
                attribution=round(float(attr_val), 4)
            ))

        # Sort features by absolute attribution magnitude
        attributions.sort(key=lambda x: abs(x.attribution), reverse=True)

        REQUEST_COUNT.labels(endpoint=endpoint, status="200").inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_t)

        return ExplanationResponse(
            prediction=pred,
            label=label,
            base_value=round(base_val, 4),
            feature_attributions=attributions,
            disclaimer=(
                "Feature attributions reflect local tree attribution against base value "
                "and do not constitute proof that the model is correct, unbiased, or fair."
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        PREDICTION_ERRORS.labels(endpoint=endpoint, error_type=type(e).__name__).inc()
        REQUEST_COUNT.labels(endpoint=endpoint, status="400").inc()
        raise HTTPException(status_code=400, detail=f"Explanation generation failed: {str(e)}")

