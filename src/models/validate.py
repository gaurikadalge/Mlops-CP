from typing import Dict, Any, Optional


def quality_gate(
    candidate_metrics: Dict[str, float],
    reference_metrics: Optional[Dict[str, float]] = None,
    min_f1: float = 0.5,
    max_fpr: float = 0.1,
    max_forgetting: Optional[float] = None
) -> bool:
    """
    Determines if a candidate model meets deployment criteria:
    - Recent F1 >= min_f1
    - Recent FPR <= max_fpr
    - (Optional) Forgetting <= max_forgetting
    - (Optional) Relative drop vs reference model <= threshold
    """
    f1 = candidate_metrics.get("f1_score", candidate_metrics.get("Recent F1", candidate_metrics.get("recent_f1", 0.0)))
    fpr = candidate_metrics.get("fpr", candidate_metrics.get("FPR", candidate_metrics.get("recent_fpr", 1.0)))

    # Basic threshold checks
    if f1 < min_f1 or fpr > max_fpr:
        return False

    # Optional forgetting constraint
    if max_forgetting is not None:
        forgetting = candidate_metrics.get("forgetting", candidate_metrics.get("Forgetting", 0.0))
        if forgetting > max_forgetting:
            return False

    # Relative checks against current model if reference metrics provided
    if reference_metrics:
        ref_f1 = reference_metrics.get("f1_score", reference_metrics.get("Recent F1", reference_metrics.get("recent_f1", 0.0)))
        if f1 < ref_f1 - 0.1:
            return False

    return True

