"""
app_paths.py
Resolves the location of the user's data folder (training_actions.json,
catalog.json, companies.json, holidays.json, settings.json).

The folder itself is chosen freely by the user — it can live inside a
cloud-synced directory (Google Drive, Dropbox, ...) so the same data
travels between computers. What each machine remembers locally is only a
small "pointer" file in %APPDATA%, containing the absolute path to that
folder as seen from THIS machine. The pointer is never synced: each
computer has its own, and the absolute path may differ between machines
even when they point at the same underlying (synced) content.

This module has no GUI dependency. The GUI layer supplies an
`ask_callback` used only when the data folder still needs to be chosen
(first run, or the previously remembered folder is no longer reachable).
"""

import json
import os
from pathlib import Path

APP_NAME = "PinkCat AutoCalendar"

# Files expected inside the user's data folder, with their "empty" defaults.
# Used only when initializing a brand-new folder, so the rest of the app
# never has to guess what an absent file means.
DEFAULT_FILES: dict[str, object] = {
    "training_actions.json": [],
    "catalog.json": [],
    "companies.json": [],
    "holidays.json": {},
    "settings.json": {},
}


def pointer_path() -> Path:
    """Path to the local, per-machine pointer file (never synced)."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        # Non-Windows dev environment fallback; production target is Windows.
        appdata = str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / APP_NAME / "config.json"


def read_pointer() -> Path | None:
    """Returns the remembered data folder for this machine, or None if unset."""
    p = pointer_path()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        raw = data.get("data_folder", "")
        return Path(raw) if raw else None
    except Exception:
        return None


def write_pointer(folder: Path) -> None:
    """Remembers `folder` as this machine's data folder."""
    p = pointer_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"data_folder": str(folder)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def init_new_folder(folder: Path) -> None:
    """
    Creates `folder` if needed and seeds it with empty default JSON files,
    but never overwrites files that already exist (so pointing "create new"
    at a folder that already has data is harmless).
    """
    folder.mkdir(parents=True, exist_ok=True)
    for filename, default in DEFAULT_FILES.items():
        f = folder / filename
        if not f.exists():
            f.write_text(
                json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8"
            )


def current_data_dir() -> Path:
    """
    Reads the already-resolved data folder for this machine, with no GUI
    involved. Used by modules (catalog.py, language.py, ...) that run after
    startup has already called get_data_dir() once.

    Raises RuntimeError if the folder was never resolved — that indicates a
    bug (something read data before main_window.py finished startup), not a
    normal "first run" situation, so it is not meant to be caught silently.
    """
    pointer = read_pointer()
    if pointer is None or not pointer.exists():
        raise RuntimeError(
            "Data folder not resolved yet. get_data_dir() must run once at "
            "startup (see main_window.py) before any module reads user data."
        )
    return pointer


def get_data_dir(ask_callback) -> Path:
    """
    Returns the resolved user-data folder for this machine.

    ask_callback(stale_pointer: Path | None) -> Path
        Called only when we don't already have a working folder. Receives
        the previously remembered path (or None on a true first run) so the
        GUI can tell the user "that folder is missing" vs "welcome, first
        time here". Must return a folder that is ready to use — if the user
        chose "create new", the callback is responsible for calling
        init_new_folder() before returning.
    """
    pointer = read_pointer()

    if pointer is not None and pointer.exists():
        return pointer

    folder = ask_callback(pointer)
    write_pointer(folder)
    return folder
