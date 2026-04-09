"""
Generate realistic IndiGo airline datasets for Network Planning and Schedule Validation.

Outputs:
  MASTER_SCHEDULE.csv        - 100,000 rows  (IndiGo internal master)
  PUBLISHED_SCHEDULE.csv     - Derived, no codeshare columns, with errors
  CODESHARE_PARTNER_DATA.csv - Codeshare flights only, with inconsistencies
"""

import csv
import random
from math import ceil

random.seed(42)

# ── Tunable constants ─────────────────────────────────────────────────────────
TARGET           = 100

CODESHARE_RATE   = 0.10    # 10% of master flights have codeshare

# Published Schedule error rates (independent per row)
PUB_REMOVE_RATE  = 0.008   # ~800 flights omitted entirely
PUB_TIME_RATE    = 0.15    # 25% get a departure/arrival time shift
PUB_ACFT_RATE    = 0.08    # 8%  get aircraft type swapped
PUB_TERM_RATE    = 0.05    # 10% get wrong terminal

# Codeshare Partner Data error rates
CS_REMOVE_RATE   = 0.012   # ~1.2% partner records missing (broken codeshare)
CS_TIME_RATE     = 0.05    # 20% have a timing mismatch (±10–20 min)
CS_UNAVAIL_RATE  = 0.08    # 8%  marked "Unavailable"

# ── Airport → terminal list ───────────────────────────────────────────────────
AIRPORTS = {
    "DEL": ["T1", "T2", "T3"],
    "BOM": ["T1", "T2"],
    "BLR": ["T1", "T2"],
    "HYD": ["T1"],
    "MAA": ["T1", "T4"],
    "GOI": ["T1"],
    "CCU": ["T1", "T2"],
    "AMD": ["T1"],
    "PNQ": ["T1"],
    "JAI": ["T1"],
    "LKO": ["T1"],
    "NAG": ["T1"],
    "COK": ["T1"],
    "IXC": ["T1"],
    "BBI": ["T1"],
    "ATQ": ["T1"],
    "VTZ": ["T1"],
    "SXR": ["T1"],
    "TRV": ["T1"],
    "IXB": ["T1"],
}

# ── Route durations in minutes (one-way) ─────────────────────────────────────
BASE_DURATIONS = {
    # DEL hub
    ("DEL","BOM"):130, ("DEL","BLR"):165, ("DEL","HYD"):120, ("DEL","MAA"):165,
    ("DEL","GOI"):165, ("DEL","CCU"):135, ("DEL","AMD"):90,  ("DEL","PNQ"):140,
    ("DEL","JAI"):60,  ("DEL","LKO"):75,  ("DEL","NAG"):115, ("DEL","COK"):195,
    ("DEL","IXC"):55,  ("DEL","BBI"):140, ("DEL","ATQ"):60,  ("DEL","VTZ"):155,
    ("DEL","SXR"):75,  ("DEL","TRV"):195, ("DEL","IXB"):120,
    # BOM hub
    ("BOM","BLR"):75,  ("BOM","HYD"):90,  ("BOM","MAA"):90,  ("BOM","GOI"):60,
    ("BOM","CCU"):165, ("BOM","AMD"):70,  ("BOM","PNQ"):45,  ("BOM","JAI"):120,
    ("BOM","LKO"):145, ("BOM","NAG"):75,  ("BOM","COK"):105, ("BOM","IXC"):135,
    ("BOM","BBI"):165, ("BOM","VTZ"):120, ("BOM","TRV"):105, ("BOM","ATQ"):135,
    ("BOM","IXB"):165, ("BOM","SXR"):140,
    # BLR hub
    ("BLR","HYD"):70,  ("BLR","MAA"):60,  ("BLR","GOI"):80,  ("BLR","CCU"):150,
    ("BLR","AMD"):120, ("BLR","PNQ"):85,  ("BLR","COK"):60,  ("BLR","TRV"):75,
    ("BLR","VTZ"):90,  ("BLR","NAG"):105, ("BLR","LKO"):165, ("BLR","JAI"):150,
    ("BLR","IXB"):165,
    # HYD hub
    ("HYD","MAA"):70,  ("HYD","GOI"):90,  ("HYD","CCU"):140, ("HYD","AMD"):110,
    ("HYD","COK"):90,  ("HYD","NAG"):85,  ("HYD","BBI"):120, ("HYD","VTZ"):60,
    ("HYD","TRV"):95,  ("HYD","LKO"):155, ("HYD","PNQ"):75,  ("HYD","IXB"):160,
    # MAA hub
    ("MAA","GOI"):105, ("MAA","CCU"):150, ("MAA","COK"):60,  ("MAA","TRV"):65,
    ("MAA","BBI"):130, ("MAA","VTZ"):75,  ("MAA","AMD"):130, ("MAA","PNQ"):95,
    ("MAA","LKO"):165, ("MAA","IXB"):160,
    # CCU hub
    ("CCU","BBI"):50,  ("CCU","IXB"):60,  ("CCU","LKO"):120, ("CCU","VTZ"):140,
    ("CCU","NAG"):130, ("CCU","GOI"):165, ("CCU","COK"):160, ("CCU","JAI"):150,
    # GOI
    ("GOI","COK"):80,  ("GOI","BBI"):130, ("GOI","TRV"):95,  ("GOI","AMD"):85,
    ("GOI","PNQ"):55,  ("GOI","NAG"):90,
    # AMD
    ("AMD","JAI"):70,  ("AMD","PNQ"):75,  ("AMD","COK"):130, ("AMD","LKO"):120,
    ("AMD","NAG"):90,  ("AMD","IXC"):110,
    # PNQ
    ("PNQ","HYD"):80,  ("PNQ","COK"):95,  ("PNQ","CCU"):150, ("PNQ","NAG"):75,
    ("PNQ","LKO"):155,
    # JAI
    ("JAI","LKO"):80,  ("JAI","IXC"):75,  ("JAI","ATQ"):80,  ("JAI","SXR"):80,
    # LKO
    ("LKO","NAG"):100, ("LKO","BBI"):110, ("LKO","IXC"):90,  ("LKO","IXB"):130,
    # Regional
    ("IXC","ATQ"):30,  ("COK","TRV"):40,  ("VTZ","BBI"):75,
    ("NAG","BBI"):100, ("BBI","IXB"):70,
}

