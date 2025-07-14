import PySimpleGUI as psg
from is_matrix_forge.monitor.gui.layout.base import Layout as BaseLayout


from is_matrix_forge.log_engine import ROOT_LOGGER as PARENT_LOGGER


MOD_LOGGER = PARENT_LOGGER.get_child('monitor.gui.windows.main.layout')


class Layout(BaseLayout):
    @property
    def BLUEPRINT(self):
        return [

            [psg.Text('Brightness'), psg.Slider((0, 255), key='BRIGHTNESS_SLIDER', enable_events=True)],
            [psg.Button('Animate'), psg.Checkbox('Animated', key='ANIMATED_CHKBOX'),
             psg.Button('Exit', key='EXIT_BTTN')],

        ].copy()

