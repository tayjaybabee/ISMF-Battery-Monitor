from inspy_logger import InspyLogger, Loggable


ROOT_LOGGER = InspyLogger('ISMFBatteryMonitor', console_level='info', no_file_logging=True)

__all__ = [
    'Loggable',
    'ROOT_LOGGER'
]
""" List of exported classes and functions for exposure to the public. """
