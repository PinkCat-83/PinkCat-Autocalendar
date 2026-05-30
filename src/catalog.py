"""
catalog.py
Data access layer for reference data: course catalog, companies.
Locations are now stored as an array inside each company (company["locations"]).
All functions load from / save to their respective JSON files.
"""

from pathlib import Path
from src.export import load_json, save_json

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

CATALOG_JSON   = DATA_DIR / "catalog.json"
COMPANIES_JSON = DATA_DIR / "companies.json"
MODALITIES_JSON = DATA_DIR / "modalities.json"


# ── Generic helpers ───────────────────────────────────────────────────────────

def _load(path: Path) -> list:
    try:
        return load_json(path)
    except FileNotFoundError:
        return []


def _save(data: list, path: Path) -> None:
    save_json(data, path)


# ── Course catalog ────────────────────────────────────────────────────────────

def load_catalog() -> list[dict]:
    return _load(CATALOG_JSON)

def save_catalog(items: list[dict]) -> None:
    _save(items, CATALOG_JSON)

def catalog_names() -> list[str]:
    return [c["name"] for c in load_catalog()]


# ── Companies ─────────────────────────────────────────────────────────────────

def load_companies() -> list[dict]:
    return _load(COMPANIES_JSON)

def save_companies(items: list[dict]) -> None:
    _save(items, COMPANIES_JSON)

def company_names() -> list[str]:
    return [c["name"] for c in load_companies()]

def locations_for_company(company_name: str) -> list[dict]:
    """Return the list of location dicts {name, maps_url} for a given company."""
    for c in load_companies():
        if c["name"] == company_name:
            locs = c.get("locations", [])
            # Support legacy format (list of strings)
            return [l if isinstance(l, dict) else {"name": l, "maps_url": ""}
                    for l in locs]
    return []

def location_names_for_company(company_name: str) -> list[str]:
    """Return just the name strings for a company's locations."""
    return [l["name"] for l in locations_for_company(company_name)]

def maps_url_for_location(company_name: str, location_name: str) -> str:
    """Return the maps_url for a specific location, or empty string if not found."""
    for loc in locations_for_company(company_name):
        if loc["name"] == location_name:
            return loc.get("maps_url", "")
    return ""

def all_location_names() -> list[str]:
    """Flat sorted list of all location name strings across all companies."""
    seen = set()
    result = []
    for c in load_companies():
        for loc in c.get("locations", []):
            name = loc["name"] if isinstance(loc, dict) else loc
            if name not in seen:
                seen.add(name)
                result.append(name)
    return sorted(result)


# ── Modalities ────────────────────────────────────────────────────────────────

def load_modalities() -> list[dict]:
    """Return list of modality dicts with 'key' and 'label_key' fields."""
    return _load(MODALITIES_JSON)

def modality_keys() -> list[str]:
    return [m["key"] for m in load_modalities()]
