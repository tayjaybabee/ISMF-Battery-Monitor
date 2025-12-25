from argparse import Namespace
import importlib
import threading

import pytest

cli_main = importlib.import_module('ismf_battery_monitor.scripts.battery_monitor.main')


class DummyController:
    def __init__(self, name):
        self.name = name
        self._thread_safe = True

    def clear(self):
        return None

    def __repr__(self):  # pragma: no cover - helps with assertion diffs
        return f'<DummyController {self.name}>'


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


def _mock_controller_cache(monkeypatch, controllers):
    class DummyCache:
        def get(self):
            return controllers

    monkeypatch.setattr(cli_main, 'get_cached_controllers', lambda: DummyCache())


def test_defaults_use_right_for_display_and_left_for_animation(monkeypatch):
    left = DummyController('left')
    right = DummyController('right')
    _mock_controller_cache(monkeypatch, [left, right])
    monkeypatch.setattr(cli_main, 'find_leftmost', lambda ctrls: ctrls[0])
    monkeypatch.setattr(cli_main, 'find_rightmost', lambda ctrls: ctrls[1])

    args = _build_args()
    cli = cli_main.BatteryMonitorCLI(args)

    controllers = cli._prepare_controllers()

    assert cli.display_controller is right
    assert cli.animation_controller is left
    assert set(controllers) == {left, right}


def test_draw_scene_omits_charge_indicator(monkeypatch):
    args = _build_args()
    cli = cli_main.BatteryMonitorCLI(args)
    cli.display_controller = DummyController('display')

    captured = {}

    def fake_scene_factory(battery_percent, *, charging_state, show_charge_indicator, **_):
        captured['charging_state'] = charging_state
        captured['show_charge_indicator'] = show_charge_indicator
        captured['battery_percent'] = battery_percent

        class DummyScene:
            def draw(self, controller):
                captured['controller'] = controller

        return DummyScene()

    monkeypatch.setattr(cli_main, 'get_composite_scene_for_battery_level', fake_scene_factory)

    cli._draw_scene(42)

    assert captured == {
        'battery_percent': 42,
        'charging_state': None,
        'show_charge_indicator': False,
        'controller': cli.display_controller,
    }


def test_animation_loop_runs_on_left_matrix(monkeypatch):
    left = DummyController('left')
    args = _build_args()
    cli = cli_main.BatteryMonitorCLI(args)
    cli.animation_controller = left
    cli.animation_charging_state = True

    calls = []

    def fake_up(controller, **kwargs):
        calls.append(('up', controller, kwargs))
        cli.stop_event.set()

    monkeypatch.setattr(cli_main, 'play_batt_up_animation', fake_up)
    monkeypatch.setattr(cli_main, 'play_batt_down_animation', lambda *_, **__: None)

    thread = threading.Thread(target=cli._animation_loop)
    thread.start()
    thread.join(timeout=2)

    assert calls == [('up', left, {
        'brightness': args.animation_brightness,
        'frame_duration': args.frame_duration,
        'direction': args.scroll_direction,
    })]
