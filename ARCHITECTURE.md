# IndigoGo System Architecture & Design Document

## Executive Summary

The IndigoGo Airline Schedule Validation System is a modular, production-grade Python application that validates airline flight schedules and codeshare agreements. It compares internal "master" schedules against publicly-distributed "published" schedules, detects discrepancies with severity classification, and validates partner airline codeshare data.

**Key Metrics:**
- Processes 100,000+ flights per run
- Identifies schedule accuracy, discrepancy rates, and codeshare health
- Generates structured CSV reports and KPI summaries
- Runs with comprehensive logging and error handling

---

## System Architecture

### High-Level Pipeline

```
INPUT (3 CSVs)
    ↓
[Data Loading & Validation] → Load, normalize, validate schemas
    ↓
[Schedule Validation Engine] → Compare master vs. published
    ↓
[Discrepancy Detection] → Categorize issues, assign severity
    ↓
[Codeshare Validation] → Validate partner flights
    ↓
[KPI Computation] → Calculate metrics
    ↓
[Data Export] → Write CSVs to output/
    ↓
OUTPUT (3 CSVs + Summary Report)
```

### Module Dependencies

```
main.py
  ├── data.loader
  │   └── data.validator
  ├── validation.schedule_validator
  ├── discrepancy.detector
  ├── codeshare.codeshare_validator
  ├── kpi.metrics
  ├── export.exporter
  ├── utils.logger
  ├── utils.config
  └── utils.reporting
```

---

## Phase 1: Data Loading & Validation

**Module**: `src/data/loader.py`, `src/data/validator.py`

### Responsibility
Load CSV files, validate schemas, and normalize column names.

### Process
1. **Read CSV**: Use `pd.read_csv(filepath, dtype=str)` to preserve string types
2. **Validate Schema**: Check all required columns exist
3. **Normalize Columns**: Rename columns to canonical names (e.g., `flight_number` → `flight_id`)
4. **Add Missing Fields**: Ensure all DataFrames have consistent columns (e.g., add `has_codeshare` to published)

### Input
- `MASTER_SCHEDULE.csv`: 100,000 rows, 12 columns
- `PUBLISHED_SCHEDULE.csv`: 99,209 rows, 9 columns
- `CODESHARE_PARTNER_DATA.csv`: Partner flight data, 4 columns

### Output
- `df_master`: Normalized master schedule
- `df_published`: Normalized published schedule
- `df_codeshare`: Partner codeshare data

### Key Logic
```python
# Column renaming
rename_map = {
    "flight_number": "flight_id",
    "partner_flight_number": "partner_flight_id",
}
df = df.rename(columns=rename_map)

# Schema validation
missing = [col for col in required_cols if col not in df.columns]
if missing:
    raise DataValidationError(f"Missing columns: {missing}")
```

---

## Phase 2: Schedule Validation Engine

**Module**: `src/validation/schedule_validator.py`

### Responsibility
Compare master and published schedules to identify discrepancies.

### Process
1. **Parse Timestamps**: Convert time strings (HH:MM format) to pandas datetime
2. **Outer Merge**: Join on `flight_id` to find common and missing flights
3. **Compute Differences**: Calculate time deltas for departure/arrival
4. **Check Attributes**: Compare aircraft type, terminal
5. **Apply Rules**: Assign severity based on discrepancy type

### Key Checks
| Issue Type | Rule | Default Severity |
|-----------|------|-----------------|
| Missing in Published | Flight exists in master but not published | **Critical** |
| Time Mismatch | `abs(time_diff) > 60 min` | **High** |
| Aircraft Mismatch | Aircraft type differs | **High** |
| Terminal Mismatch | Terminal differs | **Medium** |
| Time Mismatch (Minor) | `15 < abs(time_diff) <= 60 min` | **Medium** |
| Time Mismatch (Tiny) | `0 < abs(time_diff) <= 15 min` | **Low** |

### Example Output
```
flight_id: 6E100000
  departure_time_master: 2026-01-01 05:01:00
  departure_time_published: 2026-01-01 05:16:00
  departure_diff_minutes: 15.0
  severity: Low
  issue_summary: Departure time mismatch; Arrival time mismatch
```

---

## Phase 3: Discrepancy Detection System

**Module**: `src/discrepancy/detector.py`

### Responsibility
Sort and prioritize discrepancies by severity for downstream focus.

### Process
1. **Sort by Severity**: Critical → High → Medium → Low → OK
2. **Preserve Metadata**: Keep all issue details
3. **Return Full Report**: Send complete dataset for next phases

