import xgboost as xgb
import pandas as pd
from typing import Dict, Any

def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series, config: Dict[str, Any] = None) -> xgb.XGBClassifier:
    """Trains an XGBoost model on the provided data."""
    if config is None:
        config = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'use_label_encoder': False
        }
        
    model = xgb.XGBClassifier(**config)
    model.fit(X_train, y_train)
    
    return model
