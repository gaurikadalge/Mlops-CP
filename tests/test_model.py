import pytest
import pandas as pd
import numpy as np
from src.models.train import train_xgboost
from src.models.predict import predict_xgboost
from src.models.validate import quality_gate


def test_train_and_predict_xgboost():
    np.random.seed(42)
    X = pd.DataFrame({
        'f1': np.random.normal(0, 1, 100),
        'f2': np.random.normal(5, 2, 100)
    })
    # Simple linearly separable target
    y = (X['f1'] + X['f2'] > 5).astype(int)
    
    model = train_xgboost(X, y)
    preds = predict_xgboost(model, X)
    
    assert len(preds) == 100
    assert set(preds).issubset({0, 1})
    accuracy = (preds == y).mean()
    assert accuracy > 0.85


def test_quality_gate_thresholds():
    # Passing metrics
    good_metrics = {"f1_score": 0.88, "fpr": 0.03, "forgetting": 0.02}
    assert quality_gate(good_metrics, min_f1=0.7, max_fpr=0.05) is True

    # Failing due to low F1
    low_f1 = {"f1_score": 0.45, "fpr": 0.02}
    assert quality_gate(low_f1, min_f1=0.7) is False

    # Failing due to high FPR
    high_fpr = {"f1_score": 0.85, "fpr": 0.15}
    assert quality_gate(high_fpr, max_fpr=0.1) is False

    # Relative drop against reference model
    ref_metrics = {"f1_score": 0.90}
    degraded_metrics = {"f1_score": 0.78, "fpr": 0.02}  # Drop of 0.12 > 0.10 threshold
    assert quality_gate(degraded_metrics, reference_metrics=ref_metrics) is False
