"""
locations_widget.py
Reusable widget for viewing and editing a list of locations.
Used in the company editor (CompanyDialog).
Each location is a dict: {"name": str, "maps_url": str}.
Design mirrors ContactsWidget for visual consistency.
"""

import customtkinter as ctk
import src.language as lang


class LocationsWidget(ctk.CTkFrame):
    """
    Embeddable location list editor.
    Header has a [+] button to append a new row (mirrors ContactsWidget).
    Each row has: [location name] [maps url] [✕]
    When there are no rows, a standalone [+] is shown in the scroll area.
    Call .get_locations() to retrieve the current list of dicts.
    """

    def __init__(self, parent, locations: list | None = None,
                 scroll_height: int = 340, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        # Normalise legacy format (list of strings)
        raw = locations or []
        self._locations: list[dict] = [
            l if isinstance(l, dict) else {"name": l, "maps_url": ""}
            for l in raw
        ]
        self._rows: list[dict] = []
        self._scroll_height = scroll_height
        self._build_ui()

    def _build_ui(self):
        # Column header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkButton(
            header, text="+", width=28, height=28,
            fg_color="#27AE60", hover_color="#1E8449",
            command=self._add_row,
        ).grid(row=0, column=0, padx=4)
        ctk.CTkLabel(header, text=lang.get("location_name"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     anchor="w").grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(header, text=lang.get("location_maps_url"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     anchor="w").grid(row=0, column=2, padx=4, sticky="ew")
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=2)
        ctk.CTkLabel(header, text="", width=28).grid(row=0, column=3, padx=4)

        # Scrollable rows area
        self._rows_frame = ctk.CTkScrollableFrame(
            self, height=self._scroll_height, label_text="")
        self._rows_frame.pack(fill="both", expand=True)

        if self._locations:
            for loc in self._locations:
                self._add_row(name=loc.get("name", ""),
                              maps_url=loc.get("maps_url", ""))
        else:
            self._refresh_empty_hint()

    def _add_row(self, name: str = "", maps_url: str = ""):
        """Append a new location row at the end of the list."""
        row_frame = ctk.CTkFrame(self._rows_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        row_frame.columnconfigure(0, weight=1)
        row_frame.columnconfigure(1, weight=2)

        # Location name entry
        ent_name = ctk.CTkEntry(row_frame, width=160)
        ent_name.insert(0, name)
        ent_name.grid(row=0, column=0, padx=(4, 4), sticky="ew")

        # Maps URL entry
        ent_url = ctk.CTkEntry(row_frame, width=260)
        ent_url.insert(0, maps_url)
        ent_url.grid(row=0, column=1, padx=(0, 4), sticky="ew")

        # [✕] remove
        btn_del = ctk.CTkButton(
            row_frame, text="✕", width=28, height=28,
            fg_color="#C0392B", hover_color="#922B21",
            command=lambda rf=row_frame: self._remove_row(rf))
        btn_del.grid(row=0, column=2, padx=(2, 6))

        self._rows.append({"frame": row_frame, "entry": ent_name, "url": ent_url})

        self.after(30, ent_name.focus_set)

    def _remove_row(self, row_frame: ctk.CTkFrame):
        self._rows = [r for r in self._rows if r["frame"] is not row_frame]
        row_frame.destroy()
        self._refresh_empty_hint()

    def _refresh_empty_hint(self):
        """Show a lone [+] in the scroll area only when there are no rows."""
        if hasattr(self, "_empty_btn") and self._empty_btn.winfo_exists():
            self._empty_btn.destroy()
        if not self._rows:
            self._empty_btn = ctk.CTkButton(
                self._rows_frame, text="+", width=28, height=28,
                fg_color="#27AE60", hover_color="#1E8449",
                command=lambda: (self._empty_btn.destroy(),
                                 self._add_row()))
            self._empty_btn.pack(anchor="w", padx=2, pady=4)

    def get_locations(self) -> list[dict]:
        result = []
        for r in self._rows:
            name = r["entry"].get().strip()
            if name:
                result.append({"name": name, "maps_url": r["url"].get().strip()})
        return result
