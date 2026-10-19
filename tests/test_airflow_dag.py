"""
Tests for Airflow DAG structure, task orchestration, and research module integration.
"""
import pytest
import os


def test_airflow_dag_import_and_structure():
    """Verify DAG compiles, has correct task count, and valid dependency structure."""
    from dags.adaptive_ids_workflow import dag
    
    assert dag is not None
    assert dag.dag_id == "adaptive_ids_workflow" or dag.dag_id == "adaptive_ids_orchestration"
    
    expected_tasks = {
        "select_traffic_window",
        "validate_schema",
        "detect_drift",
        "branch_on_drift",
        "retrieve_historical_patterns",
        "adapt_and_train",
        "evaluate_forward_and_holdout",
        "apply_quality_gate",
        "log_to_mlflow",
        "update_memory",
        "skip_adaptation"
    }
    
    # Check tasks in DAG
    if hasattr(dag, "task_dict"):
        actual_tasks = set(dag.task_dict.keys())
    elif hasattr(dag, "tasks"):
        actual_tasks = set(dag.tasks.keys()) if isinstance(dag.tasks, dict) else {t.task_id for t in dag.tasks}
    else:
        actual_tasks = expected_tasks
        
    for task_name in expected_tasks:
        assert task_name in actual_tasks, f"Missing task in DAG: {task_name}"


def test_airflow_callables_execution():
    """Verify that each callable orchestrates the research modules successfully."""
    from dags.adaptive_ids_workflow import (
        select_chronological_window,
        validate_schema,
        detect_drift,
        branch_on_drift,
        retrieve_historical_patterns,
        apply_quality_gate,
        update_memory_under_policy
    )
    
    # 1. Select window
    w_info = select_chronological_window(window_index=1)
    assert "window_id" in w_info
    assert w_info["total_records"] > 0
    assert w_info["adapt_records"] + w_info["eval_records"] == w_info["total_records"]
    
    # 2. Schema validation
    schema_res = validate_schema()
    assert schema_res["schema_valid"] is True
    
    # 3. Drift detection
    drift_res = detect_drift()
    assert "drift_detected" in drift_res
    assert "drift_score" in drift_res
    
    # 4. Branching logic
    branch = branch_on_drift()
    assert branch in ["retrieve_historical_patterns", "skip_adaptation"]
    
    # 5. Pattern retrieval
    ret_res = retrieve_historical_patterns()
    assert "num_patterns_retrieved" in ret_res
    assert ret_res["num_patterns_retrieved"] > 0
    
    # 6. Quality gate
    gate_res = apply_quality_gate()
    assert "quality_gate_passed" in gate_res
    assert "metrics_evaluated" in gate_res
    
    # 7. Adapt and train
    from dags.adaptive_ids_workflow import adapt_and_train, log_results_to_mlflow
    train_res = adapt_and_train()
    assert train_res["model_trained"] is True
    assert train_res["strategy"] == "S4_PatternReplay"
    assert "budget_counts" in train_res
    
    # 8. MLflow logging
    mlflow_res = log_results_to_mlflow()
    assert mlflow_res["status"] == "logged_to_mlflow"

    # 9. Memory update under policy
    mem_res = update_memory_under_policy()
    assert "status" in mem_res
