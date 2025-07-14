from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Optional

from chime import play_wav

from inspyre_toolbox.syntactic_sweets.classes.decorators.aliases import add_aliases, method_alias

from is_matrix_forge.log_engine import ROOT_LOGGER as PARENT_LOGGER
from is_matrix_forge.assets.audio import PLUG_ALERT_MAP


MOD_LOGGER = PARENT_LOGGER.get_child('notify.sounds.base')


@add_aliases
class Sound(ABC):
    """
    Abstract base class for audio notifications.
    """
    __allowed_types: set = {'plugged', 'unplugged'}

    def __init__(
            self,
            wav_file: Union[str, Path],
            notify_type: str,
    ) -> None:
        self.__initialized = False
        self.__notify_type = None
        self.__wav_file    = None

        self.wav_file_path = wav_file
        self.notify_type   = notify_type
        # Initialize here

    @property
    def ALLOWED_TYPES(self):
        """
        The allowed values for the notify_type property. Read-only property.

        Returns:
            set[str]:
                A set of allowed notify-types.
        """
        return self.__allowed_types

    @property
    def notify_type(self):
        return self.__notify_type

    @notify_type.setter
    def notify_type(self, new: str) -> None:
        if self.__initialized:
            raise RuntimeError('Cannot change notify type after initialization@')

        if not isinstance(new, str):
            raise TypeError(f'new must be of type `str`, not {type(new)}')

        if new not in self.ALLOWED_TYPES:
            raise ValueError(f'new must be one of {self.ALLOWED_TYPES}, not {new}')
        
        self.__notify_type = new

    @property
    def wav_file_path(self) -> Path:
        """
        Get the path to the .wav file that will be played.

        Returns:
            Path:
                The path to the .wav file.
        """
        return self.__wav_file

    @wav_file_path.setter
    def wav_file_path(self, new: Union[str, Path]) -> None:
        """
        Set the path to the .wav file that will be played. Setting this should be done during initialization. After
        initialization, this should not (and will not) be changed, as it will break the sound.
        """
        if self.__initialized:
            raise RuntimeError('Cannot change wave file path after initialization.')

        if isinstance(new, str):
            new = Path(new)

        if not isinstance(new, Path):
            raise TypeError(f'new must be of type `str` or `Path`, not {type(new)}')

        self.__wav_file = new

    @method_alias('play')
    def notify(self) -> None:
        """
        Play the audio notification.

        Returns:
            None
        """
        play_wav(self.wav_file_path)

    def __repr__(self):
        return f"<Sound notify_type={self.notify_type!r} wav_file_path={self.wav_file_path!r}>"



