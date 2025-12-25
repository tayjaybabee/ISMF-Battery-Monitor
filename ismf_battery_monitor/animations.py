from __future__ import annotations

from importlib import resources
from threading import Event

from easy_exit_calls import ExitCallHandler
from is_matrix_forge.led_matrix.controller.helpers import find_leftmost, find_rightmost
from is_matrix_forge.led_matrix.display.animations.animation import Animation

from ismf_battery_monitor.controllers import cached_controllers
from ismf_battery_monitor._compat import CustomRootException


CONTROLLERS = cached_controllers
ECH = ExitCallHandler()


RUNNING_ANIMATION_THREADS = []


class AnimationException(CustomRootException):
    """Base exception for animation related failures."""


def _load_animation_from_package(filename: str) -> Animation:
    """Load an animation JSON file bundled with the package."""

    package = __package__
    if not package:  # pragma: no cover - defensive
        raise AnimationException('Animation resources are unavailable in standalone mode.')

    try:
        with resources.path(package, filename) as animation_path:
            return Animation.from_file(str(animation_path))
    except (FileNotFoundError, ModuleNotFoundError, AttributeError) as exc:
        raise AnimationException(f"Could not load animation '{filename}'.") from exc


class ControllerNotThreadsafeError(AnimationException):
    def __init__(self):
        super().__init__('Controller is not thread-safe.')


def ensure_thread_safety(controller):
    if not controller._thread_safe:
        raise ControllerNotThreadsafeError()
    else:
        return None


def stop_all_animations():
    for ani in RUNNING_ANIMATION_THREADS:
        stop_animation(ani)

    ECH.unregister_handler(stop_all_animations)


def stop_animation(animation):
    """

    :param animation:
    :return:
    """
    animation.stop()
    for dev in animation.devices:
        dev.clear()
    RUNNING_ANIMATION_THREADS.remove(animation)


def unplugged(controller, *, brightness: int | None = None, frame_duration: float = 0.03,
              direction: str = 'vertical_up'):
    """
    Scrolls 'UNPLUGGED' vertically up the specified LED matrix.

    Parameters:
        controller (LEDMatrixController):
            The controller to animate.

        brightness (int):
            The brightness (percentage) to use for the animation.

        frame_duration (float):
            The duration (in seconds) of each frame.
    """
    ensure_thread_safety(controller)
    controller.clear()
    prev_brightness = getattr(controller, 'brightness', None)
    if brightness is not None:
        controller.set_brightness(brightness)
    controller.scroll_text('UNPLUGGED', direction=direction, frame_duration=frame_duration)
    if prev_brightness is not None:
        controller.set_brightness(prev_brightness)


def plugged_in(controller, *, brightness: int | None = None, frame_duration: float = 0.03,
               direction: str = 'vertical_up'):
    """
    Runs a `scroll_text` animation reading "PLUGGED IN" on the given controller.

    Parameters:
         controller (LEDMatrixController):
            The controller to animate.
    """
    ensure_thread_safety(controller)
    controller.clear()
    prev_brightness = getattr(controller, 'brightness', None)
    if brightness is not None:
        controller.set_brightness(brightness)
    controller.scroll_text('PLUGGED IN', direction=direction, frame_duration=frame_duration)
    if prev_brightness is not None:
        controller.set_brightness(prev_brightness)


def _play_battery_direction_animation(controller, *, charging: bool, brightness: int | None = None,
                                      frame_duration: float = 1.0, loop: bool = False) -> None:
    ensure_thread_safety(controller)
    controller.clear()
    prev_brightness = getattr(controller, 'brightness', None)
    if brightness is not None:
        controller.set_brightness(brightness)

    filename = 'batt_up.json' if charging else 'batt_down.json'
    ani = _load_animation_from_package(filename)
    ani.set_all_frame_durations(frame_duration)
    ani.loop = loop
    ani.play(controller)

    if prev_brightness is not None:
        controller.set_brightness(prev_brightness)


def play_batt_up_animation(controller, *, brightness: int | None = None,
                           frame_duration: float = 1.0, loop: bool = False, **_: object) -> None:
    _play_battery_direction_animation(
        controller,
        charging=True,
        brightness=brightness,
        frame_duration=frame_duration,
        loop=loop
    )


def play_batt_down_animation(controller, *, brightness: int | None = None,
                             frame_duration: float = 1.0,  loop: bool = False, **_: object) -> None:
    _play_battery_direction_animation(
        controller,
        charging=False,
        brightness=brightness,
        frame_duration=frame_duration,
        loop=loop
    )


def play_batt_direction_loop(
    controller,
    *,
    charging: bool,
    stop_event: Event,
    brightness: int | None = None,
    frame_duration: float = 1.0,
) -> None:
    """
    Play battery charging/discharging animation in a stoppable loop.
    
    Note: The stop_event is only checked between animation iterations, not during
    playback itself. This means the thread cannot respond to stop requests until
    the current animation completes, which may delay shutdown by up to one full
    animation cycle.
    
    Args:
        controller: The LED matrix controller to animate
        charging: True for charging animation, False for discharging
        stop_event: Event to signal the loop to stop
        brightness: Optional brightness level for the animation
        frame_duration: Duration of each animation frame in seconds
    """
    ensure_thread_safety(controller)
    prev_brightness = getattr(controller, 'brightness', None)
    if brightness is not None:
        controller.set_brightness(brightness)

    filename = 'batt_up.json' if charging else 'batt_down.json'
    ani = _load_animation_from_package(filename)
    ani.set_all_frame_durations(frame_duration)
    ani.loop = False

    try:
        while not stop_event.is_set():
            controller.clear()
            ani.play(controller)
    finally:
        if prev_brightness is not None:
            controller.set_brightness(prev_brightness)
        controller.clear()


def drain_progress(
        controller=None,
        check_interval=3,
    ):
    if controller is None:
        controller = find_leftmost(CONTROLLERS)

    ensure_thread_safety(controller)
    controller.clear()

    ani = _load_animation_from_package('batt_down.json')

    ani.set_all_frame_durations(1)

    ani.play(controller)

    RUNNING_ANIMATION_THREADS.remove(ani)


def second_matrix_unplugged(controller=None, loop=True):
    """
    Shows a battery draining animations.

    Does the following;
        1. Loads the animation from file
        2. Sets the frame duration to 1
        3. Sets the loop to the specified value
        4. Adds the animation to the running animations list
        5. Registers the stop animation handler
        6. Plays the animation
        7. Unregisters the stop animation handler
        8. Removes the animation from the running animations list

    Parameters:
        controller (LEDMatrixController):
            The controller to animate.

        loop (bool):
            Whether to loop the animation.
    """
    if controller is None:
        controller = find_rightmost(CONTROLLERS)

    ensure_thread_safety(controller)
    controller.clear()

    ani = _load_animation_from_package('batt_down.json')

    ani.set_all_frame_durations(1)

    if loop:
        ani.loop = loop

    ani.play(controller)

    RUNNING_ANIMATION_THREADS.remove(ani)


ECH.register_handler(stop_all_animations)
