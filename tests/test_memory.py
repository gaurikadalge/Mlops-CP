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


def test_wasserstein_distance_and_ranking():
    # Arrange: generate synthetic empirical distributions
    import numpy as np
    from src.memory.retrieve import calculate_wasserstein_distance
    
    np.random.seed(42)
    # Current unlabeled traffic
    curr_df = pd.DataFrame({
        'f1': np.random.normal(50, 5, 500),
        'f2': np.random.normal(100, 10, 500)
    })
    
    # Exact match distribution
    p_exact = pd.DataFrame({
        'f1': np.random.normal(50, 5, 500),
        'f2': np.random.normal(100, 10, 500)
    })
    
    # Near distribution (slight shift)
    p_near = pd.DataFrame({
        'f1': np.random.normal(55, 5, 500),
        'f2': np.random.normal(110, 10, 500)
    })
    
    # Far distribution (large shift)
    p_far = pd.DataFrame({
        'f1': np.random.normal(200, 5, 500),
        'f2': np.random.normal(500, 10, 500)
    })
    
    dist_exact = calculate_wasserstein_distance(curr_df, p_exact)
    dist_near = calculate_wasserstein_distance(curr_df, p_near)
    dist_far = calculate_wasserstein_distance(curr_df, p_far)
    
    # Assert distances are strictly monotonic
    assert dist_exact < dist_near < dist_far
    
    # Test retrieval ranking with memory map
    memory = [
        {"pattern_id": "far", "sample_data": p_far},
        {"pattern_id": "near", "sample_data": p_near},
        {"pattern_id": "exact", "sample_data": p_exact}
    ]
    top_p = retrieve_patterns(curr_df, memory, top_k=2)
    assert len(top_p) == 2
    assert top_p[0][0] == "exact"
    assert top_p[1][0] == "near"


def test_unlabeled_retrieval_does_not_access_labels():
    # Verify retrieval functions seamlessly when current traffic has NO labels
    import numpy as np
    np.random.seed(42)
    curr_unlabeled = pd.DataFrame({
        'duration': np.random.normal(10, 2, 200),
        'bytes': np.random.normal(1000, 100, 200)
    })
    assert 'Label' not in curr_unlabeled.columns
    assert 'Attack Type' not in curr_unlabeled.columns

    p1 = pd.DataFrame({'duration': np.random.normal(10, 2, 200), 'bytes': np.random.normal(1000, 100, 200)})
    p2 = pd.DataFrame({'duration': np.random.normal(50, 2, 200), 'bytes': np.random.normal(5000, 100, 200)})

    memory = [{"pattern_id": "p1", "sample_data": p1}, {"pattern_id": "p2", "sample_data": p2}]
    ranked = retrieve_patterns(curr_unlabeled, memory, top_k=1)
    assert ranked[0][0] == "p1"

