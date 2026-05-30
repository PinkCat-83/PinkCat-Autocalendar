# PinkCat AutoCalendar

Desktop application for generating annual teaching calendars.
Originally built in Excel/VBA; rebuilt in Python with a full GUI.

---

## Nomenclature

These terms are used consistently throughout the codebase, documentation, and UI. When adding new features, always use the correct term.

| Term | Spanish | Definition |
|------|---------|------------|
| **Course** (*Curso*) | Curso | A reusable course type defined in the catalog: name, short name, total hours, and description. Does not have dates, company, or location. |
| **Company** (*Empresa*) | Empresa | The organization that commissions a training action. Has a name, acronym, and a list of teaching locations. |
| **Training action** (*Acción formativa*) | Acción formativa | A concrete instance of a Course delivered by a Company at a specific location, on specific dates and times. Stored in `training_actions.json`. |

### Key distinctions

- A **Course** is the *what* — the subject matter and hours. It lives in `catalog.json`.
- A **Company** is the *who* — the client. It lives in `companies.json`.
- A **Training action** is the *when, where, and for whom* — the scheduled delivery. It lives in `training_actions.json`.

### Field naming conventions

| Field | Belongs to | Purpose |
|-------|-----------|---------|
| `name` | Course, Company, Training action | Full display name |
| `short_name` | Course | Abbreviated name for compact UI display (max 8 chars) |
| `acronym` | Company | Short identifier for the company (max 8 chars) |
| `id` | Training action | Unique stable identifier (`course_001`, `course_002`, …) |

---

## Features

- **Monthly calendar view** — color-coded by training action, navigable by month and year
- **Automatic schedule generation** — skips weekends, public holidays, and action-specific non-teaching dates
- **Public holiday rendering** — holiday cells shown with a red tint and the holiday name
- **Conflict detection** — warns if two training actions are assigned to the same day and shift
- **Decimal hours support** — e.g. 2.5 h/day works correctly
- **Multi-language UI** — switch language at runtime via dropdown; preference is saved automatically across sessions
- **Auto layout detection** — detects screen resolution on startup and applies HD or 2K preset automatically
- **Fixed window size** — no resize lag
- **Tab navigation** — Calendar · Courses · Companies · Holidays
- **Training action management** — add, edit, and delete training actions directly from the GUI
- **Reference data management** — manage the course catalog (with short names), companies (with acronyms and locations), and holidays from dedicated tabs
- **Contacts** — each training action can have multiple contacts (name, role, phone, email)
- **Company locations** — each company holds its own list of teaching locations with an optional Google Maps URL; selecting a company in the action dialog filters the location dropdown automatically
- **Google Maps integration** — each location can store a Maps URL; it auto-fills when a known location is selected, and opens in the default browser via the 🗺 button
- **Action-specific holidays** — managed via a dedicated dialog with a calendar picker per row
- **Flexible date input** — date fields accept `YYYY-MM-DD`, `DD/MM/YYYY`, or `YYYY/MM/DD` with any separator (`-`, `/`, `.`)
- **Custom action colors** — each training action can have a custom background and text color, chosen from a Word-style color picker; falls back to the automatic pastel palette if not set
- **Pending confirmation flag** — training actions can be marked as pending; shown with a warning icon in the calendar
- **Stable action colors** — each training action is assigned a pastel color by its unique `id`; colors remain consistent across the whole session
- **Company logo** — displayed in the top-right corner; clicking it opens the company website
- **Single instance enforcement** — only one instance of the app can run at a time (Windows mutex)
- **JSON storage** — one `training_actions.json` for input, one `calendar_YYYY.json` output per year
- **Persistent settings** — language preference saved to `data/settings.json`
- **Economic data ready** — `rate_per_hour` and `withholding_pct` fields exist in the data model for a future tax summary feature

---

## Project structure

