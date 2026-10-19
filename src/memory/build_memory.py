import pandas as pd
from typing import Dict, Any, List, Tuple
from src.memory.profile import profile_pattern


def build_historical_memory(
    hist_df: pd.DataFrame,
    feature_cols: List[str],
    attack_column: str = "Attack Type",
    label_column: str = "Label",
    min_samples: int = 50,
    samples_per_pattern: int = 4000,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], Dict[str, pd.DataFrame]]:
    """
    Constructs the Historical Pattern Memory bank from historical training data.
    
    Returns:
        memory_patterns: List of pattern profiles with statistics and empirical samples.
        memory_data_map: Dict mapping attack_type -> DataFrame of sample flows with labels.
    """
    memory_patterns = []
    memory_data_map = {}
    
    if attack_column not in hist_df.columns:
        raise ValueError(f"Attack column '{attack_column}' not found in historical data.")

    attack_types = [a for a in hist_df[attack_column].dropna().unique() if a != "BENIGN"]

    for attack_type in sorted(attack_types):
        subset = hist_df[hist_df[attack_column] == attack_type]
        if len(subset) >= min_samples:
            pattern_features = subset[feature_cols]
            profile = profile_pattern(
                pattern_features,
                pattern_id=str(attack_type),
                feature_columns=feature_cols,
                include_samples=True,
                max_samples=samples_per_pattern,
                seed=seed
            )
            memory_patterns.append(profile)

            # Store sampled raw data (features + label) for replay
            cols_to_keep = [c for c in feature_cols if c in subset.columns]
            if label_column in subset.columns:
                cols_to_keep.append(label_column)
            
            pattern_full = subset[cols_to_keep]
            n_samples = min(samples_per_pattern, len(pattern_full))
            memory_data_map[str(attack_type)] = pattern_full.sample(n=n_samples, random_state=seed)

    return memory_patterns, memory_data_map
