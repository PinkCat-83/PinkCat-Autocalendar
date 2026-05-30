"""
holidays_widget.py
Reusable widget for viewing and editing a list of course-specific holidays.
Used in the course dialog (specific_holidays field).
Each row is a single date string (ISO yyyy-mm-dd).
Design mirrors ContactsWidget / LocationsWidget for visual consistency.
"""

import re
import customtkinter as ctk
import tkinter as tk
from datetime import date
import calendar
import src.language as lang


def _parse_date(raw: str) -> str | None:
    """Accept dd/mm/yyyy or yyyy/mm/dd with any separator and return yyyy-mm-dd or None."""
    s = re.sub(r"[\/\.]", "-", raw.strip())
    parts = s.split("-")
    if len(parts) != 3:
        return None
    a, b, c = parts
    if len(a) == 4:
        normalized = f"{a}-{b.zfill(2)}-{c.zfill(2)}"
    elif len(c) == 4:
        normalized = f"{c}-{b.zfill(2)}-{a.zfill(2)}"
    else:
        return None
    try:
        date.fromisoformat(normalized)
        return normalized
    except ValueError:
        return None


class _DatePickerPopup(tk.Toplevel):
    """Inline calendar popup — same implementation as in course_dialog/tab_dialogs."""

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
        self._year  = initial.year
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
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        if not (x <= event.x_root <= x + w and y <= event.y_root <= y + h):
            self.destroy()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        outer = tk.Frame(self, bg="#2B2B2B", bd=1, relief="solid")
        outer.pack(fill="both", expand=True)

        nav = tk.Frame(outer, bg="#2B2B2B")
        nav.pack(fill="x", padx=4, pady=(4, 2))

        tk.Button(nav, text="\u25c0", bg="#2B2B2B", fg="white",
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

        tk.Button(nav, text="\u25b6", bg="#2B2B2B", fg="white",
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
                    tk.Label(cal_grid, text="", bg="#2B2B2B").grid(row=week_row, column=col)
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


class HolidaysWidget(ctk.CTkFrame):
    """
    Embeddable course-specific holidays editor.
    Header row: [+] [Date label]   — the [+] appends a new empty row.
    Data rows:  [spacer] [date entry] [📅] [✕]
    When there are no rows, a standalone [+] is shown as a fallback hint.
    Call .get_holidays() to retrieve the current list of ISO date strings.
    """

    def __init__(self, parent, holidays: list[str] | None = None,
                 scroll_height: int = 200, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._holidays: list[str] = list(holidays or [])
        self._rows: list[dict] = []
        self._scroll_height = scroll_height
        self._build_ui()

    def _build_ui(self):
        # Column header — [+] lives here only
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkButton(
            header, text="+", width=28, height=28,
            fg_color="#27AE60", hover_color="#1E8449",
            command=self._add_row
        ).grid(row=0, column=0, padx=(2, 4))
        ctk.CTkLabel(header, text=lang.get("holiday_date"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     anchor="w").grid(row=0, column=1, padx=4, sticky="ew")
        header.columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="").grid(row=0, column=2, padx=4)
        ctk.CTkLabel(header, text="").grid(row=0, column=3, padx=4)

        self._rows_frame = ctk.CTkScrollableFrame(
            self, height=self._scroll_height, label_text="")
        self._rows_frame.pack(fill="both", expand=True)

        for h in self._holidays:
            self._add_row(value=h)

    def _add_row(self, value: str = ""):
        row_frame = ctk.CTkFrame(self._rows_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        row_frame.columnconfigure(1, weight=1)

        # Invisible spacer — aligns entry with header label (mirrors ContactsWidget)
        ctk.CTkLabel(row_frame, text="", width=28).grid(row=0, column=0, padx=(2, 4))

        # Date entry
        ent = ctk.CTkEntry(row_frame, width=140)
        ent.insert(0, value)
        ent.grid(row=0, column=1, padx=4, sticky="ew")

        # [📅] calendar picker
        btn_cal = ctk.CTkButton(
            row_frame, text="\U0001f4c5", width=28, height=28,
            command=lambda e=ent: self._open_picker(e))
        btn_cal.grid(row=0, column=2, padx=(2, 2))

        # [✕] remove
        btn_del = ctk.CTkButton(
            row_frame, text="✕", width=28, height=28,
            fg_color="#C0392B", hover_color="#922B21",
            command=lambda rf=row_frame: self._remove_row(rf))
        btn_del.grid(row=0, column=3, padx=(2, 6))

        row_record = {"frame": row_frame, "entry": ent}
        self._rows.append(row_record)
        self.after(30, ent.focus_set)

    def _open_picker(self, entry: ctk.CTkEntry):
        def on_select(date_str: str):
            entry.delete(0, "end")
            entry.insert(0, date_str)
        _DatePickerPopup(self, entry, on_select)

    def _remove_row(self, row_frame: ctk.CTkFrame):
        self._rows = [r for r in self._rows if r["frame"] is not row_frame]
        row_frame.destroy()

    def get_holidays(self) -> list[str]:
        """Return valid ISO date strings, skipping empty or unparseable rows."""
        result = []
        for r in self._rows:
            raw = r["entry"].get().strip()
            parsed = _parse_date(raw)
            if parsed:
                result.append(parsed)
        return result
