"""Test fixtures and stubs for third-party dependencies."""

from __future__ import annotations

import sys
import types


def _install_is_matrix_forge_stub() -> None:
    if 'is_matrix_forge' in sys.modules:
        return

    root = types.ModuleType('is_matrix_forge')

    led_matrix = types.ModuleType('is_matrix_forge.led_matrix')
    controller_mod = types.ModuleType('is_matrix_forge.led_matrix.controller')
    helpers_mod = types.ModuleType('is_matrix_forge.led_matrix.controller.helpers')
    display_mod = types.ModuleType('is_matrix_forge.led_matrix.display')
    grid_mod = types.ModuleType('is_matrix_forge.led_matrix.display.grid')
    composite_mod = types.ModuleType('is_matrix_forge.led_matrix.display.grid.composite')
    composite_utils_mod = types.ModuleType('is_matrix_forge.led_matrix.display.grid.composite.utils')
    animations_pkg = types.ModuleType('is_matrix_forge.led_matrix.display.animations')
    animation_mod = types.ModuleType('is_matrix_forge.led_matrix.display.animations.animation')

    class LEDMatrixController:
        def __init__(self, port_name: str = 'stub'):
            self.port_name = port_name
            self._thread_safe = True
            self.brightness = 50
            self.device = self

        def set_brightness(self, value):
            self.brightness = value

        def clear(self):
            return None

        def scroll_text(self, *_args, **_kwargs):
            return None

    def get_controllers(**_kwargs):
        return [LEDMatrixController('stub-left'), LEDMatrixController('stub-right')]

    def find_leftmost(controllers):
        return controllers[0] if controllers else None

    def find_rightmost(controllers):
        return controllers[-1] if controllers else None

    class BackgroundGrid:
        def fill_bar(self, _):
            return None

    class ForegroundGrid:
        def draw_digits(self, *_args, **_kwargs):
            return None

    class CompositeGrid:
        def __init__(self, background=None, foreground=None, invert_on_overlap=True):
            self.background = background
            self.foreground = foreground
            self.invert_on_overlap = invert_on_overlap

        def draw(self, controller):
            controller.clear()

    class PercentDisplayScene:
        pass

    class Animation:
        def __init__(self):
            self.devices = []
            self.loop = False

        @classmethod
        def from_file(cls, _path):
            return cls()

        def set_all_frame_durations(self, _):
            return None

        def play(self, controller):
            self.devices = [controller]

        def stop(self):
            self.devices = []

    controller_mod.LEDMatrixController = LEDMatrixController
    controller_mod.get_controllers = get_controllers
    controller_mod.helpers = helpers_mod
    helpers_mod.find_leftmost = find_leftmost
    helpers_mod.find_rightmost = find_rightmost

    composite_mod.BackgroundGrid = BackgroundGrid
    composite_mod.ForegroundGrid = ForegroundGrid
    composite_mod.CompositeGrid = CompositeGrid
    composite_utils_mod.PercentDisplayScene = PercentDisplayScene

    animation_mod.Animation = Animation

    root.led_matrix = led_matrix
    led_matrix.controller = controller_mod
    led_matrix.controller.helpers = helpers_mod
    led_matrix.display = display_mod
    display_mod.grid = grid_mod
    grid_mod.composite = composite_mod
    grid_mod.composite.utils = composite_utils_mod
    display_mod.animations = animations_pkg
    animations_pkg.animation = animation_mod

    sys.modules['is_matrix_forge'] = root
    sys.modules['is_matrix_forge.led_matrix'] = led_matrix
    sys.modules['is_matrix_forge.led_matrix.controller'] = controller_mod
    sys.modules['is_matrix_forge.led_matrix.controller.helpers'] = helpers_mod
    sys.modules['is_matrix_forge.led_matrix.display'] = display_mod
    sys.modules['is_matrix_forge.led_matrix.display.grid'] = grid_mod
    sys.modules['is_matrix_forge.led_matrix.display.grid.composite'] = composite_mod
    sys.modules['is_matrix_forge.led_matrix.display.grid.composite.utils'] = composite_utils_mod
    sys.modules['is_matrix_forge.led_matrix.display.animations'] = animations_pkg
    sys.modules['is_matrix_forge.led_matrix.display.animations.animation'] = animation_mod


def pytest_configure(config):  # pragma: no cover - pytest hook
    _install_is_matrix_forge_stub()
