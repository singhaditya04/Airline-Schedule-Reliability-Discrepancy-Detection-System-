# IndigoGo Command Reference Card

## Quick Commands

### Run Full Pipeline
```bash
python main.py
```
Outputs: 3 CSVs + summary report + logs

### Check Data Quality
```bash
python check_data_quality.py
```
Outputs: Data profiling (nulls, duplicates, types)

### View Results
```bash
# Schedule discrepancies
python -c "import pandas as pd; pd.read_csv('output/schedule_report.csv').head()"

# Codeshare validation
python -c "import pandas as pd; pd.read_csv('output/codeshare_report.csv').head()"

# KPI summary
python -c "import pandas as pd; pd.read_csv('output/kpi_summary.csv')"
```

### Analyze Issues
```bash
# Show only critical issues
python -c "import pandas as pd; df = pd.read_csv('output/schedule_report.csv'); print(df[df['severity']=='Critical'][['flight_id', 'issue_summary']])"

# Codeshare health
python -c "import pandas as pd; df = pd.read_csv('output/codeshare_report.csv'); print(f'Health: {(df[\"severity\"]==\"OK\").sum() / len(df) * 100:.2f}%')"
```

---

## Module Quick Reference

| Module | Input | Output | Function |
|--------|-------|--------|----------|
| `loader.py` | CSV paths | DataFrames | Load + normalize |
| `validator.py` | DataFrame | Raises error | Validate schema |
| `schedule_validator.py` | master, published | schedule_report | Compare schedules |
| `detector.py` | schedule_report | schedule_report | Sort by severity |
| `codeshare_validator.py` | schedule_report, codeshare | codeshare_report | Validate codeshare |
| `metrics.py` | schedule_report, codeshare_report | kpi_summary | Compute KPIs |
| `exporter.py` | reports | CSV files | Export results |

---

## Key Classes & Functions

### Data Loading
```python
from src.data.loader import load_data
from src.utils.config import DEFAULT_INPUT_PATHS

datasets = load_data(DEFAULT_INPUT_PATHS)
master = datasets['master']
```

### Schedule Validation
```python
from src.validation import validate_schedule

schedule_report = validate_schedule(master, published)
```

### Codeshare Validation
```python
from src.codeshare import validate_codeshare

codeshare_report = validate_codeshare(schedule_report, codeshare)
```

### KPI Computation
```python
from src.kpi import compute_kpis

kpi_summary = compute_kpis(schedule_report, codeshare_report)
```

### Export Results
```python
from src.export import export_results
from src.utils.config import OUTPUT_DIR

paths = export_results(schedule_report, codeshare_report, kpi_summary, OUTPUT_DIR)
```

### Data Quality Check
```python
from src.utils.data_quality import DataQualityReport

report = DataQualityReport(df, name="MASTER")
report.print_summary()
```

### Generate Report
```python
from src.utils.reporting import generate_summary_report

summary = generate_summary_report(schedule_report, codeshare_report, kpi_summary)
print(summary)
```

---

## Configuration

### Edit Input Paths
File: `src/utils/config.py`
```python
DEFAULT_INPUT_PATHS = {
    "master": Path("/custom/path/master.csv"),
    "published": Path("/custom/path/published.csv"),
    "codeshare": Path("/custom/path/codeshare.csv"),
}
```

### Change Expected Columns
File: `src/utils/config.py`
```python
DEFAULT_COLUMNS = {
    "master": ["flight_id", "origin", ...],
    ...
}
```

---

## Output Files

### schedule_report.csv (100,000 rows)
- `flight_id`: Unique flight identifier
- `departure_time_master`: Master schedule departure
- `departure_time_published`: Published schedule departure
- `departure_diff_minutes`: Time difference in minutes
- `severity`: Critical/High/Medium/Low/OK
- `issue_summary`: Human-readable issue description

### codeshare_report.csv (34,874 rows)
- `flight_id`: Codeshare flight ID
- `partner_flight_id`: Partner airline flight ID
- `codeshare_partner`: Partner airline name
- `status`: Partner flight status
- `missing_partner_flight`: Boolean
- `severity`: Critical/High/Medium/Low/OK

