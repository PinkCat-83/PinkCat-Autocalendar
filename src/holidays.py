"""
festivos.py
Loads and manages public holidays from holidays.json.
"""

import json
from datetime import date
from pathlib import Path


def load_holidays(path: Path, year: int) -> set[date]:
    """
    Reads holidays.json and returns a set of date objects for the given year.
    Returns an empty set and prints a warning if the year is not defined.
    """
    if not path.exists():
        print(f"[WARNING] Holiday file not found: {path}")
        return set()

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    key = str(year)
    if key not in data:
        print(f"[WARNING] No holidays defined for year {year} in {path}.")
        return set()

    holidays: set[date] = set()
    for entry in data[key]:
        try:
            holidays.add(date.fromisoformat(entry["date"]))
        except (KeyError, ValueError) as e:
            print(f"[WARNING] Skipping malformed holiday entry: {entry} ({e})")

    return holidays
