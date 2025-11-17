from typing import List, Literal, Optional
from is_matrix_forge.led_matrix.controller.helpers import find_leftmost, find_rightmost
from is_matrix_forge.led_matrix.display.grid.composite import BackgroundGrid, ForegroundGrid, CompositeGrid
from is_matrix_forge.led_matrix.controller import LEDMatrixController


CONTROLLER_MAP = {
    'right': find_rightmost,
    'left':  find_leftmost
}

cached_found_controllers = []


def get_composite_scene_for_battery_level(
        battery_percent: float,
        *,
        digits_on_bottom: Optional[bool] = None,
        invert_on_overlap: bool = True,
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

    if digits_on_bottom is None:
        on_bottom = p > 85
    else:
        on_bottom = digits_on_bottom

    fg.draw_digits(p, bottom_of_grid=on_bottom)

    return CompositeGrid(
        background=bg,
        foreground=fg,
        invert_on_overlap=invert_on_overlap,
    )


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
