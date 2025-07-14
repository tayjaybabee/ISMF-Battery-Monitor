from inspyre_toolbox.exceptional import CustomRootException


class PowerMonitorGUIError(CustomRootException):
    """
    Base class for all PowerMonitor GUI errors.

    Class Attributes:
        default_message (str): Read-Only. The default message for the error.
    """
    default_message = 'An error occurred with the PowerMonitor GUI!'


class MalformedWindowError(PowerMonitorGUIError):
    """
    Raised when a window is malformed or not properly initialized.

    Class Attributes:
        default_message (str): Read-Only. The default message for the error.
    """
    default_message = 'Window is malformed or not properly initialized!'

    def __init__(self, message: str = None, **kwargs) -> None:
        """
        Initializes the MalformedWindowError.

        Parameters:
            message (Optional[str]):
                The error message to be displayed. If None, uses the default message.
        """
        if message is not None:
            self.default_message = f"{self.default_message}\n\n  Additional information from caller:\n    {message}"

        super().__init__(message=self.default_message, **kwargs)

