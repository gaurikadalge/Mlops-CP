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


def test_strict_fixed_budget_equality_s2_s3_s4(monkeypatch):
    from src.adaptation.recent_only import adapt_recent_only
    from src.evaluation.comparison import validate_budget_equality
    import src.adaptation.recent_only

    monkeypatch.setattr(src.adaptation.recent_only, "train_xgboost", mock_train)
    monkeypatch.setattr(src.adaptation.random_replay, "train_xgboost", mock_train)
    monkeypatch.setattr(src.adaptation.pattern_replay, "train_xgboost", mock_train)
    monkeypatch.setattr(src.adaptation.pattern_replay, "retrieve_patterns", lambda *args, **kwargs: [("p1", 0.1), ("p2", 0.2)])

    target_budget = 600
    recent_data = Window(
        id="W_test",
        X=pd.DataFrame({'f1': range(1000)}),
        y=pd.Series([0]*1000),
        timestamp_start=None,
        timestamp_end=None
    )
    hist_pool = pd.DataFrame({'f1': range(2000), 'Label': [1]*2000})
    memory_map = {
        "p1": pd.DataFrame({'f1': range(1000), 'Label': [1]*1000}),
        "p2": pd.DataFrame({'f1': range(1000), 'Label': [2]*1000})
    }

    # S2
    X_s2, y_s2 = adapt_recent_only(recent_data, total_budget=target_budget)
    # S3
    X_s3, y_s3 = adapt_random_replay(recent_data, hist_pool, total_budget=target_budget, recent_fraction=0.5)
    # S4
    X_s4, y_s4 = adapt_pattern_replay(recent_data, {}, [], memory_map, total_budget=target_budget, recent_fraction=0.5, top_k=2)

    # Strictly equal record counts across all three adaptation strategies
    assert len(X_s2) == len(X_s3) == len(X_s4) == target_budget
    assert len(y_s2) == len(y_s3) == len(y_s4) == target_budget

    records = [
        {"Strategy": "S2_RecentOnly", "Total Records": len(X_s2)},
        {"Strategy": "S3_RandomReplay", "Total Records": len(X_s3)},
        {"Strategy": "S4_PatternReplay", "Total Records": len(X_s4)}
    ]
    assert validate_budget_equality(records, expected_budget=target_budget) is True


def test_pattern_replay_shortfall_redistribution(monkeypatch):
    monkeypatch.setattr(src.adaptation.pattern_replay, "train_xgboost", mock_train)
    monkeypatch.setattr(src.adaptation.pattern_replay, "retrieve_patterns", lambda *args, **kwargs: [("scarce_pat", 0.1), ("abundant_pat", 0.2)])

    total_budget = 1000
    recent_budget = 500
    hist_budget = 500  # 250 targeted per pattern

    recent_data = Window(
        id="W_shortfall",
        X=pd.DataFrame({'f1': range(800)}),
        y=pd.Series([0]*800),
        timestamp_start=None,
        timestamp_end=None
    )

    # scarce_pat has only 50 records (200 deficit), abundant_pat has 1000 records
    memory_map = {
        "scarce_pat": pd.DataFrame({'f1': range(50), 'Label': [1]*50}),
        "abundant_pat": pd.DataFrame({'f1': range(1000), 'Label': [2]*1000})
    }

    X_train, y_train = adapt_pattern_replay(
        recent_data, {}, [], memory_map,
        total_budget=total_budget, recent_fraction=0.5, top_k=2
    )

    # Total budget must be strictly maintained despite deficit
    assert len(X_train) == total_budget
    assert sum(y_train == 0) == recent_budget
    assert sum(y_train == 1) == 50  # all 50 used from scarce pattern
    assert sum(y_train == 2) == 450  # 250 base + 200 redistributed from scarce

