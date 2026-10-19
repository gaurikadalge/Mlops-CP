import pandas as pd
import xgboost as xgb
from typing import Dict, Any, Optional, Tuple, Union
from src.preprocessing.loader import Window
from src.models.train import train_xgboost


def adapt_recent_only(
    recent_data: Window,
    total_budget: Optional[int] = None,
    seed: int = 42,
    model_config: Optional[Dict[str, Any]] = None,
    return_counts: bool = False
) -> Union[xgb.XGBClassifier, Tuple[xgb.XGBClassifier, Dict[str, int]]]:
    """
    Retrains the model using only recent window data.
    Enforces total_budget constraint when provided to match S3 and S4 comparisons.
    """
    X_rec = recent_data.X.copy()
    y_rec = recent_data.y.copy()

    if total_budget is not None:
        if len(X_rec) > total_budget:
            # Deterministic sample to budget constraint
            sampled_idx = X_rec.sample(n=total_budget, random_state=seed).index
            X_train = X_rec.loc[sampled_idx].reset_index(drop=True)
            y_train = y_rec.loc[sampled_idx].reset_index(drop=True)
        elif len(X_rec) < total_budget:
            # If recent data cannot satisfy budget without duplicates or leakage, use available
            X_train = X_rec.reset_index(drop=True)
            y_train = y_rec.reset_index(drop=True)
        else:
            X_train = X_rec.reset_index(drop=True)
            y_train = y_rec.reset_index(drop=True)
    else:
        X_train = X_rec.reset_index(drop=True)
        y_train = y_rec.reset_index(drop=True)

    counts = {
        "recent_count": len(X_train),
        "historical_count": 0,
        "total_count": len(X_train)
    }

    model = train_xgboost(X_train, y_train, model_config)

    if return_counts:
        return model, counts
    return model

