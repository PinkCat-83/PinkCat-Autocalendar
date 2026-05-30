"""
tab_dialogs.py
Modal dialogs for the management tabs:
  - CatalogDialog    (course catalog entry)
  - CompanyDialog    (company + locations list)
  - HolidayDialog    (single holiday entry)
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
import re
import calendar
import tkinter as tk
import src.language as lang
from gui.widgets.locations_widget import LocationsWidget


# ── Shared helpers ────────────────────────────────────────────────────────────

def _labeled_entry(frame, label: str, row: int,
                   initial: str = "", width: int = 300,
                   maxlen: int | None = None) -> ctk.CTkEntry:
    ctk.CTkLabel(frame, text=label, anchor="w", width=140).grid(
        row=row, column=0, sticky="w", pady=4, padx=4)
    ent = ctk.CTkEntry(frame, width=width)
    if maxlen is not None:
        vcmd = (frame.register(lambda s: len(s) <= maxlen), "%P")
        ent.configure(validate="key", validatecommand=vcmd)
    ent.insert(0, initial)
    ent.grid(row=row, column=1, sticky="ew", pady=4, padx=4)
    return ent


def _center_on_parent(window, parent, w: int, h: int) -> None:
    """Positions *window* (w×h) centered over *parent*."""
    window.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    window.geometry(f"{w}x{h}+{x}+{y}")


# ── Course catalog dialog ─────────────────────────────────────────────────────

class CatalogDialog(ctk.CTkToplevel):

    def __init__(self, parent, item: dict | None = None):
        super().__init__(parent)
        self.title(lang.get("catalog_new") if item is None else lang.get("catalog_edit"))
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None
        _center_on_parent(self, parent, 480, 320)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        frame.columnconfigure(1, weight=1)

        self._ent_name = _labeled_entry(frame, lang.get("catalog_name"), 0,
                                        item.get("name", "") if item else "")
        self._ent_short_name = _labeled_entry(frame, lang.get("catalog_short_name"), 1,
                                              item.get("short_name", "") if item else "",
                                              width=200, maxlen=8)
        self._ent_hours = _labeled_entry(frame, lang.get("catalog_total_hours"), 2,
                                         str(item.get("total_hours", "")) if item else "",
                                         width=100)
        self._ent_desc = _labeled_entry(frame, lang.get("catalog_description"), 3,
                                        item.get("description", "") if item else "")

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(btn_bar, text=lang.get("dialog_save"),
                      command=self._save, width=110).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text=lang.get("dialog_cancel"),
                      command=self.destroy, width=90,
                      fg_color="gray").pack(side="right")
        self.after(50, self._ent_name.focus_set)
        self.wait_window()

    def _save(self):
        name = self._ent_name.get().strip()
        if not name:
            messagebox.showerror(lang.get("error_form_title"),
                                 lang.get("error_name_required"))
            return
        try:
            hours = float(self._ent_hours.get().replace(",", "."))
            assert hours > 0
        except (ValueError, AssertionError):
            messagebox.showerror(lang.get("error_form_title"),
                                 lang.get("error_total_hours"))
            return
        self.result = {
            "name": name,
            "short_name": self._ent_short_name.get().strip(),
            "total_hours": hours,
            "description": self._ent_desc.get().strip(),
        }
        self.destroy()


# ── Company dialog ────────────────────────────────────────────────────────────

class CompanyDialog(ctk.CTkToplevel):
    """
    Dialog to add or edit a company.
    Left column: company name.
    Right column: LocationsWidget (mirrors ContactsWidget design).
    """

    def __init__(self, parent, item: dict | None = None):
        super().__init__(parent)
        self.title(lang.get("company_new") if item is None else lang.get("company_edit"))
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None
        _center_on_parent(self, parent, 820, 420)

        # ── Buttons (packed first, side=bottom) ───────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(side="bottom", fill="x", padx=16, pady=12)
        ctk.CTkButton(btn_bar, text=lang.get("dialog_save"),
                      command=self._save, width=110).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text=lang.get("dialog_cancel"),
                      command=self.destroy, width=90,
                      fg_color="gray").pack(side="right")

        # ── Main body ─────────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(14, 0))

        # ── Left column: company name ─────────────────────────────────────────
        left = ctk.CTkFrame(body, fg_color="transparent", width=260)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)

        ctk.CTkLabel(left, text=lang.get("company_name"),
                     font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w").pack(anchor="w", pady=(0, 6))

        name_row = ctk.CTkFrame(left, fg_color="transparent")
        name_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(name_row, text=lang.get("company_name"),
                     anchor="w", width=120).pack(side="left")
        self._ent_name = ctk.CTkEntry(name_row, width=160)
        self._ent_name.insert(0, item.get("name", "") if item else "")
        self._ent_name.pack(side="left", padx=(4, 0))

        acronym_row = ctk.CTkFrame(left, fg_color="transparent")
        acronym_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(acronym_row, text=lang.get("company_acronym"),
                     anchor="w", width=120).pack(side="left")
        _vcmd = (self.register(lambda s: len(s) <= 8), "%P")
        self._ent_acronym = ctk.CTkEntry(acronym_row, width=100,
                                         validate="key", validatecommand=_vcmd)
        self._ent_acronym.insert(0, item.get("acronym", "") if item else "")
        self._ent_acronym.pack(side="left", padx=(4, 0))

        # ── Right column: locations widget ────────────────────────────────────
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(right, text=lang.get("company_locations"),
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(anchor="w", pady=(0, 6))

        self._locations = LocationsWidget(
            right, locations=item.get("locations", []) if item else [])
        self._locations.pack(fill="both", expand=True)

        self.after(50, self._ent_name.focus_set)
        self.wait_window()

    def _save(self):
        name = self._ent_name.get().strip()
        if not name:
            messagebox.showerror(lang.get("error_form_title"),
                                 lang.get("error_name_required"))
            return
        self.result = {
            "name": name,
            "acronym": self._ent_acronym.get().strip(),
            "locations": self._locations.get_locations(),
        }
        self.destroy()



def _parse_date(raw: str) -> str | None:
    """
    Accept dd/mm/yyyy or yyyy/mm/dd with any separator (- / .)
    and return a normalized yyyy-mm-dd string, or None if invalid.
    """
    s = re.sub(r"[\/\.]", "-", raw.strip())
    parts = s.split("-")
    if len(parts) != 3:
        return None
    a, b, c = parts
    if len(a) == 4:        # yyyy-mm-dd
        normalized = f"{a}-{b.zfill(2)}-{c.zfill(2)}"
    elif len(c) == 4:      # dd-mm-yyyy
        normalized = f"{c}-{b.zfill(2)}-{a.zfill(2)}"
    else:
        return None
    try:
        from datetime import date as _date
        _date.fromisoformat(normalized)
        return normalized
    except ValueError:
        return None


# ── Date picker popup ─────────────────────────────────────────────────────────

class DatePickerPopup(tk.Toplevel):
    """
    Lightweight calendar popup.
    Opens anchored below a given widget; closes when a date is picked or
    when the user clicks outside. Calls on_select(date_str) with ISO format.
    """

    def __init__(self, parent, anchor_widget: ctk.CTkEntry, on_select):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._on_select = on_select

        raw = anchor_widget.get().strip()
        try:
            initial = date.fromisoformat(raw)
        except ValueError:
            initial = date.today()
        self._year = initial.year
        self._month = initial.month

        self.update_idletasks()
        x = anchor_widget.winfo_rootx()
        y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 2
        self.geometry(f"+{x}+{y}")

        self._build()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Button-1>", self._on_click)
        self.focus_set()
        self.grab_set()

    def _on_click(self, event):
        """Close if click is outside the popup bounds."""
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        if not (x <= event.x_root <= x + w and y <= event.y_root <= y + h):
            self.destroy()

    def _check_focus(self):
        pass  # no longer used

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        outer = tk.Frame(self, bg="#2B2B2B", bd=1, relief="solid")
        outer.pack(fill="both", expand=True)

        nav = tk.Frame(outer, bg="#2B2B2B")
        nav.pack(fill="x", padx=4, pady=(4, 2))

        tk.Button(nav, text="◀", bg="#2B2B2B", fg="white",
                  relief="flat", cursor="hand2", activebackground="#3A3A3A",
                  command=self._prev_month).pack(side="left")

        _month_keys = [
            "month_january","month_february","month_march","month_april",
            "month_may","month_june","month_july","month_august",
            "month_september","month_october","month_november","month_december",
        ]
        month_name = f"{lang.get(_month_keys[self._month - 1])} {self._year}"
        tk.Label(nav, text=month_name, bg="#2B2B2B", fg="white",
                 font=("Segoe UI", 10, "bold"), width=14).pack(side="left", expand=True)

        tk.Button(nav, text="▶", bg="#2B2B2B", fg="white",
                  relief="flat", cursor="hand2", activebackground="#3A3A3A",
                  command=self._next_month).pack(side="right")

        CELL_W = 32
        cal_grid = tk.Frame(outer, bg="#2B2B2B")
        cal_grid.pack(fill="x", padx=6, pady=(0, 4))
        for col in range(7):
            cal_grid.columnconfigure(col, minsize=CELL_W, uniform="day")

        abbrs = [
            lang.get("weekday_mon"), lang.get("weekday_tue"), lang.get("weekday_wed"),
            lang.get("weekday_thu"), lang.get("weekday_fri"),
            lang.get("weekday_sat"), lang.get("weekday_sun"),
        ]
        for col, abbr in enumerate(abbrs):
            tk.Label(cal_grid, text=abbr, bg="#2B2B2B", fg="#AAAAAA",
                     font=("Segoe UI", 8, "bold"),
                     anchor="center").grid(row=0, column=col, ipady=2)

        today = date.today()
        cal = calendar.monthcalendar(self._year, self._month)

        for week_row, week in enumerate(cal, start=1):
            for col, day_num in enumerate(week):
                if day_num == 0:
                    tk.Label(cal_grid, text="", bg="#2B2B2B"
                             ).grid(row=week_row, column=col)
                else:
                    is_today = (day_num == today.day and
                                self._month == today.month and
                                self._year == today.year)
                    fg = "#F4D03F" if is_today else "white"
                    btn = tk.Button(
                        cal_grid, text=str(day_num),
                        bg="#2B2B2B", fg=fg,
                        relief="flat", cursor="hand2",
                        activebackground="#4A4A4A", activeforeground="white",
                        font=("Segoe UI", 9),
                        command=lambda d=day_num: self._pick(d))
                    btn.grid(row=week_row, column=col, sticky="nsew", ipady=3)

    def _prev_month(self):
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self._build()

    def _next_month(self):
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self._build()

    def _pick(self, day: int):
        selected = date(self._year, self._month, day)
        self._on_select(selected.isoformat())
        self.destroy()

# ── Holiday dialog ────────────────────────────────────────────────────────────

class HolidayDialog(ctk.CTkToplevel):

    def __init__(self, parent, item: dict | None = None):
        super().__init__(parent)
        self.title(lang.get("holiday_new") if item is None else lang.get("holiday_edit"))
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None
        _center_on_parent(self, parent, 420, 200)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        frame.columnconfigure(1, weight=1)

        # Date row: entry + calendar picker button
        ctk.CTkLabel(frame, text=lang.get("holiday_date"),
                     anchor="w", width=140).grid(row=0, column=0, sticky="w", pady=4, padx=4)
        date_row = ctk.CTkFrame(frame, fg_color="transparent")
        date_row.grid(row=0, column=1, sticky="ew", pady=4, padx=4)
        self._ent_date = ctk.CTkEntry(date_row, width=120)
        self._ent_date.insert(0, item.get("date", "") if item else "")
        self._ent_date.pack(side="left")
        ctk.CTkButton(date_row, text="\U0001f4c5", width=32, height=28,
                      command=self._open_date_picker).pack(side="left", padx=(4, 0))

        self._ent_name = _labeled_entry(frame, lang.get("holiday_name"), 1,
                                        item.get("name", "") if item else "")

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(btn_bar, text=lang.get("dialog_save"),
                      command=self._save, width=110).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text=lang.get("dialog_cancel"),
                      command=self.destroy, width=90,
                      fg_color="gray").pack(side="right")
        self.after(50, self._ent_date.focus_set)
        self.wait_window()

    def _open_date_picker(self):
        def on_select(date_str: str):
            self._ent_date.delete(0, "end")
            self._ent_date.insert(0, date_str)
        DatePickerPopup(self, self._ent_date, on_select)

    def _save(self):
        date_str = _parse_date(self._ent_date.get())
        if date_str is None:
            messagebox.showerror(lang.get("error_form_title"),
                                 lang.get("error_start_date"))
            return
        self.result = {"date": date_str, "name": self._ent_name.get().strip()}
        self.destroy()
