"""
calendar_view.py
Monthly calendar grid widget.
Supports course highlight: when a course is selected in the panel,
teaching days of the selected course are highlighted with a yellow border.
"""

import calendar
from datetime import date

import customtkinter as ctk
import tkinter as tk

from gui.widgets.colors import ColorManager
import src.language as lang
import src.catalog as _catalog


class CalendarView(ctk.CTkFrame):

    def __init__(self, parent, color_manager: ColorManager,
                 layout: dict, on_day_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._colors = color_manager
        self._layout = layout
        self._on_day_click = on_day_click
        self._cells: list[tk.Widget] = []
        self._header_frame: ctk.CTkFrame | None = None

        # Highlight state
        self._highlight_name: str | None = None
        self._highlight_shift: str | None = None

        # Holidays map: date -> name
        self._holidays: dict[date, str] = {}

        # Store last render data for re-highlighting without full redraw
        self._last_year: int = 0
        self._last_month: int = 0
        self._last_days_by_date: dict = {}

        # Map date -> cell frame (for highlight without full rebuild)
        self._cell_map: dict[date, ctk.CTkFrame] = {}

        self._acronym_cache: dict[str, str] = {}
        self._build_header()

    # ── Weekday header ────────────────────────────────────────────────────────

    def _weekday_labels(self) -> list[str]:
        return [lang.get(f"weekday_{k}") for k in
                ("mon", "tue", "wed", "thu", "fri", "sat", "sun")]

    def _build_header(self):
        if self._header_frame:
            self._header_frame.destroy()
        self._header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._header_frame.pack(fill="x", padx=10, pady=(8, 0))
        font_size = self._layout["header_font_size"]
        sat_label = lang.get("weekday_sat")
        sun_label = lang.get("weekday_sun")
        for i, day in enumerate(self._weekday_labels()):
            color = "#E74C3C" if day == sun_label else ("#E67E22" if day == sat_label else "gray")
            ctk.CTkLabel(
                self._header_frame, text=day,
                font=ctk.CTkFont(size=font_size, weight="bold"), text_color=color
            ).grid(row=0, column=i, padx=2, sticky="ew")
            self._header_frame.columnconfigure(i, weight=1)

    def rebuild_header(self):
        self._acronym_cache: dict[str, str] = {}
        self._build_header()

    # ── Full month render ─────────────────────────────────────────────────────

    def show(self, year: int, month: int, days_by_date: dict[date, list[dict]],
             holidays: dict[date, str] | None = None):
        """Clears and redraws the full calendar grid for the given month."""
        for w in self._cells:
            w.destroy()
        self._cells.clear()
        self._cell_map.clear()

        self._last_year = year
        self._last_month = month
        self._last_days_by_date = days_by_date
        self._holidays = holidays or {}

        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=10, pady=8)
        self._cells.append(grid_frame)

        month_weeks = calendar.monthcalendar(year, month)
        while len(month_weeks) < 6:
            month_weeks.append([0] * 7)

        today = date.today()
        for week_idx, week in enumerate(month_weeks):
            for day_idx, day_num in enumerate(week):
                cell = self._build_cell(
                    grid_frame, year, month, day_num, day_idx,
                    days_by_date, today
                )
                cell.grid(row=week_idx, column=day_idx, padx=2, pady=2, sticky="nsew")
                grid_frame.columnconfigure(day_idx, weight=1)
                if day_num != 0:
                    self._cell_map[date(year, month, day_num)] = cell
            grid_frame.rowconfigure(week_idx, weight=1)

        # Re-apply highlight if one is active
        if self._highlight_name:
            self._apply_highlight()

    def _acronym(self, company: str) -> str:
        """Return acronym for a company name, with caching."""
        if company not in self._acronym_cache:
            acronym = ""
            try:
                for co in _catalog.load_companies():
                    if co.get("name") == company:
                        acronym = co.get("acronym", "")
                        break
            except Exception:
                pass
            if not acronym and "(" in company and ")" in company:
                acronym = company[company.index("(")+1:company.index(")")]
            self._acronym_cache[company] = acronym
        return self._acronym_cache[company]

    def _fmt_time(self, t) -> str:
        if t is None:
            return ""
        h = int(t)
        m = int(round((t - h) * 60))
        return f"{h:02d}:{m:02d}"

    def _build_cell(self, parent, year, month, day_num, day_idx,
                    days_by_date, today):
        cell_w = self._layout["cell_width"]
        cell_h = self._layout["cell_height"]
        day_num_size = self._layout["day_num_font_size"]
        label_size = self._layout["cell_font_size"]
        is_weekend = day_idx >= 5

        if day_num == 0:
            return ctk.CTkFrame(parent, width=cell_w, height=cell_h, fg_color="transparent")

        cell_date = date(year, month, day_num)
        courses_today = days_by_date.get(cell_date, [])
        is_today = (cell_date == today)
        is_holiday = cell_date in self._holidays

        if is_today:
            bg = "#2E86C1"
        elif is_holiday:
            bg = "#FDEDEC"   # soft red tint for holidays
        elif is_weekend:
            bg = "#F2F3F4"
        else:
            bg = "#FFFFFF"

        cell = ctk.CTkFrame(parent, width=cell_w, height=cell_h,
                            fg_color=bg, corner_radius=6)
        cell.pack_propagate(False)

        num_color = "white" if is_today else ("#C0392B" if (is_weekend or is_holiday) else None)
        lbl_num = ctk.CTkLabel(
            cell, text=str(day_num),
            font=ctk.CTkFont(size=day_num_size, weight="bold" if is_today else "normal"),
            text_color=num_color, anchor="ne")
        lbl_num.pack(anchor="ne", padx=6, pady=(4, 1))

        # Holiday name label
        if is_holiday:
            holiday_name = self._holidays[cell_date]
            if holiday_name:
                max_h = 13 if cell_w >= 140 else 10
                short = holiday_name[:max_h] + "…" if len(holiday_name) > max_h else holiday_name
                tk.Label(cell, text=short, bg="#FDEDEC", fg="#C0392B",
                         font=("Segoe UI", label_size - 1, "italic"),
                         padx=3, pady=0, anchor="w").pack(fill="x", padx=3)

        for course_day in courses_today[:3]:
            name       = course_day.get("name", "")
            short_name = course_day.get("short_name", "") or name
            shift      = course_day.get("shift", "")
            company    = course_day.get("company", "")
            start_time = course_day.get("start_time")
            end_time   = course_day.get("end_time")
            confirmed  = not course_day.get("pending", False)

            bg_color = self._colors.bg_color_for(course_day)
            fg_color = self._colors.text_color_for(course_day)

            acronym  = self._acronym(company)
            time_str = (f"{self._fmt_time(start_time)}–{self._fmt_time(end_time)}"
                        if start_time is not None else "")

            # Outer row frame — colored bg, fixed height
            row_h = label_size + 10
            row = tk.Frame(cell, bg=bg_color, height=row_h, cursor="hand2")
            row.pack(fill="x", padx=3, pady=1)
            row.pack_propagate(False)

            # Warning icon for unconfirmed — black background strip on the left
            if not confirmed:
                lbl_warn = tk.Label(row, text="⚠", bg="#111111", fg="#F4D03F",
                                    font=("Segoe UI", label_size - 1),
                                    padx=3, pady=0)
                lbl_warn.pack(side="left", fill="y")
                lbl_warn.bind("<Button-1>",
                              lambda e, d=cell_date, c=courses_today: self._on_day_click(d, c))

            # Left: short_name
            lbl_left = tk.Label(row, text=short_name, bg=bg_color, fg=fg_color,
                                font=("Segoe UI", label_size),
                                anchor="w", padx=3, pady=0)
            lbl_left.pack(side="left")

            # Centre: acronym
            if acronym:
                lbl_acronym = tk.Label(row, text=acronym, bg=bg_color, fg=fg_color,
                                       font=("Segoe UI", label_size),
                                       anchor="center", padx=3, pady=0)
                lbl_acronym.pack(side="left", fill="x", expand=True)
                lbl_acronym.bind("<Button-1>",
                                 lambda e, d=cell_date, c=courses_today: self._on_day_click(d, c))
            else:
                lbl_left.pack_configure(fill="x", expand=True)

            # Right: time range (aligned right)
            if time_str:
                lbl_right = tk.Label(row, text=time_str, bg=bg_color, fg=fg_color,
                                     font=("Segoe UI", label_size - 1),
                                     anchor="e", padx=3, pady=0)
                lbl_right.pack(side="right")
                lbl_right.bind("<Button-1>",
                               lambda e, d=cell_date, c=courses_today: self._on_day_click(d, c))

            # Bind click on entire row and left label
            if self._on_day_click:
                row.bind("<Button-1>",
                         lambda e, d=cell_date, c=courses_today: self._on_day_click(d, c))
                lbl_left.bind("<Button-1>",
                              lambda e, d=cell_date, c=courses_today: self._on_day_click(d, c))

        if len(courses_today) > 3:
            ctk.CTkLabel(cell, text=f"+{len(courses_today) - 3}",
                         font=ctk.CTkFont(size=label_size),
                         text_color="gray").pack(anchor="w", padx=4)

        if self._on_day_click and courses_today:
            cell.bind("<Button-1>",
                      lambda e, d=cell_date, c=courses_today: self._on_day_click(d, c))
            lbl_num.bind("<Button-1>",
                         lambda e, d=cell_date, c=courses_today: self._on_day_click(d, c))

        return cell

    # ── Highlight ─────────────────────────────────────────────────────────────

    def highlight_course(self, name: str | None, shift: str | None):
        """
        Highlights all days belonging to the given course+shift with a glowing border.
        All other cells remain visually unchanged.
        Pass None to clear the highlight.
        """
        self._highlight_name = name
        self._highlight_shift = shift
        self._apply_highlight()

    def _apply_highlight(self):
        name = self._highlight_name
        shift = self._highlight_shift

        for cell_date, cell in self._cell_map.items():
            courses_today = self._last_days_by_date.get(cell_date, [])
            is_weekend = cell_date.weekday() >= 5
            is_today = (cell_date == date.today())

            # Base background color (unchanged from normal render)
            if is_today:
                base_bg = "#2E86C1"
            elif is_weekend:
                base_bg = "#F2F3F4"
            else:
                base_bg = "#FFFFFF"

            is_match = (name is not None and any(
                c.get("name") == name and c.get("shift") == shift
                for c in courses_today))

            if is_match:
                # Matching day — bright yellow border only, bg unchanged
                cell.configure(fg_color=base_bg, border_width=3, border_color="#F4D03F")
            else:
                # All other cells — normal appearance, no border
                cell.configure(fg_color=base_bg, border_width=0)
