import pandas as pd


SEVERITY_PRIORITY = {
    "Critical": 3,
    "High": 2,
    "Medium": 1,
    "Low": 0,
    "OK": -1,
}


def detect_discrepancies(schedule_report: pd.DataFrame) -> pd.DataFrame:
    """Return the full schedule report sorted by issue severity."""
    if schedule_report.empty:
        return schedule_report.copy()

    report = schedule_report.copy()
    report["severity_rank"] = report["severity"].map(SEVERITY_PRIORITY).fillna(-1)
    report = report.sort_values(
        by=["severity_rank", "flight_id"], ascending=[False, True]
    ).drop(columns=["severity_rank"])
    return report
