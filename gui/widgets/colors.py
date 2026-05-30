"""
colors.py
Assigns a stable color to each course for display in the calendar grid.
Colors are assigned by position in training_actions.json at session start (using the
unique 'id' field), so the same course instance always gets the same color
regardless of render order or shared names.
"""

PALETTE_LIGHT = [
    "#F9A8D4",  # Pink / Fuchsia pastel
    "#A7D7A8",  # Green pastel
    "#A3B8E8",  # Blue (navy/royal) pastel
    "#FDE99A",  # Yellow pastel
    "#F4A9A8",  # Red pastel
    "#FDCBA0",  # Orange pastel
    "#A8E4F0",  # Cyan / Sky Blue pastel
    "#D4B8F0",  # Lilac pastel
]

_TEXT_COLORS = ["#1C1C1C"] * len(PALETTE_LIGHT)


class ColorManager:
    """
    Assigns and remembers a color index per course *id*.
    Falls back to course name if no id is present (backwards compatibility).
    Call pre_assign() at startup and after any course list change
    so that colors are stable across the whole session.
    """

    def __init__(self):
        self._map: dict[str, int] = {}   # id → palette index
        self._next = 0

    def _key(self, course: dict) -> str:
        """Returns the stable key for a course dict: id if present, else name."""
        return course.get("id") or course.get("name", "")

    def pre_assign(self, courses: list[dict]) -> None:
        """
        Assign colors to all courses in JSON order.
        Already-assigned keys are skipped, so re-calling is safe
        and won't shift existing assignments.
        """
        for course in courses:
            k = self._key(course)
            if k and k not in self._map:
                self._map[k] = self._next % len(PALETTE_LIGHT)
                self._next += 1

    def bg_color(self, course_id_or_name: str) -> str:
        """Look up by id or name string directly."""
        if course_id_or_name not in self._map:
            self._map[course_id_or_name] = self._next % len(PALETTE_LIGHT)
            self._next += 1
        return PALETTE_LIGHT[self._map[course_id_or_name]]

    def bg_color_for(self, course: dict) -> str:
        """Return custom color if set, else palette color."""
        if course.get("bg_color"):
            return course["bg_color"]
        k = self._key(course)
        if k not in self._map:
            self._map[k] = self._next % len(PALETTE_LIGHT)
            self._next += 1
        return PALETTE_LIGHT[self._map[k]]

    def text_color_for(self, course: dict) -> str:
        """Return custom text color if set, else default dark."""
        if course.get("text_color"):
            return course["text_color"]
        k = self._key(course)
        if k not in self._map:
            self.bg_color_for(course)
        return _TEXT_COLORS[self._map[k]]

    # ── Legacy helpers kept for call-sites that pass a name string ────────────
    def text_color(self, course_name: str) -> str:
        if course_name not in self._map:
            self.bg_color(course_name)
        return _TEXT_COLORS[self._map[course_name]]

    def reset(self):
        """Clears all color assignments. Avoid calling during a session."""
        self._map.clear()
        self._next = 0
