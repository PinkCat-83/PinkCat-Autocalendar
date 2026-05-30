"""
calendar_logic_mixin.py
Mixin for MainWindow that owns calendar-related logic:
  - Course CRUD (add, edit, delete, find)
  - Calendar generation and month refresh
  - Month/year navigation
  - Day-detail popup
  - Course selection highlight

Lives in gui/calendar_logic_mixin.py.
"""

from collections import defaultdict
from datetime import date
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from gui.dialogs.course_dialog import CourseDialog
from src.calendar_gen import generate_calendar
from src.holidays import load_holidays
from src.export import load_json
import src.language as lang
import src.catalog as catalog

BASE_DIR      = Path(__file__).parent.parent.parent
DATA_DIR      = BASE_DIR / "data"
TRAINING_ACTIONS_JSON  = DATA_DIR / "training_actions.json"
HOLIDAYS_JSON = DATA_DIR / "holidays.json"

MONTH_KEYS = [
    "month_january","month_february","month_march","month_april",
    "month_may","month_june","month_july","month_august",
    "month_september","month_october","month_november","month_december",
]


def _translate_shift(shift: str) -> str:
    key_map = {"Morning": "shift_morning",
               "Afternoon": "shift_afternoon",
               "Other": "shift_other"}
    return lang.get(key_map.get(shift, "shift_morning"))


