import pytest
import pandas as pd
import numpy as np
from src.preprocessing.loader import Window
from src.adaptation.random_replay import adapt_random_replay
from src.adaptation.pattern_replay import adapt_pattern_replay

# Mock the train_xgboost so we don't actually train a model during data tests
import src.adaptation.random_replay
import src.adaptation.pattern_replay

def mock_train(X, y, config):
    return (X, y) # Return the data instead of a model so we can assert shapes

def test_random_replay_budget(monkeypatch):
    monkeypatch.setattr(src.adaptation.random_replay, "train_xgboost", mock_train)
    
    # Arrange
    total_budget = 1000
    recent_data = Window(
        id="W1",
        X=pd.DataFrame({'f1': range(800)}),
        y=pd.Series([0]*800),
        timestamp_start=None,
        timestamp_end=None
    )
    historical_data = pd.DataFrame({'f1': range(2000), 'Label': [1]*2000})
    
    # Act
    X_train, y_train = adapt_random_replay(recent_data, historical_data, total_budget=total_budget, recent_fraction=0.5)
    
    # Assert
    assert len(X_train) == total_budget
    assert len(y_train) == total_budget
    # Since recent fraction is 0.5, we should have 500 recent and 500 historical
    assert sum(y_train == 0) == 500
    assert sum(y_train == 1) == 500

def test_pattern_replay_budget(monkeypatch):
    monkeypatch.setattr(src.adaptation.pattern_replay, "train_xgboost", mock_train)
    
    # Arrange
    total_budget = 1000
    recent_data = Window(
        id="W1",
        X=pd.DataFrame({'f1': range(800)}),
        y=pd.Series([0]*800),
        timestamp_start=None,
        timestamp_end=None
    )
    
    current_profile = {} # Doesn't matter, we'll mock retrieval
    memory_patterns = []
    
    # Mock retrieval to return two patterns
    monkeypatch.setattr(src.adaptation.pattern_replay, "retrieve_patterns", lambda *args, **kwargs: [("p1", 0.1), ("p2", 0.2)])
    
    memory_data_map = {
        "p1": pd.DataFrame({'f1': range(1000), 'Label': [1]*1000}),
        "p2": pd.DataFrame({'f1': range(1000), 'Label': [2]*1000})
    }
    
    # Act
    X_train, y_train = adapt_pattern_replay(
        recent_data, current_profile, memory_patterns, memory_data_map, 
        total_budget=total_budget, recent_fraction=0.5, top_k=2
    )
    
    # Assert
    assert len(X_train) == total_budget
    assert len(y_train) == total_budget
    assert sum(y_train == 0) == 500 # 50% recent
    assert sum(y_train == 1) == 250 # 25% pattern 1
    assert sum(y_train == 2) == 250 # 25% pattern 2
