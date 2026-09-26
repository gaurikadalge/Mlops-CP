import math
from typing import Dict, Any, List, Tuple

def calculate_distance(current_profile: Dict[str, Any], pattern_profile: Dict[str, Any], epsilon: float = 1e-6) -> float:
    """
    Calculates statistical distance between current drift profile and a historical pattern.
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

def retrieve_patterns(current_profile: Dict[str, Any], memory: List[Dict[str, Any]], top_k: int) -> List[Tuple[str, float]]:
    """
    Retrieves Top-K relevant patterns from historical memory based on statistical distance.
    """
    scores = []
    
    for pattern in memory:
        distance = calculate_distance(current_profile, pattern)
        # We can define similarity as inverse of distance, but returning distance is fine for ranking (lower is better)
        scores.append((pattern["pattern_id"], distance))
        
    # Sort by distance (ascending)
    scores.sort(key=lambda x: x[1])
    
    return scores[:top_k]
