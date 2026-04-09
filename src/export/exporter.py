from pathlib import Path

import pandas as pd


def export_results(
    schedule_report: pd.DataFrame,
    codeshare_report: pd.DataFrame,
    kpi_summary: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    schedule_path = output_dir / "schedule_report.csv"
    codeshare_path = output_dir / "codeshare_report.csv"
    kpi_path = output_dir / "kpi_summary.csv"

    schedule_report.to_csv(schedule_path, index=False)
    codeshare_report.to_csv(codeshare_path, index=False)
    kpi_summary.to_csv(kpi_path, index=False)

    return {
        "schedule_report": schedule_path,
        "codeshare_report": codeshare_path,
        "kpi_summary": kpi_path,
    }
