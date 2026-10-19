import pandas as pd
from typing import Dict, Any, List, Optional


def create_strategy_result(
    strategy: str,
    recent_f1: float,
    historical_f1: float,
    forgetting: float,
    fpr: float,
    recent_records: int,
    historical_records: int,
    total_records: int,
    training_time: float,
    window_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Standardizes result dictionary for each adaptation strategy.
    """
    return {
        "Strategy": strategy,
        "Window": window_id or "N/A",
        "Recent F1": round(recent_f1, 4),
        "Historical F1": round(historical_f1, 4),
        "Forgetting": round(forgetting, 4),
        "FPR": round(fpr, 4),
        "Recent Records": int(recent_records),
        "Hist Records": int(historical_records),
        "Total Records": int(total_records),
        "Training Time (s)": round(training_time, 4)
    }


def build_comparison_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Creates a pandas DataFrame summarizing strategy performance.
    """
    df = pd.DataFrame(results)
    return df


def validate_budget_equality(
    results: List[Dict[str, Any]],
    expected_budget: int,
    strategies_to_check: Optional[List[str]] = None
) -> bool:
    """
    Verifies that compared strategies strictly adhere to identical total record budgets.
    Raises ValueError if any audited strategy violates the budget constraint.
    """
    if strategies_to_check is None:
        strategies_to_check = ["S3_RandomReplay", "S4_PatternReplay"]

    for r in results:
        strat = r.get("Strategy", "")
        if any(s in strat for s in strategies_to_check):
            actual = r.get("Total Records", 0)
            if actual != expected_budget:
                raise ValueError(
                    f"Budget violation for {strat}: expected exactly {expected_budget} records, got {actual}."
                )
    return True
