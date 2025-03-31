#!/usr/bin/python3 env
""" 
Test example file for rpiMotorlib.py  Stepper motor A4988 NEMA 

Note:
Comment in code  blocks marked:
"EMERGENCY STOP BUTTON CODE" to Test motor stop method with Push Button
and place push button to VCC on GPIO 17 :: VCC - PB1Pin1 , GPIO17 - PB1Pin2
"""

import time
import RPi.GPIO as GPIO

"""
# local install path For development USE 
# library testing import
# 1. Comment in Next 2 lines 
import sys
sys.path.insert(0, '/home/gavin/Documents/tech/RpiMotorLib/')
"""

"""
# pipx installed path, use this if you have installed package with pipx
import sys
sys.path.insert(0, '/home/gavin/.local/pipx/venvs/rpimotorlib/lib/python3.11/site-packages/')
"""

# library import
from RpiMotorLib import RpiMotorLib

"""
# EMERGENCY STOP BUTTON CODE: See docstring
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
"""

# ====== Tests for motor ======
# Microstep Resolution MS1-MS3 -> GPIO Pin , can be set to (-1,-1,-1) to turn off 
GPIO_pins = (-1, -1, -1)
direction = 21  # Direction -> GPIO Pin
step = 20 # Step -> GPIO Pin

# Declare an named instance of class pass GPIO-PINs
# (self, direction_pin, step_pin, mode_pins , motor_type):
mymotortest = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")


def main():
    """main function loop"""

    # ====== Tests for motor A4988 NEMA ====
    """
    # EMERGENCY STOP BUTTON CODE:  See docstring
    GPIO.add_event_detect(17, GPIO.RISING, callback=button_callback)
    """
    mymotortest.motor_go(False, "Half", 150, 0.001, True, 1)


    time.sleep(1)


"""
# EMERGENCY STOP BUTTON CODE: See docstring
def button_callback(channel):
    print("Test file: Stopping motor")
    mymotortest.motor_stop()
"""

# ===================MAIN===============================

if __name__ == '__main__':
    print("TEST START")
    main()
    GPIO.cleanup()
    print("TEST END")
    exit()

# =====================END===============================