### Output
Same schema as phase 2, but sorted by severity priority.

---

## Phase 4: Codeshare Validation Engine

**Module**: `src/codeshare/codeshare_validator.py`

### Responsibility
Validate codeshare flights against partner airline data.

### Process
1. **Filter**: Select only flights with `has_codeshare == "Yes"`
2. **Join Partner Data**: Left merge on `partner_flight_id`
3. **Check Existence**: Detect missing partner flights
4. **Validate Time Alignment**: Compare departure times
5. **Check Status**: Ensure partner status is "Available"

### Severity Rules
| Issue | Severity |
|-------|----------|
| Missing partner flight | **Critical** |
| Partner status not "Available" | **High** |
| Time mismatch > 30 min | **High** |
| Time mismatch 15-30 min | **Medium** |
| Time mismatch 0-15 min | **Low** |

### Example Output
```
flight_id: 6E100000
  partner_flight_id: TK6000
  codeshare_partner: Turkish Airlines
  partner_departure_time: 2026-01-01 05:00:00
  status: Available
  severity: OK
```

---

## Phase 5: KPI Metrics Computation

**Module**: `src/kpi/metrics.py`

### Responsibility
Compute key performance indicators for schedule and codeshare health.

### KPIs Calculated

| KPI | Formula | Interpretation |
|-----|---------|-----------------|
| **Schedule Accuracy %** | `(total - discrepant) / total * 100` | Percentage of flights with no issues |
| **Discrepancy Rate %** | `discrepant / total * 100` | Percentage of flights with any issue |
| **Codeshare Health %** | `codeshare_ok / total_codeshare * 100` | Percentage of codeshare with all validations passed |
| **Critical Issue Count** | `sum(severity == Critical)` | Total critical-severity issues across systems |

### Example Output
```
┌─────────────────┬─────────┐
│ metric          │ value   │
├─────────────────┼─────────┤
│ schedule_accuracy_pct     │ 61.70   │
│ discrepancy_rate_pct      │ 38.30   │
│ codeshare_health_pct      │ 72.61   │
│ critical_issue_count      │ 1177    │
└─────────────────┴─────────┘
```

---

## Phase 6: Data Export Layer

**Module**: `src/export/exporter.py`

### Responsibility
Write validation results to CSV files for downstream analysis.

### Output Files

1. **schedule_report.csv**
   - One row per flight in merged dataset
   - Columns: `flight_id`, departure/arrival times, discrepancy flags, severity, issue summary
   - Use case: Detailed analysis, root cause investigation

2. **codeshare_report.csv**
   - One row per codeshare flight
   - Columns: `flight_id`, `partner_flight_id`, partner times, status, severity, issue summary
   - Use case: Codeshare health monitoring

3. **kpi_summary.csv**
   - 8 rows (one per KPI)
   - Columns: `metric`, `value`
   - Use case: Executive dashboards, trend analysis

---

## Phase 7 (Optional): Visualization & Reporting

**Modules**: `src/utils/reporting.py`, `check_data_quality.py`

### Responsibility
Generate human-readable summary reports and data quality insights.

### Features
- Console summary with formatted tables
- Discrepancy counts by type
- Severity distribution with percentages
- Data quality metrics (nulls, duplicates, types)

### Example Output
```
======================================================================
AIRLINE SCHEDULE VALIDATION REPORT
======================================================================

KEY PERFORMANCE INDICATORS (KPIs)
----------------------------------------------------------------------
  Schedule Accuracy Pct                    61.70%
  Discrepancy Rate Pct                     38.30%
  Critical Issue Count                     1177

ISSUE SEVERITY DISTRIBUTION
----------------------------------------------------------------------
  Critical        791        (0.8%)
  High            8279       (8.3%)
  Medium          21065      (21.1%)
  Low             8168       (8.2%)
  OK              61697      (61.7%)
```

---

## Error Handling & Logging

### Logging Strategy
- **Level**: INFO for progress, ERROR for failures
- **Destination**: Console + `logs/pipeline.log`
- **Format**: `TIMESTAMP | LEVEL | LOGGER | MESSAGE`

### Error Types
- **`DataValidationError`**: Schema/data integrity issues
- **FileNotFoundError**: Missing input files
- **Exception**: Unhandled, logged and re-raised

### Example Logs
```
2026-04-09 18:01:11 | INFO | indigogo | Starting Airline Schedule Validation pipeline
2026-04-09 18:01:12 | INFO | indigogo | Successfully loaded datasets: master, published, codeshare
2026-04-09 18:01:19 | INFO | indigogo | Schedule validation complete. Total flights processed: 100000
2026-04-09 18:01:21 | INFO | indigogo | Pipeline completed successfully.
```

