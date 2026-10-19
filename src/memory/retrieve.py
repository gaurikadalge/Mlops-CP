import math
from typing import Dict, Any, List, Tuple, Union, Optional
import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance


def calculate_wasserstein_distance(
    current_data: Union[pd.DataFrame, np.ndarray, Dict[str, np.ndarray]],
    pattern_data: Union[pd.DataFrame, np.ndarray, Dict[str, np.ndarray]],
    feature_columns: Optional[List[str]] = None,
    epsilon: float = 1e-6
) -> float:
    """
    Calculates scale-normalized 1D Wasserstein distance averaged across numerical features.
    
    For each feature f:
        W_norm(u, v) = W_1(u, v) / (std(v) + epsilon)
        
    This ensures features with large numerical magnitudes (e.g., flow duration)
    do not dwarf features with smaller ranges (e.g., packet lengths).
    No label information is used during this calculation.
    """
    total_distance = 0.0
    valid_features = 0

    # Extract sample dicts whether inputs are DataFrame, dict, or profile
    if isinstance(current_data, pd.DataFrame):
        u_samples = {c: current_data[c].dropna().to_numpy(dtype=float) for c in current_data.select_dtypes(include=['number']).columns}
    elif isinstance(current_data, dict):
        u_samples = current_data.get("feature_samples", current_data)
    else:
        u_samples = None

    if isinstance(pattern_data, pd.DataFrame):
        v_samples = {c: pattern_data[c].dropna().to_numpy(dtype=float) for c in pattern_data.select_dtypes(include=['number']).columns}
    elif isinstance(pattern_data, dict):
        v_samples = pattern_data.get("feature_samples", pattern_data)
    else:
        v_samples = None

    if u_samples is not None and v_samples is not None and isinstance(u_samples, dict) and isinstance(v_samples, dict):
        cols = feature_columns if feature_columns is not None else [c for c in u_samples.keys() if c in v_samples]
        for col in cols:
            if col in u_samples and col in v_samples:
                u = np.asarray(u_samples[col], dtype=float)
                v = np.asarray(v_samples[col], dtype=float)
                u = u[~np.isnan(u)]
                v = v[~np.isnan(v)]
                if len(u) > 0 and len(v) > 0:
                    raw_w = float(wasserstein_distance(u, v))
                    v_std = float(np.std(v))
                    norm_w = raw_w / (v_std + epsilon)
                    total_distance += norm_w
                    valid_features += 1
    else:
        # Fallback for 2D numpy arrays
        u_arr = np.asarray(current_data, dtype=float)
        v_arr = np.asarray(pattern_data, dtype=float)
        num_features = min(u_arr.shape[1], v_arr.shape[1])
        for j in range(num_features):
            u = u_arr[:, j]
            v = v_arr[:, j]
            u = u[~np.isnan(u)]
            v = v[~np.isnan(v)]
            if len(u) > 0 and len(v) > 0:
                raw_w = float(wasserstein_distance(u, v))
                v_std = float(np.std(v))
                norm_w = raw_w / (v_std + epsilon)
                total_distance += norm_w
                valid_features += 1

    if valid_features == 0:
        return float('inf')

    return total_distance / valid_features


def calculate_distance(current_profile: Dict[str, Any], pattern_profile: Dict[str, Any], epsilon: float = 1e-6) -> float:
    """
    Calculates statistical distance between current drift profile and a historical pattern.
    Preserved for backward-compatibility with summary statistics profiles.
    """
    total_distance = 0.0
    valid_features = 0
    
    current_stats = current_profile.get("feature_statistics", current_profile)
    pattern_stats = pattern_profile.get("feature_statistics", {})
    
    for feature, c_stat in current_stats.items():
        if feature in pattern_stats:
            p_stat = pattern_stats[feature]
            
            c_mean = c_stat["mean"]
            p_mean = p_stat["mean"]
            p_std = p_stat["std"]
            
            if not math.isnan(c_mean) and not math.isnan(p_mean) and not math.isnan(p_std):
                distance = abs(c_mean - p_mean) / (p_std + epsilon)
                total_distance += distance
                valid_features += 1
                
    if valid_features == 0:
        return float('inf')
        
    return total_distance / valid_features


def retrieve_patterns(
    current_input: Union[Dict[str, Any], pd.DataFrame],
    memory: List[Dict[str, Any]],
    top_k: int,
    method: str = "auto",
    feature_columns: Optional[List[str]] = None,
    memory_data_map: Optional[Dict[str, pd.DataFrame]] = None
) -> List[Tuple[str, float]]:
    """
    Retrieves Top-K relevant patterns from historical memory based on statistical distance.
    Supports empirical Wasserstein distance ('wasserstein') or summary statistics distance ('stats').
    """
    scores = []

    # Determine method
    use_wasserstein = (method == "wasserstein")
    if method == "auto":
        # If current_input is DataFrame and either memory items have 'sample_data' or memory_data_map is provided
        if isinstance(current_input, pd.DataFrame):
            use_wasserstein = True
        elif isinstance(current_input, dict) and "feature_samples" in current_input:
            use_wasserstein = True
        elif any(isinstance(p, dict) and ("sample_data" in p or "feature_samples" in p) for p in memory):
            use_wasserstein = True
        elif memory_data_map is not None:
            use_wasserstein = True

    for pattern in memory:
        pattern_id = pattern.get("pattern_id", "unknown")

        if use_wasserstein:
            # Locate empirical samples for this pattern
            pattern_samples = None
            if memory_data_map is not None and pattern_id in memory_data_map:
                pattern_samples = memory_data_map[pattern_id]
            elif "sample_data" in pattern:
                pattern_samples = pattern["sample_data"]
            elif "feature_samples" in pattern:
                pattern_samples = pattern["feature_samples"]

            if pattern_samples is not None:
                dist = calculate_wasserstein_distance(
                    current_input, pattern_samples, feature_columns=feature_columns
                )
            else:
                # Fallback to stats distance if pattern lacks raw sample array
                dist = calculate_distance(current_input, pattern)
        else:
            dist = calculate_distance(current_input, pattern)

        scores.append((pattern_id, dist))

    # Sort by distance (ascending: lower distance = higher similarity)
    scores.sort(key=lambda x: x[1])
    return scores[:top_k]

