import pandas as pd
import xgboost as xgb
from typing import Dict, Any
from src.preprocessing.loader import Window
from src.models.train import train_xgboost

def adapt_recent_only(recent_data: Window, model_config: Dict[str, Any] = None) -> xgb.XGBClassifier:
    """
    Retrains the model using only the recent window data.
    """
    return train_xgboost(recent_data.X, recent_data.y, model_config)
