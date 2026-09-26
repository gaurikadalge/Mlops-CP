import pandas as pd
import xgboost as xgb
from typing import Dict, Any
from src.preprocessing.loader import Window
from src.models.train import train_xgboost

def adapt_random_replay(recent_data: Window, historical_data: pd.DataFrame, total_budget: int, recent_fraction: float = 0.5, seed: int = 42, model_config: Dict[str, Any] = None) -> xgb.XGBClassifier:
    """
    Retrains the model using recent data and a random sample of historical data.
    """
    recent_budget = int(total_budget * recent_fraction)
    historical_budget = total_budget - recent_budget
    
    # Sample recent data
    recent_df = recent_data.X.copy()
    recent_df['Label'] = recent_data.y
    
    if len(recent_df) > recent_budget:
        recent_sample = recent_df.sample(n=recent_budget, random_state=seed)
    else:
        recent_sample = recent_df
        # Adjust historical budget if we don't have enough recent data
        historical_budget = total_budget - len(recent_sample)
        
    # Sample historical data
    if len(historical_data) > historical_budget:
        historical_sample = historical_data.sample(n=historical_budget, random_state=seed)
    else:
        historical_sample = historical_data
        
    # Combine datasets
    combined_data = pd.concat([recent_sample, historical_sample], ignore_index=True)
    
    # Check budget constraint
    # assert len(combined_data) <= total_budget, f"Exceeded total budget! {len(combined_data)} > {total_budget}"
    
    y_train = combined_data['Label']
    X_train = combined_data.drop(columns=['Label'])
    
    return train_xgboost(X_train, y_train, model_config)
