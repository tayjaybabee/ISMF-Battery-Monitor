from __future__ import annotations

import ctypes
from ctypes import wintypes
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from ismf_battery_monitor.battery import BatteryStatus
from ismf_battery_monitor.controllers import get_cached_controllers  # lazy accessor
from is_matrix_forge.led_matrix.controller.helpers import find_leftmost, find_rightmost


# ----------------------------- Win32 Structures & Constants -----------------------------

class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus',        wintypes.BYTE),
        ('BatteryFlag',         wintypes.BYTE),
        ('BatteryLifePercent',  wintypes.BYTE),
        ('SystemStatusFlag',    wintypes.BYTE),
        ('BatteryLifeTime',     wintypes.DWORD),
        ('BatteryFullLifeTime', wintypes.DWORD),
    ]


# ACLineStatus
AC_OFFLINE = 0
AC_ONLINE  = 1
AC_UNKNOWN = 255

# BatteryFlag bitfield
BF_HIGH        = 0x01
BF_LOW         = 0x02
BF_CRITICAL    = 0x04
BF_CHARGING    = 0x08
BF_NO_BATTERY  = 0x80
BF_UNKNOWN     = 0xFF  # returned when status cannot be determined

# Sentinels
PCT_UNKNOWN   = 255
TIME_UNKNOWN  = 0xFFFFFFFF


def _get_system_power_status() -> Optional[SYSTEM_POWER_STATUS]:
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    fn = kernel32.GetSystemPowerStatus
    fn.argtypes = [ctypes.POINTER(SYSTEM_POWER_STATUS)]
    fn.restype = wintypes.BOOL
    sps = SYSTEM_POWER_STATUS()
    ok = fn(ctypes.byref(sps))
    return sps if ok else None


# --------------------------------- Lazy controller helpers ---------------------------------

def _resolve_left_right():
    controllers = get_cached_controllers()
    if len(controllers) == 0:
        return None, None
    left  = find_leftmost(controllers.get())
    right = find_rightmost(controllers.get())
    return left, right


# ------------------------------------- Battery Monitor -------------------------------------

class BatteryMonitor:
    """
    Monitors battery status on Windows via GetSystemPowerStatus.

    Parameters:
        poll_interval (float):
            Seconds between polls (default: 1.0).
        debounce_secs (float):
            Minimum seconds between callback invocations even if state is noisy (default: 0).

    Methods:
        start(callback):
            Start background polling; callback receives BatteryStatus on meaningful change.

        stop():
            Stop the background thread.

        last_status:
            Most recent BatteryStatus (or None).

        plugged_in (Optional[bool]):
            Is the AC line plugged in?

        percent_charged (Optional[int]):


    Notes:
        - Controllers (LEFT/RIGHT) are resolved lazily to avoid import-time side effects.
        - The callback runs on the monitor thread; keep it fast or offload work.
    """

    def __init__(self, poll_interval: float = 1.0, debounce_secs: float = 0.0):
        self.poll_interval = poll_interval
        self.debounce_secs = debounce_secs

        self._stop_event                           = threading.Event()
        self._thread: Optional[threading.Thread]   = None
        self._last_status: Optional[BatteryStatus] = None
        self._last_emit_ts: float                  = 0.0

        self._left_matrix  = None
        self._right_matrix = None

        # Resolve matrices lazily (won't enumerate on import)
        self._left_matrix, self._right_matrix = _resolve_left_right()

    # ---------- Public API ----------

    @property
    def last_status(self) -> Optional[BatteryStatus]:
        return self._last_status

    @property
    def percent_charged(self) -> Optional[int]:
        return None if self._last_status is None else self._last_status.battery_percent

    @property
    def plugged_in(self) -> Optional[bool]:
        return None if self._last_status is None else self._last_status.ac_online

    def status(self) -> Optional[BatteryStatus]:
        return self._read_status()

    def start(self, callback: Callable[[BatteryStatus], None]) -> None:
        '''
        Start monitoring in a background thread. The callback is called with a new
        BatteryStatus when a meaningful change is detected.
        '''
        # Reset state in case of reuse
        self._stop_event.clear()

        def run_loop():
            while not self._stop_event.is_set():
                status = self._read_status()
                if status and self._should_emit(status):
                    try:
                        callback(status)
                    except Exception as e:
                        # Don’t let a user callback kill the monitor
                        print(f'[BatteryMonitor] callback error: {e}')
                    self._last_status = status
                    self._last_emit_ts = time.time()
                time.sleep(self.poll_interval)

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        '''Stop monitoring and join the thread.'''
        if self._thread:
            self._stop_event.set()
            self._thread.join()
            self._thread = None

    # Context manager sugar
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

    # ---------- Internals ----------

    def _read_status(self) -> Optional[BatteryStatus]:
        sps = _get_system_power_status()
        if sps is None:
            return None

        ac_online = (sps.ACLineStatus == AC_ONLINE)
        no_battery = (sps.BatteryFlag & BF_NO_BATTERY) != 0

        pct = None if sps.BatteryLifePercent == PCT_UNKNOWN else int(sps.BatteryLifePercent)
        secs_left = None if sps.BatteryLifeTime == TIME_UNKNOWN else int(sps.BatteryLifeTime)
        secs_full = None if sps.BatteryFullLifeTime == TIME_UNKNOWN else int(sps.BatteryFullLifeTime)
        charging = (sps.BatteryFlag & BF_CHARGING) != 0

        # Timestamp the snapshot explicitly (use UTC)
        snap = BatteryStatus(
            ac_online=ac_online,
            battery_percent=pct,
            secs_left=secs_left,
            secs_full=secs_full,
            charging=charging,
            no_battery=no_battery,
            timestamp=datetime.now(timezone.utc),
        )
        return snap

    def _should_emit(self, curr: BatteryStatus) -> bool:
        # Debounce window
        if self.debounce_secs > 0 and (time.time() - self._last_emit_ts) < self.debounce_secs:
            return False

        prev = self._last_status
        if prev is None:
            return True

        # Meaningful deltas
        if curr.ac_online != prev.ac_online:
            return True
        if curr.charging != prev.charging:
            return True

        # Percentage changed by >= 1 (ignore None)
        if curr.battery_percent is not None and prev.battery_percent is not None:
            if abs(curr.battery_percent - prev.battery_percent) >= 1:
                return True

        # If secs_left becomes known/unknown or changes a lot (>= 60s), emit
        if (curr.secs_left is None) != (prev.secs_left is None):
            return True
        if curr.secs_left is not None and prev.secs_left is not None:
            if abs(curr.secs_left - prev.secs_left) >= 60:
                return True

        return False


__all__ = ['BatteryMonitor']
