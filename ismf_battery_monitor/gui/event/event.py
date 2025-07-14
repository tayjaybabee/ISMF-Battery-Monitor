from __future__ import annotations

from typing import Optional
from is_matrix_forge.log_engine import ROOT_LOGGER as PARENT_LOGGER, Loggable
from dataclasses import dataclass, field


__initialized = False


if __initialized:
    from ..windows.base import WindowBase


MOD_LOGGER = PARENT_LOGGER.get_child('monitor.gui.event.event')


@dataclass
class ElementArgMap():
    pos_args: tuple = field(default_factory=tuple)
    kw_args: dict = field(default_factory=dict)


class Event(Loggable):
    def __init__(
            self,
            key: Optional[str],
            window: WindowBase,
            callback: Optional[callable] = None,
            element_arg_map: Optional[dict] = None,

    ) -> None:
        """
        Initializes the Event.

        Parameters:
            key (str):
                The unique string identifier for the event.

            callback (Optional[callable]):
                The callable to be called when the event is triggered.

            pass_window_values (bool):
                Whether to pass window values to the callback function.
        """
        super().__init__(MOD_LOGGER)
        self.__callback      = None
        self.__failed        = 0
        self.__initialized   = False
        self.__key           = None
        self.__times_handled = 0

        self.key = key

        if callback is not None:
            self.callback = callback

        self.__initialized = True

    @property
    def callback(self) -> callable:
        """
        The callback function for the event.

        The callback function is called whenever the event is triggered. The
        function should accept zero or more arguments.

        Returns:
            callable:
                The callback function for the event.

        Raises:
            TypeError:
                If the callback is not callable.

        """
        return self.__callback

    @callback.setter
    def callback(self, new: callable) -> None:
        """
        The callback function for the event.

        The callback function is called whenever the event is triggered. The
        function should accept zero or more arguments.

        Parameters:
            new (callable):
                The new value for the callback.

        Raises:
            TypeError:
                If the new value is not callable.
        """
        if not callable(new):
            raise TypeError(f"callback must be callable, not {type(new)}")

        self.__callback = new

    @property
    def times_failed(self) -> int:
        """
        The number of times the callback function has failed. (**Read-Only**)

        If the callback function fails, an error is raised and the number of
        times it has failed is incremented.

        Returns:
            int:
                The number of times the callback function has failed.
        """
        return self.__failed


    @property
    def key(self):
        """
        The key of the event.

        The key is the identifier for this event. It is used to look up the event
        in the collection.

        Returns:
            str:
                The key of the event.
        """
        return self.__key

    @key.setter
    def key(self, new: Optional[str]):
        """
        The key of the event.

        The key is the identifier for this event. It is used to look up the event
        in the collection.

        If the event is an `ExitEvent` (a special event given to every window
        handler collection), the key is allowed to be `None`. Otherwise, the key
        must be a string.

        Parameters:
            new (Optional[str]):
                The new key of the event.

        Raises:
            RuntimeError:
                If the key is changed after initialization.
            TypeError:
                If the new key is not a string.
        """
        # Allow for `key` to allow `None` as a value if it is from `ExitEvent` (a special event given to every window
        # handler collection)
        if new is None and isinstance(self, ExitEvent):
            self._Event__key = None
            return

        if self.__initialized:
            raise RuntimeError("Cannot change key after initialization")

        if not isinstance(new, str):
            raise TypeError(f"key must be of type `str`, not {type(new)}")

        self.__key = new.upper()

    @property
    def times_handled(self):
        """
        The number of times the event has been handled.

        This property returns the count of how many times the `handle` method
        has been invoked for this event.

        Returns:
            int:
                The number of times the event has been handled.
        """
        return self.__times_handled

    def handle(self, callback_args: tuple = (), callback_kwargs: Optional[dict] = None):
        """
        Handles an event by calling the associated callback.

        Parameters:
            callback_args (tuple):
                The arguments to be passed to the callback.

            callback_kwargs (Optional[dict]):
                The keyword arguments to be passed to the callback.

        Returns:
            Any:
                The return value of the callback, or None if no callback is associated with the event.
        """
        if callback_kwargs is None:
            callback_kwargs = {}

        self.__times_handled += 1

        if self.callback:
            try:
                return self.callback(*callback_args, **callback_kwargs)
            except Exception as e:
                self.__failed += 1
                raise e from e

        return None


class ExitEvent(Event):
    """
    A special event that can be applied to any PySimpleGUI main loop to recognize and handle a press of the 'X' button.
    """
    def __init__(self):
        super().__init__(key=None,)

    @property
    def key(self) -> None:
        return None

    @key.setter
    def key(self, new: None) -> None:
        raise ValueError('The key of an ExitEvent cannot be set.')


__initialized = True

