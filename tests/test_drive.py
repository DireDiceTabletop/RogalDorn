from tests.bootstrap import *

import time
import pigpio

import config

from hardware.continuous_servo import ContinuousRotationServo
from hardware.drive import Drive


def main():

    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError("Could not connect to pigpiod")

    left = ContinuousRotationServo(pi, **config.LEFT_TRACK)
    right = ContinuousRotationServo(pi, **config.RIGHT_TRACK)

    drive = Drive(left, right)

    print("Forward")
    drive.forward()
    time.sleep(2)

    print("Stop")
    drive.stop()
    time.sleep(1)

    print("Reverse")
    drive.reverse()
    time.sleep(2)

    print("Stop")
    drive.stop()

    left.disable()
    right.disable()

    pi.stop()


if __name__ == "__main__":
    main()
