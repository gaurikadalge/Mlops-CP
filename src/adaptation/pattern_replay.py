import pandas as pd
import xgboost as xgb
from typing import Dict, Any, List, Tuple
from src.preprocessing.loader import Window
from src.models.train import train_xgboost
from src.memory.retrieve import retrieve_patterns

def adapt_pattern_replay(recent_data: Window, current_profile: Dict[str, Any], memory_patterns: List[Dict[str, Any]], memory_data_map: Dict[str, pd.DataFrame], total_budget: int, recent_fraction: float = 0.5, top_k: int = 2, seed: int = 42, model_config: Dict[str, Any] = None) -> xgb.XGBClassifier:
    """
    Retrains the model using recent data and pattern-aware selected historical data.
    """
    recent_budget = int(total_budget * recent_fraction)
    historical_budget = total_budget - recent_budget
    
    # 1. Prepare recent data
    recent_df = recent_data.X.copy()
    recent_df['Label'] = recent_data.y
    
    if len(recent_df) > recent_budget:
        recent_sample = recent_df.sample(n=recent_budget, random_state=seed)
    else:
        recent_sample = recent_df
        historical_budget = total_budget - len(recent_sample)
        
    # 2. Retrieve relevant historical patterns
    top_patterns = retrieve_patterns(current_profile, memory_patterns, top_k=top_k)
    
    # 3. Allocate historical budget and sample data
    historical_samples = []
    
    if top_patterns and historical_budget > 0:
        budget_per_pattern = historical_budget // len(top_patterns)
        remaining_budget = historical_budget
        
        for i, (pattern_id, _) in enumerate(top_patterns):
            # Give any leftover division remainder to the last pattern
            current_budget = budget_per_pattern if i < len(top_patterns) - 1 else remaining_budget
            
            pattern_df = memory_data_map.get(pattern_id)
            if pattern_df is not None and not pattern_df.empty:
                if len(pattern_df) > current_budget:
                    sampled = pattern_df.sample(n=current_budget, random_state=seed)
                else:
                    sampled = pattern_df
                    
                historical_samples.append(sampled)
                remaining_budget -= len(sampled)
            else:
                remaining_budget -= 0 # No data found for pattern
                
    # 4. Combine and train
    datasets_to_concat = [recent_sample] + historical_samples
    combined_data = pd.concat(datasets_to_concat, ignore_index=True)
    
    y_train = combined_data['Label']
    X_train = combined_data.drop(columns=['Label'])
    
    return train_xgboost(X_train, y_train, model_config)
