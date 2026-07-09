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

    try:

        print("Forward 50%")
        drive.forward(0.5)
        time.sleep(2)

        print("Stop")
        drive.stop()
        time.sleep(1)

        print("Reverse 50%")
        drive.reverse(0.5)
        time.sleep(2)

        print("Stop")
        drive.stop()
        time.sleep(1)

        print("Turn Left")
        drive.turn_left(0.5)
        time.sleep(2)

        print("Stop")
        drive.stop()
        time.sleep(1)

        print("Turn Right")
        drive.turn_right(0.5)
        time.sleep(2)

        print("Stop")
        drive.stop()

    finally:

        left.disable()
        right.disable()

        pi.stop()


if __name__ == "__main__":
    main()
