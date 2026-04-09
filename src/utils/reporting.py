"""Reporting utilities for generating summary insights."""
import pandas as pd


def generate_discrepancy_summary(schedule_report: pd.DataFrame) -> pd.DataFrame:
    """Generate summary of discrepancies by type and severity."""
    if schedule_report.empty:
        return pd.DataFrame()

    # Count discrepancies by type
    issue_types = {
        "Missing in Published": schedule_report["missing_in_published"].sum(),
        "Missing in Master": schedule_report["missing_in_master"].sum(),
        "Departure Time Mismatch": schedule_report["departure_diff_minutes"].notna().sum(),
        "Arrival Time Mismatch": schedule_report["arrival_diff_minutes"].notna().sum(),
        "Aircraft Mismatch": schedule_report["aircraft_mismatch"].sum(),
        "Terminal Mismatch": schedule_report["terminal_mismatch"].sum(),
    }

    # Count by severity
    severity_counts = schedule_report["severity"].value_counts().to_dict()

    summary = {
        "Issue Type": list(issue_types.keys()),
        "Count": list(issue_types.values()),
    }

    return pd.DataFrame(summary)


def generate_severity_distribution(schedule_report: pd.DataFrame) -> pd.DataFrame:
    """Generate distribution of issues by severity level."""
    if schedule_report.empty:
        return pd.DataFrame()

    severity_counts = schedule_report["severity"].value_counts().reset_index()
    severity_counts.columns = ["severity", "count"]

    severity_order = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0, "OK": -1}
    severity_counts["order"] = severity_counts["severity"].map(severity_order)
    severity_counts = severity_counts.sort_values("order", ascending=False).drop("order", axis=1)

    severity_counts["percent"] = (
        severity_counts["count"] / severity_counts["count"].sum() * 100
    ).round(2)

    return severity_counts


def generate_codeshare_summary(codeshare_report: pd.DataFrame) -> pd.DataFrame:
    """Generate summary of codeshare validation issues."""
    if codeshare_report.empty:
        return pd.DataFrame(
            {
                "Issue Type": ["No Codeshare Flights"],
                "Count": [0],
            }
        )

    codeshare_issues = {
        "Missing Partner Flight": codeshare_report["missing_partner_flight"].sum(),
        "Time Mismatch": codeshare_report["time_mismatch_minutes"].notna().sum(),
        "Not Available": codeshare_report["not_available"].sum(),
    }

    return pd.DataFrame({
        "Issue Type": list(codeshare_issues.keys()),
        "Count": list(codeshare_issues.values()),
    })


def generate_summary_report(
    schedule_report: pd.DataFrame,
    codeshare_report: pd.DataFrame,
    kpi_summary: pd.DataFrame,
) -> str:
    """Generate a text summary report of the validation results."""
    lines = [
        "\n" + "="*70,
        "AIRLINE SCHEDULE VALIDATION REPORT",
        "="*70,
        "",
    ]

    # KPI Metrics
    if not kpi_summary.empty:
        lines.append("KEY PERFORMANCE INDICATORS (KPIs)")
        lines.append("-" * 70)
        for _, row in kpi_summary.iterrows():
            metric = row["metric"].replace("_", " ").title()
            value = row["value"]
            if "pct" in row["metric"]:
                lines.append(f"  {metric:<40} {value:.2f}%")
            else:
                lines.append(f"  {metric:<40} {int(value)}")
        lines.append("")

    # Schedule Discrepancies
    if not schedule_report.empty:
        lines.append("SCHEDULE DISCREPANCY SUMMARY")
        lines.append("-" * 70)
        disc_summary = generate_discrepancy_summary(schedule_report)
        for _, row in disc_summary.iterrows():
            lines.append(f"  {row['Issue Type']:<40} {row['Count']:<10}")
        lines.append("")

    # Severity Distribution
    if not schedule_report.empty:
        lines.append("ISSUE SEVERITY DISTRIBUTION")
        lines.append("-" * 70)
        severity_dist = generate_severity_distribution(schedule_report)
        for _, row in severity_dist.iterrows():
            lines.append(
                f"  {row['severity']:<15} {row['count']:<10} ({row['percent']:.1f}%)"
            )
        lines.append("")

    # Codeshare Summary
    if not codeshare_report.empty:
        lines.append("CODESHARE VALIDATION SUMMARY")
        lines.append("-" * 70)
        codeshare_summary = generate_codeshare_summary(codeshare_report)
        for _, row in codeshare_summary.iterrows():
            lines.append(f"  {row['Issue Type']:<40} {row['Count']:<10}")
        lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)