### kpi_summary.csv (8 rows)
- `metric`: KPI name
- `value`: Numeric value

---

## Severity Levels

| Level | Color | Threshold |
|-------|-------|-----------|
| Critical | 🔴 Red | Missing flights, missing partner |
| High | 🟠 Orange | Aircraft mismatch, >60 min time diff |
| Medium | 🟡 Yellow | Terminal mismatch, 15-60 min time diff |
| Low | 🟢 Light | <15 min time diff |
| OK | ✅ Green | No issues |

---

## Troubleshooting Commands

### Check if files exist
```bash
ls -la Dataset/
ls -la output/
ls -la logs/
```

### View logs
```bash
tail -f logs/pipeline.log
```

### Check dataset sizes
```bash
python -c "import pandas as pd; print('Master:', len(pd.read_csv('Dataset/MASTER_SCHEDULE.csv'))); print('Published:', len(pd.read_csv('Dataset/PUBLISHED_SCHEDULE.csv')))"
```

### List missing columns
```python
import pandas as pd
master = pd.read_csv('Dataset/MASTER_SCHEDULE.csv')
expected = ['flight_id', 'origin', 'destination', ...]
missing = [col for col in expected if col not in master.columns]
print("Missing:", missing)
```

### Show top discrepancies
```python
import pandas as pd
df = pd.read_csv('output/schedule_report.csv')
print(df[df['severity']=='High'].head(10))
```

---

## Environmental Setup

### Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Check Python Version
```bash
python --version  # Requires 3.10+
```

---

## Typical Workflow

1. **Setup** (one-time)
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Pipeline**
   ```bash
   python main.py
   ```

3. **Check Data Quality** (optional)
   ```bash
   python check_data_quality.py
   ```

4. **Review Results**
   ```bash
   # Open output/schedule_report.csv in Excel
   # Check output/kpi_summary.csv for metrics
   # Review logs/pipeline.log for details
   ```

5. **Modify Rules** (if needed)
   ```bash
   # Edit src/validation/schedule_validator.py
   # Edit src/codeshare/codeshare_validator.py
   # Re-run: python main.py
   ```

---

## Performance Benchmarks

- **100k flights**: ~12 seconds
- **Memory**: ~200 MB
- **I/O**: ~3 seconds (CSV read/write)
- **Processing**: ~8 seconds (validation)

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| FileNotFoundError | Ensure CSVs in Dataset/ folder |
| DataValidationError | Check CSV headers match config.py |
| Empty outputs | Verify input CSVs have data |
| Encoding error | Use UTF-8 encoding, check terminal |
| Import error | Ensure pip install completed |

---

## File Modification Checklist

✅ = Safe to edit after understanding code
⚠️ = Edit only if needed

| File | Edit? | Impact |
|------|-------|--------|
| `main.py` | ✅ | Orchestration order |
| `src/utils/config.py` | ✅ | Input paths, columns |
| `src/validation/schedule_validator.py` | ✅ | Severity rules |
| `src/codeshare/codeshare_validator.py` | ✅ | Codeshare rules |
| `src/kpi/metrics.py` | ✅ | KPI formulas |
| `src/data/loader.py` | ⚠️ | Data loading logic |
| `src/export/exporter.py` | ⚠️ | Output format |
| `.venv/` | ❌ | Don't modify |
| `Dataset/` | ❌ | Don't modify (input) |

---

## Useful Python Snippets

### Custom Analysis
```python
from src.data.loader import load_data
from src.utils.config import DEFAULT_INPUT_PATHS
from src.validation import validate_schedule

datasets = load_data(DEFAULT_INPUT_PATHS)
report = validate_schedule(datasets['master'], datasets['published'])

# Filter by severity
critical = report[report['severity'] == 'Critical']
print(f"Critical issues: {len(critical)}")

# Group by route
by_route = report.groupby(['origin_master', 'destination_master']).size()
print(by_route.head(10))

# Time stats
print(f"Avg time diff: {report['departure_diff_minutes'].mean():.2f} min")
```

---

**Version**: 1.0  
**Created**: April 9, 2026  
**Status**: Production Ready  
