import pandas as pd


def compute_kpis(
    schedule_report: pd.DataFrame,
    codeshare_report: pd.DataFrame,
) -> pd.DataFrame:
    master_rows = schedule_report[~schedule_report["missing_in_master"]] if not schedule_report.empty else schedule_report
    total_master_flights = master_rows["flight_id"].nunique() if not master_rows.empty else 0

    schedule_issues = (
        master_rows[master_rows["severity"] != "OK"]["flight_id"].nunique()
        if not master_rows.empty
        else 0
    )

    total_codeshare_flights = codeshare_report["flight_id"].nunique() if not codeshare_report.empty else 0
    codeshare_ok = (
        codeshare_report[codeshare_report["severity"] == "OK"]["flight_id"].nunique()
        if not codeshare_report.empty
        else 0
    )

    critical_schedule_count = (
        schedule_report[schedule_report["severity"] == "Critical"]["flight_id"].nunique()
        if not schedule_report.empty
        else 0
    )
    critical_codeshare_count = (
        codeshare_report[codeshare_report["severity"] == "Critical"]["flight_id"].nunique()
        if not codeshare_report.empty
        else 0
    )

    schedule_accuracy = (
        (total_master_flights - schedule_issues) / total_master_flights * 100
        if total_master_flights > 0
        else 0.0
    )
    discrepancy_rate = (
        schedule_issues / total_master_flights * 100 if total_master_flights > 0 else 0.0
    )
    codeshare_health = (
        codeshare_ok / total_codeshare_flights * 100 if total_codeshare_flights > 0 else 0.0
    )

    metrics = [
        {"metric": "total_master_flights", "value": total_master_flights},
        {"metric": "total_codeshare_flights", "value": total_codeshare_flights},
        {"metric": "schedule_accuracy_pct", "value": round(schedule_accuracy, 2)},
        {"metric": "discrepancy_rate_pct", "value": round(discrepancy_rate, 2)},
        {"metric": "codeshare_health_pct", "value": round(codeshare_health, 2)},
        {"metric": "critical_issue_count", "value": critical_schedule_count + critical_codeshare_count},
        {"metric": "critical_schedule_issues", "value": critical_schedule_count},
        {"metric": "critical_codeshare_issues", "value": critical_codeshare_count},
    ]

    return pd.DataFrame(metrics)
