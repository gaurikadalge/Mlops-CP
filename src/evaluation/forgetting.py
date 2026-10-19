import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import xgboost as xgb
from src.models.predict import predict_xgboost
from src.evaluation.metrics import evaluate_performance


def calculate_forgetting(baseline_hist_f1: float, current_hist_f1: float) -> float:
    """
    Computes catastrophic forgetting metric:
        Forgetting = F1_baseline_historical - F1_current_historical
    A positive value indicates performance degradation on historical attacks.
    A negative or zero value indicates retention or positive transfer.
    """
    return float(baseline_hist_f1 - current_hist_f1)


def evaluate_historical_retention(
    model: xgb.XGBClassifier,
    hist_test_X: pd.DataFrame,
    hist_test_y: pd.Series,
    baseline_hist_f1: float
) -> Dict[str, float]:
    """
    Evaluates an adapted model on the held-out historical test set and returns
    historical F1, FPR, and the forgetting metric relative to the baseline model.
    """
    preds = predict_xgboost(model, hist_test_X)
    perf = evaluate_performance(hist_test_y.to_numpy(), preds)
    current_hist_f1 = perf["f1_score"]
    forgetting = calculate_forgetting(baseline_hist_f1, current_hist_f1)

    return {
        "historical_f1": current_hist_f1,
        "historical_fpr": perf["fpr"],
        "forgetting": forgetting,
        "historical_precision": perf["precision"],
        "historical_recall": perf["recall"]
    }
