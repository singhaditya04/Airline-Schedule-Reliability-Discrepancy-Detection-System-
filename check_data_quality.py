"""Script to run data quality checks on input datasets."""
from src.data.loader import load_data
from src.utils.config import DEFAULT_INPUT_PATHS
from src.utils.data_quality import DataQualityReport


def run_data_quality_checks():
    """Load datasets and print quality reports."""
    print("\nRunning data quality checks on input datasets...\n")

    datasets = load_data(DEFAULT_INPUT_PATHS)

    for dataset_name, df in datasets.items():
        report = DataQualityReport(df, name=dataset_name.upper())
        report.print_summary()


if __name__ == "__main__":
    run_data_quality_checks()
