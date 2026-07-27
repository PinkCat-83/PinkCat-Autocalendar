"""
data_folder_dialog.py
First-use / relink dialog: asks the user to point at an existing data
folder or create a new one. Never offers a default location — the user
always chooses explicitly, with two clear, dedicated buttons (no relying
on "Cancel" as an implicit second option).
"""

from pathlib import Path
from tkinter import filedialog, simpledialog, messagebox

import customtkinter as ctk

import src.language as lang
from src.app_paths import init_new_folder


def _center_on_screen(win: ctk.CTkToplevel, width: int, height: int):
    win.update_idletasks()
    x = (win.winfo_screenwidth() - width) // 2
    y = (win.winfo_screenheight() - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


def ask_data_folder(parent: ctk.CTk, stale_pointer: Path | None,
                    manual: bool = False) -> Path | None:
    """
    Shows the modal dialog and blocks until the user has chosen or created a
    valid data folder, or (manual=True only) cancelled. Returns the
    resolved, ready-to-use folder path, or None if cancelled.

    manual=True is used when the user explicitly asks to switch folders from
    a working app (e.g. a "change data folder" button) — as opposed to the
    automatic first-run / folder-missing flows, which read `stale_pointer`
    to decide their wording and cannot be cancelled (a working data folder
    is mandatory to run the app at all).
    """
    result: dict[str, Path | None] = {"folder": None}

    dialog = ctk.CTkToplevel(parent)
    dialog.title(lang.get("data_folder_dialog_title"))
    dialog.resizable(False, False)
    dialog.grab_set()

    WIDTH, HEIGHT = 520, 320
    _center_on_screen(dialog, WIDTH, HEIGHT)

    body = ctk.CTkFrame(dialog, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=20)

    if manual:
        heading = lang.get("data_folder_change_heading")
        detail = lang.get("data_folder_change_detail")
    elif stale_pointer is not None:
        heading = lang.get("data_folder_missing_heading")
        detail = lang.get("data_folder_missing_detail", path=str(stale_pointer))
    else:
        heading = lang.get("data_folder_welcome_heading")
        detail = lang.get("data_folder_welcome_detail")

    ctk.CTkLabel(
        body, text=heading, font=ctk.CTkFont(size=16, weight="bold"),
        wraplength=470, justify="left",
    ).pack(anchor="w", pady=(0, 8))

    ctk.CTkLabel(
        body, text=detail, wraplength=470, justify="left",
    ).pack(anchor="w", pady=(0, 16))

    ctk.CTkLabel(
        body, text=lang.get("data_folder_cloud_hint"),
        wraplength=470, justify="left", text_color="#2E86C1",
        font=ctk.CTkFont(size=12),
    ).pack(anchor="w", pady=(0, 20))

    btn_row = ctk.CTkFrame(body, fg_color="transparent")
    btn_row.pack(fill="x", pady=(0, 4))

    def _choose_existing():
        chosen = filedialog.askdirectory(
            title=lang.get("data_folder_pick_existing_title"), mustexist=True
        )
        if not chosen:
            return  # user backed out of the OS picker — dialog stays open
        result["folder"] = Path(chosen)
        dialog.destroy()

    def _create_new():
        parent_dir = filedialog.askdirectory(
            title=lang.get("data_folder_pick_parent_title"), mustexist=True
        )
        if not parent_dir:
            return
        name = simpledialog.askstring(
            lang.get("data_folder_name_prompt_title"),
            lang.get("data_folder_name_prompt_body"),
            parent=dialog,
        )
        if not name:
            return
        new_folder = Path(parent_dir) / name
        if new_folder.exists() and any(new_folder.iterdir()):
            proceed = messagebox.askyesno(
                lang.get("data_folder_folder_exists_title"),
                lang.get("data_folder_folder_exists_body", path=str(new_folder)),
                parent=dialog,
            )
            if not proceed:
                return
        init_new_folder(new_folder)
        result["folder"] = new_folder
        dialog.destroy()

    ctk.CTkButton(
        btn_row, text=lang.get("data_folder_btn_existing"),
        height=44, fg_color="#2E86C1", hover_color="#1E5F8C",
        command=_choose_existing,
    ).pack(fill="x", pady=(0, 10))

    ctk.CTkButton(
        btn_row, text=lang.get("data_folder_btn_new"),
        height=44, fg_color="#27AE60", hover_color="#1E8449",
        command=_create_new,
    ).pack(fill="x")

    if manual:
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)  # cancel allowed
    else:
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # no implicit close/cancel
    parent.wait_window(dialog)

    return result["folder"]
