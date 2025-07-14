from __future__ import annotations
from typing import Optional

from .event import MOD_LOGGER as __MOD_LOGGER, Event, Loggable
from .errors import EventExistsError, EventLookupError

__initialized = False

if __initialized:
    from ..windows.base import WindowBase


MOD_LOGGER = __MOD_LOGGER.parent.get_child('collection')


class EventCollection(Loggable):
    def __init__(
            self,
            window: WindowBase
    ):
        """
        Initializes an EventCollection instance.

        This constructor sets up the logging and initializes an empty list to hold events.
        """
        super().__init__(MOD_LOGGER)
        self.__events = []

    def __iter__(self):
        return iter(self.__events)

    def __len__(self):
        return len(self.__events)

    @property
    def event_names(self):
        return [e.key for e in self.__events]

    @property
    def events(self):
        return self.__events

    @property
    def exit_event_exists(self) -> bool:
        """
        Checks if an ExitEvent exists in the collection.

        This method checks if any events in the collection are an instance of ExitEvent.

        Returns:
            bool:
                True if an ExitEvent exists in the collection, False otherwise.
        """
        from ..event.event import ExitEvent

        return any(isinstance(event, ExitEvent) for event in self.events)

    @property
    def times_failed(self):
        """
        The total number of times all events in the collection have failed.

        This property is a shortcut to get the total number of times all events
        in the collection have failed. It does this by summing up the `times_failed`
        property of each event in the collection.

        Returns:
            int:
                The total number of times all events in the collection have failed.
        """
        times = 0

        if self.events:
            for event in self.events:
                times += event.times_failed
        else:
            self.method_logger.warn_once('No events in collection, returning 0')

        return times

    @property
    def times_handled(self) -> int:
        times = 0

        if self.events:
            for event in self.events:
                times += event.times_handled
        else:
            self.method_logger.warn_once('No events in collection, returning 0')

        return times

    def add_event(self, event: Event) -> None:
        if not isinstance(event, Event):
            raise TypeError(f"event must be of type `Event`, not {type(event)}")

        if event.key in self.event_names:
            raise EventExistsError(event_name=event.key)

        self.__events.append(event)

    def clear(self) -> None:
        self.method_logger.info('Clearing all events in collection...')
        self.events.clear()

    def create_event(self, key: str, callback: Optional[callable] = None) -> None:
        if key is None and self.exit_event_exists:
            raise EventExistsError(event_name='ExitEvent')
        elif key is None and not self.exit_event_exists:
            from ..event.event import ExitEvent
            return self.add_event(ExitEvent())

        key = key.upper()

        if key in self.event_names:
            raise EventExistsError(event_name=key)

        return self.add_event(Event(key=key, callback=callback))

    def handle_event(self, event: str, callback_args: tuple = (), callback_kwargs: Optional[dict] = None):
        print('Reached handle_event')
        event = self.lookup(event)

        if event is None:
            raise EventLookupError(event_name=event)

        return event.handle(callback_args=callback_args, callback_kwargs=callback_kwargs)

    def lookup(self, event_key: str) -> Optional[Event]:
        """
        Looks up an event in the collection by its key.

        Parameters:
            event_key (str):
                The key of the event to be looked up.

        Returns:
            Event or None:
                The event with the given key, or None if not found.

        Raises:
            TypeError:
                If 'event_key' is not of type `str`.
        """
        if not isinstance(event_key, str):
            raise TypeError(f"'event_key' must be of type `str`, not {type(event_key)}")

        return next(
            (e for e in self.__events if e.key.lower() == event_key.lower()), None
        )


__initialized = True
