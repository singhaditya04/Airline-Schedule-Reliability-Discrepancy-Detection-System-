from typing import Iterable, List

import pandas as pd


class DataValidationError(Exception):
    pass


def validate_schema(df: pd.DataFrame, required_columns: Iterable[str], dataset_name: str) -> None:
    """Ensure the DataFrame contains all required columns."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise DataValidationError(
            f"{dataset_name} is missing required columns: {', '.join(missing)}"
        )


def validate_non_empty(df: pd.DataFrame, dataset_name: str) -> None:
    """Ensure the DataFrame is not empty."""
    if df.empty:
        raise DataValidationError(f"{dataset_name} contains no records.")


def validate_required_columns(df: pd.DataFrame, required_columns: List[str], dataset_name: str) -> None:
    validate_schema(df, required_columns, dataset_name)
    validate_non_empty(df, dataset_name)
