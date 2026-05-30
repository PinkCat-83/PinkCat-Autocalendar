"""
management_tabs_mixin.py
Mixin for MainWindow that owns the three management tabs:
  Courses (catalog) · Companies · Holidays
and the shared helpers _wire_save / _run_dialog that those tabs rely on.

Note: Locations are now managed inside each company (CompanyDialog),
so the standalone Locations tab has been removed.
"""

from pathlib import Path

import customtkinter as ctk

from gui.widgets.table_view import TableView
from gui.dialogs.tab_dialogs import CatalogDialog, CompanyDialog, HolidayDialog
from tkinter import ttk
from src.holidays import load_holidays
import src.language as lang
import src.catalog as catalog

BASE_DIR   = Path(__file__).parent.parent.parent
DATA_DIR   = BASE_DIR / "data"
HOLIDAYS_JSON = DATA_DIR / "holidays.json"


class ManagementTabsMixin:
    """
    Mixin that provides _build_catalog_tab, _build_companies_tab,
    _build_holidays_tab, and their supporting helpers.

    Expects the host class to expose:
        self._layout   – layout dict from detect_layout()
        self._year     – currently displayed year (int)
        self._holidays – set[date], updated when holidays change
        self._regenerate_and_refresh()  – triggers calendar rebuild
    """

    # ── Tab: Course catalog ───────────────────────────────────────────────────

    def _build_catalog_tab(self, parent):
        L = self._layout
        cols = [
            ("name",        lang.get("col_name"),        3),
            ("short_name",  lang.get("col_short_name"),  2),
            ("total_hours", lang.get("col_total_hours"),  1),
            ("description", lang.get("col_description"), 4),
        ]
        self._catalog_table = TableView(
            parent, columns=cols, layout=L,
            add_label=lang.get("btn_add_action"),
            on_add=lambda: self._run_dialog(CatalogDialog),
            on_edit=lambda item: self._run_dialog(CatalogDialog, item),
            on_delete=lambda item: item,
        )
        self._catalog_table.pack(fill="both", expand=True)
        self._catalog_table.load(catalog.load_catalog())

        # Wire save — catalog tab uses direct monkey-patching (pre-dates _wire_save)
        orig_add  = self._catalog_table._add
        orig_edit = self._catalog_table._edit
        orig_del  = self._catalog_table._delete

        def _save_catalog():
            catalog.save_catalog(self._catalog_table.get_items())

        def add():
            orig_add(); _save_catalog()
        def edit():
            orig_edit(); _save_catalog()
        def delete():
            orig_del(); _save_catalog()

        self._catalog_table._add    = add
        self._catalog_table._btn_add.configure(command=add)
        self._catalog_table._edit   = edit
        self._catalog_table._btn_edit.configure(command=edit)
        self._catalog_table._delete = delete
        self._catalog_table._btn_delete.configure(command=delete)

    # ── Tab: Companies ────────────────────────────────────────────────────────

    def _build_companies_tab(self, parent):
        L = self._layout
        cols = [
            ("name",      lang.get("col_name"),      3),
            ("acronym",   lang.get("col_acronym"),    1),
            ("locations", lang.get("col_locations"),  1),
        ]
        self._companies_table = TableView(
            parent, columns=cols, layout=L,
            add_label=lang.get("btn_add_company"),
            on_add=lambda: self._run_dialog(CompanyDialog),
            on_edit=lambda item: self._run_dialog(CompanyDialog, item),
            on_delete=lambda item: item,
        )
        self._companies_table.pack(fill="both", expand=True)
        self._companies_table.load(catalog.load_companies())
        self._wire_save(self._companies_table,
                        lambda: catalog.save_companies(
                            self._companies_table.get_items()))
    # ── Tab: Holidays ─────────────────────────────────────────────────────────

    def _build_holidays_tab(self, parent):
        """
        Holidays tab — tree grouped by year, all years shown at once.
        Uses a ttk.Treeview directly (no TableView) so we can have
        collapsible year groups.
        """
        import tkinter as tk
        from tkinter import ttk
        from src.export import load_json as _lj

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(frame, fg_color="transparent")
        toolbar.pack(fill="x", padx=12, pady=(12, 6))
        ctk.CTkButton(
            toolbar, text=lang.get("btn_add_holiday"),
            command=self._holidays_add,
            height=34, width=160, font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 6))
        self._btn_holiday_edit = ctk.CTkButton(
            toolbar, text=lang.get("panel_edit"),
            command=self._holidays_edit, state="disabled",
            height=34, width=110, font=ctk.CTkFont(size=13),
            fg_color="#BDBDBD", hover_color="#2E86C1",
            text_color="#F0F0F0", text_color_disabled="#F0F0F0",
        )
        self._btn_holiday_edit.pack(side="left", padx=(0, 6))
        self._btn_holiday_delete = ctk.CTkButton(
            toolbar, text=lang.get("panel_delete"),
            command=self._holidays_delete, state="disabled",
            height=34, width=110, font=ctk.CTkFont(size=13),
            fg_color="#BDBDBD", hover_color="#922B21",
            text_color="#F0F0F0", text_color_disabled="#F0F0F0",
        )
        self._btn_holiday_delete.pack(side="left")

        # ── Treeview ──────────────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._holidays_tree = ttk.Treeview(
            tree_frame, style="TableView.Treeview",
            columns=("date", "name"), show="tree headings", selectmode="browse",
        )
        self._holidays_tree.heading("#0",    text="")
        self._holidays_tree.heading("date",  text=lang.get("col_date"))
        self._holidays_tree.heading("name",  text=lang.get("col_name"))
        self._holidays_tree.column("#0",    width=60,  stretch=False)
        self._holidays_tree.column("date",  width=120, stretch=False)
        self._holidays_tree.column("name",  width=400, stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._holidays_tree.yview)
        self._holidays_tree.configure(yscrollcommand=vsb.set)
        self._holidays_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._holidays_tree.bind("<<TreeviewSelect>>", self._holidays_on_select)
        self._holidays_tree.bind("<Double-1>",          self._holidays_on_double)

        self._holidays_load_tree()

    def _holidays_load_tree(self):
        """Load all years from holidays.json into the grouped Treeview."""
        from src.export import load_json as _lj
        tree = self._holidays_tree
        # Clear
        for item in tree.get_children():
            tree.delete(item)
        try:
            data = _lj(HOLIDAYS_JSON)
        except Exception:
            data = {}
        # Remove the _note meta-key if present
        years = sorted(k for k in data if k.isdigit())
        for year in years:
            entries = sorted(data[year], key=lambda x: x.get("date", ""))
            year_node = tree.insert("", "end", iid=f"year_{year}",
                                   text=year, open=False, values=("", ""))
            for entry in entries:
                tree.insert(year_node, "end",
                            values=(entry.get("date", ""),
                                    entry.get("name", "")))

    def _holidays_on_select(self, _event=None):
        sel = self._holidays_tree.selection()
        # Enable edit/delete only when a leaf (holiday) row is selected
        is_leaf = bool(sel) and not sel[0].startswith("year_")
        if is_leaf:
            self._btn_holiday_edit.configure(state="normal", fg_color="#2E86C1", text_color="#FFFFFF")
            self._btn_holiday_delete.configure(state="normal", fg_color="#C0392B", text_color="#FFFFFF")
        else:
            self._btn_holiday_edit.configure(state="disabled", fg_color="#BDBDBD", text_color="#F0F0F0", text_color_disabled="#F0F0F0")
            self._btn_holiday_delete.configure(state="disabled", fg_color="#BDBDBD", text_color="#F0F0F0", text_color_disabled="#F0F0F0")

    def _holidays_on_double(self, event):
        sel = self._holidays_tree.selection()
        if sel and not sel[0].startswith("year_"):
            self._holidays_edit()

    def _holidays_selected_item(self) -> dict | None:
        sel = self._holidays_tree.selection()
        if not sel or sel[0].startswith("year_"):
            return None
        vals = self._holidays_tree.item(sel[0], "values")
        return {"date": vals[0], "name": vals[1]}

    def _holidays_add(self):
        dlg = HolidayDialog(self)
        if not dlg.result:
            return
        entry = dlg.result          # {"date": "YYYY-MM-DD", "name": "..."}
        year  = entry["date"][:4]
        # Duplicate check across the whole file
        from src.export import load_json as _lj
        try:
            data = _lj(HOLIDAYS_JSON)
        except Exception:
            data = {}
        existing_dates = [
            h["date"] for entries in data.values()
            if isinstance(entries, list) for h in entries
        ]
        if entry["date"] in existing_dates:
            from tkinter import messagebox
            messagebox.showwarning(
                lang.get("error_form_title"),
                lang.get("error_holiday_duplicate"),
            )
            return
        data.setdefault(year, [])
        data[year].append(entry)
        data[year] = sorted(data[year], key=lambda x: x.get("date", ""))
        self._holidays_save(data)

    def _holidays_edit(self):
        item = self._holidays_selected_item()
        if not item:
            return
        old_date = item["date"]
        dlg = HolidayDialog(self, item)
        if not dlg.result:
            return
        entry    = dlg.result
        new_date = entry["date"]
        from src.export import load_json as _lj
        try:
            data = _lj(HOLIDAYS_JSON)
        except Exception:
            data = {}
        # Remove old entry from its correct year bucket
        old_year = old_date[:4]
        if old_year in data:
            data[old_year] = [h for h in data[old_year] if h["date"] != old_date]
        # Duplicate check (excluding the entry being edited)
        existing_dates = [
            h["date"] for entries in data.values()
            if isinstance(entries, list) for h in entries
        ]
        if new_date in existing_dates:
            from tkinter import messagebox
            messagebox.showwarning(
                lang.get("error_form_title"),
                lang.get("error_holiday_duplicate"),
            )
            return
        # Insert into correct year bucket
        new_year = new_date[:4]
        data.setdefault(new_year, [])
        data[new_year].append(entry)
        data[new_year] = sorted(data[new_year], key=lambda x: x.get("date", ""))
        self._holidays_save(data)

    def _holidays_delete(self):
        item = self._holidays_selected_item()
        if not item:
            return
        from tkinter import messagebox
        if not messagebox.askyesno(lang.get("confirm_delete_title"),
                                   lang.get("confirm_delete_msg")):
            return
        date_str = item["date"]
        year     = date_str[:4]
        from src.export import load_json as _lj
        try:
            data = _lj(HOLIDAYS_JSON)
        except Exception:
            data = {}
        if year in data:
            data[year] = [h for h in data[year] if h["date"] != date_str]
        self._holidays_save(data)

    def _holidays_save(self, data: dict):
        """Persist *data* to disk, reload calendar holidays, refresh tree."""
        from src.export import save_json as _sj
        _sj(data, HOLIDAYS_JSON)
        self._holidays = load_holidays(HOLIDAYS_JSON, self._year)
        self._regenerate_and_refresh()
        self._holidays_load_tree()
        self._btn_holiday_edit.configure(state="disabled", fg_color="#BDBDBD", text_color="#F0F0F0", text_color_disabled="#F0F0F0")
        self._btn_holiday_delete.configure(state="disabled", fg_color="#BDBDBD", text_color="#F0F0F0", text_color_disabled="#F0F0F0")

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _wire_save(self, table: TableView, save_fn):
        """Wrap each CRUD button on *table* so it calls *save_fn* after the action."""
        for attr, btn_attr in [("_add", "_btn_add"),
                                ("_edit", "_btn_edit"),
                                ("_delete", "_btn_delete")]:
            orig = getattr(table, attr)

            def make_wrapper(o, s):
                def wrapper():
                    o()
                    s()
                return wrapper

            wrapped = make_wrapper(orig, save_fn)
            setattr(table, attr, wrapped)
            btn = getattr(table, btn_attr)
            current_text = btn.cget("text")
            btn.configure(command=wrapped, text=current_text)

    def _run_dialog(self, DialogClass, item=None):
        """Open a modal dialog and return its result."""
        dlg = DialogClass(self) if item is None else DialogClass(self, item)
        return dlg.result
