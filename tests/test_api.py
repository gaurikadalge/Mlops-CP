import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from src.pipeline.serve import app, model, explainer
import src.pipeline.serve as serve_module
from src.models.train import train_xgboost
import shap


@pytest.fixture(scope="module")
def client():
    # Setup test model so predict and explain endpoints have a valid model in test environment
    np.random.seed(42)
    feature_names = ["Flow Duration", "Flow Bytes/s", "Packet Length Mean"]
    X = pd.DataFrame(np.random.normal(50, 10, (100, 3)), columns=feature_names)
    y = (X["Flow Duration"] > 50).astype(int)
    test_model = train_xgboost(X, y)
    
    # Inject test model into serve module
    serve_module.model = test_model
    serve_module.model_metadata["strategy"] = "S4_PatternReplay"
    serve_module.model_metadata["run_id"] = "test-run-123"
    try:
        serve_module.explainer = shap.TreeExplainer(test_model)
    except Exception:
        serve_module.explainer = None

    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["strategy"] == "S4_PatternReplay"


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    metrics_text = response.text
    assert "ids_http_requests_total" in metrics_text
    assert "ids_predictions_total" in metrics_text
    assert "ids_model_info" in metrics_text


def test_predict_endpoint_valid_benign_or_attack(client):
    payload = {
        "features": {
            "Flow Duration": 20.0,
            "Flow Bytes/s": 3500.0,
            "Packet Length Mean": 40.0
        }
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert data["prediction"] in [0, 1]
    assert data["label"] in ["Attack", "Benign"]
    assert "probability" in data
    assert data["strategy"] == "S4_PatternReplay"


def test_predict_invalid_inputs(client):
    # Empty features dict
    empty_resp = client.post("/predict", json={"features": {}})
    assert empty_resp.status_code == 422  # Pydantic validation error

    # Non-numeric string feature
    invalid_type_resp = client.post("/predict", json={
        "features": {"Flow Duration": "not-a-number"}
    })
    assert invalid_type_resp.status_code == 422

    # Malformed payload structure
    bad_structure_resp = client.post("/predict", json={"invalid_key": 123})
    assert bad_structure_resp.status_code == 422


def test_explain_endpoint_shap(client):
    payload = {
        "features": {
            "Flow Duration": 65.0,
            "Flow Bytes/s": 4200.0,
            "Packet Length Mean": 25.0
        }
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "label" in data
    assert "base_value" in data
    assert "feature_attributions" in data
    assert len(data["feature_attributions"]) == 3
    # Check attribution fields
    first_attr = data["feature_attributions"][0]
    assert "feature" in first_attr
    assert "feature_value" in first_attr
    assert "attribution" in first_attr
    assert "disclaimer" in data
    assert "not constitute proof" in data["disclaimer"]



def test_telemetry_sync_endpoint(client):
    response = client.post("/telemetry/sync")
    assert response.status_code == 200
    assert response.json()["status"] == "synchronized"
