from .base import Sound
from ..audio import PLUG_ALERT_MAP


PLUGGED_NOTIFY   = Sound(PLUG_ALERT_MAP['plugged'], 'plugged')
UNPLUGGED_NOTIFY = Sound(PLUG_ALERT_MAP['unplugged'], 'unplugged')
