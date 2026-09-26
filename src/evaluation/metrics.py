import numpy as np
from sklearn.metrics import f1_score, confusion_matrix
from typing import Dict, Any

def evaluate_performance(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Evaluates basic classification performance.
    """
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    # Calculate False Positive Rate
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    else:
        # Handle edge cases where only one class is present in y_true
        fpr = 0.0
        
    return {
        "f1_score": f1,
        "fpr": fpr
    }

def calculate_forgetting(f1_before: float, f1_after: float) -> float:
    """
    Calculates forgetting on historical data after adaptation.
    """
    return f1_before - f1_after
