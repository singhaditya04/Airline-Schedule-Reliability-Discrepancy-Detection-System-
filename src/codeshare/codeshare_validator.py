import pandas as pd

CODESHARE_COLUMNS = [
    "partner_flight_id",
    "departure_time",
    "arrival_time",
    "status",
]


def _parse_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%H:%M", errors="coerce")


def _issue_summary(row: pd.Series) -> str:
    issues = []
    if row["missing_partner_flight"]:
        issues.append("Missing partner flight")
    if row["time_mismatch_minutes"] is not None and row["time_mismatch_minutes"] > 0:
        issues.append("Partner time mismatch")
    if row["not_available"]:
        issues.append("Partner status not Available")
    return "; ".join(issues) if issues else "OK"


def _assign_severity(row: pd.Series) -> str:
    if row["missing_partner_flight"]:
        return "Critical"
    if row["not_available"]:
        return "High"
    if row["time_mismatch_minutes"] is not None and row["time_mismatch_minutes"] > 30:
        return "High"
    if row["time_mismatch_minutes"] is not None and 15 < row["time_mismatch_minutes"] <= 30:
        return "Medium"
    if row["time_mismatch_minutes"] is not None and 0 < row["time_mismatch_minutes"] <= 15:
        return "Low"
    return "OK"


def validate_codeshare(
    schedule_report: pd.DataFrame,
    codeshare_df: pd.DataFrame,
) -> pd.DataFrame:
    if schedule_report.empty:
        return pd.DataFrame()

    missing_columns = [col for col in CODESHARE_COLUMNS if col not in codeshare_df.columns]
    if missing_columns:
        raise ValueError(
            f"Codeshare partner dataset is missing required columns: {', '.join(missing_columns)}"
        )

    partner_data = codeshare_df.copy()
    partner_data["departure_time"] = _parse_datetime(partner_data["departure_time"])
    partner_data["arrival_time"] = _parse_datetime(partner_data["arrival_time"])

    reference = schedule_report[
        schedule_report["has_codeshare"].astype(str).str.strip().str.lower() == "yes"
    ].copy()

    if reference.empty:
        return pd.DataFrame(
            columns=[
                "flight_id",
                "partner_flight_id",
                "codeshare_partner",
                "departure_time_master",
                "partner_departure_time",
                "arrival_time_master",
                "partner_arrival_time",
                "status",
                "missing_partner_flight",
                "time_mismatch_minutes",
                "not_available",
                "issue_summary",
                "severity",
            ]
        )

    merged = reference.merge(
        partner_data,
        on="partner_flight_id",
        how="left",
        suffixes=("", "_partner"),
    )

    merged["partner_departure_time"] = merged["departure_time"]
    merged["partner_arrival_time"] = merged["arrival_time"]
    merged["missing_partner_flight"] = merged["partner_departure_time"].isna()

    merged["time_mismatch_minutes"] = merged.apply(
        lambda row: abs(
            (row["departure_time_master"] - row["partner_departure_time"]).total_seconds() / 60
        )
        if pd.notna(row["departure_time_master"]) and pd.notna(row["partner_departure_time"])
        else None,
        axis=1,
    )

    merged["not_available"] = merged["status"].fillna("").str.strip().str.lower() != "available"

    merged["issue_summary"] = merged.apply(_issue_summary, axis=1)
    merged["severity"] = merged.apply(_assign_severity, axis=1)

    return merged[
        [
            "flight_id",
            "partner_flight_id",
            "codeshare_partner",
            "departure_time_master",
            "partner_departure_time",
            "arrival_time_master",
            "partner_arrival_time",
            "status",
            "missing_partner_flight",
            "time_mismatch_minutes",
            "not_available",
            "issue_summary",
            "severity",
        ]
    ]
