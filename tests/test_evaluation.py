import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.preprocessing.loader import Window, split_temporal_window
from src.evaluation.forgetting import calculate_forgetting, evaluate_historical_retention
from src.evaluation.comparison import validate_budget_equality, create_strategy_result
from src.models.train import train_xgboost


def test_chronological_leakage_prevention():
    # Arrange: create temporal window with explicit timestamps
    base_time = datetime(2023, 1, 1, 0, 0)
    timestamps = [base_time + timedelta(minutes=i) for i in range(100)]
    df = pd.DataFrame({
        'feat': range(100),
        'Label': [0]*50 + [1]*50,
        'Timestamp': timestamps
    })
    
    window = Window(
        id="W_chrono",
        X=df[['feat']],
        y=df['Label'],
        timestamp_start=timestamps[0],
        timestamp_end=timestamps[-1]
    )
    # Attach timestamps to X temporarily to verify chronological ordering
    window.X['ts'] = timestamps

    # Act: split into 60% adapt / 40% eval
    adapt_w, eval_w = split_temporal_window(window, train_ratio=0.6)

    # Assert
    assert len(adapt_w.X) == 60
    assert len(eval_w.X) == 40
    assert len(adapt_w.X) + len(eval_w.X) == 100

    max_adapt_ts = adapt_w.X['ts'].max()
    min_eval_ts = eval_w.X['ts'].min()

    # Strict chronological boundary: adapt timestamps are strictly earlier than eval timestamps
    assert max_adapt_ts < min_eval_ts
    assert len(set(adapt_w.X['feat']).intersection(set(eval_w.X['feat']))) == 0


def test_forgetting_calculation():
    # Baseline F1 = 0.90, current F1 = 0.65 -> Forgetting = +0.25 (degraded)
    assert calculate_forgetting(0.90, 0.65) == pytest.approx(0.25)
    
    # Baseline F1 = 0.80, current F1 = 0.85 -> Forgetting = -0.05 (improved/retained)
    assert calculate_forgetting(0.80, 0.85) == pytest.approx(-0.05)


def test_evaluate_historical_retention():
    np.random.seed(42)
    X = pd.DataFrame({'f1': np.random.normal(0, 1, 100)})
    y = (X['f1'] > 0).astype(int)
    
    model = train_xgboost(X, y)
    res = evaluate_historical_retention(model, X, y, baseline_hist_f1=0.95)

    assert "historical_f1" in res
    assert "historical_fpr" in res
    assert "forgetting" in res
    assert res["historical_f1"] > 0.80
    assert res["forgetting"] == pytest.approx(0.95 - res["historical_f1"])


def test_validate_budget_equality_catches_discrepancy():
    # Valid equal budget
    valid_results = [
        create_strategy_result("S3_RandomReplay", 0.85, 0.90, 0.05, 0.02, 2000, 2000, 4000, 0.5),
        create_strategy_result("S4_PatternReplay", 0.86, 0.92, 0.03, 0.02, 2000, 2000, 4000, 0.5)
    ]
    assert validate_budget_equality(valid_results, expected_budget=4000) is True

    # Invalid unequal budget: S4 only has 3800
    invalid_results = [
        create_strategy_result("S3_RandomReplay", 0.85, 0.90, 0.05, 0.02, 2000, 2000, 4000, 0.5),
        create_strategy_result("S4_PatternReplay", 0.86, 0.92, 0.03, 0.02, 2000, 1800, 3800, 0.5)
    ]
    with pytest.raises(ValueError, match="Budget violation for S4_PatternReplay"):
        validate_budget_equality(invalid_results, expected_budget=4000)
