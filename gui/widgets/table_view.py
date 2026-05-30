"""
table_view.py
Generic scrollable table with Add / Edit / Delete buttons.
Used as the base for the Courses, Companies, Locations, and Holidays tabs.

Built on ttk.Treeview so that column headers are always pixel-perfectly
aligned with the data rows, regardless of content or window size.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import src.language as lang


# ── Treeview style constants ───────────────────────────────────────────────────

_BG_ROW_ODD  = "#f0f0f0"
_BG_ROW_EVEN = "#e2e2e2"
_BG_SELECTED = "#2E86C1"
_FG_SELECTED = "#ffffff"
_BG_HEADER   = "#c8c8c8"
_FG_HEADER   = "#1a1a1a"

# Disabled button style — matches courses_panel.py
_BTN_DISABLED_FG   = "#BDBDBD"
_BTN_DISABLED_TEXT = "#F0F0F0"


class TableView(ctk.CTkFrame):
    """
    Reusable management table.

    columns: list of (field_key, header_label, weight) tuples
    on_add:    called with no args — caller opens dialog, returns new item or None
    on_edit:   called with the selected item dict
    on_delete: called with the selected item dict
    """

    def __init__(self, parent, columns: list[tuple],
                 on_add, on_edit, on_delete,
                 layout: dict, add_label: str | None = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._columns   = columns
        self._on_add    = on_add
        self._on_edit   = on_edit
        self._on_delete = on_delete
        self._layout    = layout
        self._add_label = add_label or lang.get("panel_add")
        self._items: list[dict] = []

        font_size = max(layout.get("card_font_size", 12), 12)
        self._font       = ("Segoe UI", font_size)
        self._font_bold  = ("Segoe UI", font_size, "bold")
        self._row_height = font_size * 3  # generous row height

        self._build_ui()

    def _build_ui(self):
        self._apply_treeview_style()

        # ── Action buttons (top) ──────────────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=12, pady=(12, 6))

        self._btn_add = ctk.CTkButton(
            btn_bar, text=self._add_label,
            command=self._add, height=34, width=160,
            font=ctk.CTkFont(size=13))
        self._btn_add.pack(side="left", padx=(0, 6))

        self._btn_edit = ctk.CTkButton(
            btn_bar, text=lang.get("panel_edit"),
            command=self._edit, height=34, width=110,
            fg_color=_BTN_DISABLED_FG, hover_color="#2E86C1",
            text_color=_BTN_DISABLED_TEXT, text_color_disabled=_BTN_DISABLED_TEXT,
            state="disabled",
            font=ctk.CTkFont(size=13))
        self._btn_edit.pack(side="left", padx=(0, 6))

        self._btn_delete = ctk.CTkButton(
            btn_bar, text=lang.get("panel_delete"),
            command=self._delete, height=34, width=110,
            fg_color=_BTN_DISABLED_FG, hover_color="#C0392B",
            text_color=_BTN_DISABLED_TEXT, text_color_disabled=_BTN_DISABLED_TEXT,
            state="disabled",
            font=ctk.CTkFont(size=13))
        self._btn_delete.pack(side="left")

        # ── Treeview + scrollbar ──────────────────────────────────────────────
        tree_container = ctk.CTkFrame(self, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        col_ids = [fk for fk, _, _ in self._columns]
        self._tree = ttk.Treeview(
            tree_container,
            columns=col_ids,
            show="headings",
            style="TableView.Treeview",
            selectmode="browse",
        )

        scrollbar = ttk.Scrollbar(tree_container, orient="vertical",
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

        # Configure columns
        for field_key, label, weight in self._columns:
            self._tree.heading(field_key, text=label, anchor="w")
            # minwidth proportional to weight; stretch fills remaining space
            self._tree.column(field_key, anchor="w", minwidth=80 * weight,
                               stretch=True)

        # Alternating row tags
        self._tree.tag_configure("odd",  background=_BG_ROW_ODD)
        self._tree.tag_configure("even", background=_BG_ROW_EVEN)

        # Selection & double-click
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>",         self._on_double_click)

    def _apply_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TableView.Treeview",
            background=_BG_ROW_ODD,
            fieldbackground=_BG_ROW_ODD,
            foreground="#1a1a1a",
            font=self._font,
            rowheight=self._row_height,
        )
        style.configure(
            "TableView.Treeview.Heading",
            background=_BG_HEADER,
            foreground=_FG_HEADER,
            font=self._font_bold,
            relief="raised",
            borderwidth=1,
            padding=(8, 6),
        )
        style.map(
            "TableView.Treeview",
            background=[("selected", _BG_SELECTED)],
            foreground=[("selected", _FG_SELECTED)],
        )
        style.map(
            "TableView.Treeview.Heading",
            background=[("active", "#b8b8b8")],
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self, items: list[dict]):
        self._items = items
        self._btn_edit.configure(state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)
        self._btn_delete.configure(state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)
        self._render_rows()

    def refresh_language(self):
        self._btn_add.configure(text=lang.get("panel_add"))
        self._btn_edit.configure(text=lang.get("panel_edit"))
        self._btn_delete.configure(text=lang.get("panel_delete"))

    def get_items(self) -> list[dict]:
        return self._items

    # ── Row rendering ─────────────────────────────────────────────────────────

    def _render_rows(self):
        self._tree.delete(*self._tree.get_children())
        for idx, item in enumerate(self._items):
            values = []
            for field_key, _, _ in self._columns:
                raw = item.get(field_key, "")
                if isinstance(raw, list):
                    # Extract "name" if list of dicts, else stringify directly
                    parts = [x["name"] if isinstance(x, dict) else str(x) for x in raw]
                    values.append(", ".join(parts) if parts else "-")
                else:
                    values.append(str(raw))
            tag = "even" if idx % 2 == 0 else "odd"
            self._tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))

    def _selected_index(self) -> int | None:
        sel = self._tree.selection()
        return int(sel[0]) if sel else None

    # ── Events ────────────────────────────────────────────────────────────────

    def _on_select(self, _event):
        if self._tree.selection():
            self._btn_edit.configure(state="normal", fg_color="#2E86C1", text_color="#FFFFFF")
            self._btn_delete.configure(state="normal", fg_color="#C0392B", text_color="#FFFFFF")
        else:
            self._btn_edit.configure(state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)
            self._btn_delete.configure(state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)

    def _on_double_click(self, _event):
        if self._selected_index() is not None:
            self._edit()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add(self):
        result = self._on_add()
        if result:
            self._items.append(result)
            self._render_rows()

    def _edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        result = self._on_edit(self._items[idx])
        if result:
            self._items[idx] = result
            self._tree.selection_remove(self._tree.selection())
            self._render_rows()

    def _delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        item = self._items[idx]
        name = item.get("name", "")
        if messagebox.askyesno(lang.get("confirm_delete_title"),
                               lang.get("confirm_delete_msg", name=name)):
            self._items.pop(idx)
            self._btn_edit.configure(state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)
            self._btn_delete.configure(state="disabled", fg_color=_BTN_DISABLED_FG, text_color=_BTN_DISABLED_TEXT)
            self._render_rows()
