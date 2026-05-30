"""
contacts_widget.py
Reusable widget for viewing and editing a list of contacts.
Used in both the company editor and the course dialog.
Each contact has: name, role, phone, email.
"""

import customtkinter as ctk
from tkinter import messagebox
import src.language as lang
import tkinter as tk


class ContactsWidget(ctk.CTkFrame):
    """
    Embeddable contact list editor.
    Each row has: [+] [name] [role] [phone] [email] [📋] [✕]
    The [+] button inserts a new empty row immediately below that row.
    When there are no rows, a standalone [+] is shown to create the first one.
    Call .get_contacts() to retrieve the current list.
    """

    def __init__(self, parent, contacts: list[dict] | None = None,
                 scroll_height: int = 340, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._contacts: list[dict] = list(contacts or [])
        self._rows: list[dict] = []
        self._scroll_height = scroll_height
        self._build_ui()

    # ── Column indices ────────────────────────────────────────────────────────
    # col 0 : [+] add button
    # col 1-4: name, role, phone, email entries
    # col 5 : [📋] copy email
    # col 6 : [✕]  remove

    def _build_ui(self):
        # Column headers — col 0 left blank to align with the [+] button
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(header, text="", width=32).grid(row=0, column=0, padx=4)
        for col, key in enumerate(["contact_name", "contact_role",
                                   "contact_phone", "contact_email"], start=1):
            ctk.CTkLabel(header, text=lang.get(key),
                         font=ctk.CTkFont(size=10, weight="bold"),
                         anchor="w").grid(row=0, column=col, padx=4, sticky="ew")
            header.columnconfigure(col, weight=1)
        ctk.CTkLabel(header, text="").grid(row=0, column=5, padx=4)
        ctk.CTkLabel(header, text="").grid(row=0, column=6, padx=4)

        # Scrollable rows area
        self._rows_frame = ctk.CTkScrollableFrame(
            self, height=self._scroll_height, label_text="")
        self._rows_frame.pack(fill="both", expand=True)

        # Populate existing contacts (or show the empty-state + button)
        if self._contacts:
            for c in self._contacts:
                self._add_row(data=c)
        else:
            self._refresh_empty_hint()

    def _add_row(self, after_frame=None, data: dict | None = None):
        """
        Insert a new contact row.
        - after_frame: if given, insert the new row immediately after that frame.
        - data: pre-fill with existing contact dict.
        """
        c = data or {}

        row_frame = ctk.CTkFrame(self._rows_frame, fg_color="transparent")

        # Determine insertion position in the rows list
        if after_frame is not None:
            idx = next((i for i, r in enumerate(self._rows)
                        if r["frame"] is after_frame), len(self._rows) - 1)
            insert_at = idx + 1
        else:
            insert_at = len(self._rows)

        # Place the frame visually — pack doesn't support mid-list insertion,
        # so we re-pack all frames in order after inserting.
        row_frame.pack(fill="x", pady=2)

        # [+] button — adds a row below this one
        btn_add = ctk.CTkButton(
            row_frame, text="+", width=28, height=28,
            fg_color="#27AE60", hover_color="#1E8449",
            command=lambda rf=row_frame: self._add_row(after_frame=rf))
        btn_add.grid(row=0, column=0, padx=(2, 4))

        entries = {}
        for col, field in enumerate(["name", "role", "phone", "email"], start=1):
            ent = ctk.CTkEntry(row_frame, width=120)
            ent.insert(0, c.get(field, ""))
            ent.grid(row=0, column=col, padx=4, sticky="ew")
            row_frame.columnconfigure(col, weight=1)
            entries[field] = ent

        # [📋] copy email
        btn_copy = ctk.CTkButton(
            row_frame, text="📋", width=28, height=28,
            fg_color="#2471A3", hover_color="#1A5276",
            command=lambda e=entries["email"]: self._copy_email(e))
        btn_copy.grid(row=0, column=5, padx=(8, 2))

        # [✕] remove
        btn_del = ctk.CTkButton(
            row_frame, text="✕", width=28, height=28,
            fg_color="#C0392B", hover_color="#922B21",
            command=lambda rf=row_frame: self._remove_row(rf))
        btn_del.grid(row=0, column=6, padx=(2, 6))

        row_record = {"frame": row_frame, "entries": entries}
        self._rows.insert(insert_at, row_record)

        # Re-pack all frames to enforce visual order
        self._repack_rows()

    def _repack_rows(self):
        """Re-pack all row frames in list order so insertions appear correctly."""
        for r in self._rows:
            r["frame"].pack_forget()
        for r in self._rows:
            r["frame"].pack(fill="x", pady=2)

    def _remove_row(self, row_frame: ctk.CTkFrame):
        self._rows = [r for r in self._rows if r["frame"] is not row_frame]
        row_frame.destroy()
        self._refresh_empty_hint()

    def _refresh_empty_hint(self):
        """Show a lone [+] button when there are no rows, hide it when there are."""
        # Remove any existing hint
        if hasattr(self, "_empty_btn") and self._empty_btn.winfo_exists():
            self._empty_btn.destroy()
        if not self._rows:
            self._empty_btn = ctk.CTkButton(
                self._rows_frame, text="+", width=28, height=28,
                fg_color="#27AE60", hover_color="#1E8449",
                command=lambda: (self._empty_btn.destroy(),
                                 self._add_row()))
            self._empty_btn.pack(anchor="w", padx=2, pady=4)

    def _copy_email(self, email_entry: ctk.CTkEntry):
        email = email_entry.get().strip()
        if email:
            self.clipboard_clear()
            self.clipboard_append(email)

    def get_contacts(self) -> list[dict]:
        result = []
        for row in self._rows:
            entries = row["entries"]
            values = {f: entries[f].get().strip() for f in entries}
            if any(values.values()):
                result.append(values)
        return result
