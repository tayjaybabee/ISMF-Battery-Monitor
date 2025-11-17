import sys
from threading import Event
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(sys.platform.startswith('win'), reason='Real BatteryMonitor exists on Windows')
def test_monitor_not_implemented_off_windows():
    from ismf_battery_monitor.monitor import BatteryMonitor as DispatchBatteryMonitor

    with pytest.raises(NotImplementedError):
        DispatchBatteryMonitor()


@pytest.mark.parametrize(
    (
        'initial_pct',
        'ac_line_status',
        'battery_flag',
        'expected_ac_online',
        'expected_charging',
    ),
    [
        (0, 0, 0, False, False),
        (10, 0, 0x00, False, False),
        (25, 1, 0x08, True, True),
        (85, 1, 0x08, True, True),
    ],
)
def test_windows_monitor_invokes_callback(
    monkeypatch,
    initial_pct,
    ac_line_status,
    battery_flag,
    expected_ac_online,
    expected_charging,
):
    from ismf_battery_monitor.monitor.windows import BatteryMonitor

    snapshots = [
        SimpleNamespace(
            ACLineStatus=ac_line_status,
            BatteryFlag=battery_flag,
            BatteryLifePercent=initial_pct,
            BatteryLifeTime=3600,
            BatteryFullLifeTime=7200,
        ),
    ]
    iterator = iter(snapshots)

    def fake_status():
        try:
            return next(iterator)
        except StopIteration:
            return snapshots[-1]

    monkeypatch.setattr('ismf_battery_monitor.monitor.windows._get_system_power_status', fake_status)

    event = Event()
    results = []

    monitor = BatteryMonitor(poll_interval=0.01)

    def callback(status):
        results.append(status)
        event.set()

    monitor.start(callback)
    assert event.wait(1.0)
    monitor.stop()

    assert results
    assert results[0].battery_percent == initial_pct
    assert results[0].ac_online is expected_ac_online
    assert results[0].charging is expected_charging
