import pandas as pd
from scipy.stats import ks_2samp
from typing import Dict, Any, List

def detect_drift(reference_window: pd.DataFrame, current_window: pd.DataFrame, p_value_threshold: float = 0.05, min_drifted_features: int = 3) -> Dict[str, Any]:
    """
    Detects drift between a reference window and a current window using the KS test.
    """
    drifted_features = []
    feature_statistics = {}
    ks_scores = []
    
    # Compare each numerical feature
    for column in reference_window.select_dtypes(include=['number']).columns:
        if column in current_window.columns:
            ref_data = reference_window[column].dropna()
            curr_data = current_window[column].dropna()
            
            if len(ref_data) > 0 and len(curr_data) > 0:
                ks_stat, p_value = ks_2samp(ref_data, curr_data)
                ks_scores.append(ks_stat)
                
                feature_statistics[column] = {
                    'ks_stat': ks_stat,
                    'p_value': p_value
                }
                
                if p_value < p_value_threshold:
                    drifted_features.append(column)
                    
    # Calculate overall drift score
    drift_score = sum(ks_scores) / len(ks_scores) if ks_scores else 0.0
    
    # Determine if drift is detected based on threshold
    drift_detected = len(drifted_features) >= min_drifted_features
    
    return {
        "drift_detected": drift_detected,
        "drift_score": drift_score,
        "drifted_features": drifted_features,
        "feature_statistics": feature_statistics
    }
