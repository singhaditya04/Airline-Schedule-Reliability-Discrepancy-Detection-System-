from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.data.validator import validate_schema
from src.utils.config import COLUMN_RENAME_MAP, DEFAULT_COLUMNS


def load_csv(filepath: Path, expected_columns: List[str]) -> pd.DataFrame:
    """Load a CSV file and validate its raw schema."""
    df = pd.read_csv(filepath, dtype=str)
    validate_schema(df, expected_columns, filepath.name)
    return df


def normalize_columns(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    rename_map = COLUMN_RENAME_MAP.get(dataset_name, {})
    normalized = df.rename(columns=rename_map).copy()

    if dataset_name == "published":
        normalized["has_codeshare"] = normalized.get("has_codeshare", "No")
        normalized["codeshare_partner"] = normalized.get("codeshare_partner", "")
        normalized["partner_flight_id"] = normalized.get("partner_flight_id", "")

    return normalized


def load_data(paths: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """Load all required datasets and return normalized DataFrames."""
    loaded = {}
    for name, path in paths.items():
        filepath = Path(path)
        if not filepath.exists():
            raise FileNotFoundError(f"Required dataset not found: {filepath}")

        expected_columns = DEFAULT_COLUMNS.get(name)
        if expected_columns is None:
            raise ValueError(f"No expected columns defined for dataset: {name}")

        df = load_csv(filepath, expected_columns)
        df = normalize_columns(df, name)
        loaded[name] = df

    return loaded
