import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score, confusion_matrix
from typing import Dict, Any


def evaluate_performance(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Evaluates classification performance including F1, FPR, Precision, Recall, and Accuracy.
    """
    y_true_arr = np.asarray(y_true).astype(int)
    y_pred_arr = np.asarray(y_pred).astype(int)

    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    acc = float(accuracy_score(y_true_arr, y_pred_arr))

    # Calculate False Positive Rate
    cm = confusion_matrix(y_true_arr, y_pred_arr)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    elif cm.shape == (1, 1):
        # Single class case
        fpr = 0.0
        tn, fp, fn, tp = int(cm[0, 0]), 0, 0, 0
    else:
        fpr = 0.0
        tn, fp, fn, tp = 0, 0, 0, 0

    return {
        "f1_score": f1,
        "fpr": fpr,
        "precision": prec,
        "recall": rec,
        "accuracy": acc,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn)
    }


def calculate_forgetting(f1_before: float, f1_after: float) -> float:
    """
    Calculates forgetting on historical data after adaptation:
    Forgetting = F1_before - F1_after
    Positive values mean the model forgot historical attack patterns.
    """
    return float(f1_before - f1_after)

