import time
import pigpio

import config

from hardware.continuous_servo import ContinuousRotationServo
from hardware.drive import Drive
from hardware.tank_controller import TankController


def main():

    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError("Could not connect to pigpiod")

    left = ContinuousRotationServo(pi, **config.LEFT_TRACK)
    right = ContinuousRotationServo(pi, **config.RIGHT_TRACK)

    drive = Drive(left, right)

    tank = TankController(drive)

    try:

        print("Forward")
        tank.forward(0.5)
        time.sleep(2)

        print("Stop")
        tank.stop()
        time.sleep(1)

        print("Turn Left")
        tank.turn_left(0.5)
        time.sleep(2)

        print("Stop")
        tank.stop()
        time.sleep(1)

        print("Turn Right")
        tank.turn_right(0.5)
        time.sleep(2)

        print("Stop")
        tank.stop()

    finally:

        left.disable()
        right.disable()
        pi.stop()


if __name__ == "__main__":
    main()
