from __future__ import annotations

from typing import List, Literal, Optional
from is_matrix_forge.led_matrix.controller.helpers import find_leftmost, find_rightmost
from is_matrix_forge.led_matrix.display.grid.composite import BackgroundGrid, ForegroundGrid, CompositeGrid
from is_matrix_forge.led_matrix.controller import LEDMatrixController


CONTROLLER_MAP = {
    'right': find_rightmost,
    'left':  find_leftmost
}

cached_found_controllers = []


CHARGING_ICON = [
    [0, 1, 0, 0],
    [1, 1, 1, 0],
    [0, 1, 0, 0],
]

DISCHARGING_ICON = [
    [0, 0, 1, 0],
    [0, 1, 1, 1],
    [0, 0, 1, 0],
]


def get_composite_scene_for_battery_level(
        battery_percent: float,
        *,
        digits_on_bottom: Optional[bool] = None,
        invert_on_overlap: bool = True,
        charging_state: Optional[bool] = None,
        show_charge_indicator: bool = True,
):
    """
    Returns a CompositeGrid scene for the given battery percentage.

    Parameters:
          battery_percent Union[int, float]:
              The battery percentage to display.

    Returns:
          CompositeGrid:
              The composite grid scene for the given battery percentage.
    """
    p = round(battery_percent)

    bg = BackgroundGrid()
    bg.fill_bar(p)

    fg = ForegroundGrid()

    on_bottom = p > 85 if digits_on_bottom is None else digits_on_bottom

    fg.draw_digits(p, bottom_of_grid=on_bottom)

    if show_charge_indicator:
        _apply_charge_indicator(fg, charging_state)

    return CompositeGrid(
        background=bg,
        foreground=fg,
        invert_on_overlap=invert_on_overlap,
    )


def _apply_charge_indicator(foreground: ForegroundGrid, charging_state: Optional[bool]) -> None:
    if charging_state is None:
        return

    pattern = CHARGING_ICON if charging_state else DISCHARGING_ICON
    height = len(pattern)
    width = len(pattern[0]) if pattern else 0

    for row in range(height):
        for col in range(width):
            if not pattern[row][col]:
                continue
            try:
                if col < foreground.width and row < foreground.height:  # type: ignore[attr-defined]
                    foreground._grid[col][row] = 1  # type: ignore[attr-defined]
            except AttributeError:  # pragma: no cover - fallback if grid lacks internals
                return


def draw_battery_level(
        battery_percent: float,
        grid: CompositeGrid = None,
        side: Literal['right', 'left'] = 'left',
        controllers: List[LEDMatrixController] = None,
        *,
        digits_on_bottom: Optional[bool] = None,
        invert_on_overlap: bool = True,
):
    global cached_found_controllers

    if grid is None:
        grid = get_composite_scene_for_battery_level(
            battery_percent,
            digits_on_bottom=digits_on_bottom,
            invert_on_overlap=invert_on_overlap,
        )

    if controllers is None and not cached_found_controllers:
        from is_matrix_forge.led_matrix.controller import get_controllers
        controllers = get_controllers(threaded=True, clear_on_init=True, skip_all_init_animations=True)
    elif cached_found_controllers is not None:
        controllers = cached_found_controllers

    cached_found_controllers = controllers

    controller = CONTROLLER_MAP[side.lower().strip()](controllers)
    grid.draw(controller)
