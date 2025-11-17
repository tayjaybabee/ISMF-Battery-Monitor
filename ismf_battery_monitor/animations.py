from importlib import resources

from easy_exit_calls import ExitCallHandler
from is_matrix_forge.led_matrix.controller.helpers import find_leftmost, find_rightmost
from is_matrix_forge.led_matrix.display.animations.animation import Animation
from inspyre_toolbox.exceptional import CustomRootException

from ismf_battery_monitor.controllers import cached_controllers


CONTROLLERS = cached_controllers
ECH = ExitCallHandler()


RUNNING_ANIMATION_THREADS = []


class AnimationException(CustomRootException):
    """Base exception for animation related failures."""


def _load_animation_from_package(filename: str) -> Animation:
    """Load an animation JSON file bundled with the package."""

    package = __package__
    if not package:  # pragma: no cover - defensive
        raise AnimationException(
            "Animation resources are unavailable when 'animations' is executed directly."
        )

    try:
        resource = resources.files(package) / filename
    except (FileNotFoundError, ModuleNotFoundError, AttributeError) as exc:  # pragma: no cover - defensive
        raise AnimationException(
            f"Animation file '{filename}' is not bundled with the package."
        ) from exc

    if not resource.exists():  # pragma: no cover - defensive
        raise AnimationException(f"Animation file '{filename}' could not be located.")

    with resources.as_file(resource) as animation_path:
        try:
            return Animation.from_file(str(animation_path))
        except FileNotFoundError as exc:  # pragma: no cover - defensive
            raise AnimationException(
                f"Animation file '{filename}' became unavailable during load."
            ) from exc


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


def unplugged(controller, brightness=50, frame_duration=0.03):
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
    prev_brightness = controller.brightness
    controller.set_brightness(brightness)
    controller.scroll_text('UNPLUGGED', direction='vertical_up', frame_duration=frame_duration)
    controller.set_brightness(prev_brightness)


def plugged_in(controller):
    """
    Runs a `scroll_text` animation reading "PLUGGED IN" on the given controller.

    Parameters:
         controller (LEDMatrixController):
            The controller to animate.
    """
    ensure_thread_safety(controller)
    controller.clear()
    controller.scroll_text('PLUGGED IN', direction='vertical_up', frame_duration=0.03)


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
