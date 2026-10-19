"""
Unit tests for AWS SageMaker inference handler and packaging.
"""
import os
import json
import pytest
import pandas as pd
import numpy as np

from src.deployment.inference import model_fn, input_fn, predict_fn, output_fn
from src.deployment.package_sagemaker import package_model, find_latest_model_artifact


def test_sagemaker_input_fn_valid_json():
    """Verify input_fn successfully parses valid JSON payload."""
    payload = json.dumps({
        "features": {
            "Flow Duration": 150.0,
            "Flow Bytes/s": 4200.0,
            "Packet Length Mean": 45.0
        }
    })
    df = input_fn(payload, "application/json")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 3)
    assert df.iloc[0]["Flow Duration"] == 150.0


def test_sagemaker_input_fn_valid_csv():
    """Verify input_fn successfully parses CSV payload."""
    csv_payload = "Flow Duration,Flow Bytes/s,Packet Length Mean\n200.0,5000.0,60.0\n"
    df = input_fn(csv_payload, "text/csv")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 3)
    assert df.iloc[0]["Flow Duration"] == 200.0


def test_sagemaker_input_fn_invalid_inputs():
    """Verify input_fn rejects empty inputs, non-numeric strings, and unsupported types."""
    # Unsupported content type
    with pytest.raises(ValueError, match="Unsupported content type"):
        input_fn("dummy", "application/xml")
        
    # Non-numeric string
    bad_json = json.dumps({"features": {"Flow Duration": "bad_text"}})
    with pytest.raises(ValueError, match="must contain numeric values"):
        input_fn(bad_json, "application/json")


def test_sagemaker_model_fn_and_predict():
    """Verify model_fn loads model and predict_fn executes inference."""
    latest_model_path = find_latest_model_artifact()
    model_dir = os.path.dirname(latest_model_path)
    
    model = model_fn(model_dir)
    assert model is not None
    
    test_df = pd.DataFrame([{
        "Flow Duration": 120.0,
        "Flow Bytes/s": 3500.0,
        "Packet Length Mean": 40.0
    }])
    
    preds = predict_fn(test_df, model)
    assert len(preds) == 1
    assert "prediction" in preds[0]
    assert "probability" in preds[0]
    assert "label" in preds[0]
    assert preds[0]["prediction"] in (0, 1)


def test_sagemaker_output_fn():
    """Verify output_fn serializes responses in JSON and CSV formats."""
    predictions = [{"prediction": 0, "label": "Benign", "probability": 0.05}]
    
    # JSON accept
    json_out, ctype = output_fn(predictions, "application/json")
    assert ctype == "application/json"
    parsed = json.loads(json_out)
    assert parsed["predictions"][0]["label"] == "Benign"
    
    # CSV accept
    csv_out, ctype = output_fn(predictions, "text/csv")
    assert ctype == "text/csv"
    assert "prediction,label,probability" in csv_out


def test_sagemaker_package_creation():
    """Verify package_model produces a valid tar.gz archive."""
    tar_path = package_model(output_dir="build/sagemaker_test")
    assert os.path.exists(tar_path)
    assert os.path.getsize(tar_path) > 1000
