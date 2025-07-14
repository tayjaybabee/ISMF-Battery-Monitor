from abc import ABC, abstractmethod
from ..layout.base import Layout
from ..errors import MalformedWindowError
from ..event import EventCollection
from ..metaclasses import SingletonABCMeta
import PySimpleGUI as psg


class WindowBase(metaclass=SingletonABCMeta):
    """
    Base class for all windows in the monitor control panel GUI.
    """
    DEFAULT_TITLE = 'LED Matrix Battery Monitor'

    @property
    def EVENT_COLLECTION(self):
        if self._event_collection is None:
            self._event_collection = EventCollection(self)
        return self._event_collection

    @property
    @abstractmethod
    def LAYOUT(self) -> Layout:
        pass

    def __init__(
            self,
            title:           str,
            skip_auto_build: bool = False,
            skip_auto_run:   bool = False
    ) -> None:
        self._auto_build       = None
        self._auto_run         = None
        self._event_collection = None
        self.__initialized     = False
        self._layout           = None
        self._title            = None
        self.__running         = False
        self.__window          = None

        # Set the values for instance variables/properties
        self.title      = title
        self.auto_build = not skip_auto_build
        self.auto_run   = not skip_auto_run

        self.__post_init__()

    def __post_init__(self):
        if self.auto_build:
            self.build()
            if self.auto_run:
                self.start()

    def _set_window_title(self, new_title: str, do_not_change_capitalization: bool = False) -> None:
        if not isinstance(new_title, str):
            raise TypeError('Window title must be a string.')

        if self.window is None:
            raise RuntimeError('Window not built yet.')

        self._title = new_title if do_not_change_capitalization else new_title.title()
        self.window.set_title(self._title)

    @property
    def auto_build(self):
        return bool(self._auto_build)

    @auto_build.setter
    def auto_build(self, new: bool) -> None:
        if self.initialized:
            raise RuntimeError('Cannot change auto_build after initialization.')

        if not isinstance(new, bool):
            raise TypeError(f'new must be of type `bool`, not {type(new)}')

        self._auto_build = new

    @property
    def auto_run(self):
        return bool(self._auto_run)

    @auto_run.setter
    def auto_run(self, new: bool) -> None:
        if self.initialized:
            raise RuntimeError('Cannot change auto_run after initialization.')

        if not isinstance(new, bool):
            raise TypeError(f'new must be of type `bool`, not {type(new)}')

        self._auto_run = new

    @property
    def built(self):
        try:
            return bool(self.layout) and bool(self.window)
        except RuntimeError:
            return False

    @property
    def initialized(self):
        """
        Whether the window has been initialized.

        The window is considered initialized if `WindowBase.__init__` has
        been called and finished successfully.

        Returns:
            bool:
                Whether the window has been initialized.
        """
        return bool(self.__initialized)

    @property
    def layout(self):
        """
        The `PySimpleGUI` layout for this window.

        The layout is constructed from the `WindowBase.layout_class` using the
        `WindowBase.layout_kwargs` constructor arguments.

        The layout is built automatically if `WindowBase.auto_build` is
        `True` (the default).

        Raises:
            RuntimeError:
                If the layout has not been built yet.

        Returns:
            List[List[sg.Element]]:
                A 2D list of `PySimpleGUI` elements representing the layout.
        """
        if self._layout is None:
            raise RuntimeError('Layout not built yet.')

        return self._layout

    @property
    def running(self):
        """
        Whether the window is currently running.

        A window is considered running if it has been started
        (i.e. `WindowBase.start` has been called) and has not been
        stopped (i.e. `WindowBase.stop` has been called). If this
        returns `True`, the window main loop is most-likely running.

        Returns:
            bool:
                Whether the window is currently running.
        """
        return bool(self.__running)

    @running.setter
    def running(self, new: bool) -> None:
        """
        Set the running status of the window.

        This method sets the `running` status of the window. It raises an error if
        attempting to start the window by setting `running` to True directly, instead
        of using the `start` method. It also ensures that the value assigned is a boolean.

        Parameters:
            new (bool):
                The new running status.

        Raises:
            RuntimeError:
                If attempting to start the window by setting `running` to True.

            TypeError:
                If the new value is not a boolean.
        """
        if not self.__running and new:
            raise RuntimeError('Cannot start window by setting running to True. Use "start" method instead.')

        if not isinstance(new, bool):
            raise TypeError(f'new must be of type `bool`, not {type(new)}')

        self.__running = new
        if not self.__running and new:
            raise RuntimeError('Cannot start window by setting running to True. Use "start" method instead.')

        self.__running = new

    @property
    def title(self):
        """
        The title of the window.

        This property returns the current title of the window. The title is used
        to identify the window and can be displayed on the window's title bar.

        Returns:
            str:
                The current title of the window.
        """
        return self._title

    @title.setter
    def title(self, new):
        """
        Set the title of the window.

        This method sets the title of the window, which is displayed on the window's title bar.
        The title is also used to identify the window in the taskbar or other window management
        interfaces.

        If the window is currently running, the title is updated immediately.

        Parameters:
            new (str):
                The new title of the window.

        Raises:
            TypeError:
                If the new title is not a string.
        """
        if not isinstance(new, str):
            raise TypeError(f'Window title must be a string, not {type(new)}')
        if new != self.title:
            self._title = new

            if self.running:
                self._set_window_title(new)

    @property
    def window(self):
        """
        The window object.

        This property returns the underlying window object, which is an instance of
        `PySimpleGUI.Window`. This object can be used to manipulate the window,
        e.g. to add or remove widgets, set the window's title, or to close the
        window.

        Returns:
            PySimpleGUI.Window:
                The underlying window object.
        """
        return self.__window

    @window.deleter
    def window(self):
        """
        Deletes the window object and stops the window if it is running.

        This deleter will also stop the window if it is running, and rebuild the
        layout if it exists.

        This is a convenience method to ensure that the window is properly shut
        down when it is no longer needed. It is called automatically when the
        window is garbage collected.

        Note that this method does not raise an error if the window is not
        running or if the layout does not exist. This is a no-op in those cases.
        """
        if self.running:
            self.stop()

        if self.layout:
            self.layout.rebuild()

    def build(self):
        if self.built:
            raise RuntimeError('Window already built.')
        self.LAYOUT.build()
        self._layout = self.LAYOUT.layout
        self.__window = psg.Window(self.title, layout=self.layout, finalize=True)
        if getattr(self, '__post_build__', None):
            print('post_build')
    def build_event_handlers(self):
        if not self.EVENT_COLLECTION.events:
            raise RuntimeError('No event handlers found to build!')

    def close(self):
        if self.window and self.running:
            self.window.close()
        elif not self.window:
            raise RuntimeError('Window not built yet, nothing to stop.')
        else:
            raise RuntimeError('Window not running, nothing to stop.')

        self.window.close()

    def handle_event(self, event, values):
        for handler in self.EVENT_COLLECTION:
            if handler.key == event:

                handler.callback

    def run(self):
        if not self.built:
            raise RuntimeError('Window not built yet.')

        if not self.running:
            raise RuntimeError('Window is not running. Start it first.')

        while self.running:
            event, values = self.window.read(timeout=100)

            if event is None:
                break

            self.handle_event(event, values)

        self.stop()

    def start(self):
        if self.running:
            raise RuntimeError('One cannot start a window that is already running.')

        if not self.window:
            raise RuntimeError('Window not built yet.')

        self.__running = True
        self.run()
        self.stop()

    def stop(self):
        if not self.running:
            raise RuntimeError('One cannot stop a window that is not running.')

        self.close()
        if self.running:
            self.running = False
