"""
main_window.py
Main application window with tab navigation:
  Calendar | Courses | Companies | Locations | Holidays

Modular structure:
  gui/calendar_logic_mixin.py  — CRUD, refresh, navigation, day popup
  gui/management_tabs_mixin.py — Catalog, Companies, Locations, Holidays tabs
"""

from datetime import date
from pathlib import Path
from tkinter import messagebox

import webbrowser
from PIL import Image
import customtkinter as ctk

from gui.widgets.colors import ColorManager
from gui.calendar.calendar_view import CalendarView
from gui.calendar.training_panel import TrainingPanel
from gui.widgets.layout import detect_layout
from gui.core.calendar_logic_mixin import CalendarLogicMixin, MONTH_KEYS
from gui.core.management_tabs_mixin import ManagementTabsMixin
from src.holidays import load_holidays
from src.export import save_json, load_json
import src.language as lang

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
TRAINING_ACTIONS_JSON  = DATA_DIR / "training_actions.json"
HOLIDAYS_JSON = DATA_DIR / "holidays.json"

TAB_KEYS = ["tab_calendar","tab_courses","tab_companies","tab_holidays"]


class MainWindow(CalendarLogicMixin, ManagementTabsMixin, ctk.CTk):

    def __init__(self):
        super().__init__()

        available_langs = lang.load()
        self._layout = detect_layout()
        w = self._layout["window_width"]
        h = self._layout["window_height"]

        self.resizable(False, False)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._year  = date.today().year
        self._month = date.today().month
        self._actions: list[dict] = []
        self._generated_calendar: dict = {}
        self._color_manager = ColorManager()
        self._holidays: set[date] = set()
        self._available_langs = available_langs

        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")

        self._load_data()
        self._build_ui()
        self._update_title()
        self._regenerate_and_refresh()

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_data(self):
        if TRAINING_ACTIONS_JSON.exists():
            try:
                self._actions = load_json(TRAINING_ACTIONS_JSON)
            except Exception as e:
                messagebox.showwarning(lang.get("warning_title"),
                                       f"{lang.get('warning_actions_read')}\n{e}")
                self._actions = []
        else:
            self._actions = []
        self._color_manager.pre_assign(self._actions)
        self._holidays = load_holidays(HOLIDAYS_JSON, self._year)

    def _save_actions(self):
        try:
            save_json(self._actions, TRAINING_ACTIONS_JSON)
        except Exception as e:
            messagebox.showerror(lang.get("error_title"),
                                 f"{lang.get('error_actions_save')}\n{e}")

    def _update_title(self):
        self.title(f"{lang.get('app_title')}  [{self._layout['name']}]")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        L = self._layout
        top_h   = L["top_bar_height"]
        title_s = L["title_font_size"]
        nav_s   = L["nav_font_size"]

        # ── Top bar ───────────────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, height=top_h, corner_radius=0)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        self._lbl_app_title = ctk.CTkLabel(
            top_bar, text=f"📅 {lang.get('app_title')}",
            font=ctk.CTkFont(size=title_s, weight="bold"))
        self._lbl_app_title.pack(side="left", padx=20)

        self._btn_prev_year = ctk.CTkButton(
            top_bar, text=lang.get("nav_year_prev"), width=80, height=34,
            command=self._prev_year)
        self._btn_prev_year.pack(side="left", padx=4, pady=10)

        self._lbl_year = ctk.CTkLabel(
            top_bar, text=str(self._year),
            font=ctk.CTkFont(size=nav_s, weight="bold"), width=70)
        self._lbl_year.pack(side="left")

        self._btn_next_year = ctk.CTkButton(
            top_bar, text=lang.get("nav_year_next"), width=80, height=34,
            command=self._next_year)
        self._btn_next_year.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(top_bar, text="  |  ", text_color="gray").pack(side="left")

        ctk.CTkButton(top_bar, text="◀", width=40, height=34,
                      command=self._prev_month).pack(side="left", padx=2, pady=10)
        self._lbl_month = ctk.CTkLabel(
            top_bar, text=lang.get(MONTH_KEYS[self._month-1]),
            font=ctk.CTkFont(size=nav_s, weight="bold"), width=130)
        self._lbl_month.pack(side="left")
        ctk.CTkButton(top_bar, text="▶", width=40, height=34,
                      command=self._next_month).pack(side="left", padx=2, pady=10)

        self._btn_today = ctk.CTkButton(
            top_bar, text=lang.get("nav_today"), width=70, height=34,
            command=self._go_to_today)
        self._btn_today.pack(side="left", padx=10, pady=10)

        # Right side of top bar
        # ── Company logo (right of language selector) ─────────────────────────
        try:
            _logo_h = int(top_h * 0.72)          # ~37px on HD, ~46px on 2K
            _logo_w = int(_logo_h * 1384 / 1168) # preserve aspect ratio
            _img_path = BASE_DIR / "img" / "logo.png"
            _pil = Image.open(_img_path).resize((_logo_w, _logo_h), Image.LANCZOS)
            _ctk_img = ctk.CTkImage(light_image=_pil, size=(_logo_w, _logo_h))
            _logo_lbl = ctk.CTkLabel(top_bar, image=_ctk_img, text="",
                                     cursor="hand2")
            _logo_lbl.pack(side="right", padx=(8, 4))
            _logo_lbl.bind("<Button-1>",
                           lambda e: webbrowser.open("https://ayaxprofesor.es"))
        except Exception:
            pass  # logo missing or PIL unavailable — silently skip
        ctk.CTkLabel(top_bar, text=self._layout["name"],
                     font=ctk.CTkFont(size=10), text_color="gray"
                     ).pack(side="right", padx=(0,12))

        self._lang_var = ctk.StringVar(value=lang.current())
        ctk.CTkOptionMenu(
            top_bar, values=self._available_langs,
            variable=self._lang_var, width=110,
            command=self._change_language,
        ).pack(side="right", padx=12)


        # ── Tab bar ───────────────────────────────────────────────────────────
        # Classic tab look: colored shelf, tabs sit on top.
        # Active tab: white bg, no bottom border, bold text.
        # Inactive tabs: light gray bg, bottom shelf border visible, muted text.
        TAB_H    = 38
        SHELF_H  = 4
        SHELF_BG = "#2E86C1"   # blue shelf / active tab indicator

        # Shelf strip below tabs (always visible, gives "resting on" feel)
        shelf = ctk.CTkFrame(self, height=SHELF_H, corner_radius=0,
                             fg_color=SHELF_BG)
        shelf.pack(fill="x")

        # Tab row above the shelf
        tab_bar = ctk.CTkFrame(self, height=TAB_H, corner_radius=0,
                               fg_color="#DDE4ED")
        tab_bar.pack(fill="x", before=shelf)
        tab_bar.pack_propagate(False)

        self._tab_buttons: list[ctk.CTkButton] = []
        self._active_tab = 0

        for i, key in enumerate(TAB_KEYS):
            btn = ctk.CTkButton(
                tab_bar, text=lang.get(key),
                width=150, height=TAB_H, corner_radius=0,
                command=lambda idx=i: self._switch_tab(idx),
                fg_color="#DDE4ED",       # inactive: medium gray-blue
                hover_color="#C8D4E3",
                text_color="#445566",
                border_width=0,
                font=ctk.CTkFont(size=self._layout["card_font_size"]),
            )
            btn.pack(side="left")
            self._tab_buttons.append(btn)

        # ── Tab content frames ────────────────────────────────────────────────
        self._tab_frames: list[ctk.CTkFrame] = []
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        for _ in TAB_KEYS:
            f = ctk.CTkFrame(container, fg_color="transparent")
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._tab_frames.append(f)

        # ── Build each tab ────────────────────────────────────────────────────
        self._build_calendar_tab(self._tab_frames[0])
        self._build_catalog_tab(self._tab_frames[1])
        self._build_companies_tab(self._tab_frames[2])
        self._build_holidays_tab(self._tab_frames[3])

        self._switch_tab(0)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status_bar = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray")
        self._status_bar.pack(side="bottom", pady=4)

    # ── Tab: Calendar ─────────────────────────────────────────────────────────

    def _build_calendar_tab(self, parent):
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=8, pady=8)

        self._training_panel = TrainingPanel(
            body, color_manager=self._color_manager,
            layout=self._layout,
            on_add=self._add_action, on_edit=self._edit_action,
            on_delete=self._delete_action, on_select=self._on_course_select,
            on_goto=self._goto_course_start)
        self._training_panel.pack(side="right", fill="y", padx=(6,0))

        self._calendar_view = CalendarView(
            body, color_manager=self._color_manager,
            layout=self._layout, on_day_click=self._on_day_click,
            fg_color="transparent")
        self._calendar_view.pack(side="left", fill="both", expand=True)

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        for i, (frame, btn) in enumerate(
                zip(self._tab_frames, self._tab_buttons)):
            if i == idx:
                frame.lift()
                btn.configure(
                    fg_color="#FFFFFF",       # white — appears "raised" off the shelf
                    hover_color="#F0F4F8",
                    text_color="#1A3A5C",     # dark blue text
                    font=ctk.CTkFont(size=self._layout["card_font_size"],
                                     weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="#DDE4ED",       # recessed gray-blue
                    hover_color="#C8D4E3",
                    text_color="#445566",     # muted text
                    font=ctk.CTkFont(size=self._layout["card_font_size"],
                                     weight="normal"),
                )

    # ── Language ──────────────────────────────────────────────────────────────

    def _change_language(self, selected: str):
        lang.set_language(selected)
        self._update_title()
        self._lbl_app_title.configure(text=f"📅 {lang.get('app_title')}")
        self._btn_prev_year.configure(text=lang.get("nav_year_prev"))
        self._btn_next_year.configure(text=lang.get("nav_year_next"))
        self._btn_today.configure(text=lang.get("nav_today"))
        for i, key in enumerate(TAB_KEYS):
            self._tab_buttons[i].configure(text=lang.get(key))
        self._training_panel.refresh_language()
        self._catalog_table.refresh_language()
        self._companies_table.refresh_language()
        self._calendar_view.rebuild_header()
        self._refresh_month()  # updates _lbl_month and _lbl_year

    def _goto_course_start(self, year: int, month: int):
        """Navigates the calendar to the given year/month and switches to the calendar tab."""
        self._year  = year
        self._month = month
        self._switch_tab(0)
        self._regenerate_and_refresh()

    # ── end of MainWindow ─────────────────────────────────────────────────────