class CalendarLogicMixin:
    """
    Mixin that provides calendar generation, month refresh, navigation,
    course CRUD, and the day-detail popup.

    Expects the host class to expose:
        self._layout              – layout dict from detect_layout()
        self._year / self._month  – currently displayed period (int)
        self._actions             – list[dict], the loaded course data
        self._holidays            – set[date]
        self._generated_calendar  – dict produced by generate_calendar()
        self._color_manager       – ColorManager instance
        self._calendar_view       – CalendarView widget
        self._training_panel       – TrainingPanel widget
        self._status_bar          – CTkLabel at the bottom
        self._lbl_month           – CTkLabel showing the month name
        self._lbl_year            – CTkLabel showing the year
        self._save_actions()      – persists self._actions to disk
    """

    # ── Calendar generation ───────────────────────────────────────────────────

    def _regenerate_and_refresh(self):
        relevant_years = {str(self._year), str(self._year - 1)}
        actions_relevant = [
            c for c in self._actions
            if c.get("start_date", "")[:4] in relevant_years
        ]

        holidays_combined: set[date] = (
            load_holidays(HOLIDAYS_JSON, self._year) |
            load_holidays(HOLIDAYS_JSON, self._year - 1)
        )
        self._holidays = holidays_combined

        self._color_manager.pre_assign(self._actions)
        self._generated_calendar = generate_calendar(actions_relevant,
                                                     holidays_combined)
        self._refresh_month()

    def _refresh_month(self):
        self._lbl_month.configure(text=lang.get(MONTH_KEYS[self._month - 1]))
        self._lbl_year.configure(text=str(self._year))

        days_by_date: dict[date, list[dict]] = defaultdict(list)
        actions_month: dict[str, dict] = {}
        actions_year:  dict[str, dict] = {}

        # Build short_name lookup from catalog: course name → short_name
        _short_names: dict[str, str] = {
            c.get("name", ""): c.get("short_name", "")
            for c in catalog.load_catalog()
        }

        # Build confirmed lookup from self._actions (source of truth): id → bool
        _confirmed: dict[str, bool] = {
            c.get("id", ""): not c.get("pending", False)
            for c in self._actions
        }

        # Build custom color lookup: id → (bg_color, text_color)
        _custom_colors: dict[str, tuple[str, str]] = {
            c.get("id", ""): (c.get("bg_color", ""), c.get("text_color", ""))
            for c in self._actions
            if c.get("bg_color")
        }

        for course in self._generated_calendar.get("courses", []):
            # Use id as the unique key; fall back to name+shift for old data
            course_id = course.get("id") or f"{course['name']}_{course['shift']}"
            if course_id not in actions_year:
                _cbg, _ctxt = _custom_colors.get(course.get("id", ""), ("", ""))
                actions_year[course_id] = {
                    "id":          course.get("id", ""),
                    "name":        course["name"],
                    "short_name":  _short_names.get(course["name"], ""),
                    "shift":       course["shift"],
                    "pending":     not _confirmed.get(course.get("id", ""), True),
                    "location":    course["location"],
                    "company":     course.get("company", ""),
                    "start_time":  course.get("start_time"),
                    "end_time":    course.get("end_time"),
                    "total_hours": course["total_hours"],
                    "start_date":  str(course["start_date"]),
                    "end_date":    str(course["end_date"]),
                    "bg_color":    _cbg,
                    "text_color":  _ctxt,
                }
            for day in course.get("days", []):
                try:
                    raw = day["date"]
                    d = raw if isinstance(raw, date) else date.fromisoformat(str(raw))
                except (KeyError, ValueError):
                    continue
                if d.year == self._year and d.month == self._month:
                    _dbg, _dtxt = _custom_colors.get(course.get("id", ""), ("", ""))
                    days_by_date[d].append({
                        "id":         course.get("id", ""),
                        "name":       course["name"],
                        "short_name": _short_names.get(course["name"], ""),
                        "shift":      course["shift"],
                        "pending":    not _confirmed.get(course.get("id", ""), True),
                        "hours":      day["hours"],
                        "location":   day["location"],
                        "company":    course.get("company", ""),
                        "start_time": course.get("start_time"),
                        "end_time":   course.get("end_time"),
                        "bg_color":   _dbg,
                        "text_color": _dtxt,
                    })
                    if course_id not in actions_month:
                        actions_month[course_id] = actions_year[course_id]

        try:
            hdata = load_json(HOLIDAYS_JSON)
            holiday_map: dict[date, str] = {
                date.fromisoformat(e["date"]): e.get("name", "")
                for e in hdata.get(str(self._year), [])
                if e.get("date", "").startswith(str(self._year))
            }
        except Exception:
            holiday_map = {}

        self._calendar_view.show(self._year, self._month,
                                 days_by_date, holiday_map)
        self._training_panel.update(list(actions_month.values()),
                                   list(actions_year.values()))

        conflicts = self._generated_calendar.get("conflicts", [])
        total_s   = sum(len(v) for v in days_by_date.values())
        month_n   = lang.get(MONTH_KEYS[self._month - 1])
        status = (f"{len(actions_month)} {lang.get('status_active_courses')} {month_n}"
                  f"  •  {total_s} {lang.get('status_sessions')}")
        if conflicts:
            status += f"  ⚠ {len(conflicts)} {lang.get('status_conflicts')}"
        self._status_bar.configure(text=status)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _prev_month(self):
        if self._month == 1:
            self._month = 12; self._year -= 1; self._regenerate_and_refresh()
        else:
            self._month -= 1; self._refresh_month()

    def _next_month(self):
        if self._month == 12:
            self._month = 1; self._year += 1; self._regenerate_and_refresh()
        else:
            self._month += 1; self._refresh_month()

    def _prev_year(self):
        self._year -= 1; self._regenerate_and_refresh()

    def _next_year(self):
        self._year += 1; self._regenerate_and_refresh()

    def _go_to_today(self):
        today = date.today()
        changed = today.year != self._year
        self._year, self._month = today.year, today.month
        if changed:
            self._regenerate_and_refresh()
        else:
            self._refresh_month()

    # ── Course CRUD ───────────────────────────────────────────────────────────

    def _add_action(self):
        dlg = CourseDialog(self)
        if dlg.result:
            # Assign a new unique id to the new course
            existing_ids = {c.get("id", "") for c in self._actions}
            n = 1
            while f"course_{n:03d}" in existing_ids:
                n += 1
            dlg.result["id"] = f"course_{n:03d}"
            self._actions.append(dlg.result)
            self._save_actions()
            self._regenerate_and_refresh()

    def _edit_action(self, action: dict):
        """action is a summary dict from the sidebar; look up the full object."""
        full = self._find_action(action)
        if not full:
            messagebox.showerror(lang.get("error_title"),
                                 lang.get("error_action_not_found"))
            return
        dlg = CourseDialog(self, full)
        if dlg.result:
            # Preserve the original id
            dlg.result["id"] = full.get("id", "")
            idx = next((i for i, c in enumerate(self._actions) if c is full), None)
            if idx is not None:
                self._actions[idx] = dlg.result
                self._save_actions()
                self._regenerate_and_refresh()

    def _delete_action(self, action: dict):
        name = action.get("name", "")
        if not messagebox.askyesno(lang.get("confirm_delete_title"),
                                   lang.get("confirm_delete_msg", name=name)):
            return
        full = self._find_action(action)
        if full:
            idx = next((i for i, c in enumerate(self._actions) if c is full), None)
            if idx is not None:
                self._actions.pop(idx)
                self._save_actions()
                self._regenerate_and_refresh()

    def _find_action(self, action: dict) -> dict | None:
        """
        Find the full course object in self._actions.
        Matches by id when available; falls back to name+shift+start_date
        so two courses with the same name and shift (different months) are
        never confused.
        """
        pid = action.get("id", "")
        if pid:
            match = next((c for c in self._actions if c.get("id") == pid), None)
            if match:
                return match

        # Fallback: name + shift + start_date
        n  = action.get("name", "")
        s  = action.get("shift", "")
        sd = action.get("start_date", "")
        return next(
            (c for c in self._actions
             if c.get("name") == n
             and c.get("shift") == s
             and c.get("start_date", "") == sd),
            None,
        )

    def _on_course_select(self, name: str, shift: str):
        self._calendar_view.highlight_course(name, shift)

    # ── Day detail popup ──────────────────────────────────────────────────────

    def _on_day_click(self, day: date, courses: list[dict]):
        """Show a popup with details of every course on *day*."""
        weekday_keys = [
            "popup_day_monday", "popup_day_tuesday", "popup_day_wednesday",
            "popup_day_thursday", "popup_day_friday",
            "popup_day_saturday", "popup_day_sunday",
        ]
        day_name   = lang.get(weekday_keys[day.weekday()])
        month_name = lang.get(MONTH_KEYS[day.month - 1])
        date_str   = f"{day_name}, {day.day} {month_name} {day.year}"

        popup = ctk.CTkToplevel(self)
        popup.title(date_str)
        popup.resizable(False, False)
        popup.grab_set()
        popup.update_idletasks()
        w, h = 420, 320
        x = self.winfo_rootx() + (self.winfo_width()  - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        popup.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkLabel(
            popup, text=date_str,
            font=ctk.CTkFont(size=self._layout["nav_font_size"], weight="bold"),
        ).pack(padx=16, pady=(16, 8))

        for course in courses:
            # Use bg_color_for so color resolves by id, not name
            card_bg = self._color_manager.bg_color_for(course)
            card = ctk.CTkFrame(popup, fg_color=card_bg, corner_radius=8)
            card.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(
                card, text=course.get("name", ""),
                font=ctk.CTkFont(size=self._layout["card_font_size"], weight="bold"),
                text_color="#111111", anchor="w",
            ).pack(anchor="w", padx=10, pady=(6, 2))
            info = (f"{_translate_shift(course.get('shift', ''))}"
                    f"  •  {course.get('location', '')}"
                    f"  •  {course.get('hours', '')}h")
            ctk.CTkLabel(
                card, text=info,
                font=ctk.CTkFont(size=self._layout["card_detail_font_size"]),
                text_color="#333333", anchor="w",
            ).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkButton(
            popup, text=lang.get("popup_close"),
            command=popup.destroy, width=100,
        ).pack(pady=12)
