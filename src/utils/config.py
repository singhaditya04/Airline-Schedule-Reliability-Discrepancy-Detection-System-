from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "Dataset"
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"

DEFAULT_INPUT_PATHS = {
    "master": DATA_DIR / "MASTER_SCHEDULE.csv",
    "published": DATA_DIR / "PUBLISHED_SCHEDULE.csv",
    "codeshare": DATA_DIR / "CODESHARE_PARTNER_DATA.csv",
}

DEFAULT_COLUMNS = {
    "master": [
        "flight_number",
        "origin",
        "destination",
        "departure_time",
        "arrival_time",
        "aircraft_type",
        "day_of_operation",
        "terminal",
        "operating_carrier",
        "has_codeshare",
        "codeshare_partner",
        "partner_flight_number",
    ],
    "published": [
        "flight_number",
        "origin",
        "destination",
        "departure_time",
        "arrival_time",
        "aircraft_type",
        "day_of_operation",
        "terminal",
        "operating_carrier",
    ],
    "codeshare": [
        "partner_flight_number",
        "departure_time",
        "arrival_time",
        "status",
    ],
}

COLUMN_RENAME_MAP = {
    "master": {
        "flight_number": "flight_id",
        "partner_flight_number": "partner_flight_id",
    },
    "published": {
        "flight_number": "flight_id",
    },
    "codeshare": {
        "partner_flight_number": "partner_flight_id",
    },
}
