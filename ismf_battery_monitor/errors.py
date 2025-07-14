from inspyre_toolbox.exceptional import CustomRootException


class PowerMonitorError(CustomRootException):
    """
    Base class for all PowerMonitor errors.

    Class Attributes:
        default_message (str): Read-Only. The default message for the error.
    """
    default_message = 'An error occurred while monitoring the battery!'


class PowerMonitorNotRunningError(PowerMonitorError):
    """
    Raised when a method is called on a PowerMonitor instance that is not running, but should be to perform the action.
    """
    def __init__(self, message = None):
        msg = 'The PowerMonitor is not running, can not perform action on a non-running instance!'
        if message is not None:
            msg += f'\n\nAdditional information from caller: {message}'

        super().__init__(msg)


class BatteryStateUnknownError(PowerMonitorError):
    """
    Raised when the state of the battery cannot be determined.
    """
    def __init__(self, message = None):
        msg = 'The state of the battery cannot be determined!'
        if message is not None:
            msg += f'\n\nAdditional information from caller: {message}'

        super().__init__(msg)
