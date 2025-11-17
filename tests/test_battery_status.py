from datetime import datetime, timezone
from types import SimpleNamespace

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
