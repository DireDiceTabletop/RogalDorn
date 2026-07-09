from tests.bootstrap import *

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pigpio

import config

from hardware.servo import Servo


pi = pigpio.pi()

servo = Servo(pi, config.LEFT_TRACK_SERVO_GPIO)

print("Forward")
servo.pulse(1700)

time.sleep(2)

print("Stop")
servo.pulse(1500)

time.sleep(2)

print("Reverse")
servo.pulse(1300)

time.sleep(2)

servo.stop()

pi.stop()