# Build symmetric routes (reverse direction ≈ same duration ± small variation)
ALL_ROUTES = {}
for (o, d), dur in BASE_DURATIONS.items():
    ALL_ROUTES[(o, d)] = dur
    if (d, o) not in BASE_DURATIONS:
        ALL_ROUTES[(d, o)] = dur + random.randint(-10, 15)

ROUTE_LIST = list(ALL_ROUTES.keys())

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

AIRCRAFT      = ["A320", "A321"]
ALT_AIRCRAFT  = {"A320": "A321", "A321": "A320"}

CODESHARE_PARTNERS = [
    ("Qatar Airways",    "QR", 5000),
    ("British Airways",  "BA", 7000),
    ("Turkish Airlines", "TK", 6000),
    ("Air Arabia",       "G9", 8000),
    ("Emirates",         "EK", 9000),
]

# ── CSV schemas ───────────────────────────────────────────────────────────────
MASTER_FIELDS = [
    "flight_number", "origin", "destination", "departure_time", "arrival_time",
    "aircraft_type", "day_of_operation", "terminal", "operating_carrier",
    "has_codeshare", "codeshare_partner", "partner_flight_number",
]
PUBLISHED_FIELDS = [
    "flight_number", "origin", "destination", "departure_time", "arrival_time",
    "aircraft_type", "day_of_operation", "terminal", "operating_carrier",
]
CODESHARE_FIELDS = [
    "partner_flight_number", "departure_time", "arrival_time", "status",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(minutes: int) -> str:
    h, m = divmod(int(minutes) % 1440, 60)
    return f"{h:02d}:{m:02d}"

def shift_time(time_str: str, delta: int) -> str:
    h, m = map(int, time_str.split(":"))
    return fmt(h * 60 + m + delta)

def pick_terminal(airport: str) -> str:
    return random.choice(AIRPORTS[airport])

def alt_terminal(airport: str, current: str) -> str:
    opts = AIRPORTS[airport]
    others = [t for t in opts if t != current]
    return random.choice(others) if others else ("T2" if current == "T1" else "T1")

# ── Dataset 1 – MASTER_SCHEDULE ───────────────────────────────────────────────
def generate_master(target: int) -> list[dict]:
    total_combos = len(ROUTE_LIST) * len(DAYS)
    slots = ceil(target / total_combos)   # time slots per route × day

    records = []
    fn_counter = 100_000                  # 6E100000 … 6E199999
    pc = {p[1]: p[2] for p in CODESHARE_PARTNERS}  # partner flight# counters

    for day in DAYS:
        for (orig, dest) in ROUTE_LIST:
            if len(records) >= target:
                break
            dur = ALL_ROUTES[(orig, dest)]
            # Spread slots between 05:00 (300) and 22:30 (1350)
            window_start, window_end = 300, 1350
            step = (window_end - window_start) / max(slots, 1)

            for i in range(slots):
                if len(records) >= target:
                    break
                dep = int(window_start + i * step + random.randint(-7, 7))
                dep = max(300, min(dep, 1350))

                has_cs = random.random() < CODESHARE_RATE
                if has_cs:
                    partner = random.choice(CODESHARE_PARTNERS)
                    cs_name = partner[0]
                    cs_pfx  = partner[1]
                    pf_num  = f"{cs_pfx}{pc[cs_pfx]}"
                    pc[cs_pfx] += 1
                else:
                    cs_name = "NA"
                    pf_num  = "NA"

                records.append({
                    "flight_number":          f"6E{fn_counter}",
                    "origin":                 orig,
                    "destination":            dest,
                    "departure_time":         fmt(dep),
                    "arrival_time":           fmt(dep + dur),
                    "aircraft_type":          random.choice(AIRCRAFT),
                    "day_of_operation":       day,
                    "terminal":               pick_terminal(orig),
                    "operating_carrier":      "IndiGo",
                    "has_codeshare":          "Yes" if has_cs else "No",
                    "codeshare_partner":      cs_name,
                    "partner_flight_number":  pf_num,
                })
                fn_counter += 1

        if len(records) >= target:
            break

    return records[:target]

# ── Dataset 2 – PUBLISHED_SCHEDULE ───────────────────────────────────────────
def generate_published(master: list[dict]) -> tuple[list[dict], dict]:
    published = []
    stats = {"removed": 0, "time": 0, "aircraft": 0, "terminal": 0}

    for row in master:
        # Randomly remove flight
        if random.random() < PUB_REMOVE_RATE:
            stats["removed"] += 1
            continue

        p = {k: row[k] for k in PUBLISHED_FIELDS}

        # Time shift
        if random.random() < PUB_TIME_RATE:
            delta = random.choice([-30, -25, -20, -15, -10, 10, 15, 20, 25, 30])
            p["departure_time"] = shift_time(p["departure_time"], delta)
            p["arrival_time"]   = shift_time(p["arrival_time"],   delta)
            stats["time"] += 1

        # Aircraft type swap
        if random.random() < PUB_ACFT_RATE:
            p["aircraft_type"] = ALT_AIRCRAFT[p["aircraft_type"]]
            stats["aircraft"] += 1

        # Terminal change
        if random.random() < PUB_TERM_RATE:
            p["terminal"] = alt_terminal(p["origin"], p["terminal"])
            stats["terminal"] += 1

        published.append(p)

    return published, stats

# ── Dataset 3 – CODESHARE_PARTNER_DATA ───────────────────────────────────────
def generate_codeshare(master: list[dict]) -> tuple[list[dict], dict]:
    cs_data = []
    stats = {"total_eligible": 0, "removed": 0, "time_mismatch": 0, "unavailable": 0}

    for row in master:
        if row["has_codeshare"] != "Yes":
            continue
        stats["total_eligible"] += 1

        # Missing record (broken codeshare)
        if random.random() < CS_REMOVE_RATE:
            stats["removed"] += 1
            continue

        dep = row["departure_time"]
        arr = row["arrival_time"]

        # Timing mismatch
        if random.random() < CS_TIME_RATE:
            delta = random.choice([-20, -15, -10, 10, 15, 20])
            dep = shift_time(dep, delta)
            arr = shift_time(arr, delta)
            stats["time_mismatch"] += 1

        # Status
        status = "Unavailable" if random.random() < CS_UNAVAIL_RATE else "Available"
        if status == "Unavailable":
            stats["unavailable"] += 1

        cs_data.append({
            "partner_flight_number": row["partner_flight_number"],
            "departure_time":        dep,
            "arrival_time":          arr,
            "status":                status,
        })

    return cs_data, stats

# ── CSV writer ────────────────────────────────────────────────────────────────
def write_csv(path: str, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {len(rows):>8,} rows  ->  {path}")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[1/3] Generating MASTER_SCHEDULE ({TARGET:,} rows)...")
    master = generate_master(TARGET)

    print("[2/3] Generating PUBLISHED_SCHEDULE...")
    published, pub_stats = generate_published(master)

    print("[3/3] Generating CODESHARE_PARTNER_DATA...")
    codeshare, cs_stats = generate_codeshare(master)

    write_csv("MASTER_SCHEDULE.csv",        master,    MASTER_FIELDS)
    write_csv("PUBLISHED_SCHEDULE.csv",     published, PUBLISHED_FIELDS)
    write_csv("CODESHARE_PARTNER_DATA.csv", codeshare, CODESHARE_FIELDS)

    # ── Summary ───────────────────────────────────────────────────────────────
    cs_yes = sum(1 for r in master if r["has_codeshare"] == "Yes")
    print()
    print("=" * 52)
    print("  GENERATION SUMMARY")
    print("=" * 52)
    print(f"  MASTER_SCHEDULE")
    print(f"    Total rows          : {len(master):>8,}")
    print(f"    Unique flight #s    : {len({r['flight_number'] for r in master}):>8,}")
    print(f"    Unique routes       : {len({(r['origin'],r['destination']) for r in master}):>8,}")
    print(f"    Codeshare (Yes)     : {cs_yes:>8,}  ({cs_yes/len(master)*100:.1f}%)")
    print(f"    Days of operation   : {len({r['day_of_operation'] for r in master}):>8,}")
    print()
    print(f"  PUBLISHED_SCHEDULE")
    print(f"    Total rows          : {len(published):>8,}")
    print(f"    Flights removed     : {pub_stats['removed']:>8,}")
    print(f"    Time errors         : {pub_stats['time']:>8,}")
    print(f"    Aircraft errors     : {pub_stats['aircraft']:>8,}")
    print(f"    Terminal errors     : {pub_stats['terminal']:>8,}")
    print()
    print(f"  CODESHARE_PARTNER_DATA")
    print(f"    Total rows          : {len(codeshare):>8,}")
    print(f"    Missing records     : {cs_stats['removed']:>8,}")
    print(f"    Timing mismatches   : {cs_stats['time_mismatch']:>8,}")
    print(f"    Unavailable status  : {cs_stats['unavailable']:>8,}")
    print("=" * 52)