---

## Data Quality Considerations

### Null Handling
- CSV nulls (missing values) are handled per module
- Time parsing: Nulls → NaT (Not a Time)
- String comparisons: Nulls → empty strings

### Type Preservation
- Load with `dtype=str` to preserve flight IDs (e.g., "6E100000", not numeric)
- Convert to datetime only when needed (time comparison)
- Final exports preserve string types

### Duplicate Management
- No implicit deduplication; report as-is
- Merges use `how="outer"` to retain all records
- Codeshare uses `how="left"` to preserve all master flights

---

## Performance Characteristics

### Timeline (100k flights)
- Data loading: ~1 second
- Schedule validation: ~8 seconds
- Codeshare validation: ~2 seconds
- KPI computation: <0.1 seconds
- Export: ~1 second
- **Total**: ~12 seconds

### Memory Usage
- Master DataFrame: ~50 MB
- Published DataFrame: ~50 MB
- Codeshare DataFrame: ~5 MB
- Working memory: ~200 MB total

### Scalability
- Vectorized pandas operations (no explicit loops)
- Outer merge with ~100k unique keys: O(n log n)
- Fits in memory for up to 1M flights
- For larger datasets: Consider chunking or dask

---

## Extension Points

### Adding New Validations
1. Create a new module in `src/`
2. Define inputs (DataFrame) and outputs (DataFrame or dict)
3. Add severity rules
4. Wire into `main.py`

### Adding New KPIs
1. Edit `src/kpi/metrics.py`
2. Add formula in `compute_kpis()`
3. Return in summary DataFrame

### Customizing Severity Rules
Edit severity assignment in:
- `src/validation/schedule_validator.py`: Schedule rules
- `src/codeshare/codeshare_validator.py`: Codeshare rules

---

## Testing Strategy

### Unit Tests
Test each module independently with mock DataFrames.

### Integration Tests
Test full pipeline with sample datasets.

### Example Test
```python
def test_schedule_validation():
    master = pd.DataFrame({
        "flight_id": ["6E100"],
        "departure_time": ["05:00"],
    })
    published = pd.DataFrame({
        "flight_id": ["6E100"],
        "departure_time": ["05:15"],
    })
    result = validate_schedule(master, published)
    assert result["departure_diff_minutes"].iloc[0] == 15.0
    assert result["severity"].iloc[0] == "Low"
```

---

## Configuration Management

**File**: `src/utils/config.py`

Centralized configuration:
- Input file paths
- Expected column definitions
- Column rename mappings
- Output directory

Change configuration without modifying code:
```python
DEFAULT_INPUT_PATHS = {
    "master": "/custom/path/MASTER_SCHEDULE.csv",
    "published": "/custom/path/PUBLISHED_SCHEDULE.csv",
    "codeshare": "/custom/path/CODESHARE_PARTNER_DATA.csv",
}
```

---

## Production Readiness Checklist

- [x] Modular architecture (7 independent modules)
- [x] Type hints and docstrings
- [x] Comprehensive error handling
- [x] Logging at all critical points
- [x] Edge case handling (nulls, empties, duplicates)
- [x] Configuration management
- [x] Output validation (files exist)
- [x] README and documentation
- [x] Performance tested (100k flights in ~12s)
- [x] Extensibility (easy to add new checks)

---

## Business Context (Real-World Scenarios)

### Use Case 1: Daily Schedule Audit
- Run every night to detect schedule discrepancies
- Alert ops team on Critical issues
- Track historical trends via KPI export

### Use Case 2: Codeshare Health Monitoring
- Weekly codeshare validation
- Detect partners with high time mismatches
- Identify bookability issues

### Use Case 3: Schedule Accuracy Reporting
- Monthly accuracy report for executives
- Compare accuracy across routes
- Root cause analysis of high-discrepancy flights

---

## Future Enhancements

1. **Dashboard**: Streamlit UI for interactive analysis
2. **Real-time Pipeline**: Message queue integration for live validation
3. **Machine Learning**: Anomaly detection using historical patterns
4. **Alerting**: Email/SMS notifications on critical issues
5. **Database**: Store results in PostgreSQL for historical analysis
6. **Web API**: REST endpoint for remote validation requests

---

## Contact & Support

For questions on architecture, design decisions, or usage:
- Review inline code comments
- Check `README.md` for module descriptions
- Examine test files for usage examples
- Contact: data-engineering@indigogo.local
