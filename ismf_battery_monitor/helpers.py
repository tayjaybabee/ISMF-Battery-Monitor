import psutil
from psutil import sensors_battery as get_battery_info
from .errors import BatteryStateUnknownError
from typing import Optional


def get_plugged_status(battery_info: Optional[psutil._common.sbattery] = None) -> bool:
    """
    Retrieves the plugged-in status of the system.

    Args:
        battery_info (Optional[psutil._common.sbattery]):
            The battery information to get the plugged-in status from. If not provided, it will be retrieved
            with :func:`psutil.sensors_battery`.

    Returns:
        bool:
            Whether the system is currently plugged into power.

    Raises:
        TypeError:
            If the provided `battery_info` is not a `psutil._common.sbattery` instance.

        BatteryStateUnknownError:
            If an error occurs while retrieving the plugged-in status.

    Examples:
        >>> get_plugged_status() # returns True if the system is plugged in, False otherwise

    See Also:
        - :func:`psutil.sensors_battery`
        - :exc:`BatteryStateUnknownError`
    """
    return check_plugged_in()


def check_plugged_in():
    return get_battery_info().power_plugged


def get_battery_percentage():
    return get_battery_info().percent
