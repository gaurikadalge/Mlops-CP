import pandas as pd
import xgboost as xgb
from typing import Dict, Any, Optional, Tuple, Union
from src.preprocessing.loader import Window
from src.models.train import train_xgboost


def adapt_random_replay(
    recent_data: Window,
    historical_data: pd.DataFrame,
    total_budget: int,
    recent_fraction: float = 0.5,
    seed: int = 42,
    model_config: Optional[Dict[str, Any]] = None,
    return_counts: bool = False
) -> Union[xgb.XGBClassifier, Tuple[xgb.XGBClassifier, Dict[str, int]]]:
    """
    Retrains the model using recent data and a random sample of historical data.
    Strictly enforces total_budget constraint without duplicates or replacement.
    """
    recent_budget = int(total_budget * recent_fraction)
    historical_budget = total_budget - recent_budget

    recent_df = recent_data.X.copy()
    recent_df['Label'] = recent_data.y.values

    # 1. Sample recent data
    if len(recent_df) >= recent_budget:
        recent_sample = recent_df.sample(n=recent_budget, random_state=seed, replace=False)
    else:
        recent_sample = recent_df
        historical_budget = total_budget - len(recent_sample)

    # 2. Sample historical data
    if len(historical_data) >= historical_budget:
        historical_sample = historical_data.sample(n=historical_budget, random_state=seed, replace=False)
    else:
        historical_sample = historical_data

    # 3. Combine datasets
    combined_data = pd.concat([recent_sample, historical_sample], ignore_index=True)

    actual_counts = {
        "recent_count": len(recent_sample),
        "historical_count": len(historical_sample),
        "total_count": len(combined_data)
    }

    y_train = combined_data['Label']
    X_train = combined_data.drop(columns=['Label'])

    model = train_xgboost(X_train, y_train, model_config)

    if return_counts:
        return model, actual_counts
    return model

