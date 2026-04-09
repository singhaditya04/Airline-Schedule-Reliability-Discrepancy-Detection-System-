# IndigoGo Airline Schedule Validation System

A modular, production-grade airline schedule validation engine for comparing internal master schedules against published schedules and validating codeshare partner data. Built inspired by real-world airline operations like IndiGo.

## Project Overview

This system provides:
- **Schedule Validation Engine**: Compare master vs. published schedules to detect discrepancies
- **Discrepancy Detection**: Categorize and severity-rank all issues (Critical, High, Medium, Low)
- **Codeshare Validation**: Validate partner flights and ensure bookability
- **KPI Metrics**: Calculate schedule accuracy, discrepancy rates, and codeshare health
- **Data Export**: Generate structured CSV reports for downstream analysis
- **Comprehensive Logging**: Track all operations with structured logging to files and console

## Project Structure

```
IndigoGoProject/
├── src/
│   ├── data/              # Data loading and schema validation
│   │   ├── loader.py      # CSV loader with normalization
│   │   └── validator.py   # Data validation rules
│   ├── validation/        # Schedule validation engine
│   │   └── schedule_validator.py
│   ├── discrepancy/       # Discrepancy detection
│   │   └── detector.py
│   ├── codeshare/         # Codeshare validation engine
│   │   └── codeshare_validator.py
│   ├── kpi/               # KPI metrics computation
│   │   └── metrics.py
│   ├── export/            # Results export
│   │   └── exporter.py
│   └── utils/
│       ├── config.py      # Configuration and paths
│       ├── logger.py      # Logging setup
│       ├── helpers.py     # Data transformation utilities
│       ├── data_quality.py # Data quality reporting
│       └── reporting.py   # Summary report generation
├── Dataset/               # Input CSV files
│   ├── MASTER_SCHEDULE.csv
│   ├── PUBLISHED_SCHEDULE.csv
│   └── CODESHARE_PARTNER_DATA.csv
├── output/                # Generated output reports (created at runtime)
├── logs/                  # Execution logs (created at runtime)
├── main.py                # Pipeline orchestration entrypoint
├── check_data_quality.py  # Data quality check utility
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Getting Started

### Prerequisites
- Python 3.10+
- Virtual environment (venv, conda, etc.)

### Installation

1. Clone/navigate to the project:
```bash
cd c:\Users\KIIT\Documents\IndigoGoProject
```

2. (Optional) Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Pipeline

Execute the main pipeline:
```bash
python main.py
```

This will:
1. Load and validate all input datasets
2. Run schedule validation (master vs. published)
3. Detect and categorize discrepancies
4. Validate codeshare flights
5. Compute KPIs
6. Export results to CSV files
7. Print a summary report to console

**Output files** are generated in the `output/` directory:
- `schedule_report.csv` - Full schedule validation results with all discrepancies
- `codeshare_report.csv` - Codeshare validation results per codeshare flight
- `kpi_summary.csv` - Key performance indicators as metrics

**Logs** are written to `logs/pipeline.log` with INFO and ERROR level details.

### Data Quality Checks

Run data quality analysis on input datasets:
```bash
python check_data_quality.py
```

This generates null counts, duplicate summaries, and basic statistics per dataset.

## Module Documentation

### Data Loading (`src/data/`)
- **`loader.py`**: Loads CSV files with schema validation and column normalization
  - Converts `flight_number` → `flight_id`, `partner_flight_number` → `partner_flight_id`
  - Adds missing codeshare columns to published schedule

- **`validator.py`**: Schema validation and data integrity checks
  - Validates required columns exist
  - Raises `DataValidationError` on missing/invalid data

### Schedule Validation (`src/validation/schedule_validator.py`)
Compares master vs. published schedules:
- Detects missing flights (in one schedule but not the other)
- Computes time differences (departure/arrival) in minutes
- Checks aircraft type and terminal assignments
- Assigns severity levels:
  - **Critical**: Missing flights
  - **High**: Aircraft mismatch, time diff >60 min
  - **Medium**: Terminal mismatch, time diff 15-60 min
  - **Low**: Time diff <15 min
  - **OK**: No issues

### Discrepancy Detection (`src/discrepancy/detector.py`)
- Sorts schedule report by severity (Critical → High → Medium → Low → OK)
- Returns full report for downstream processing

### Codeshare Validation (`src/codeshare/codeshare_validator.py`)
Validates codeshare flights against partner data:
- Filters master flights where `has_codeshare == "Yes"`
- Checks for missing partner flights
- Verifies time alignment (departure times must match)
- Checks partner status is "Available"
- Assigns severity (Critical/High/Medium/Low/OK)

### KPI Metrics (`src/kpi/metrics.py`)
Computes:
- **Schedule Accuracy %**: (total_flights - discrepant) / total_flights * 100
- **Discrepancy Rate %**: discrepant / total_flights * 100
- **Codeshare Health %**: codeshare_ok / total_codeshare * 100
- **Critical Issue Count**: Total critical-severity issues across schedules and codeshare

### Export (`src/export/exporter.py`)
- Exports DataFrames to CSV files without index
- Creates `output/` directory if needed
- Returns dictionary of exported file paths

### Reporting (`src/utils/reporting.py`)
- Generates summary reports with issue counts by type
- Provides severity distribution percentages
- Formats text report for console output

## Configuration

Edit `src/utils/config.py` to:
- Change input file paths (e.g., different dataset locations)
- Define expected columns per dataset
- Customize column rename mappings

Example:
```python
DEFAULT_INPUT_PATHS = {
    "master": DATA_DIR / "MASTER_SCHEDULE.csv",
    "published": DATA_DIR / "PUBLISHED_SCHEDULE.csv",
    "codeshare": DATA_DIR / "CODESHARE_PARTNER_DATA.csv",
}
```

## Architecture Highlights

### Modularity
- Each phase (load, validate, detect, export) is a self-contained module
- Functions have clear inputs/outputs and minimal dependencies
- Easy to test, debug, and extend

### Error Handling
- Custom `DataValidationError` for validation failures
- Try-except blocks around I/O operations
- Comprehensive logging at all stages

### Performance
- Uses pandas vectorized operations (no explicit loops)
- Merge operations optimized with outer joins
- Handles datasets with 100k+ records efficiently

### Extensibility
- Add custom severity rules in `schedule_validator.py`
- Extend codeshare logic by modifying `codeshare_validator.py`
- Add new KPIs in `metrics.py`

## Example Usage

```python
from src.data.loader import load_data
from src.validation import validate_schedule
from src.kpi import compute_kpis
from src.utils.config import DEFAULT_INPUT_PATHS

