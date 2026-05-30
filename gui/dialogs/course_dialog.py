"""
course_dialog.py
Modal dialog for adding or editing a scheduled course.
Layout: two columns side by side (course fields left, contacts right),
action buttons at the bottom. Fits comfortably without scrolling.

Company dropdown: when changed, updates the location dropdown with that
company's locations. The user can still type any custom location manually.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
import calendar
import tkinter as tk
from tkinter import ttk
import re
import webbrowser
import src.language as lang
import src.catalog as catalog
from gui.dialogs.contacts_widget import ContactsWidget
from gui.widgets.holidays_widget import HolidaysWidget

WEEKDAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_LABEL_KEYS = ["weekday_mon", "weekday_tue", "weekday_wed",
                      "weekday_thu", "weekday_fri", "weekday_sat", "weekday_sun"]


def _modality_labels() -> list[str]:
    """Return translated labels for all modalities, in order."""
    return [lang.get(f"modality_{m['key']}") for m in catalog.load_modalities()]


def _shifts() -> list[str]:
    return [lang.get("shift_morning"), lang.get("shift_afternoon"), lang.get("shift_other")]


def _center_on_parent(window, parent, w: int, h: int) -> None:
    """Positions *window* (w×h) centered over *parent*."""
    window.update_idletasks()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    x = px + (pw - w) // 2
    y = py + (ph - h) // 2
    window.geometry(f"{w}x{h}+{x}+{y}")


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


class DatePickerPopup(tk.Toplevel):
    """
    Lightweight calendar popup.
    Opens anchored below a given widget; closes when a date is picked or
    when the user clicks outside. Calls on_select(date_str) with ISO format.
    """

    def __init__(self, parent, anchor_widget: ctk.CTkEntry, on_select):
        super().__init__(parent)
        self.overrideredirect(True)   # no title bar
        self.attributes("-topmost", True)
        self._on_select = on_select

        # Parse current entry value or default to today
        raw = anchor_widget.get().strip()
        try:
            initial = date.fromisoformat(raw)
        except ValueError:
            initial = date.today()
        self._year = initial.year
        self._month = initial.month

        # Position below the anchor widget
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

        # ── Navigation header ─────────────────────────────────────────────────
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

        # ── Unified grid: day-of-week headers + day buttons ──────────────────
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



# ── Color picker dialog ────────────────────────────────────────────────────────

_WORD_PALETTE = [
    # Row 1 — whites / light grays
    ["#FFFFFF","#F2F2F2","#D9D9D9","#BFBFBF","#A6A6A6","#808080","#595959","#404040","#262626","#0D0D0D"],
    # Row 2 — light theme colors
    ["#FFF2CC","#FFE699","#FFD966","#FFC000","#FF9900","#FF6600","#FF0000","#CC0000","#990000","#660000"],
    ["#DEEAF1","#BDD7EE","#9DC3E6","#2E75B6","#1F4E79","#0070C0","#00B0F0","#00FFFF","#007272","#003366"],
    ["#E2EFDA","#C6E0B4","#A9D18E","#70AD47","#538135","#375623","#00FF00","#00CC00","#009900","#006600"],
    ["#FCE4D6","#F8CBAD","#F4B183","#ED7D31","#C55A11","#833C00","#FF00FF","#CC00CC","#990099","#660066"],
    ["#EAD1DC","#D4A5C7","#BE78B5","#9C27B0","#6A1B9A","#4A148C","#7B1FA2","#AB47BC","#CE93D8","#E1BEE7"],
    # Row 3 — standard pastel palette (current defaults)
    ["#F9A8D4","#A7D7A8","#A3B8E8","#FDE99A","#F4A9A8","#FDCBA0","#A8E4F0","#D4B8F0","#F0D4B8","#B8F0D4"],
    # Row 4 — dark / vivid
    ["#FF0000","#FF7F00","#FFFF00","#00FF00","#0000FF","#4B0082","#9400D3","#FF1493","#00CED1","#696969"],
]

_FLAT_PALETTE = [c for row in _WORD_PALETTE for c in row]


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    return 0.299 * r + 0.587 * g + 0.114 * b


class ColorPickerDialog(tk.Toplevel):
    """
    Word-style color picker.
    Shows a grid of color swatches. Returns (bg_color, text_color) or (None, None).
    """

    SWATCH = 22   # px per swatch
    GAP    = 2

    def __init__(self, parent, current_bg: str = "", current_text: str = ""):
        super().__init__(parent)
        self.title(lang.get("color_picker_title"))
        self.resizable(False, False)
        self.grab_set()
        self.attributes("-topmost", True)

        self.result_bg:   str | None = None
        self.result_text: str | None = None

        self._sel_bg   = current_bg   or "#FDE99A"
        self._sel_text = current_text or "#1C1C1C"

        self._build()
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        self.wait_window()

    def _build(self):
        S = self.SWATCH
        G = self.GAP

        outer = tk.Frame(self, bg="#2B2B2B", padx=12, pady=12)
        outer.pack(fill="both", expand=True)

        # ── Background color section ──────────────────────────────────────────
        tk.Label(outer, text=lang.get("color_bg_label"),
                 bg="#2B2B2B", fg="white",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

        bg_grid = tk.Frame(outer, bg="#2B2B2B")
        bg_grid.pack(anchor="w")
        self._bg_buttons: dict[str, tk.Frame] = {}
        for r, row in enumerate(_WORD_PALETTE):
            for c, color in enumerate(row):
                f = tk.Frame(bg_grid, width=S, height=S, bg=color,
                             highlightthickness=1,
                             highlightbackground="#888888",
                             cursor="hand2")
                f.grid(row=r, column=c, padx=G//2, pady=G//2)
                f.bind("<Button-1>", lambda e, col=color: self._pick_bg(col))
                self._bg_buttons[color] = f

        # Preview + selected bg indicator
        self._lbl_bg_preview = tk.Label(
            outer, text=f"  {lang.get('color_selected')}: {self._sel_bg}  ",
            bg=self._sel_bg,
            fg="#000000" if _luminance(self._sel_bg) > 0.5 else "#FFFFFF",
            font=("Segoe UI", 9), relief="solid", bd=1)
        self._lbl_bg_preview.pack(anchor="w", pady=(6, 0))

        # ── Text color section ────────────────────────────────────────────────
        tk.Label(outer, text=lang.get("color_text_label"),
                 bg="#2B2B2B", fg="white",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(14, 4))

        text_grid = tk.Frame(outer, bg="#2B2B2B")
        text_grid.pack(anchor="w")
        self._text_buttons: dict[str, tk.Frame] = {}
        # For text color only show neutrals + darks (first 2 rows)
        text_palette = _WORD_PALETTE[0:1] + [
            ["#000000","#1C1C1C","#333333","#4D4D4D","#666666","#808080",
             "#CC0000","#0070C0","#375623","#4A148C"]
        ]
        for r, row in enumerate(text_palette):
            for c, color in enumerate(row):
                f = tk.Frame(text_grid, width=S, height=S, bg=color,
                             highlightthickness=1,
                             highlightbackground="#888888",
                             cursor="hand2")
                f.grid(row=r, column=c, padx=G//2, pady=G//2)
                f.bind("<Button-1>", lambda e, col=color: self._pick_text(col))
                self._text_buttons[color] = f

        self._lbl_text_preview = tk.Label(
            outer, text=f"  {lang.get('color_selected')}: {self._sel_text}  ",
            bg=self._sel_bg,
            fg=self._sel_text,
            font=("Segoe UI", 9, "bold"), relief="solid", bd=1)
        self._lbl_text_preview.pack(anchor="w", pady=(6, 0))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_bar = tk.Frame(outer, bg="#2B2B2B")
        btn_bar.pack(fill="x", pady=(14, 0))

        tk.Button(btn_bar, text=lang.get("dialog_cancel"),
                  command=self.destroy,
                  bg="#555555", fg="white", relief="flat",
                  padx=12, pady=4, cursor="hand2").pack(side="right", padx=(4, 0))
        tk.Button(btn_bar, text=lang.get("dialog_save"),
                  command=self._confirm,
                  bg="#2E86C1", fg="white", relief="flat",
                  padx=12, pady=4, cursor="hand2").pack(side="right")

        # Highlight current selections
        self._highlight_bg(self._sel_bg)
        self._highlight_text(self._sel_text)

    def _pick_bg(self, color: str):
        self._sel_bg = color
        lum = _luminance(color)
        self._lbl_bg_preview.configure(
            bg=color, text=f"  {lang.get('color_selected')}: {color}  ",
            fg="#000000" if lum > 0.5 else "#FFFFFF")
        self._lbl_text_preview.configure(bg=color)
        self._highlight_bg(color)

    def _pick_text(self, color: str):
        self._sel_text = color
        self._lbl_text_preview.configure(
            fg=color, text=f"  {lang.get('color_selected')}: {color}  ")
        self._highlight_text(color)

    def _highlight_bg(self, color: str):
        for c, f in self._bg_buttons.items():
            f.configure(highlightthickness=2 if c == color else 1,
                        highlightbackground="#F4D03F" if c == color else "#888888")

    def _highlight_text(self, color: str):
        for c, f in self._text_buttons.items():
            f.configure(highlightthickness=2 if c == color else 1,
                        highlightbackground="#F4D03F" if c == color else "#888888")

    def _confirm(self):
        self.result_bg   = self._sel_bg
        self.result_text = self._sel_text
        self.destroy()


class CourseDialog(ctk.CTkToplevel):

    def __init__(self, parent, course: dict | None = None):
        super().__init__(parent)
        self.title(lang.get("dialog_new_title") if course is None
                   else lang.get("dialog_edit_title"))
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        _center_on_parent(self, parent, 1060, 620)

        self.result: dict | None = None
        self._original = course or {}

        # Load reference data
        self._catalog_items  = catalog.load_catalog()
        self._catalog_map    = {c["name"]: c for c in self._catalog_items}
        self._catalog_names  = [""] + [c["name"] for c in self._catalog_items]
        self._company_names  = [""] + catalog.company_names()

        # Modalities: keep parallel lists of keys and translated labels
        self._modality_items  = catalog.load_modalities()   # [{"key": ..., ...}]
        self._modality_keys   = [m["key"] for m in self._modality_items]

        # Build company → locations map for dynamic filtering
        # Each location is {"name": str, "maps_url": str}
        self._company_locations: dict[str, list[dict]] = {}
        for c in catalog.load_companies():
            locs = c.get("locations", [])
            self._company_locations[c["name"]] = [
                l if isinstance(l, dict) else {"name": l, "maps_url": ""}
                for l in locs
            ]

        self._custom_bg   = (course or {}).get("bg_color", "")
        self._custom_text = (course or {}).get("text_color", "")

        self._build_ui()
        if course:
            self._populate(course)

        # Trace location changes (including manual typing)
        self.cmb_location._entry.bind(
            "<FocusOut>",
            lambda e: self._on_location_select(self.cmb_location.get().strip()))

        self.after(50, self.cmb_name.focus_set)
        self.wait_window()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Bottom: action buttons (packed first so they're pinned) ──────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=16, pady=12)
        ctk.CTkButton(btn_frame, text=lang.get("dialog_save"),
                      command=self._save, width=180, height=46).pack(side="right", padx=6)
        ctk.CTkButton(btn_frame, text=lang.get("dialog_cancel"),
                      command=self.destroy, width=150, height=46,
                      fg_color="#6B7280", hover_color="#4B5563",
                      text_color="#FFFFFF").pack(side="right", padx=(0, 4))

        # ── Main body: two columns ────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(14, 0))
        body.columnconfigure(0, weight=0, minsize=340)
        body.columnconfigure(1, weight=1)

        # ── Left column: course fields ────────────────────────────────────────
        left = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        ctk.CTkLabel(left, text=lang.get("dialog_section_details"),
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        # Color picker button — shows current bg color as swatch
        self._color_frame = ctk.CTkFrame(left, fg_color="transparent")
        self._color_frame.grid(row=0, column=1, sticky="e", pady=(0, 6))
        self._btn_color = tk.Button(
            self._color_frame, text="  🎨  ", relief="flat", cursor="hand2",
            font=("Segoe UI", 10), bg="#FDE99A", fg="#1C1C1C",
            activebackground="#FDE99A",
            command=self._open_color_picker)
        self._btn_color.pack(side="left")
        self._lbl_color_hint = tk.Label(
            self._color_frame, text=lang.get("color_picker_hint"),
            font=("Segoe UI", 8), bg="SystemButtonFace", fg="#888888")
        self._lbl_color_hint.pack(side="left", padx=(4, 0))

        def field(label_key, row, widget):
            ctk.CTkLabel(left, text=lang.get(label_key),
                         anchor="w", width=130).grid(
                row=row, column=0, sticky="w", pady=3)
            widget.grid(row=row, column=1, sticky="ew", pady=3, padx=(4, 0))
            left.columnconfigure(1, weight=1)

        self.cmb_name = ctk.CTkComboBox(left, values=self._catalog_names,
                                         width=220, command=self._on_catalog_select)
        field("dialog_name", 1, self.cmb_name)

        # Company dropdown — triggers location update
        self.cmb_company = ctk.CTkComboBox(
            left, values=self._company_names, width=220,
            command=self._on_company_select)
        field("dialog_company", 2, self.cmb_company)

        # Location dropdown — populated dynamically based on selected company
        self.cmb_location = ctk.CTkComboBox(left, values=[""], width=220,
                                             command=self._on_location_select)
        field("dialog_location", 3, self.cmb_location)

        # Maps URL — auto-filled when location is selected from dropdown
        maps_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.ent_maps_url = ctk.CTkEntry(maps_frame, width=170)
        self.ent_maps_url.pack(side="left", fill="x", expand=True)
        self._btn_maps = ctk.CTkButton(
            maps_frame, text="🗺", width=32, height=28,
            command=self._open_maps)
        self._btn_maps.pack(side="left", padx=(4, 0))
        field("dialog_maps_url", 4, maps_frame)

        self.cmb_shift = ctk.CTkComboBox(left, values=_shifts(), width=140)
        self.cmb_shift.set(lang.get("shift_morning"))
        field("dialog_shift", 5, self.cmb_shift)

        # Modality dropdown — value stored as key, displayed as translated label
        self.cmb_modality = ctk.CTkComboBox(
            left, values=_modality_labels(), width=200)
        if _modality_labels():
            self.cmb_modality.set(_modality_labels()[0])
        field("dialog_modality", 6, self.cmb_modality)

        self.ent_start_time = ctk.CTkEntry(left, width=90)
        field("dialog_start_time", 7, self.ent_start_time)

        self.ent_end_time = ctk.CTkEntry(left, width=90)
        field("dialog_end_time", 8, self.ent_end_time)

        self.ent_total_hours = ctk.CTkEntry(left, width=90)
        field("dialog_total_hours", 9, self.ent_total_hours)

        # Start date — entry + calendar picker button
        date_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.ent_start_date = ctk.CTkEntry(date_frame, width=100)
        self.ent_start_date.pack(side="left")
        ctk.CTkButton(
            date_frame, text="📅", width=32, height=28,
            command=self._open_date_picker
        ).pack(side="left", padx=(4, 0))
        field("dialog_start_date", 10, date_frame)

        # Confirmed checkbox — row 11, right after start date
        self._pending_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            left,
            text=lang.get("action_pending_confirmation"),
            variable=self._pending_var,
        ).grid(row=11, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # Teaching days
        ctk.CTkLabel(left, text=lang.get("dialog_teaching_days"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     anchor="w").grid(row=12, column=0, columnspan=2, sticky="w", pady=(10, 2))

        days_frame = ctk.CTkFrame(left, fg_color="transparent")
        days_frame.grid(row=13, column=0, columnspan=2, sticky="w")
        self._day_vars: dict[str, ctk.BooleanVar] = {}
        for i, (day_key, label_key) in enumerate(zip(WEEKDAY_KEYS, WEEKDAY_LABEL_KEYS)):
            var = ctk.BooleanVar(value=(day_key not in ("saturday", "sunday")))
            self._day_vars[day_key] = var
            ctk.CTkCheckBox(days_frame, text=lang.get(label_key),
                            variable=var, width=54).grid(row=0, column=i, padx=2)

        # Specific holidays — opens a separate dialog
        self._specific_holidays: list[str] = []
        ctk.CTkButton(left, text=lang.get("dialog_specific_holidays"),
                      command=self._open_holidays_dialog,
                      width=220, height=30
                      ).grid(row=14, column=0, columnspan=2, sticky="w", pady=(22, 2))


        # ── Right column: contacts ────────────────────────────────────────────
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text=lang.get("contact_section"),
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(anchor="w", pady=(0, 6))

        self._contacts = ContactsWidget(right)
        self._contacts.pack(fill="both", expand=True)



    def _open_color_picker(self):
        dlg = ColorPickerDialog(
            self,
            current_bg=self._custom_bg,
            current_text=self._custom_text)
        if dlg.result_bg is not None:
            self._custom_bg   = dlg.result_bg
            self._custom_text = dlg.result_text
            self._btn_color.configure(
                bg=self._custom_bg, activebackground=self._custom_bg,
                fg=self._custom_text)

    def _open_date_picker(self):
        def on_select(date_str: str):
            self.ent_start_date.delete(0, "end")
            self.ent_start_date.insert(0, date_str)
        DatePickerPopup(self, self.ent_start_date, on_select)

    def _on_catalog_select(self, name: str):
        item = self._catalog_map.get(name)
        if item and not self.ent_total_hours.get().strip():
            self.ent_total_hours.delete(0, "end")
            self.ent_total_hours.insert(0, str(item.get("total_hours", "")))

    def _on_company_select(self, company_name: str):
        """Update location dropdown with the selected company's locations."""
        locs = self._company_locations.get(company_name, [])
        names = [l["name"] for l in locs]
        options = [""] + names if names else [""]
        self.cmb_location.configure(values=options)
        if len(names) == 1:
            self.cmb_location.set(names[0])
            self._on_location_select(names[0])
        else:
            self.cmb_location.set("")
            self._on_location_select("")

    def _on_location_select(self, location_name: str):
        """Auto-fill maps URL when a known location is selected."""
        company_name = self.cmb_company.get().strip()
        locs = self._company_locations.get(company_name, [])
        known = {l["name"]: l.get("maps_url", "") for l in locs}

        if location_name in known:
            url = known[location_name]
            self.ent_maps_url.delete(0, "end")
            self.ent_maps_url.insert(0, url)
            # White background — known location
            self.ent_maps_url.configure(fg_color=["#F9F9F9", "#343638"])
        else:
            # Red tint — custom / unknown location
            self.ent_maps_url.configure(fg_color="#FADBD8")

    def _open_maps(self):
        """Open the maps URL in the default browser."""
        url = self.ent_maps_url.get().strip()
        if url:
            import webbrowser
            webbrowser.open(url)

    def _open_holidays_dialog(self):
        dlg = _HolidaysDialog(self, self._specific_holidays)
        if dlg.result is not None:
            self._specific_holidays = dlg.result
            self._update_holidays_label()

    def _update_holidays_label(self):
        pass  # label removed; count is visible inside the holidays dialog

    def _populate(self, course: dict):
        self.cmb_name.set(course.get("name", ""))
        # Note: _on_catalog_select is NOT called here — all fields are
        # populated explicitly from the saved course data below.

        company = course.get("company", "")
        self.cmb_company.set(company)
        # Populate location options for this company first, then set saved value
        self._on_company_select(company)
        saved_location = course.get("location", "")
        saved_maps_url = course.get("maps_url", "")
        # Ensure saved location is in the dropdown even if not in company list
        current_values = list(self.cmb_location.cget("values"))
        if saved_location and saved_location not in current_values:
            current_values.append(saved_location)
            self.cmb_location.configure(values=current_values)
        self.cmb_location.set(saved_location)
        # Restore maps URL; check if location is known to set bg correctly
        self.ent_maps_url.delete(0, "end")
        self.ent_maps_url.insert(0, saved_maps_url)
        locs = self._company_locations.get(company, [])
        known_names = [l["name"] for l in locs]
        if saved_location and saved_location not in known_names:
            self.ent_maps_url.configure(fg_color="#FADBD8")

        shift_map = {
            "Morning":   lang.get("shift_morning"),
            "Afternoon": lang.get("shift_afternoon"),
            "Other":     lang.get("shift_other"),
        }
        self.cmb_shift.set(shift_map.get(course.get("shift", "Morning"),
                                         lang.get("shift_morning")))

        # Modality: stored as key, displayed as translated label
        saved_mod_key = course.get("modality", "")
        if saved_mod_key in self._modality_keys:
            idx = self._modality_keys.index(saved_mod_key)
            self.cmb_modality.set(_modality_labels()[idx])
        elif _modality_labels():
            self.cmb_modality.set(_modality_labels()[0])
        self.ent_start_time.insert(0, str(course.get("start_time", "")))
        self.ent_end_time.insert(0, str(course.get("end_time", "")))
        self.ent_total_hours.insert(0, str(course.get("total_hours", "")))
        self.ent_start_date.insert(0, course.get("start_date", ""))
        days = course.get("teaching_days", {})
        for day, var in self._day_vars.items():
            var.set(days.get(day, False))
        self._specific_holidays = list(course.get("specific_holidays", []))
        self._update_holidays_label()
        self._pending_var.set(course.get("pending", False))
        if course.get("bg_color"):
            self._custom_bg   = course["bg_color"]
            self._custom_text = course.get("text_color", "#1C1C1C")
            self._btn_color.configure(
                bg=self._custom_bg, activebackground=self._custom_bg,
                fg=self._custom_text)
        for contact in course.get("contacts", []):
            self._contacts._add_row(data=contact)

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        errors = []

        name = self.cmb_name.get().strip()
        if not name:
            errors.append(lang.get("error_name_required"))

        company  = self.cmb_company.get().strip()
        location = self.cmb_location.get().strip()

        shift_reverse = {
            lang.get("shift_morning"):   "Morning",
            lang.get("shift_afternoon"): "Afternoon",
            lang.get("shift_other"):     "Other",
        }
        shift = shift_reverse.get(self.cmb_shift.get(), "Morning")

        # Modality: resolve displayed label back to its key
        mod_labels = _modality_labels()
        mod_label_sel = self.cmb_modality.get()
        if mod_label_sel in mod_labels:
            modality = self._modality_keys[mod_labels.index(mod_label_sel)]
        else:
            modality = self._modality_keys[0] if self._modality_keys else ""

        try:
            start_time = float(self.ent_start_time.get().replace(",", "."))
        except ValueError:
            errors.append(lang.get("error_start_time"))
            start_time = 0.0

        try:
            end_time = float(self.ent_end_time.get().replace(",", "."))
        except ValueError:
            errors.append(lang.get("error_end_time"))
            end_time = 0.0

        daily_hours = round(end_time - start_time, 4) if end_time > start_time else 0
        if daily_hours <= 0 and not errors:
            errors.append(lang.get("error_time_order"))

        try:
            total_hours = float(self.ent_total_hours.get().replace(",", "."))
            if total_hours <= 0:
                raise ValueError
        except ValueError:
            errors.append(lang.get("error_total_hours"))
            total_hours = 0.0

        start_date_str = _parse_date(self.ent_start_date.get())
        if start_date_str is None:
            errors.append(lang.get("error_start_date"))

        teaching_days = {day: self._day_vars[day].get() for day in WEEKDAY_KEYS}
        if not any(teaching_days.values()):
            errors.append(lang.get("error_no_teaching_days"))

        specific_holidays = self._specific_holidays

        if errors:
            messagebox.showerror(lang.get("error_form_title"),
                                 "\n".join(f"• {e}" for e in errors))
            return

        maps_url = self.ent_maps_url.get().strip()

        self.result = {
            "name":              name,
            "location":          location,
            "maps_url":          maps_url,
            "company":           company,
            "shift":             shift,
            "modality":          modality,
            "pending":           self._pending_var.get(),
            "start_time":        start_time,
            "end_time":          end_time,
            "daily_hours":       daily_hours,
            "total_hours":       total_hours,
            "start_date":        start_date_str,
            "teaching_days":     teaching_days,
            "specific_holidays": specific_holidays,
            "contacts":          self._contacts.get_contacts(),
            "bg_color":          self._custom_bg,
            "text_color":        self._custom_text,
            "rate_per_hour":     self._original.get("rate_per_hour", 0.0),
            "withholding_pct":   self._original.get("withholding_pct", 0.0),
        }
        self.destroy()


# ── Specific holidays dialog ──────────────────────────────────────────────────

class _HolidaysDialog(ctk.CTkToplevel):
    """
    Modal dialog for editing course-specific holidays.
    Opens from CourseDialog when the user clicks the "Specific holidays" button.
    """

    def __init__(self, parent, holidays: list[str]):
        super().__init__(parent)
        self.title(lang.get("dialog_specific_holidays"))
        self.resizable(False, False)
        self.grab_set()
        self.result: list[str] | None = None

        # Center over parent
        self.update_idletasks()
        w, h = 420, 460
        x = parent.winfo_rootx() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(side="bottom", fill="x", padx=16, pady=12)
        ctk.CTkButton(btn_bar, text=lang.get("dialog_save"),
                      command=self._save, width=110).pack(side="right", padx=4)
        ctk.CTkButton(btn_bar, text=lang.get("dialog_cancel"),
                      command=self.destroy, width=90,
                      fg_color="gray").pack(side="right")

        # Widget
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(14, 0))

        self._widget = HolidaysWidget(body, holidays=holidays, scroll_height=340)
        self._widget.pack(fill="both", expand=True)

        self.wait_window()

    def _save(self):
        self.result = self._widget.get_holidays()
        self.destroy()
