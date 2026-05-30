"""
export.py
JSON serialization and file I/O for the calendar and economic summary.
"""

import json
from datetime import date
from pathlib import Path


class DateEncoder(json.JSONEncoder):
    """Serializes Python date objects as ISO strings (YYYY-MM-DD)."""

    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def save_json(data: dict, path: Path) -> None:
    """
    Saves a dictionary as a formatted JSON file.
    Creates parent directories if they do not exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DateEncoder)
    print(f"[OK] Saved: {path}")


def load_json(path: Path) -> dict | list:
    """Loads JSON from disk. Raises FileNotFoundError if the file does not exist."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
