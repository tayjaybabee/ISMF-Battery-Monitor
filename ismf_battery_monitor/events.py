from is_matrix_forge.log_engine import ROOT_LOGGER
from .monitor import PowerMonitor
from .helpers import get_battery_percentage

MOD_LOGGER = ROOT_LOGGER.get_child('monitor.events')


def event_to_bool(event: str) -> bool:
    """
    Converts an event to a boolean.

    Parameters:
        event:
            The string representation of the event to convert.

    Returns:
        bool:
            The converted boolean value.

    Raises:
        ValueError:
            If the event is not a valid boolean value.

    Examples:
        >>> event_to_bool('true')
        True
        >>> event_to_bool('false')
        False
        >>> event_to_bool('invalid')
        Traceback (most recent call last):
            ...
        ValueError: invalid is not a valid boolean value.
    """
    log = MOD_LOGGER.get_child('event_to_bool')
    event = event.lower().strip()
    log.debug(f'Received {event}...')

    if event in ['on', 'true', 'plugged']:
        log.debug(f'Event "{event}" determined to mean "plugged"/True')
        return True
    elif event in ['off', 'false', 'unplugged']:
        log.debug(f'Event "{event}" determined to mean "unplugged"/False')
        return False
    else:
        log.error('Unable to determine event meaning')
        raise ValueError(f'{event} is not a valid boolean value.')


def __handle_device_plugged_in(power_monitor):
    pm = power_monitor
    log = MOD_LOGGER.get_child('__handle_device_plugged_in')
    log.debug(f'Raw value from `PowerMonitor().plugged_in`: {pm.plugged_in}')
    log.debug(
        f'Plugged in: {pm.plugged_in} '
        f'Controller Animating: {pm.controller.is_animating}'
        f'Last State: {pm.last_state}'
    )
    if pm.plugged_in and not pm.controller.is_animating and (not pm.last_state or pm.last_state is None):
        pm.notify('plugged')
        pm.controller.clear()
        pm._last_state = True


def __handle_device_unplugged(power_monitor):
    pm = power_monitor
    if pm.unplugged and not pm.controller.is_animating and (pm.last_state or pm.last_state is None):
        pm.notify('unplugged')
        pm.controller.clear()
        pm._last_state = False

    pm.controller.draw_percentage(get_battery_percentage())


def handle_event(event: str, power_monitor: PowerMonitor):
    log = MOD_LOGGER.get_child('handle_event')
    log.debug(f'Handling {event}...')
    log.debug(f'PowerMonitor: {power_monitor}')
    log.debug(f'PowerMonitor.last_state: {power_monitor.last_state}')
    log.debug(f'PowerMonitor.plugged_in: {power_monitor.plugged_in}')
    event = event_to_bool(event)

    pm = power_monitor

    if event:
        __handle_device_plugged_in(pm)
    else:
        __handle_device_unplugged(pm)
