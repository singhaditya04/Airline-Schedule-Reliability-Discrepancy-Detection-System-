from typing import Dict, List

import pandas as pd

from src.data.validator import DataValidationError, validate_required_columns

EXPECTED_SCHEDULE_COLUMNS = [
    "flight_id",
    "origin",
    "destination",
    "departure_time",
    "arrival_time",
    "aircraft_type",
    "terminal",
    "has_codeshare",
    "codeshare_partner",
    "partner_flight_id",
]


def _parse_datetime_column(df: pd.DataFrame, column_name: str) -> pd.Series:
    return pd.to_datetime(df[column_name], format="%H:%M", errors="coerce")


def _build_issue_summary(row: pd.Series) -> str:
    issues: List[str] = []

    if row["missing_in_published"]:
        issues.append("Missing in published schedule")
    if row["missing_in_master"]:
        issues.append("Orphan published flight")
    if row["departure_diff_minutes"] is not None and row["departure_diff_minutes"] > 0:
        issues.append("Departure time mismatch")
    if row["arrival_diff_minutes"] is not None and row["arrival_diff_minutes"] > 0:
        issues.append("Arrival time mismatch")
    if row["aircraft_mismatch"]:
        issues.append("Aircraft mismatch")
    if row["terminal_mismatch"]:
        issues.append("Terminal mismatch")

    return "; ".join(issues) if issues else "OK"


def _assign_severity(row: pd.Series) -> str:
    if row["missing_in_published"] or row["missing_in_master"]:
        return "Critical"

    if row["aircraft_mismatch"]:
        return "High"

    if (
        row["departure_diff_minutes"] is not None
        and row["departure_diff_minutes"] > 60
    ) or (
        row["arrival_diff_minutes"] is not None
        and row["arrival_diff_minutes"] > 60
    ):
        return "High"

    if row["terminal_mismatch"]:
        return "Medium"

    if (
        row["departure_diff_minutes"] is not None
        and 15 < row["departure_diff_minutes"] <= 60
    ) or (
        row["arrival_diff_minutes"] is not None
        and 15 < row["arrival_diff_minutes"] <= 60
    ):
        return "Medium"

    if (
        row["departure_diff_minutes"] is not None
        and 0 < row["departure_diff_minutes"] <= 15
    ) or (
        row["arrival_diff_minutes"] is not None
        and 0 < row["arrival_diff_minutes"] <= 15
    ):
        return "Low"

    return "OK"


def validate_schedule(
    master_df: pd.DataFrame,
    published_df: pd.DataFrame,
) -> pd.DataFrame:
    validate_required_columns(master_df, EXPECTED_SCHEDULE_COLUMNS, "master_schedule")
    validate_required_columns(published_df, EXPECTED_SCHEDULE_COLUMNS, "published_schedule")

    master = master_df.copy()
    published = published_df.copy()

    master["departure_time"] = _parse_datetime_column(master, "departure_time")
    master["arrival_time"] = _parse_datetime_column(master, "arrival_time")
    published["departure_time"] = _parse_datetime_column(published, "departure_time")
    published["arrival_time"] = _parse_datetime_column(published, "arrival_time")

    merged = master.merge(
        published,
        on="flight_id",
        how="outer",
        suffixes=("_master", "_published"),
        indicator=True,
    )

    merged["missing_in_published"] = merged["_merge"] == "left_only"
    merged["missing_in_master"] = merged["_merge"] == "right_only"

    merged["departure_diff_minutes"] = merged.apply(
        lambda row: abs(
            (row["departure_time_master"] - row["departure_time_published"]).total_seconds() / 60
        )
        if pd.notna(row["departure_time_master"]) and pd.notna(row["departure_time_published"])
        else None,
        axis=1,
    )

    merged["arrival_diff_minutes"] = merged.apply(
        lambda row: abs(
            (row["arrival_time_master"] - row["arrival_time_published"]).total_seconds() / 60
        )
        if pd.notna(row["arrival_time_master"]) and pd.notna(row["arrival_time_published"])
        else None,
        axis=1,
    )

    merged["aircraft_mismatch"] = (
        merged["aircraft_type_master"].fillna("")
        != merged["aircraft_type_published"].fillna("")
    ) & (~merged["missing_in_published"] & ~merged["missing_in_master"])

    merged["terminal_mismatch"] = (
        merged["terminal_master"].fillna("")
        != merged["terminal_published"].fillna("")
    ) & (~merged["missing_in_published"] & ~merged["missing_in_master"])

    merged["has_codeshare"] = merged["has_codeshare_master"].fillna(
        merged["has_codeshare_published"].fillna("No")
    )
    merged["codeshare_partner"] = merged["codeshare_partner_master"].fillna(
        merged["codeshare_partner_published"].fillna("")
    )
    merged["partner_flight_id"] = merged["partner_flight_id_master"].fillna(
        merged["partner_flight_id_published"].fillna("")
    )

    merged["issue_summary"] = merged.apply(_build_issue_summary, axis=1)
    merged["severity"] = merged.apply(_assign_severity, axis=1)

    columns = [
        "flight_id",
        "origin_master",
        "destination_master",
        "departure_time_master",
        "arrival_time_master",
        "aircraft_type_master",
        "terminal_master",
        "origin_published",
        "destination_published",
        "departure_time_published",
        "arrival_time_published",
        "aircraft_type_published",
        "terminal_published",
        "has_codeshare",
        "codeshare_partner",
        "partner_flight_id",
        "missing_in_published",
        "missing_in_master",
        "departure_diff_minutes",
        "arrival_diff_minutes",
        "aircraft_mismatch",
        "terminal_mismatch",
        "issue_summary",
        "severity",
    ]

    return merged[columns]
