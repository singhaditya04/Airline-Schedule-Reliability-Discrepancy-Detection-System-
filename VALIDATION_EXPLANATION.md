# Validation Explanation

This document explains how the IndigoGo schedule validation pipeline reads data, finds inconsistencies, and calculates the final values. It is written in very simple language so even a 5-year-old can follow the idea.

---

## 1. What files are used

The pipeline looks at three input files in the `Dataset` folder:

- `MASTER_SCHEDULE.csv` — the planned flight schedule from the airline.
- `PUBLISHED_SCHEDULE.csv` — the schedule published for customers.
- `CODESHARE_PARTNER_DATA.csv` — partner airline flight data when the flight has codeshare.

It also writes or compares output files in the `output` folder:

- `schedule_report.csv`
- `codeshare_report.csv`
- `kpi_summary.csv`

---

## 2. Loading the data

The program reads each file like a table of rows and columns.

The loader checks that every file has the expected column names. If a file is missing a column, it stops and shows an error.

For example, the master and published schedules both need:

- flight_id
- origin
- destination
- departure_time
- arrival_time
- aircraft_type
- day_of_operation
- terminal
- operating_carrier
- has_codeshare
- codeshare_partner
- partner_flight_id

The codeshare partner file needs:

- partner_flight_id
- departure_time
- arrival_time
- status

If the file has all required columns, it is loaded successfully.

---

## 3. How schedule inconsistencies are found

This is the most important part.

The system compares the master schedule and the published schedule using `flight_id`.

It checks five main problems:

1. Missing in published
2. Missing in master
3. Departure time mismatch
4. Arrival time mismatch
5. Aircraft mismatch
6. Terminal mismatch

### Step-by-step

1. Match each row from master and published by `flight_id`.
2. If a flight exists in master but not in published, mark it as `missing_in_published`.
3. If a flight exists in published but not in master, mark it as `missing_in_master`.
4. If both exist, compare the times and details.

### Time difference calculation

For flights that appear in both master and published:

- Convert departure and arrival times into real time values.
- Calculate the absolute difference in minutes.

For example, if master says departure at 05:00 and published says 04:40, the difference is 20 minutes.

### Aircraft mismatch

If the plane type in master is not the same as the plane type in published, it is marked as an `aircraft_mismatch`.

### Terminal mismatch

If the terminal in master and published are different, it is marked as `terminal_mismatch`.

### Issue summary

The program writes a short text description of what went wrong for each flight.

Examples:

- `OK` — everything matches.
- `Aircraft mismatch` — different plane types.
- `Departure time mismatch` — departure times are different.
- `Arrival time mismatch` — arrival times are different.
- `Missing in published schedule` — the published file does not have that flight.
- `Orphan published flight` — a flight appears only in published, not in master.

If multiple problems exist, they are joined with a semicolon.

### Severity level

Each flight gets a severity label:

- `Critical`
- `High`
- `Medium`
- `Low`
- `OK`

The rules are:

- If the flight is missing in published or missing in master → `Critical`
- If aircraft type differs → `High`
- If time difference is more than 60 minutes → `High`
- If terminal differs → `Medium`
- If time difference is between 16 and 60 minutes → `Medium`
- If time difference is between 1 and 15 minutes → `Low`
- If no issues → `OK`

This is how the system decides how serious each problem is.

---

## 4. How discrepancies are sorted

After the schedule report is built, it is sorted so the most serious issues come first.

The order is:

1. `Critical`
2. `High`
3. `Medium`
4. `Low`
5. `OK`

Within the same severity, flight IDs are sorted alphabetically.

---

## 5. How codeshare issues are found

Codeshare means the airline uses a partner flight number for the same flight.

The program only checks flights where `has_codeshare` is `Yes`.

It matches those flights to the partner file using `partner_flight_id`.

It checks three things:

1. Missing partner flight
2. Time mismatch between the master departure time and partner departure time
3. Partner status is not `Available`

### Missing partner flight

If the codeshare flight cannot be found in the partner data, this is a `missing_partner_flight` problem.

### Time mismatch calculation

If the partner flight is found, the system calculates the absolute difference in minutes between:

- master departure time
- partner departure time

If the times are different, that is a `time_mismatch_minutes` value.

### Partner availability

If the partner flight status is not exactly `Available`, then it is marked as `not_available`.

### Codeshare issue summary

The program writes text for each flight, like:

- `OK`
- `Missing partner flight`
- `Partner time mismatch`
- `Partner status not Available`

### Codeshare severity

Severity rules for codeshare:

- Missing partner flight → `Critical`
- Status not available → `High`
- Time mismatch over 30 minutes → `High`
- Time mismatch 16 to 30 minutes → `Medium`
- Time mismatch 1 to 15 minutes → `Low`
- No issues → `OK`

---

## 6. How KPI values are calculated

KPI stands for Key Performance Indicator. These are the final numbers that describe how healthy the schedule is.

The system calculates:

- `total_master_flights`
- `total_codeshare_flights`
- `schedule_accuracy_pct`
- `discrepancy_rate_pct`
- `codeshare_health_pct`
- `critical_issue_count`
- `critical_schedule_issues`
- `critical_codeshare_issues`

### total_master_flights

This counts all unique flights from the schedule report, but only flights that are not `missing_in_master`.

That means flights that are present in master or match published, not orphan published flights.

### total_codeshare_flights

This counts how many flights in the codeshare report were checked.

### schedule_accuracy_pct

This is how many master flights are good.

It uses the formula:

```
(total_master_flights - number_of_bad_schedule_flights) / total_master_flights * 100
```

A flight is bad if its severity is not `OK`.

### discrepancy_rate_pct

This is the opposite of accuracy.

It uses the formula:

```
(number_of_bad_schedule_flights) / total_master_flights * 100
```

If 25 out of 100 flights have problems, the rate is 25%.

### codeshare_health_pct

This checks how many codeshare flights are `OK`.

It uses the formula:

```
(number_of_codeshare_OK_flights) / total_codeshare_flights * 100
```

If 10 out of 11 codeshare flights are OK, the health is 90.91%.

### critical_issue_count

This adds up all serious problems from both schedule and codeshare checks.

### critical_schedule_issues

This counts flights in the schedule report whose severity is `Critical`.

### critical_codeshare_issues

This counts flights in the codeshare report whose severity is `Critical`.

---

## 7. Why this is useful

The system is like a teacher checking homework.

- The schedule report checks if the airline’s plan and the customer-facing plan match.
- The codeshare report checks partner flights for shared flights.
- The KPI summary gives a simple score for the whole set of flights.

If something is wrong, the report tells us what exactly is wrong and how bad it is.

---

## 8. Easy example

Imagine two toy cars racing.

- One car is the planned time.
- The other car is the published time.

If they start at the same time, everything is OK.
If one car starts later, that is a mismatch.
If one car is missing, that is a big problem.

The program looks at every pair and writes down whether they match.

---

## 9. Where the code lives

The main logic is in these files:

- `src/data/loader.py` — reads the files and checks the columns.
- `src/validation/schedule_validator.py` — compares master and published schedules.
- `src/discrepancy/detector.py` — sorts the discrepancies by severity.
- `src/codeshare/codeshare_validator.py` — checks codeshare partner flights.
- `src/kpi/metrics.py` — calculates the KPIs.
- `src/utils/reporting.py` — turns results into human-readable summary tables.

---

## 10. Summary for a 5-year-old

1. We have three lists of flight information.
2. We compare the first two lists to see if they match.
3. We also check special partner flights.
4. We count how many flights are good and how many have problems.
5. We make a final score that tells us if the schedule is healthy.

That is the whole process.
