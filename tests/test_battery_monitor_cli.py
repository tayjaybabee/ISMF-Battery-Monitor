from argparse import Namespace
import importlib

import pytest

cli_main = importlib.import_module('ismf_battery_monitor.scripts.battery_monitor.main')


class DummyMonitor:
    def __init__(self, poll_interval):
        self.poll_interval = poll_interval

    def start(self, *_):
        return None

    def stop(self):
        return None


def _build_args(**overrides):
    defaults = dict(
        poll_interval=1.0,
        brightness=None,
        breathing=False,
        digits_on_bottom=None,
        invert_on_overlap=True,
        left_only=False,
        right_only=False,
        show_animations=True,
        animation_brightness=50,
        frame_duration=0.5,
        scroll_direction='vertical_up',
        low_battery_threshold=20,
        critical_battery_threshold=10,
        log_file=None,
    )
    defaults.update(overrides)
    return Namespace(**defaults)


@pytest.fixture(autouse=True)
def _mock_monitor(monkeypatch):
    monkeypatch.setattr(cli_main, 'BatteryMonitor', DummyMonitor)


def test_defaults_select_right_matrix(monkeypatch):
    args = _build_args(left_only=False, right_only=False)
    cli = cli_main.BatteryMonitorCLI(args)

    controllers = ['left', 'right']
    monkeypatch.setattr(cli_main, 'find_leftmost', lambda ctrls: ctrls[0])
    monkeypatch.setattr(cli_main, 'find_rightmost', lambda ctrls: ctrls[-1])

    assert cli._filter_controllers(controllers) == ['right']


def test_batt_up_and_down_animations_based_on_charging(monkeypatch):
    args = _build_args()
    cli = cli_main.BatteryMonitorCLI(args)
    cli.controllers = ['right']
    cli.last_charging_state = False

    calls = []

    def fake_up(controller, **kwargs):
        calls.append(('up', controller, kwargs))

    def fake_down(controller, **kwargs):
        calls.append(('down', controller, kwargs))

    monkeypatch.setattr(cli_main, 'play_batt_up_animation', fake_up)
    monkeypatch.setattr(cli_main, 'play_batt_down_animation', fake_down)

    cli._maybe_run_animation(True)
    assert calls == [('up', 'right', {
        'brightness': args.animation_brightness,
        'frame_duration': args.frame_duration,
        'direction': args.scroll_direction,
    })]

    calls.clear()
    cli.last_charging_state = True
    cli._maybe_run_animation(False)
    assert calls == [('down', 'right', {
        'brightness': args.animation_brightness,
        'frame_duration': args.frame_duration,
        'direction': args.scroll_direction,
    })]

    calls.clear()
    cli.last_charging_state = False
    cli._maybe_run_animation(False)
    assert calls == []