```
PinkCat AutoCalendar/
│
├── PinkCat Autocalendar.pyw       # Entry point — double-click to launch (no console)
│
├── data/
│   ├── training_actions.json      # Scheduled training action instances
│   ├── catalog.json               # Course catalog (name, short_name, total hours, description)
│   ├── companies.json             # Companies with acronym and locations (name + maps_url)
│   ├── holidays.json              # Public holidays by year
│   ├── settings.json              # User preferences (language, etc.)
│   └── calendar_YYYY.json         # Generated calendar output
│
├── img/
│   └── logo.png                   # Company logo shown in the top bar
│
├── language/
│   └── translations.csv           # All UI strings — one column per language
│
├── src/
│   ├── calendar_gen.py            # Core calendar generation logic
│   ├── catalog.py                 # Data access for catalog and companies
│   ├── economic.py                # Economic calculations (gross, withholding, net)
│   ├── export.py                  # JSON read/write utilities
│   ├── holidays.py                # Holiday loading and management
│   └── language.py               # Language manager (reads translations.csv, persists preference)
│
└── gui/
    ├── core/
    │   ├── main_window.py             # Main application window + tab navigation
    │   ├── calendar_logic_mixin.py    # CRUD, calendar refresh, navigation, day popup
    │   └── management_tabs_mixin.py   # Catalog, Companies, Holidays tabs
    ├── calendar/
    │   ├── calendar_view.py           # Monthly calendar grid widget
    │   └── training_panel.py          # Sidebar training action list panel
    ├── dialogs/
    │   ├── course_dialog.py           # Add/edit training action dialog (incl. ColorPickerDialog)
    │   ├── tab_dialogs.py             # Dialogs for catalog, companies, holidays
    │   └── contacts_widget.py         # Inline contact list editor
    └── widgets/
        ├── table_view.py              # Generic reusable management table
        ├── colors.py                  # Per-action color assignment (by id, custom override)
        ├── layout.py                  # Screen detection and HD/2K layout presets
        ├── locations_widget.py        # Inline location list editor (name + maps_url per row)
        └── holidays_widget.py         # Inline action-specific holidays editor
```

---

## Requirements

- Python 3.11 or higher
- `customtkinter`
- `pillow` (for the company logo in the top bar)

```bash
pip install customtkinter pillow
```

No other third-party dependencies — only the Python standard library.

---

## Adding or editing training actions

Use the **📋 Training activity** button in the Calendar tab sidebar, or edit `data/training_actions.json` directly.

Each training action has the following fields:

```json
{
  "id": "course_001",
  "name": "IFCT36 - Excel Avanzado",
  "location": "Location",
  "maps_url": "https://maps.google.com/?q=...",
  "company": "Company",
  "shift": "Morning",
  "modality": "presencial",
  "start_time": 8.5,
  "end_time": 14.5,
  "daily_hours": 6,
  "total_hours": 100,
  "start_date": "2026-03-09",
  "pending": false,
  "teaching_days": {
    "monday": true,
    "tuesday": true,
    "wednesday": true,
    "thursday": true,
    "friday": true,
    "saturday": false,
    "sunday": false
  },
  "specific_holidays": ["2026-03-20", "2026-03-25"],
  "contacts": [
    {
      "name": "Carlos Ruiz",
      "role": "Training Manager",
      "phone": "928 000 002",
      "email": "c.ruiz@cicca.es"
    }
  ],
  "bg_color": "#FDE99A",
  "text_color": "#1C1C1C",
  "rate_per_hour": 18.0,
  "withholding_pct": 15.0
}
```

**Notes:**
- `id` is assigned automatically when creating via the GUI; do not edit manually
- `shift` is always stored in English (`"Morning"`, `"Afternoon"`, `"Other"`), regardless of the active UI language
- `start_time` / `end_time` use decimal hours: `8.5` = 08:30, `14.5` = 14:30
- `daily_hours` is calculated automatically from start/end times
- `specific_holidays` lists dates to skip for this action only (ISO format `YYYY-MM-DD`)
- `contacts` is an array — zero, one, or many contacts per action
- `maps_url` is auto-filled from the company's location data; can be overridden manually (entry turns red if the location is not in the company's known list)
- `pending` marks the action as not yet confirmed; shown with a ⚠ icon in the calendar
- `bg_color` / `text_color` are optional; if absent, the automatic pastel palette is used
- `rate_per_hour` and `withholding_pct` are stored but not yet displayed in the UI (planned)

---

## Managing courses (catalog)

Edit `data/catalog.json` directly, or use the **Courses** tab in the app. Each course entry has:

```json
{
  "name": "IFCT36 - Excel Avanzado",
  "short_name": "Excel Av.",
  "total_hours": 100,
  "description": ""
}
```

`short_name` is optional but recommended — it is used in compact UI views such as calendar cells and the action panel sidebar. **Maximum 8 characters.**

---

## Managing companies and locations

Edit `data/companies.json` directly, or use the **Companies** tab in the app. Each company holds its own list of locations, each with an optional Google Maps URL:

```json
[
  {
    "name": "CICCA (CIP)",
    "acronym": "CIP",
    "locations": [
      {"name": "Teatro - Centro Cultural Cicca", "maps_url": "https://maps.google.com/?q=..."},
      {"name": "Sala B", "maps_url": ""}
    ]
  }
]
```

`acronym` is optional but recommended — it is used in compact UI views. **Maximum 8 characters.**

When adding or editing a training action, selecting a company automatically filters the location dropdown to that company's locations, and the Maps URL is auto-filled. The location and URL can still be typed manually if needed; a red background on the URL field indicates the location is not in the company's known list.

---

## Managing public holidays

Edit `data/holidays.json` directly, or use the **Holidays** tab in the app. Each year is a separate key:

```json
{
  "2026": [
    {"date": "2026-01-01", "name": "New Year's Day"},
    {"date": "2026-05-30", "name": "Canary Islands Day"}
  ]
}
```

