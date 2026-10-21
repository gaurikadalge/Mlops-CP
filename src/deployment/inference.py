"""
AWS SageMaker Inference Handler for Adaptive IDS XGBoost Model.
Implements the canonical SageMaker Python SDK entry points:
  - model_fn(model_dir)
  - input_fn(request_body, request_content_type)
  - predict_fn(input_data, model)
  - output_fn(prediction, accept)
"""
import os
import io
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from typing import Dict, Any, Union, List, Tuple

# Default expected feature schema
DEFAULT_FEATURE_NAMES = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Packet Length Mean",
    "Packet Length Std",
    "SYN Flag Count",
    "ACK Flag Count"
]


def model_fn(model_dir: str) -> Union[xgb.Booster, xgb.XGBClassifier]:
    """
    Loads the trained XGBoost model from the SageMaker model artifact directory.
    Searches for model.ubj, model.json, or model.bin.
    """
    candidates = [
        os.path.join(model_dir, "model.ubj"),
        os.path.join(model_dir, "model.json"),
        os.path.join(model_dir, "model.bin"),
        os.path.join(model_dir, "xgboost-model"),
    ]
    
    # Also check recursive search in model_dir
    if not any(os.path.exists(c) for c in candidates):
        for root, _, files in os.walk(model_dir):
            for file in files:
                if file.endswith((".ubj", ".json", ".bin")):
                    candidates.append(os.path.join(root, file))
                    
    for path in candidates:
        if os.path.exists(path):
            booster = xgb.Booster()
            booster.load_model(path)
            return booster
            
    raise FileNotFoundError(f"No compatible XGBoost model artifact found in: {model_dir}")


def input_fn(request_body: Union[str, bytes], request_content_type: str = "application/json") -> pd.DataFrame:
    """
    Deserializes and validates incoming payload for inference.
    Supports application/json and text/csv.
    """
    if request_content_type in ("application/json", "application/json; charset=utf-8"):
        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")
        data = json.loads(request_body)
        
        # Support dict with 'features' key or list of dicts
        if isinstance(data, dict):
            if "features" in data:
                raw_records = [data["features"]]
            else:
                raw_records = [data]
        elif isinstance(data, list):
            raw_records = [item.get("features", item) if isinstance(item, dict) else item for item in data]
        else:
            raise ValueError("JSON request body must be an object or list of objects.")
            
        df = pd.DataFrame(raw_records)
        
    elif request_content_type in ("text/csv", "text/csv; charset=utf-8"):
        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")
        df = pd.read_csv(io.StringIO(request_body))
        # If no header provided, name columns using default features
        if df.columns.dtype == int or all(isinstance(c, int) for c in df.columns):
            cols = DEFAULT_FEATURE_NAMES[:len(df.columns)]
            df.columns = cols
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}. Use application/json or text/csv.")

    # Validation: non-empty, numeric, and finite
    if df.empty:
        raise ValueError("Input dataset is empty.")
        
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Feature column '{col}' must contain numeric values.")
        if df[col].isnull().any() or np.isinf(df[col]).any():
            raise ValueError(f"Feature column '{col}' contains NaN or infinite values.")

    return df


def predict_fn(input_data: pd.DataFrame, model: Union[xgb.Booster, xgb.XGBClassifier]) -> List[Dict[str, Any]]:
    """
    Executes model inference on validated input DataFrame.
    Returns prediction classifications, probabilities, and labels.
    """
    # Align features with model expectations if known
    expected_cols = getattr(model, "feature_names", None)
    if expected_cols is None and hasattr(model, "feature_names_in_") and model.feature_names_in_ is not None:
        expected_cols = list(model.feature_names_in_)

    if expected_cols:
        aligned_df = pd.DataFrame(index=input_data.index)
        for col in expected_cols:
            if col in input_data.columns:
                aligned_df[col] = input_data[col]
            else:
                aligned_df[col] = 0.0
        input_data = aligned_df

    if isinstance(model, xgb.Booster):
        dmatrix = xgb.DMatrix(input_data)
        raw_probs = model.predict(dmatrix)
    elif hasattr(model, "predict_proba"):
        raw_probs = model.predict_proba(input_data)[:, 1]
    else:
        raw_probs = model.predict(input_data)

    results = []
    for prob in raw_probs:
        p = float(prob)
        binary_pred = 1 if p >= 0.5 else 0
        label = "Attack" if binary_pred == 1 else "Benign"
        results.append({
            "prediction": binary_pred,
            "label": label,
            "probability": round(p, 4)
        })
    return results


def output_fn(prediction: List[Dict[str, Any]], accept: str = "application/json") -> Tuple[str, str]:
    """
    Serializes prediction results according to requested Accept header.
    """
    if accept in ("application/json", "application/json; charset=utf-8", "*/*", ""):
        return json.dumps({"predictions": prediction}), "application/json"
    elif accept in ("text/csv", "text/csv; charset=utf-8"):
        out_df = pd.DataFrame(prediction)
        return out_df.to_csv(index=False), "text/csv"
    else:
        raise ValueError(f"Unsupported Accept header: {accept}. Use application/json or text/csv.")
