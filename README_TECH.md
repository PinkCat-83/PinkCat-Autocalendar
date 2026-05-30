# 🔧 Technical README — PinkCat AutoCalendar

> Internal reference for development, debugging, and AI-assisted work.  
> → [Presentation README](./README.md)

---

## 🤖 AI Instructions

- Wait for the author to specify what needs to be done before proceeding.
- Ask for the relevant files before making any modifications.
- Follow the UI conventions in section 5 strictly — button states, inline editors, and dialog patterns are standardized across the whole app.
- Never hardcode display text in Python files — all UI strings must have an entry in `language/translations.csv`.
- `shift` is always stored in English (`"Morning"`, `"Afternoon"`, `"Other"`) regardless of the active UI language.
- `id` on training actions is assigned automatically by the GUI — never edit manually.

---

## 1. Nomenclature

These terms are used consistently throughout the codebase, documentation, and UI. Always use the correct term when adding new features.

| Term | Spanish | Definition |
|---|---|---|
| **Course** | Curso | Reusable course type in the catalog: name, short name, total hours, description. No dates, company, or location. |
| **Company** | Empresa | Organization commissioning a training action. Has name, acronym, and a list of teaching locations. |
| **Training action** | Acción formativa | Concrete instance of a Course delivered by a Company at a specific location on specific dates. |

### Field naming conventions

| Field | Belongs to | Notes |
|---|---|---|
| `name` | Course, Company, Training action | Full display name |
| `short_name` | Course | Max 8 chars — used in compact views |
| `acronym` | Company | Max 8 chars — used in compact views |
| `id` | Training action | Unique stable ID (`course_001`, …) — auto-assigned, never edit manually |

---

## 2. Project Structure

```
PinkCat AutoCalendar/
├── PinkCat Autocalendar.pyw        # Entry point (no console window)
├── data/
│   ├── training_actions.json       # Scheduled training action instances
│   ├── catalog.json                # Course catalog
│   ├── companies.json              # Companies with locations
│   ├── holidays.json               # Public holidays by year
│   ├── settings.json               # User preferences (language, etc.)
│   └── calendar_YYYY.json          # Generated calendar output
├── img/
│   └── logo.png                    # Company logo shown in the top bar
├── language/
│   └── translations.csv            # All UI strings — one column per language
├── src/
│   ├── calendar_gen.py             # Core calendar generation logic
│   ├── catalog.py                  # Data access for catalog and companies
│   ├── economic.py                 # Economic calculations (gross, withholding, net)
│   ├── export.py                   # JSON read/write utilities
│   ├── holidays.py                 # Holiday loading and management
│   └── language.py                 # Language manager (reads CSV, persists preference)
└── gui/
    ├── core/
    │   ├── main_window.py              # Main window + tab navigation
    │   ├── calendar_logic_mixin.py     # CRUD, calendar refresh, navigation, day popup
    │   └── management_tabs_mixin.py    # Catalog, Companies, Holidays tabs
    ├── calendar/
    │   ├── calendar_view.py            # Monthly calendar grid widget
    │   └── training_panel.py           # Sidebar training action list panel
    ├── dialogs/
    │   ├── course_dialog.py            # Add/edit training action dialog + ColorPickerDialog
    │   ├── tab_dialogs.py              # Dialogs for catalog, companies, holidays
    │   └── contacts_widget.py          # Inline contact list editor
    └── widgets/
        ├── table_view.py               # Generic reusable management table
        ├── colors.py                   # Per-action color assignment (by id, custom override)
        ├── layout.py                   # Screen detection and HD/2K layout presets
        ├── locations_widget.py         # Inline location list editor (name + maps_url per row)
        └── holidays_widget.py          # Inline action-specific holidays editor
```

---

## 3. Data Formats

