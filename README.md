# 🗓️ PinkCat AutoCalendar

Desktop application for generating annual teaching calendars.  
Originally built in Excel/VBA — rebuilt in Python with a full GUI.

---

## What is this?

PinkCat AutoCalendar manages the scheduling of training actions across the year: what courses are being taught, for which companies, at which locations, and on which dates. It generates a visual monthly calendar, detects scheduling conflicts, and handles holidays, shifts, and action-specific non-teaching days automatically.

---

## Key Concepts

| Term | Definition |
|---|---|
| **Course** | A reusable course type in the catalog: name, short name, total hours, description. No dates or company. |
| **Company** | The organization commissioning a training action. Has a name, acronym, and a list of teaching locations. |
| **Training action** | A concrete instance of a Course delivered by a Company, at a specific location, on specific dates and times. |

- A **Course** is the *what*. Lives in `catalog.json`.
- A **Company** is the *who*. Lives in `companies.json`.
- A **Training action** is the *when, where, and for whom*. Lives in `training_actions.json`.

---

## Features

- **Monthly calendar view** — color-coded by training action, navigable by month and year
- **Automatic schedule generation** — skips weekends, public holidays, and action-specific non-teaching dates
- **Conflict detection** — warns if two training actions share the same day and shift
- **Multi-language UI** — switch language at runtime; preference saved across sessions
- **Auto layout detection** — applies HD or 2K preset based on screen resolution at startup
- **Training action management** — add, edit, and delete directly from the GUI
- **Company locations** — each company holds its own location list with optional Google Maps URLs
- **Google Maps integration** — opens location in browser via the 🗺 button
- **Custom action colors** — Word-style color picker per action; falls back to automatic pastel palette
- **Pending confirmation flag** — unconfirmed actions shown with a ⚠ icon in the calendar
- **Contacts** — multiple contacts (name, role, phone, email) per training action
- **Action-specific holidays** — non-teaching dates managed per action via a calendar picker
- **Decimal hours support** — e.g. 2.5 h/day works correctly
- **JSON storage** — `training_actions.json` as input; `calendar_YYYY.json` as output per year
- **Single instance enforcement** — only one instance can run at a time (Windows mutex)

---

## Annual Workflow

1. Add the year's training actions via the GUI or by editing `data/training_actions.json`.
2. Verify `data/holidays.json` has entries for the new year.
3. Launch the app and navigate the months to confirm the schedule.
4. The generated calendar is saved automatically to `data/calendar_YYYY.json`.

---

## Requirements

- Python 3.11+
- `customtkinter`
- `pillow`

```bash
pip install customtkinter pillow
```

No other third-party dependencies.

---

## Planned Features

- Economic summary panel (gross income, withholding, net pay — per action and per company)
- Annual income tax report (Renta)
- PDF calendar export with a list of free periods and unconfirmed action dates

---

## Technical Documentation

For architecture, data formats, UI conventions, and AI instructions, see the **[Technical README](./README_TECH.md)**.
