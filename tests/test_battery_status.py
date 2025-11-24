from datetime import datetime, timezone
from types import SimpleNamespace

import psutil
import pytest

from ismf_battery_monitor.battery import BatteryStatus


def test_manual_battery_status_fields():
    ts = datetime.now(timezone.utc)
    status = BatteryStatus(
        ac_online=True,
        battery_percent=42,
        secs_left=3600,
        secs_full=7200,
        charging=True,
        no_battery=False,
        timestamp=ts,
    )

    assert status.timestamp is ts
    assert status.ac_online is True
    assert status.battery_percent == 42
    assert status.secs_left == 3600
    assert status.charging is True
    assert status.no_battery is False


def test_manual_status_allows_missing_percentage():
    status = BatteryStatus(
        ac_online=False,
        battery_percent=None,
        charging=False,
        no_battery=True,
    )

    assert status.battery_percent is None
    assert status.no_battery is True


def test_battery_status_defaults_timestamp():
    before = datetime.now(timezone.utc)
    status = BatteryStatus(ac_online=True)

    assert status.timestamp >= before


def test_battery_status_zero_percent():
    status = BatteryStatus(
        ac_online=False,
        battery_percent=0,
        charging=False,
        no_battery=False,
    )

    assert status.battery_percent == 0
    assert status.no_battery is False


def test_battery_status_hundred_percent():
    status = BatteryStatus(
        ac_online=True,
        battery_percent=100,
        charging=True,
        no_battery=False,
    )

    assert status.battery_percent == 100
    assert status.no_battery is False


def test_battery_status_negative_percent():
    status = BatteryStatus(
        ac_online=False,
        battery_percent=-10,
        charging=False,
        no_battery=False,
    )

    assert status.battery_percent == -10
    assert status.no_battery is False


def test_status_from_psutil(monkeypatch):
    fake_batt = SimpleNamespace(
        power_plugged=True,
        percent=75,
        secsleft=120,
    )

    monkeypatch.setattr('ismf_battery_monitor.battery.psutil.sensors_battery', lambda: fake_batt)

    status = BatteryStatus()
    assert status.ac_online is True
    assert status.battery_percent == 75
    assert status.secs_left == 120


def test_status_from_psutil_unlimited(monkeypatch):
    fake_batt = SimpleNamespace(
        power_plugged=True,
        percent=80,
        secsleft=psutil.POWER_TIME_UNLIMITED,
    )

    monkeypatch.setattr('ismf_battery_monitor.battery.psutil.sensors_battery', lambda: fake_batt)

    status = BatteryStatus()
    assert status.secs_left is None


def test_status_from_psutil_unknown(monkeypatch):
    fake_batt = SimpleNamespace(
        power_plugged=False,
        percent=60,
        secsleft=psutil.POWER_TIME_UNKNOWN,
    )

    monkeypatch.setattr('ismf_battery_monitor.battery.psutil.sensors_battery', lambda: fake_batt)

    status = BatteryStatus()
    assert status.secs_left is None


def test_status_from_psutil_none(monkeypatch):
    monkeypatch.setattr('ismf_battery_monitor.battery.psutil.sensors_battery', lambda: None)

    with pytest.raises(RuntimeError):
        BatteryStatus()


def test_status_from_psutil_invalid(monkeypatch):
    class CorruptedBattery:
        secsleft = 'not_a_number'

    monkeypatch.setattr('ismf_battery_monitor.battery.psutil.sensors_battery', lambda: CorruptedBattery())

    status = BatteryStatus()

    assert status.ac_online is None
    assert status.battery_percent is None
    assert status.secs_left is None
