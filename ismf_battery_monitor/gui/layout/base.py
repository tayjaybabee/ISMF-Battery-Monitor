from abc import abstractmethod
import copy

from is_matrix_forge.log_engine import ROOT_LOGGER, Loggable
from is_matrix_forge.monitor.gui.metaclasses import SingletonABCMeta
from inspyre_toolbox.exceptional import CustomRootException


class LayoutError(CustomRootException):
    default_message = 'An error occurred with the layout!'


class LayoutNotBuiltError(LayoutError):
    """
    Raised when the layout is not built yet.

    Class Attributes:
        default_message (str):
            **Read-Only**. The default message for the error.
    """
    default_message = 'Layout not built yet!'


class LayoutAlreadyBuiltError(LayoutError):
    """
    Raised when the layout is already built.

    Class Attributes:
        default_message (str):
            **Read-Only**. The default message for the error.
    """
    default_message = 'Layout already built!'


LOGGER = ROOT_LOGGER.get_child('monitor.gui.layout.base')


class Layout(Loggable, metaclass=SingletonABCMeta):

    @property
    @abstractmethod
    def BLUEPRINT(self):
        """Return a 2D list of PySimpleGUI elements used to build this layout."""
        raise NotImplementedError

    def __init__(self, with_logging_parent=None):
        if with_logging_parent is None:
            with_logging_parent = LOGGER

        super().__init__(with_logging_parent)

        self.__layout   = None
        self.__is_built = False

    @property
    def built(self):
        """
        Check if the layout has been built.

        Returns:
            bool:
                True if the layout has been built, False otherwise.
        """
        return self.__is_built

    @property
    def layout(self):
        """
        Get a fresh deep-copy of the built layout.

        Returns:
            List[List[PySimpleGUI.Element]]:
                A 2D list of `PySimpleGUI` elements representing the layout.

        Raises:
            LayoutNotBuiltError:
                If the layout has not been built yet.
        """
        log = self.method_logger
        if not self.built:
            log.warning('Attempted to access layout before it was built!')
            raise LayoutNotBuiltError()

        if self.__layout is None:
            err_msg = 'Layout is None, but built is True!'
            log.warning(err_msg)
            raise LayoutNotBuiltError(err_msg)

        log.debug('Returning a deep-copy of the layout.')
        return copy.deepcopy(self.__layout)

    def build(self):
        """
        Build the layout from the `BLUEPRINT` attribute once.

        Returns:
            List[List[PySimpleGUI.Element]]:
                A 2D list of `PySimpleGUI` elements representing the layout, deep-copied.

        Raises:
            LayoutAlreadyBuiltError:
                If the layout has already been built.
        """
        log = self.method_logger
        if self.built:
            log.warning('Attempted to build layout when it was already built!')
            raise LayoutAlreadyBuiltError()

        blueprint = self.BLUEPRINT
        if not isinstance(blueprint, list) or not all(isinstance(r, list) for r in blueprint):
            raise LayoutError('BLUEPRINT must be a 2D list of PySimpleGUI elements.')

        self.__layout   = copy.deepcopy(blueprint)
        log.debug('Layout built successfully.')
        self.__is_built = True
        log.debug('Marked layout as built.')

        return self.layout

    def rebuild(self):
        """
        Clear the current layout and build a new one from `BLUEPRINT`.

        Returns:
            List[List[PySimpleGUI.Element]]:
                A 2D list of `PySimpleGUI` elements representing the layout, deep-copied.

        Raises:
            LayoutNotBuiltError:
                If the layout has not been built yet.
        """
        log = self.method_logger

        if not self.built:
            log.warning('Attempted to rebuild layout when it was not built yet!')
            raise LayoutNotBuiltError('Cannot rebuild layout when it was not built yet!')

        log.debug('Rebuilding layout...')
        log.debug('Clearing current layout...')

        self.__layout   = None
        log.debug('Layout set to None.')
        self.__is_built = False
        log.debug('Layout marked as not built.')
        log.debug('Building new layout and returning...')

        return self.build()
