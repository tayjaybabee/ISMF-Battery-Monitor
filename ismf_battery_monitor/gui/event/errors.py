from inspyre_toolbox.exceptional import CustomRootException


class EventError(CustomRootException):
    default_message = 'An error occurred with event handling!'


class EventExistsError(EventError, ValueError):
    """
    Raised when an event already exists in the collection.

    Class Attributes:
        default_message (str):
            **Read-Only**. The default message for the error.
    """
    default_message = 'Event already exists in collection!'

    def __init__(self, message: str = None, event_name: str = None, skip_print: bool = False) -> None:
        """
        Initializes the EventExistsError.

        Parameters:
            message (Optional[str]):
                The error message to be displayed. If None, uses the default message.
        """
        if event_name is not None:
            self.default_message = f"'{event_name}' already exists in collection!"
        if message is not None:
            self.default_message = f"{self.default_message}\n\n  Additional information from caller:\n    {message}"

        super().__init__(message=self.default_message, skip_print=skip_print)


class EventLookupError(EventError, ValueError):
    """
    Raised when an event is not found in the collection.

    Class Attributes:
        default_message (str): Read-Only. The default message for the error.
    """
    default_message = 'Event not found in collection!'

    def __init__(self, message: str = None, event_name: str = None, skip_print: bool = False) -> None:
        """
        Initializes the EventLookupError.

        Parameters:
            message (Optional[str]):
                The error message to be displayed. If None, uses the default message.
        """
        if event_name is not None:
            self.default_message = f"'{event_name}' not found in collection!"
        if message is not None:
            self.default_message = f"{self.default_message}\n\n  Additional information from caller:\n    {message}"

        self.__additional_info = 'Test'

        super().__init__(message=self.default_message, skip_print=skip_print)
