import pytest
import pandas as pd
import numpy as np
from src.drift.ks_detector import detect_drift

def test_no_drift_identical_distributions():
    # Arrange: Create two identical normal distributions
    np.random.seed(42)
    ref_data = pd.DataFrame({'feature_1': np.random.normal(0, 1, 1000), 'feature_2': np.random.normal(5, 2, 1000)})
    curr_data = pd.DataFrame({'feature_1': np.random.normal(0, 1, 1000), 'feature_2': np.random.normal(5, 2, 1000)})
    
    # Act
    result = detect_drift(ref_data, curr_data, p_value_threshold=0.05, min_drifted_features=1)
    
    # Assert
    assert result["drift_detected"] is False
    assert len(result["drifted_features"]) == 0

def test_drift_different_distributions():
    # Arrange: Create shifted distributions
    np.random.seed(42)
    ref_data = pd.DataFrame({
        'feature_1': np.random.normal(0, 1, 1000), 
        'feature_2': np.random.normal(5, 2, 1000),
        'feature_3': np.random.normal(10, 3, 1000)
    })
    curr_data = pd.DataFrame({
        'feature_1': np.random.normal(3, 1, 1000), # Shifted mean
        'feature_2': np.random.normal(5, 5, 1000), # Shifted variance
        'feature_3': np.random.normal(15, 3, 1000) # Shifted mean
    })
    
    # Act
    result = detect_drift(ref_data, curr_data, p_value_threshold=0.05, min_drifted_features=2)
    
    # Assert
    assert result["drift_detected"] is True
    assert len(result["drifted_features"]) >= 2
