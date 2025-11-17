"""
Author:
    Inspyre Softworks

Project:
    ISMF-Battery-Monitor

File:
    ismf_battery_monitor/battery/__init__.py

Description:
    Provides the BatteryStatus class, representing current battery and
    AC line conditions. If not provided, it automatically retrieves live
    system data from psutil.sensors_battery() and timestamps the snapshot.

Dependencies:
    psutil, datetime
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
import psutil


class BatteryStatus:
    """
    Represent battery and AC line status at a point in time.

    Automatically fetches from psutil if data isn’t provided and records
    a UTC timestamp marking when the snapshot was taken.
    """

    def __init__(
        self,
        ac_online: Optional[bool] = None,
        battery_percent: Optional[int] = None,
        secs_left: Optional[int] = None,
        secs_full: Optional[int] = None,
        charging: Optional[bool] = None,
        no_battery: Optional[bool] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.timestamp = timestamp or datetime.now(timezone.utc)

        if self._no_manual_data(ac_online, battery_percent, secs_left, secs_full, charging, no_battery):
            self._init_from_psutil()
        else:
            self._init_from_args(ac_online, battery_percent, secs_left, secs_full, charging, no_battery)

    # ----------------------------------------------------------------------
    # Initialization helpers
    # ----------------------------------------------------------------------

    @staticmethod
    def _no_manual_data(*values: Optional[object]) -> bool:
        """Return True if all provided values are None."""
        return all(v is None for v in values)

    def _init_from_psutil(self) -> None:
        """
        Initialize all attributes using `psutil.sensors_battery()`.
        """

        batt = psutil.sensors_battery()
        if batt is None:
            raise RuntimeError('No battery information available (no battery detected).')

        self.ac_online = bool(batt.power_plugged)
        self.battery_percent = int(batt.percent) if batt.percent is not None else None
        self.secs_left = (
            batt.secsleft
            if batt.secsleft not in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN)
            else None
        )
        self.secs_full = None  # psutil doesn’t expose full-charge estimate
        self.charging = bool(batt.power_plugged)
        self.no_battery = False

    def _init_from_args(
        self,
        ac_online:       Optional[bool],
        battery_percent: Optional[int],
        secs_left:       Optional[int],
        secs_full:       Optional[int],
        charging:        Optional[bool],
        no_battery:      Optional[bool],
    ) -> None:
        """
        Initialize all attributes from provided arguments.
        """

        self.ac_online = ac_online if ac_online is not None else False
        self.battery_percent = battery_percent
        self.secs_left = secs_left
        self.secs_full = secs_full
        self.charging = charging if charging is not None else False
        self.no_battery = no_battery if no_battery is not None else False

    # ----------------------------------------------------------------------
    # Representation
    # ----------------------------------------------------------------------

    def __str__(self) -> str:
        ts = self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        pct = self.battery_percent if self.battery_percent is not None else 'N/A'
        secs = self.secs_left or 'N/A'
        return (
            f"[{ts}] AC {'Online' if self.ac_online else 'Offline'} | "
            f"Battery {pct}% | Secs left: {secs} | "
            f"{'Charging' if self.charging else 'Not charging'}"
        )


__all__ = [
    'BatteryStatus'
]
