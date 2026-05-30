"""
calendar_gen.py
Core calendar generation logic.
Expands each course into individual teaching days, skipping weekends,
public holidays, and course-specific non-teaching dates.
Also computes economic data per course.
"""

import math
from datetime import date, timedelta

from src.holidays import load_holidays
from src.economic import CourseSummary, calculate_annual_summary


# Weekday names as used in the course JSON (Monday = index 0)
_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _is_teaching_day(day: date, teaching_days: dict[str, bool]) -> bool:
    """Returns True if the weekday of 'day' is marked as a teaching day."""
    weekday_name = _WEEKDAYS[day.weekday()]  # weekday(): 0=Monday … 6=Sunday
    return teaching_days.get(weekday_name, False)


def _total_days_needed(total_hours: float, daily_hours: float) -> int:
    """Number of teaching days required to cover the course's total hours."""
    return math.ceil(total_hours / daily_hours)


def _last_day_hours(total_hours: float, daily_hours: float, total_days: int) -> float:
    """Actual hours taught on the last day (may be less than daily_hours)."""
    return round(total_hours - daily_hours * (total_days - 1), 4)


def generate_calendar(courses: list[dict], holidays: set[date]) -> dict:
    """
    Iterates over all courses and generates the full teaching calendar.

    Returns a dict with:
      - "courses": list of courses with their expanded teaching days
      - "economic_summary": annual totals and per-company breakdown
      - "conflicts": list of detected scheduling overlaps (same day + shift)
    """
    # Occupation index for conflict detection: (date, shift) -> course name
    occupation: dict[tuple[date, str], str] = {}
    conflicts: list[dict] = []
    generated_actions: list[dict] = []
    economic_summaries: list[CourseSummary] = []

    for course in courses:
        name = course.get("name", "Unnamed")
        shift = course.get("shift", "Morning")
        total_hours: float = course.get("total_hours", 0)
        daily_hours: float = course.get("daily_hours", 0)
        start_date = date.fromisoformat(course["start_date"])
        teaching_days: dict[str, bool] = course.get("teaching_days", {})
        specific_holidays: set[date] = {
            date.fromisoformat(d) for d in course.get("specific_holidays", [])
        }
        rate_per_hour: float = course.get("rate_per_hour", 0.0)
        withholding_pct: float = course.get("withholding_pct", 0.0)
        company: str = course.get("company", "")

        # Basic validation
        if daily_hours <= 0:
            print(f"[ERROR] Course '{name}': daily_hours must be > 0. Skipped.")
            continue
        if not any(teaching_days.values()):
            print(f"[ERROR] Course '{name}': no teaching days defined. Skipped.")
            continue

        total_days = _total_days_needed(total_hours, daily_hours)
        last_day_hrs = _last_day_hours(total_hours, daily_hours, total_days)

        days_generated: list[dict] = []
        current_date = start_date
        days_placed = 0

        while days_placed < total_days:
            is_teaching = _is_teaching_day(current_date, teaching_days)
            is_public_holiday = current_date in holidays
            is_specific_holiday = current_date in specific_holidays

            if is_teaching and not is_public_holiday and not is_specific_holiday:
                # Check for scheduling conflict
                key = (current_date, shift)
                if key in occupation:
                    conflicts.append({
                        "date": current_date,
                        "shift": shift,
                        "existing_course": occupation[key],
                        "new_course": name,
                    })
                    print(
                        f"[CONFLICT] {current_date} ({shift}): "
                        f"'{occupation[key]}' vs '{name}'"
                    )
                else:
                    occupation[key] = name

                # Hours for this day (last day may be partial)
                is_last = (days_placed == total_days - 1)
                hours_today = last_day_hrs if is_last else daily_hours


                print("GEN confirmed:", course.get("confirmed"), "->", course.get("id"))   
                 
                days_generated.append({
                    "id": course.get("id", ""),
                    "confirmed": course.get("confirmed", True),
                    "date": current_date,
                    "weekday": _WEEKDAYS[current_date.weekday()].capitalize(),
                    "shift": shift,
                    "hours": hours_today,
                    "location": course.get("location", ""),
                    "start_time": course.get("start_time"),
                    "end_time": course.get("end_time"),
                })
                days_placed += 1
                
                
                
            current_date += timedelta(days=1)

        end_date = current_date - timedelta(days=1)

        # Economic summary for this course
        actual_hours = daily_hours * (total_days - 1) + last_day_hrs
        summary = CourseSummary(
            name=name,
            company=company,
            hours_taught=actual_hours,
            rate_per_hour=rate_per_hour,
            withholding_pct=withholding_pct,
        )
        economic_summaries.append(summary)

        generated_actions.append({
            "id": course.get("id", ""),
            "name": name,
            "company": company,
            "shift": shift,
            "location": course.get("location", ""),
            "start_time": course.get("start_time"),
            "end_time": course.get("end_time"),
            "daily_hours": daily_hours,
            "total_hours": total_hours,
            "start_date": start_date,
            "end_date": end_date,
            "teaching_days_config": teaching_days,
            "specific_holidays": sorted(specific_holidays),
            "economic": summary.to_dict(),
            "days": days_generated,
        })

    annual_summary = calculate_annual_summary(economic_summaries)

    return {
        "courses": generated_actions,
        "economic_summary": annual_summary,
        "conflicts": conflicts,
    }
