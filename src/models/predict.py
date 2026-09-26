import xgboost as xgb
import pandas as pd
import numpy as np

def predict_xgboost(model: xgb.XGBClassifier, X_test: pd.DataFrame) -> np.ndarray:
    """Generates predictions using the trained XGBoost model."""
    return model.predict(X_test)
    
def predict_proba_xgboost(model: xgb.XGBClassifier, X_test: pd.DataFrame) -> np.ndarray:
    """Generates prediction probabilities using the trained XGBoost model."""
    return model.predict_proba(X_test)
