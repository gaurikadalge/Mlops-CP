from typing import Dict, Any, List
import numpy as np


def compute_aggregate_drift_score(feature_statistics: Dict[str, Dict[str, float]]) -> float:
    """
    Computes average KS statistic across all evaluated features.
    """
    if not feature_statistics:
        return 0.0
    stats = [v.get("ks_stat", 0.0) for v in feature_statistics.values()]
    return float(np.mean(stats)) if stats else 0.0


def format_drift_summary(drift_result: Dict[str, Any]) -> str:
    """
    Returns a human-readable summary of a KS drift detection result.
    """
    detected = drift_result.get("drift_detected", False)
    score = drift_result.get("drift_score", 0.0)
    drifted_features = drift_result.get("drifted_features", [])
    status = "ALERT: Significant Drift Detected" if detected else "STABLE: No Significant Drift"
    return (
        f"{status} | Score: {score:.4f} | "
        f"Drifted Features ({len(drifted_features)}): {', '.join(drifted_features[:5])}"
        + ("..." if len(drifted_features) > 5 else "")
    )
