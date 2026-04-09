"""Utility functions for data transformation and validation."""
import pandas as pd


def safe_fill_nulls(series: pd.Series, filler: str | int = "NaN") -> pd.Series:
    """Fill null values in a series safely."""
    return series.fillna(str(filler))


def normalize_string(value: str | None) -> str:
    """Normalize string input: strip whitespace and lowercase."""
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def safe_boolean_check(series: pd.Series, true_values: list[str] = None) -> pd.Series:
    """Convert series to boolean based on known true values."""
    if true_values is None:
        true_values = ["yes", "true", "1", "y"]
    
    return series.fillna("").astype(str).str.strip().str.lower().isin(true_values)


def time_diff_minutes(time1: pd.Timestamp, time2: pd.Timestamp) -> float | None:
    """Calculate time difference in minutes between two timestamps."""
    if pd.isna(time1) or pd.isna(time2):
        return None
    return abs((time1 - time2).total_seconds() / 60)