---

## Adding or editing languages

Open `language/translations.csv` in Excel. The file uses:
- **Semicolon** (`;`) as column separator
- **UTF-8 BOM** encoding (so Excel renders accented characters correctly)

Each row is a UI string key. Each column after `key` is a language.

To **add a new language**: add a new column with the language name as the header, fill in the translations, and save. The app detects it automatically on next launch.

To **edit a translation**: change the value in the relevant cell and save.

The selected language is saved automatically to `data/settings.json` and restored on next launch.

> **Rule for contributors:** every UI string must have an entry in `translations.csv`. Never hardcode display text in Python files.

---

## Layout presets

The app detects screen resolution at startup and picks the most appropriate preset:

| Preset | Trigger | Window size | Cell size |
|--------|---------|-------------|-----------|
| HD | < 2560 × 1440 | 1280 × 740 | 100 × 100 px |
| 2K | ≥ 2560 × 1440 | 1800 × 1020 | 148 × 140 px |

The active preset is shown in the top-right corner of the title bar.

---

## Annual workflow

1. Add the year's training actions via the GUI or by editing `data/training_actions.json`.
2. Verify `data/holidays.json` has entries for the new year; add the key if missing.
3. Launch `app.pyw` and navigate the months to confirm the schedule looks correct.
4. The generated calendar is saved automatically to `data/calendar_YYYY.json`.

---

## UI conventions

These rules must be followed consistently across the entire codebase. When adding new widgets or dialogs, check this section first.

### Action buttons (Add / Edit / Delete)

The standard pattern is defined in `gui/widgets/table_view.py` and must be replicated everywhere:

| State | `fg_color` | `text_color` | `hover_color` |
|-------|-----------|--------------|---------------|
| Disabled (Edit) | `#BDBDBD` | `#F0F0F0` | `#2E86C1` |
| Disabled (Delete) | `#BDBDBD` | `#F0F0F0` | `#922B21` |
| Enabled (Edit) | `#2E86C1` | `#FFFFFF` | `#2E86C1` |
| Enabled (Delete) | `#C0392B` | `#FFFFFF` | `#922B21` |

- Edit and Delete start **disabled** and become enabled only when a row is selected.
- After any save or delete operation, both buttons reset to **disabled**.
- Button labels come from translation keys `panel_edit` and `panel_delete` (never hardcoded).
- The Add button is always enabled and uses the default CTkButton style.

### Inline list editors (arrays inside dialogs)

Used for contacts (`ContactsWidget`) and locations (`LocationsWidget`). Any new widget of this type must follow the same pattern:

- **Header row**: a green `[+]` button (`fg_color="#27AE60"`, `hover_color="#1E8449"`, `width=28`, `height=28`) sits in column 0, followed by the column label(s). The `[+]` appends a new empty row at the end of the list.
- **Data rows**: no `[+]` per row. Each row contains the field entry/entries and a red `[✕]` delete button (`fg_color="#C0392B"`, `hover_color="#922B21"`, `width=28`, `height=28`) at the right end.
- **Empty state**: when there are no rows, a standalone `[+]` is shown inside the scrollable area as a fallback hint. It is destroyed and replaced by the first real row when clicked.
- Column 0 of data rows must be a fixed-width invisible spacer (`CTkLabel(text="", width=28)`) so entries align with the column label in the header, not with the `[+]` button.
- The scrollable area uses `CTkScrollableFrame`.
- New rows receive focus automatically (`self.after(30, ent.focus_set)`).

### Dialogs and pop-up windows

- All dialogs are `CTkToplevel` with `resizable(False, False)` and `grab_set()`.
- Position with `_center_on_parent(self, parent, width, height)` (defined in `tab_dialogs.py`).
- Button bar is packed `side="bottom"` first, then the body, so the bar stays pinned regardless of content height.
- The first input field receives focus via `self.after(50, widget.focus_set)`.
- Save/Cancel labels come from translation keys `dialog_save` and `dialog_cancel`.
- Validation errors use `messagebox.showerror` with key `error_form_title`. Required-field messages use specific keys (e.g. `error_name_required`, `error_start_date`) — never the generic course-name key for non-course dialogs.
- Optional fields must not block saving; only truly required fields (e.g. a date with no valid parse) should raise an error.

### Color picker

`ColorPickerDialog` (defined in `course_dialog.py`) is a Word-style swatch grid. It returns `result_bg` and `result_text`. Colors are stored as `bg_color` / `text_color` in `training_actions.json` and take precedence over the automatic palette in `ColorManager`.

---

## Planned features

- Economic summary panel (gross income, withholding, net pay — per training action and per company)
- Annual income tax report (Renta)

## TODO

- Extraer en un archivo PDF el calendario. Al principio del documento habrá un listado de los periodos de días libres y donde se hará mención también a las fechas con acciones formativas no confirmadas.