import pandas as pd
from typing import Dict, Any

def profile_pattern(pattern_data: pd.DataFrame, pattern_id: str, feature_columns: list) -> Dict[str, Any]:
    """
    Calculates the statistical profile for a given pattern.
    """
    profile = {
        "pattern_id": pattern_id,
        "count": len(pattern_data),
        "feature_statistics": {}
    }
    
    for col in feature_columns:
        if col in pattern_data.columns:
            profile["feature_statistics"][col] = {
                "mean": float(pattern_data[col].mean()),
                "std": float(pattern_data[col].std())
            }
            
    return profile
