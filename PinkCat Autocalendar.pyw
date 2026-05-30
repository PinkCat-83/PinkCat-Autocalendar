"""
app.pyw
Entry point for the AutoCalendario desktop GUI.

Usage:
    Double-click app.pyw, or: python app.pyw

Only one instance is allowed at a time. If a second launch is attempted,
the existing window is brought to the foreground and the new process exits.
"""

import sys
import ctypes
import ctypes.wintypes

from gui.core.main_window import MainWindow

_MUTEX_NAME = "PinkCatAutoCalendar_SingleInstance"


def _acquire_mutex():
    """
    Create a named Windows mutex.
    Returns the mutex handle if this is the first instance, or None if another
    instance is already running (in which case we bring it to the foreground).
    """
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        # Bring the existing window to the foreground
        HWND_BROADCAST = 0xFFFF
        WM_USER_BRING_TO_FRONT = 0x8000 + 1  # custom message; harmless if ignored
        ctypes.windll.user32.PostMessageW(HWND_BROADCAST, WM_USER_BRING_TO_FRONT, 0, 0)
        ctypes.windll.kernel32.CloseHandle(mutex)
        return None
    return mutex


def main():
    mutex = _acquire_mutex()
    if mutex is None:
        sys.exit(0)

    try:
        app = MainWindow()
        app.mainloop()
    finally:
        ctypes.windll.kernel32.ReleaseMutex(mutex)
        ctypes.windll.kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
