"""
Author: 
    Inspyre Softworks

Project:
    ISMF-Battery-Monitor

File: 
    Scripts/app.py
 

Description:
    This is the main script for the Inspyre Softworks Matrix Forge: Battery Monitor.
"""
from is_matrix_forge.led_matrix import get_controllers
from ismf_battery_monitor.monitor import PowerMonitor

CONTROLLERS = get_controllers(threaded=True)


def main():
    pm = PowerMonitor(CONTROLLERS[0])
    pm.start()


if __name__ == '__main__':
    main()

