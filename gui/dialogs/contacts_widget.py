"""
contacts_widget.py
Reusable widget for viewing and editing a list of contacts.
Used in both the company editor and the course dialog.
Each contact has: name, role, phone, email.
"""

import customtkinter as ctk
import tkinter as tk
import src.language as lang

_BG_CANVAS = "#d0d0d0"
_ROW_EVEN  = "#c8c8c8"
_ROW_ODD   = "#dcdcdc"
_BORDER    = "#a0a0a0"

# Shared column layout (header and every row use identical padx/weights):
#   col 0 : [+] button — fixed width 28
#   col 1-4: name, role, phone, email — weight=1 each, padx=3
#   col 5 : [📋] — fixed width 28, padx=(6,2)
#   col 6 : [✕]  — fixed width 28, padx=(2,4)


class ContactsWidget(ctk.CTkFrame):

    def __init__(self, parent, contacts: list[dict] | None = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._contacts: list[dict] = list(contacts or [])
        self._rows: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="#b0b0b0", corner_radius=4)
        header.pack(fill="x", pady=(0, 1))

        # col 0: [+] — same width/padx as the entry placeholder in rows
        ctk.CTkButton(header, text="+", width=28, height=24,
                      fg_color="#27AE60", hover_color="#1E8449",
                      command=self._add_row
                      ).grid(row=0, column=0, padx=(4, 3), pady=3)

        # cols 1-4: labels centered, weight=1 — mirrors the CTkEntry columns
        for col, key in enumerate(["contact_name", "contact_role",
                                   "contact_phone", "contact_email"], start=1):
            ctk.CTkLabel(header, text=lang.get(key),
                         font=ctk.CTkFont(size=10, weight="bold"),
                         fg_color="transparent", anchor="center"
                         ).grid(row=0, column=col, padx=3, sticky="ew", pady=3)
            header.columnconfigure(col, weight=1)

        # cols 5-6: spacers sized to match 📋 and ✕ buttons
        ctk.CTkLabel(header, text="", width=28, fg_color="transparent"
                     ).grid(row=0, column=5, padx=(6, 2))
        ctk.CTkLabel(header, text="", width=28, fg_color="transparent"
                     ).grid(row=0, column=6, padx=(2, 4))

        # ── Scroll area ───────────────────────────────────────────────────────
        scroll_container = tk.Frame(self, bg=_BG_CANVAS,
                                    highlightthickness=1,
                                    highlightbackground=_BORDER)
        scroll_container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(scroll_container, highlightthickness=0,
                                 bd=0, bg=_BG_CANVAS)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical",
                                 command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._rows_frame = tk.Frame(self._canvas, bg=_BG_CANVAS)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._rows_frame, anchor="nw")

        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._rows_frame.bind("<Configure>", self._on_inner_resize)
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        for c in self._contacts:
            self._add_row(data=c)

    # ── Canvas helpers ────────────────────────────────────────────────────────

    def _on_canvas_resize(self, event):
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_inner_resize(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _bind_mousewheel(self, _event):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Rows ──────────────────────────────────────────────────────────────────

    def _row_color(self, index: int) -> str:
        return _ROW_EVEN if index % 2 == 0 else _ROW_ODD

    def _recolor_rows(self):
        for i, row in enumerate(self._rows):
            row["frame"].configure(bg=self._row_color(i))

    def _add_row(self, data: dict | None = None):
        c = data or {}
        color = self._row_color(len(self._rows))
        row_frame = tk.Frame(self._rows_frame, bg=color)

        # col 0: empty placeholder — same fixed width as the [+] button
        tk.Label(row_frame, text="", width=2, bg=color).grid(
            row=0, column=0, padx=(4, 3))

        # cols 1-4: entry fields — weight=1, same padx as header labels
        entries = {}
        for col, field in enumerate(["name", "role", "phone", "email"], start=1):
            ent = ctk.CTkEntry(row_frame, width=110)
            ent.insert(0, c.get(field, ""))
            ent.grid(row=0, column=col, padx=3, pady=3, sticky="ew")
            row_frame.columnconfigure(col, weight=1)
            entries[field] = ent

        # col 5: [📋]
        ctk.CTkButton(
            row_frame, text="📋", width=28, height=28,
            fg_color="#2471A3", hover_color="#1A5276",
            command=lambda e=entries["email"]: self._copy_email(e)
        ).grid(row=0, column=5, padx=(6, 2), pady=3)

        # col 6: [✕]
        ctk.CTkButton(
            row_frame, text="✕", width=28, height=28,
            fg_color="#C0392B", hover_color="#922B21",
            command=lambda rf=row_frame: self._remove_row(rf)
        ).grid(row=0, column=6, padx=(2, 4), pady=3)

        self._rows.append({"frame": row_frame, "entries": entries})
        row_frame.pack(fill="x")

    def _remove_row(self, row_frame: tk.Frame):
        self._rows = [r for r in self._rows if r["frame"] is not row_frame]
        row_frame.destroy()
        self._recolor_rows()

    # ── Helpers ───────────────────────────────────────────────────────────────

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
