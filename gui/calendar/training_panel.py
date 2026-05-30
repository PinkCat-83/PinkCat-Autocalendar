"""
training_panel.py
Sidebar panel with two sections:
  - "Courses this month" — courses active in the visible month
  - "Courses this year"  — all courses for the current year
Selecting a card triggers a callback to highlight that course in the calendar.
Selected card has a distinct visual state (bright border + tinted background).
"""

import customtkinter as ctk
from gui.widgets.colors import ColorManager
import src.language as lang


def _month_abbrev(date_str: str) -> str:
    """Returns a short month name from a YYYY-MM-DD date string."""
    _MONTH_KEYS = [
        "month_january","month_february","month_march","month_april",
        "month_may","month_june","month_july","month_august",
        "month_september","month_october","month_november","month_december",
    ]
    try:
        month_idx = int(date_str[5:7]) - 1
        return lang.get(_MONTH_KEYS[month_idx])[:3]
    except Exception:
        return ""


def _translate_shift(shift: str) -> str:
    key_map = {"Morning": "shift_morning", "Afternoon": "shift_afternoon", "Other": "shift_other"}
    return lang.get(key_map.get(shift, "shift_morning"))


def _darken(hex_color: str, factor: float = 0.72) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = (int(c * factor) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


_BTN_EDIT_ACTIVE   = "#2E86C1"
_BTN_DELETE_ACTIVE = "#C0392B"
_BTN_DISABLED_FG   = "#BDBDBD"
_BTN_DISABLED_TEXT = "#F0F0F0"

_SEL_BORDER_COLOR = "#1A3A5C"
_SEL_BORDER_WIDTH = 4
_SEL_STRIPE_COLOR = "#1A3A5C"
_SEL_STRIPE_W     = 5


def _card_key(course: dict) -> str:
    """
    Stable unique key for a course card.
    Prefers 'id'; falls back to name+shift+start_date so two courses with
    the same name and shift (different start months) are never confused.
    """
    cid = course.get("id", "")
    if cid:
        return cid
    return f"{course.get('name', '')}_{course.get('shift', '')}_{course.get('start_date', '')}"


class TrainingPanel(ctk.CTkFrame):

    def __init__(self, parent, color_manager: ColorManager,
                 layout: dict, on_add, on_edit, on_delete,
                 on_select=None, on_goto=None, **kwargs):
        super().__init__(parent, width=layout["sidebar_width"], **kwargs)
        self.pack_propagate(False)

        self._colors = color_manager
        self._layout = layout
        self._on_add = on_add
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._on_select = on_select
        self._on_goto   = on_goto

        self._actions_month: list[dict] = []
        self._actions_year: list[dict] = []
        self._selected_key: str | None = None
        self._cards: dict[str, ctk.CTkFrame] = {}
        self._card_bgs: dict[str, str] = {}

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        title_size = self._layout["card_font_size"] + 2

        self._lbl_month_title = ctk.CTkLabel(
            self, text=lang.get("panel_title"),
            font=ctk.CTkFont(size=title_size, weight="bold"))
        self._lbl_month_title.pack(padx=12, pady=(12, 4), anchor="w")

        month_h = 210 if self._layout["name"] == "HD" else 280
        self._month_frame = ctk.CTkScrollableFrame(self, label_text="", height=month_h)
        self._month_frame.pack(fill="x", padx=8, pady=(0, 4))

        self._lbl_year_title = ctk.CTkLabel(
            self, text=lang.get("panel_year_title"),
            font=ctk.CTkFont(size=title_size, weight="bold"))
        self._lbl_year_title.pack(padx=12, pady=(8, 4), anchor="w")

        self._year_frame = ctk.CTkScrollableFrame(self, label_text="")
        self._year_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=8, pady=6)

        self._btn_add = ctk.CTkButton(
            btn_frame, text=lang.get("panel_add"),
            command=self._on_add, height=34)
        self._btn_add.pack(fill="x", pady=2)

        self._btn_edit = ctk.CTkButton(
            btn_frame, text=lang.get("panel_edit"),
            command=self._edit_selected,
            height=30,
            fg_color=_BTN_DISABLED_FG,
            hover_color=_BTN_EDIT_ACTIVE,
            text_color=_BTN_DISABLED_TEXT,
            text_color_disabled=_BTN_DISABLED_TEXT,
            state="disabled")
        self._btn_edit.pack(fill="x", pady=2)

        self._btn_delete = ctk.CTkButton(
            btn_frame, text=lang.get("panel_delete"),
            command=self._delete_selected,
            height=30,
            fg_color=_BTN_DISABLED_FG,
            hover_color=_BTN_DELETE_ACTIVE,
            text_color=_BTN_DISABLED_TEXT,
            text_color_disabled=_BTN_DISABLED_TEXT,
            state="disabled")
        self._btn_delete.pack(fill="x", pady=2)

    def refresh_language(self):
        self._lbl_month_title.configure(text=lang.get("panel_title"))
        self._lbl_year_title.configure(text=lang.get("panel_year_title"))
        self._btn_add.configure(text=lang.get("panel_add"))
        self._btn_edit.configure(text=lang.get("panel_edit"))
        self._btn_delete.configure(text=lang.get("panel_delete"))

    # ── Button state helpers ──────────────────────────────────────────────────

    def _enable_action_buttons(self):
        self._btn_edit.configure(
            state="normal", fg_color=_BTN_EDIT_ACTIVE, text_color="#FFFFFF")
        self._btn_delete.configure(
            state="normal", fg_color=_BTN_DELETE_ACTIVE, text_color="#FFFFFF")

    def _disable_action_buttons(self):
        self._btn_edit.configure(
            state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)
        self._btn_delete.configure(
            state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)

    # ── Public update methods ─────────────────────────────────────────────────

    def update(self, actions_month: list[dict], actions_year: list[dict] | None = None):
        self._actions_month = actions_month
        if actions_year is not None:
            month_keys = {_card_key(c) for c in actions_month}
            self._actions_year = [
                c for c in actions_year
                if _card_key(c) not in month_keys
            ]

        self._cards.clear()
        self._card_bgs.clear()
        self._disable_action_buttons()

        sorted_month = sorted(self._actions_month, key=lambda c: c.get("start_date", ""))
        self._render_section(self._month_frame, sorted_month, "panel_empty", compact=False)
        sorted_year = sorted(self._actions_year,
                             key=lambda c: c.get("start_date", ""))
        self._render_section(self._year_frame, sorted_year, "panel_year_empty", compact=True)

        if self._selected_key and self._selected_key in self._cards:
            self._apply_selected_style(self._selected_key)
            self._enable_action_buttons()
        else:
            self._selected_key = None

    def deselect(self):
        if self._selected_key and self._selected_key in self._cards:
            self._apply_normal_style(self._selected_key)
        self._selected_key = None
        self._disable_action_buttons()

    # ── Card rendering ────────────────────────────────────────────────────────

    def _render_section(self, frame: ctk.CTkScrollableFrame,
                        courses: list[dict], empty_key: str,
                        compact: bool = False):
        for w in frame.winfo_children():
            w.destroy()

        if not courses:
            ctk.CTkLabel(frame, text=lang.get(empty_key),
                         text_color="gray",
                         font=ctk.CTkFont(size=self._layout["card_detail_font_size"])
                         ).pack(pady=6)
            return

        card_font   = self._layout["card_font_size"] + 1
        detail_font = self._layout["card_detail_font_size"] + 1
        wrap        = self._layout["sidebar_width"] - 60

        for course in courses:
            name     = course.get("name", "Unnamed")
            shift    = _translate_shift(course.get("shift", ""))
            location = course.get("location", "")
            hours    = course.get("total_hours", "?")
            start    = course.get("start_date", "")
            end      = course.get("end_date", "")
            key      = _card_key(course)

            # Use bg_color_for so color resolves by id, not by name
            card_bg = self._colors.bg_color_for(course)
            self._card_bgs[key] = card_bg

            if compact:
                # Build display string: short_name (or name) · acronym · Mon YY
                short    = course.get("short_name", "") or name
                company  = course.get("company", "")

                acronym = ""
                try:
                    import src.catalog as _cat
                    for co in _cat.load_companies():
                        if co.get("name") == company:
                            acronym = co.get("acronym", "")
                            break
                except Exception:
                    pass
                if not acronym and "(" in company and ")" in company:
                    acronym = company[company.index("(")+1:company.index(")")]

                # Month + 2-digit year: "Ene 26"
                try:
                    _MONTH_ABBREVS = [
                        "month_january","month_february","month_march","month_april",
                        "month_may","month_june","month_july","month_august",
                        "month_september","month_october","month_november","month_december",
                    ]
                    m_idx  = int(start[5:7]) - 1
                    m_abbr = lang.get(_MONTH_ABBREVS[m_idx])[:3]
                    yr2    = start[2:4]
                    date_label = f"{m_abbr} {yr2}"
                except Exception:
                    date_label = ""

                row = ctk.CTkFrame(frame, corner_radius=4,
                                   border_width=0, fg_color=card_bg, height=26)
                row.pack(fill="x", pady=1, padx=2)
                row.pack_propagate(False)
                self._cards[key] = row

                card_text = course.get("text_color") or "#111111"

                # Accent bar
                ctk.CTkFrame(row, width=4, corner_radius=0,
                             fg_color=_darken(card_bg, 0.6)).pack(side="left", fill="y")

                # Date — fixed width, right side
                ctk.CTkLabel(row, text=date_label,
                             font=ctk.CTkFont(size=detail_font),
                             text_color=card_text,
                             anchor="e", width=48).pack(side="right", padx=(0, 6))

                # short_name — fixed width, left
                ctk.CTkLabel(row, text=short,
                             font=ctk.CTkFont(size=detail_font),
                             text_color=card_text,
                             anchor="w", width=90).pack(side="left", padx=(6, 0))

                # acronym — fixed width, left-aligned within column
                ctk.CTkLabel(row, text=acronym,
                             font=ctk.CTkFont(size=detail_font),
                             text_color=card_text,
                             anchor="w", width=60).pack(side="left", padx=(30, 0))

                for widget in [row] + list(row.winfo_children()):
                    widget.bind("<Button-1>", lambda e, k=key, c=course: self._select(k, c))
                    widget.bind("<Double-Button-1>", lambda e, k=key, c=course: self._goto_course(c))

            else:
                # Fixed height: 2 lines of name + 1 line of detail
                card_h = (card_font + 2) * 2 + (detail_font + 2) + 14
                card = ctk.CTkFrame(frame, corner_radius=6, height=card_h,
                                    border_width=0, fg_color=card_bg)
                card.pack(fill="x", pady=2, padx=2)
                card.pack_propagate(False)
                self._cards[key] = card

                # ── Accent bar on the left ────────────────────────────────
                accent = ctk.CTkFrame(card, width=5, corner_radius=0,
                                      fg_color=_darken(card_bg, 0.55))
                accent.pack(side="left", fill="y")

                # ── Content area ──────────────────────────────────────────
                inner = ctk.CTkFrame(card, fg_color="transparent")
                inner.pack(side="left", fill="both", expand=True,
                           padx=(6, 4), pady=4)

                card_text = course.get("text_color") or "#111111"

                # Row 1: course name — fixed to 2 lines via wraplength
                ctk.CTkLabel(inner, text=name,
                             font=ctk.CTkFont(size=card_font, weight="bold"),
                             text_color=card_text,
                             anchor="w", wraplength=wrap - 24,
                             justify="left",
                             height=(card_font + 2) * 2).pack(anchor="w")

                # Row 2: acronym · shift · time range
                company    = course.get("company", "")
                start_time = course.get("start_time")
                end_time   = course.get("end_time")

                def _fmt_time(t):
                    if t is None:
                        return ""
                    h = int(t)
                    m = int(round((t - h) * 60))
                    return f"{h:02d}:{m:02d}"

                time_str = (f"{_fmt_time(start_time)}–{_fmt_time(end_time)}"
                            if start_time is not None else "")

                acronym = ""
                try:
                    import src.catalog as _cat
                    for co in _cat.load_companies():
                        if co.get("name") == company:
                            acronym = co.get("acronym", "")
                            break
                except Exception:
                    pass
                if not acronym and "(" in company and ")" in company:
                    acronym = company[company.index("(")+1:company.index(")")]

                detail_parts = [p for p in [acronym, shift, time_str] if p]
                detail_str = "  ·  ".join(detail_parts)

                ctk.CTkLabel(inner, text=detail_str,
                             font=ctk.CTkFont(size=detail_font),
                             text_color=card_text,
                             anchor="w").pack(anchor="w")

                # Bind clicks on card and all children
                for widget in [card, accent, inner] + list(inner.winfo_children()):
                    widget.bind("<Button-1>",
                                lambda e, k=key, c=course: self._select(k, c))
                    widget.bind("<Double-Button-1>",
                                lambda e, k=key, c=course: self._double_click(k, c))
                card.bind("<Button-1>", lambda e, k=key, c=course: self._select(k, c))
                card.bind("<Double-Button-1>", lambda e, k=key, c=course: self._double_click(k, c))

            if key == self._selected_key:
                self._apply_selected_style(key)

    # ── Selection ─────────────────────────────────────────────────────────────

    def _select(self, key: str, course: dict):
        if self._selected_key and self._selected_key in self._cards:
            self._apply_normal_style(self._selected_key)

        if self._selected_key == key:
            self._selected_key = None
            self._disable_action_buttons()
            if self._on_select:
                self._on_select(None, None)
            return

        self._selected_key = key
        self._apply_selected_style(key)
        self._enable_action_buttons()

        if self._on_select:
            self._on_select(course.get("name"), course.get("shift", ""))

    def _double_click(self, key: str, course: dict):
        self._select(key, course)
        self._on_edit(course)

    def _apply_selected_style(self, key: str):
        card = self._cards.get(key)
        if not card:
            return
        normal_bg = self._card_bgs.get(key, "#CCCCCC")
        card.configure(
            border_width=_SEL_BORDER_WIDTH,
            border_color=_SEL_BORDER_COLOR,
            fg_color=_darken(normal_bg),
        )
        for child in card.winfo_children():
            if isinstance(child, ctk.CTkLabel) and child.cget("text"):
                child.configure(text_color="#000000")

    def _apply_normal_style(self, key: str):
        card = self._cards.get(key)
        if not card:
            return
        normal_bg = self._card_bgs.get(key, "#CCCCCC")
        card.configure(border_width=0, fg_color=normal_bg)
        # Reset text colors recursively (handles both flat and inner-frame layouts)
        def _reset_labels(widget, first=True):
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkLabel) and child.cget("text"):
                    child.configure(text_color="#111111" if first else "#444444")
                    first = False
                elif isinstance(child, ctk.CTkFrame):
                    _reset_labels(child, first)
        _reset_labels(card)

    # ── Selected course lookup ────────────────────────────────────────────────

    def selected_course(self) -> dict | None:
        if self._selected_key is None:
            return None
        for c in self._actions_month + self._actions_year:
            if _card_key(c) == self._selected_key:
                return c
        return None

    def _goto_course(self, course: dict):
        if self._on_goto:
            start = course.get("start_date", "")
            try:
                year  = int(start[:4])
                month = int(start[5:7])
                self._on_goto(year, month)
            except (ValueError, IndexError):
                pass

    def _edit_selected(self):
        c = self.selected_course()
        if c:
            self._on_edit(c)

    def _delete_selected(self):
        c = self.selected_course()
        if c:
            self._on_delete(c)
