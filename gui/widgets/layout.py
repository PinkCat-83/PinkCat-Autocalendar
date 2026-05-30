"""
layout.py
Detects screen resolution and returns the appropriate fixed layout config.
Supports HD (1920x1080) and 2K (2560x1440) presets.
"""

import tkinter as tk


# ── Layout presets ────────────────────────────────────────────────────────────

LAYOUT_HD = {
    "name": "HD",
    "window_width": 1280,
    "window_height": 740,
    "cell_width": 100,
    "cell_height": 100,
    "cell_font_size": 8,
    "day_num_font_size": 13,
    "header_font_size": 13,
    "sidebar_width": 280,
    "top_bar_height": 52,
    "title_font_size": 16,
    "nav_font_size": 14,
    "card_font_size": 11,
    "card_detail_font_size": 10,
}

LAYOUT_2K = {
    "name": "2K",
    "window_width": 1800,
    "window_height": 1020,
    "cell_width": 148,
    "cell_height": 140,
    "cell_font_size": 10,
    "day_num_font_size": 17,
    "header_font_size": 16,
    "sidebar_width": 360,
    "top_bar_height": 64,
    "title_font_size": 22,
    "nav_font_size": 17,
    "card_font_size": 13,
    "card_detail_font_size": 12,
}


def detect_layout() -> dict:
    """
    Creates a temporary hidden Tk root to read screen dimensions,
    then returns the most appropriate layout preset.
    2K threshold: screen width >= 2560 or height >= 1440.
    """
    root = tk.Tk()
    root.withdraw()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.destroy()

    print(f"[Layout] Screen detected: {screen_w}x{screen_h}")

    if screen_w >= 2560 or screen_h >= 1440:
        print(f"[Layout] Using 2K preset.")
        return LAYOUT_2K
    else:
        print(f"[Layout] Using HD preset.")
        return LAYOUT_HD
