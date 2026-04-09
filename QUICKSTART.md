# Quick Start Guide - IndigoGo Schedule Validation System

## 30-Second Setup

```bash
# 1. Navigate to project
cd c:\Users\KIIT\Documents\IndigoGoProject

# 2. Install dependencies (if not done)
pip install -r requirements.txt

# 3. Run the pipeline
python main.py

# Output: 3 CSV files in output/ + console summary report
```

## What Just Happened?

Your pipeline:
1. ✅ Loaded 100k+ flights from 3 CSV files
2. ✅ Detected schedule discrepancies (time, aircraft, terminal mismatches)
3. ✅ Validated 34k+ codeshare flights against partner data
4. ✅ Computed KPIs (Schedule Accuracy: 61.70%, Codeshare Health: 72.61%)
5. ✅ Generated 3 detailed CSV reports
6. ✅ Logged all operations to `logs/pipeline.log`

---

## Understanding the Output

### 1. **Console Report**
Printed to terminal - summary of KPIs, issue distribution, codeshare health.

### 2. **CSV Reports** (in `output/`)

#### `schedule_report.csv`
- **100,000 rows** (one per flight)
- Columns: `flight_id`, `departure_time_master`, `departure_time_published`, `departure_diff_minutes`, `severity`, `issue_summary`
- Use: Root cause analysis, rate-per-route trending

#### `codeshare_report.csv`
- **34,874 rows** (one per codeshare flight)
- Columns: `flight_id`, `partner_flight_id`, `status`, `missing_partner_flight`, `severity`
- Use: Partner performance monitoring

#### `kpi_summary.csv`
- **8 rows** (one per KPI metric)
- Columns: `metric`, `value`
- Use: KPI tracking, dashboard feeds

### 3. **Log File** (`logs/pipeline.log`)
- Timestamps, INFO/ERROR levels, operation summaries
- Use: Debugging, audit trails

---

## Common Tasks

### View Discrepancy Report
```bash
# Open schedule_report.csv in Excel/Pandas
import pandas as pd
df = pd.read_csv('output/schedule_report.csv')

# Show only critical issues
critical = df[df['severity'] == 'Critical']
print(critical[['flight_id', 'issue_summary']])
```

### Check Codeshare Health
```python
df = pd.read_csv('output/codeshare_report.csv')
print("Missing partner flights:", df['missing_partner_flight'].sum())
print("Not available:", df['not_available'].sum())
print("Overall health:", (df['severity'] == 'OK').sum() / len(df) * 100, "%")
```

### View KPI Metrics
```python
kpi = pd.read_csv('output/kpi_summary.csv')
print(kpi.to_string(index=False))
```

---

## Customizing the System

### Add a New Severity Rule
Edit `src/validation/schedule_validator.py`:

```python
# In _assign_severity() function, add:
if row['aircraft_mismatch']:
    return "Critical"  # Change from "High" to "Critical"
```

### Change Input File Paths
Edit `src/utils/config.py`:

```python
DEFAULT_INPUT_PATHS = {
    "master": Path("/new/path/master.csv"),
    "published": Path("/new/path/published.csv"),
    "codeshare": Path("/new/path/codeshare.csv"),
}
```

### Add a New KPI
Edit `src/kpi/metrics.py`:

```python
# In compute_kpis(), add:
new_kpi = {
    "metric": "avg_discrepancy_severity",
    "value": calculate_avg_severity(schedule_report)
}
metrics.append(new_kpi)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `FileNotFoundError` | Ensure 3 CSVs are in `Dataset/` folder |
| `DataValidationError: missing columns` | Check CSV headers match expected columns in `config.py` |
| Empty output files | Check input data has rows (not just headers) |
| Memory error on large datasets | Reduce dataset size or use chunking |
| Logs not appearing | Check `logs/` folder was created; restart Python if needed |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `main.py` | Pipeline orchestrator - run this |
| `src/utils/config.py` | Configuration (paths, columns, etc.) |
| `src/validation/schedule_validator.py` | Schedule comparison logic |
| `src/codeshare/codeshare_validator.py` | Codeshare validation logic |
| `src/kpi/metrics.py` | KPI calculations |
| `README.md` | Full documentation |
| `ARCHITECTURE.md` | Design decisions, extending |

---

## Performance Tips

- **100k flights**: ~12 seconds (current)
- **1M flights**: ~120 seconds (estimated, still in-memory)
- **Larger**: Consider batching or Dask

Run with smaller dataset for testing:
```python
df = pd.read_csv('Dataset/MASTER_SCHEDULE.csv', nrows=1000)  # Load first 1000 rows
```

---

## Next Steps

1. ✅ Run the pipeline: `python main.py`
2. 📊 Open `output/schedule_report.csv` in Excel
3. 📈 Review KPIs in `output/kpi_summary.csv`
4. 💬 Check logs in `logs/pipeline.log`
5. 🛠️ Customize severity rules or KPIs (if needed)
6. 🔄 Schedule pipeline as a cron job or Windows task

---

## Getting Help

**Code Questions?**
- Check docstrings: `from src.validation import validate_schedule; help(validate_schedule)`
- Read inline comments in relevant `.py` file
- Review test examples (if tests exist)

**Architecture Questions?**
- See `ARCHITECTURE.md` for detailed design
- Review each module's docstring

**Data Questions?**
- Run `python check_data_quality.py` for data profiling
- Examine first 5 rows: `pd.read_csv('Dataset/MASTER_SCHEDULE.csv').head()`

---

## Example: Build a Custom Report

```python
from src.data.loader import load_data
from src.validation import validate_schedule
from src.utils.config import DEFAULT_INPUT_PATHS

# Load data
datasets = load_data(DEFAULT_INPUT_PATHS)
master = datasets['master']
published = datasets['published']

# Run validation
schedule = validate_schedule(master, published)

# Custom analysis
critical_flights = schedule[schedule['severity'] == 'Critical']
print(f"Critical flights: {len(critical_flights)}")
print(critical_flights[['flight_id', 'origin', 'destination']].head(10))

# Export to Excel
critical_flights.to_excel('critical_flights.xlsx', index=False)
```

**That's it!** You now have a custom analysis built on the system.

---

Happy validating! 🚀