# Load datasets
datasets = load_data(DEFAULT_INPUT_PATHS)
master = datasets["master"]
published = datasets["published"]

# Run validation
schedule_report = validate_schedule(master, published)

# Extract metrics
accuracy = compute_kpis(schedule_report, pd.DataFrame())
print(f"Schedule Accuracy: {accuracy}")
```

## Troubleshooting

**Issue**: FileNotFoundError for CSV files
- **Solution**: Ensure Dataset/ folder contains the three required CSV files

**Issue**: DataValidationError for missing columns
- **Solution**: Check CSV headers match the expected columns in `config.py`

**Issue**: Memory error on large datasets
- **Solution**: Consider chunking data or using dask for very large files (>1GB)

## Future Enhancements

- [ ] Dashboard UI (Streamlit/Plotly)
- [ ] Database integration (PostgreSQL)
- [ ] Real-time validation with message queues
- [ ] Machine learning for anomaly detection
- [ ] Email alerting for critical issues
- [ ] Web API for remote validation

## Contributing

When adding new features:
1. Create a new module in the appropriate `src/` subfolder
2. Write docstrings and type hints
3. Add error handling and logging
4. Test with sample data
5. Update this README

## License

Proprietary - IndiGo Airlines Schedule System

## Contact

For questions or issues, contact: data-engineering@indigogo.local
