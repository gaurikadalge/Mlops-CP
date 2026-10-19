import pandas as pd
import xgboost as xgb
from typing import Dict, Any, List, Optional, Tuple, Union
from src.preprocessing.loader import Window
from src.models.train import train_xgboost
from src.memory.retrieve import retrieve_patterns


def adapt_pattern_replay(
    recent_data: Window,
    current_profile: Union[Dict[str, Any], pd.DataFrame],
    memory_patterns: List[Dict[str, Any]],
    memory_data_map: Dict[str, pd.DataFrame],
    total_budget: int,
    recent_fraction: float = 0.5,
    top_k: int = 2,
    seed: int = 42,
    model_config: Optional[Dict[str, Any]] = None,
    return_counts: bool = False,
    historical_fallback_pool: Optional[pd.DataFrame] = None
) -> Union[xgb.XGBClassifier, Tuple[xgb.XGBClassifier, Dict[str, int]]]:
    """
    Retrains the model using recent data and pattern-aware selected historical data.
    Strictly guarantees that total_budget equals S3 (random replay) budget
    by redistributing any shortfalls across retrieved patterns or available historical data.
    """
    recent_budget = int(total_budget * recent_fraction)
    historical_budget = total_budget - recent_budget

    # 1. Prepare and sample recent data
    recent_df = recent_data.X.copy()
    recent_df['Label'] = recent_data.y.values

    if len(recent_df) >= recent_budget:
        recent_sample = recent_df.sample(n=recent_budget, random_state=seed, replace=False)
    else:
        recent_sample = recent_df
        historical_budget = total_budget - len(recent_sample)

    # 2. Retrieve relevant historical patterns
    # No label information from current_data is used
    top_patterns = retrieve_patterns(
        current_profile,
        memory_patterns,
        top_k=top_k,
        memory_data_map=memory_data_map
    )

    # 3. Allocate historical budget with shortfall redistribution
    historical_samples = []
    deficit = historical_budget

    if top_patterns and historical_budget > 0:
        base_per_pattern = historical_budget // len(top_patterns)
        pattern_allocations = {pat_id: base_per_pattern for pat_id, _ in top_patterns}
        # Assign division remainder to the first pattern
        first_pat_id = top_patterns[0][0]
        pattern_allocations[first_pat_id] += historical_budget - sum(pattern_allocations.values())

        # First pass: sample from patterns up to allocation
        unfilled_budget = 0
        collected_dfs = []
        for pat_id, _ in top_patterns:
            target_alloc = pattern_allocations[pat_id]
            pat_df = memory_data_map.get(pat_id)
            if pat_df is not None and not pat_df.empty:
                if len(pat_df) >= target_alloc:
                    sampled = pat_df.sample(n=target_alloc, random_state=seed, replace=False)
                    collected_dfs.append(sampled)
                else:
                    collected_dfs.append(pat_df)
                    unfilled_budget += (target_alloc - len(pat_df))
            else:
                unfilled_budget += target_alloc

        # Second pass: if any patterns had a deficit, redistribute to patterns that have surplus capacity
        if unfilled_budget > 0:
            for pat_id, _ in top_patterns:
                pat_df = memory_data_map.get(pat_id)
                already_sampled_count = pattern_allocations[pat_id]
                if pat_df is not None and len(pat_df) > already_sampled_count:
                    surplus_available = len(pat_df) - already_sampled_count
                    take = min(surplus_available, unfilled_budget)
                    # Sample additional records excluding already sampled
                    extra = pat_df.iloc[already_sampled_count:already_sampled_count + take]
                    collected_dfs.append(extra)
                    unfilled_budget -= take
                    if unfilled_budget == 0:
                        break

        # Third pass: if still deficit, fallback to historical_fallback_pool
        if unfilled_budget > 0 and historical_fallback_pool is not None and not historical_fallback_pool.empty:
            take = min(len(historical_fallback_pool), unfilled_budget)
            fallback_sample = historical_fallback_pool.sample(n=take, random_state=seed, replace=False)
            collected_dfs.append(fallback_sample)
            unfilled_budget -= take

        historical_samples = collected_dfs

    # 4. Combine datasets
    datasets_to_concat = [recent_sample] + historical_samples
    combined_data = pd.concat(datasets_to_concat, ignore_index=True)

    actual_counts = {
        "recent_count": len(recent_sample),
        "historical_count": sum(len(h) for h in historical_samples),
        "total_count": len(combined_data)
    }

    y_train = combined_data['Label']
    X_train = combined_data.drop(columns=['Label'])

    model = train_xgboost(X_train, y_train, model_config)

    if return_counts:
        return model, actual_counts
    return model

