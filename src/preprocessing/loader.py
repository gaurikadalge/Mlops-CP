import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Window:
    id: str
    X: pd.DataFrame
    y: pd.Series
    timestamp_start: pd.Timestamp
    timestamp_end: pd.Timestamp

def load_dataset(path: str, label_column: str = 'Label', timestamp_column: str = 'Timestamp') -> pd.DataFrame:
    """Loads dataset and performs basic cleaning."""
    df = pd.read_csv(path)
    
    # Basic validation
    if label_column not in df.columns:
        raise ValueError(f"Label column {label_column} not found in dataset.")
        
    # Clean invalid/infinite values
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    # If timestamp column exists, sort by it to preserve chronological order
    if timestamp_column in df.columns:
        df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        df = df.sort_values(by=timestamp_column).reset_index(drop=True)
        
    return df

def create_temporal_windows(df: pd.DataFrame, window_size: int, label_column: str = 'Label', timestamp_column: str = 'Timestamp') -> List[Window]:
    """Generates temporal windows from the dataset without shuffling."""
    windows = []
    num_windows = len(df) // window_size
    
    for i in range(num_windows):
        start_idx = i * window_size
        end_idx = start_idx + window_size
        
        window_df = df.iloc[start_idx:end_idx].copy()
        
        y = window_df[label_column]
        X = window_df.drop(columns=[label_column])
        
        # Determine timestamps if available
        if timestamp_column in window_df.columns:
            ts_start = window_df[timestamp_column].min()
            ts_end = window_df[timestamp_column].max()
            X = X.drop(columns=[timestamp_column])
        else:
            ts_start, ts_end = None, None
            
        windows.append(Window(
            id=f"W{i+1}",
            X=X,
            y=y,
            timestamp_start=ts_start,
            timestamp_end=ts_end
        ))
        
    return windows


def split_temporal_window(window: Window, train_ratio: float = 0.6) -> Tuple[Window, Window]:
    """
    Splits a Window strictly chronologically into an adaptation (training) slice
    and an evaluation (unseen forward testing) slice.
    
    Guarantees:
    - Zero future data leakage into the adaptation split.
    - Zero evaluation on records used for fitting.
    """
    n = len(window.X)
    split_idx = int(n * train_ratio)
    
    adapt_window = Window(
        id=f"{window.id}_adapt",
        X=window.X.iloc[:split_idx].copy().reset_index(drop=True),
        y=window.y.iloc[:split_idx].copy().reset_index(drop=True),
        timestamp_start=window.timestamp_start,
        timestamp_end=None
    )
    eval_window = Window(
        id=f"{window.id}_eval",
        X=window.X.iloc[split_idx:].copy().reset_index(drop=True),
        y=window.y.iloc[split_idx:].copy().reset_index(drop=True),
        timestamp_start=None,
        timestamp_end=window.timestamp_end
    )
    return adapt_window, eval_window

