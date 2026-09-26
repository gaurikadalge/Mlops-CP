from typing import Dict, Any

def quality_gate(candidate_metrics: Dict[str, float], reference_metrics: Dict[str, float] = None, min_f1: float = 0.5, max_fpr: float = 0.1) -> bool:
    """
    Determines if a candidate model meets the criteria to replace the current model.
    """
    f1 = candidate_metrics.get("f1_score", 0.0)
    fpr = candidate_metrics.get("fpr", 1.0)
    
    # Basic threshold checks
    if f1 < min_f1 or fpr > max_fpr:
        return False
        
    # Relative checks against current model if reference metrics provided
    if reference_metrics:
        ref_f1 = reference_metrics.get("f1_score", 0.0)
        # We don't want a massive drop in F1 (e.g., dropping by more than 0.1)
        if f1 < ref_f1 - 0.1:
            return False
            
    return True