### Training action (`data/training_actions.json`)

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
    "monday": true, "tuesday": true, "wednesday": true,
    "thursday": true, "friday": true, "saturday": false, "sunday": false
  },
  "specific_holidays": ["2026-03-20"],
  "contacts": [
    { "name": "Carlos Ruiz", "role": "Training Manager", "phone": "928 000 002", "email": "c.ruiz@company.es" }
  ],
  "bg_color": "#FDE99A",
  "text_color": "#1C1C1C",
  "rate_per_hour": 18.0,
  "withholding_pct": 15.0
}
```

| Field | Notes |
|---|---|
| `id` | Auto-assigned by GUI — never edit manually |
| `shift` | Always stored in English: `"Morning"`, `"Afternoon"`, `"Other"` |
| `start_time` / `end_time` | Decimal hours: `8.5` = 08:30, `14.5` = 14:30 |
| `daily_hours` | Calculated automatically from start/end times |
| `specific_holidays` | Dates to skip for this action only (ISO `YYYY-MM-DD`) |
| `maps_url` | Auto-filled from company location data; red background if location not in known list |
| `pending` | Shown with ⚠ icon in calendar |
| `bg_color` / `text_color` | Optional — falls back to automatic pastel palette if absent |
| `rate_per_hour` / `withholding_pct` | Stored but not yet displayed in UI (planned) |

### Course (`data/catalog.json`)

```json
{ "name": "IFCT36 - Excel Avanzado", "short_name": "Excel Av.", "total_hours": 100, "description": "" }
```

`short_name` max 8 chars — used in calendar cells and sidebar.

### Company (`data/companies.json`)

```json
[{
  "name": "CICCA (CIP)",
  "acronym": "CIP",
  "locations": [
    { "name": "Teatro - Centro Cultural Cicca", "maps_url": "https://maps.google.com/?q=..." }
  ]
}]
```

`acronym` max 8 chars. Selecting a company in the action dialog filters location dropdown automatically.

### Holidays (`data/holidays.json`)

```json
{
  "2026": [
    { "date": "2026-01-01", "name": "New Year's Day" }
  ]
}
```

Each year is a separate key. Add the key for a new year before scheduling actions in it.

---

## 4. Language System

All UI strings live in `language/translations.csv`:
- Separator: `;`
- Encoding: UTF-8 BOM (so Excel renders accented characters correctly)
- Each row is a key; each column after `key` is a language

To add a language: add a column, fill translations, save. The app detects it automatically on next launch.

> **Rule:** Every UI string must have an entry in `translations.csv`. Never hardcode display text in Python files.

---

## 5. UI Conventions

### Action buttons (Add / Edit / Delete)

Standard pattern defined in `gui/widgets/table_view.py` — replicate everywhere:

| State | `fg_color` | `text_color` | `hover_color` |
|---|---|---|---|
| Disabled (Edit) | `#BDBDBD` | `#F0F0F0` | `#2E86C1` |
| Disabled (Delete) | `#BDBDBD` | `#F0F0F0` | `#922B21` |
| Enabled (Edit) | `#2E86C1` | `#FFFFFF` | `#2E86C1` |
| Enabled (Delete) | `#C0392B` | `#FFFFFF` | `#922B21` |

- Edit and Delete start **disabled** — enabled only when a row is selected.
- After any save or delete, both buttons reset to **disabled**.
- Labels come from translation keys `panel_edit` and `panel_delete` — never hardcoded.

### Inline list editors (contacts, locations)

Used in `ContactsWidget` and `LocationsWidget`. Any new widget of this type must follow the same pattern:

- **Header row:** green `[+]` button (`fg_color="#27AE60"`, `hover_color="#1E8449"`, `width=28`, `height=28`) in column 0, followed by column labels. Appends a new empty row.
- **Data rows:** field entries + red `[✕]` button (`fg_color="#C0392B"`, `hover_color="#922B21"`, `width=28`, `height=28`) at right end.
- **Empty state:** standalone `[+]` inside the scrollable area as fallback — destroyed and replaced by the first real row when clicked.
- Column 0 of data rows must be a fixed-width invisible spacer (`CTkLabel(text="", width=28)`) to align entries with the column label, not the `[+]` button.
- Scrollable area uses `CTkScrollableFrame`.
- New rows receive focus automatically: `self.after(30, ent.focus_set)`.

### Dialogs

- All dialogs: `CTkToplevel`, `resizable(False, False)`, `grab_set()`.
- Position with `_center_on_parent(self, parent, width, height)` (defined in `tab_dialogs.py`).
- Button bar packed `side="bottom"` first, then body — bar stays pinned regardless of content height.
- First input field gets focus via `self.after(50, widget.focus_set)`.
- Save/Cancel labels: translation keys `dialog_save` and `dialog_cancel`.
- Validation errors: `messagebox.showerror` with key `error_form_title`. Required-field messages use specific keys — never the generic course-name key for non-course dialogs.
- Optional fields must not block saving.

### Color picker

`ColorPickerDialog` (in `course_dialog.py`) — Word-style swatch grid. Returns `result_bg` and `result_text`. Stored as `bg_color` / `text_color` in `training_actions.json`; takes precedence over the automatic palette in `ColorManager`.

---

## 6. Layout Presets

| Preset | Trigger | Window size | Cell size |
|---|---|---|---|
| HD | < 2560 × 1440 | 1280 × 740 | 100 × 100 px |
| 2K | ≥ 2560 × 1440 | 1800 × 1020 | 148 × 140 px |

Active preset shown in the top-right corner of the title bar. Defined in `gui/widgets/layout.py`.

---

## 7. Pending Tasks

- [ ] **PDF calendar export** — document starts with a list of free periods and mentions unconfirmed action dates
- [ ] **Economic summary panel** — gross income, withholding, net pay per action and per company
- [ ] **Annual tax report (Renta)**
