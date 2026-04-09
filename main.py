from pathlib import Path

from src.codeshare import validate_codeshare
from src.data.loader import load_data
from src.discrepancy import detect_discrepancies
from src.export import export_results
from src.kpi import compute_kpis
from src.utils.config import DEFAULT_INPUT_PATHS, LOG_DIR, OUTPUT_DIR
from src.utils.logger import setup_logging
from src.utils.reporting import generate_summary_report
from src.validation import validate_schedule


def main() -> None:
    logger = setup_logging(LOG_DIR / "pipeline.log")
    logger.info("Starting Airline Schedule Validation pipeline")

    try:
        datasets = load_data(DEFAULT_INPUT_PATHS)
        logger.info("Successfully loaded datasets: %s", ", ".join(datasets.keys()))

        master_df = datasets["master"]
        published_df = datasets["published"]
        codeshare_df = datasets["codeshare"]

        schedule_report = validate_schedule(master_df, published_df)
        schedule_report = detect_discrepancies(schedule_report)
        logger.info("Schedule validation complete. Total flights processed: %d", len(schedule_report))

        codeshare_report = validate_codeshare(schedule_report, codeshare_df)
        logger.info("Codeshare validation complete. Total codeshare records: %d", len(codeshare_report))

        kpi_summary = compute_kpis(schedule_report, codeshare_report)
        logger.info("KPI computation complete.")

        exported_paths = export_results(schedule_report, codeshare_report, kpi_summary, OUTPUT_DIR)
        logger.info("Exported results to: %s", OUTPUT_DIR)

        summary_report = generate_summary_report(schedule_report, codeshare_report, kpi_summary)
        print(summary_report)

        logger.info("Pipeline completed successfully.")

    except Exception as exc:
        logger.exception("Pipeline execution failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
