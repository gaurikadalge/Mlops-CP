import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


def profile_pattern(
    pattern_data: pd.DataFrame,
    pattern_id: str,
    feature_columns: List[str],
    include_samples: bool = True,
    max_samples: int = 2000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Calculates the statistical profile for a given pattern.
    Optionally stores subsampled empirical distributions for Wasserstein distance computation.
    """
    profile = {
        "pattern_id": pattern_id,
        "count": len(pattern_data),
        "feature_statistics": {},
        "feature_samples": {}
    }
    
    # Optional subsampling for memory efficiency
    if include_samples and len(pattern_data) > max_samples:
        sample_df = pattern_data.sample(n=max_samples, random_state=seed)
    else:
        sample_df = pattern_data

    for col in feature_columns:
        if col in pattern_data.columns:
            series = pattern_data[col].dropna()
            profile["feature_statistics"][col] = {
                "mean": float(series.mean()) if len(series) > 0 else 0.0,
                "std": float(series.std()) if len(series) > 0 else 0.0
            }
            if include_samples and col in sample_df.columns:
                profile["feature_samples"][col] = sample_df[col].dropna().to_numpy(dtype=float)
            
    return profile

