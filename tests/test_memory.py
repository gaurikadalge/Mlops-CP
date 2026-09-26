import pytest
import pandas as pd
from src.memory.profile import profile_pattern
from src.memory.retrieve import calculate_distance, retrieve_patterns

def test_profile_pattern():
    # Arrange
    df = pd.DataFrame({
        'feat1': [1, 2, 3, 4, 5],
        'feat2': [10, 20, 30, 40, 50]
    })
    
    # Act
    profile = profile_pattern(df, "test_pattern", ['feat1', 'feat2'])
    
    # Assert
    assert profile["pattern_id"] == "test_pattern"
    assert profile["count"] == 5
    assert profile["feature_statistics"]["feat1"]["mean"] == 3.0
    assert profile["feature_statistics"]["feat2"]["mean"] == 30.0

def test_retrieve_patterns():
    # Arrange
    current_profile = {
        "feature_statistics": {
            "feat1": {"mean": 10.0, "std": 1.0},
            "feat2": {"mean": 20.0, "std": 1.0}
        }
    }
    
    memory = [
        {
            "pattern_id": "far_pattern",
            "feature_statistics": {
                "feat1": {"mean": 100.0, "std": 1.0},
                "feat2": {"mean": 200.0, "std": 1.0}
            }
        },
        {
            "pattern_id": "close_pattern",
            "feature_statistics": {
                "feat1": {"mean": 11.0, "std": 1.0},
                "feat2": {"mean": 21.0, "std": 1.0}
            }
        },
        {
            "pattern_id": "exact_pattern",
            "feature_statistics": {
                "feat1": {"mean": 10.0, "std": 1.0},
                "feat2": {"mean": 20.0, "std": 1.0}
            }
        }
    ]
    
    # Act
    top_patterns = retrieve_patterns(current_profile, memory, top_k=2)
    
    # Assert
    assert len(top_patterns) == 2
    assert top_patterns[0][0] == "exact_pattern"
    assert top_patterns[1][0] == "close_pattern"
