import time
import pigpio

import config
from hardware.continuous_servo import ContinuousRotationServo


def main():

    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError("Could not connect to pigpiod")

    servo = ContinuousRotationServo(pi, **config.LEFT_TRACK)

    speeds = [
        -1.0,
        -0.75,
        -0.5,
        -0.25,
        0,
        0.25,
        0.5,
        0.75,
        1.0,
        0
    ]

    try:

        for speed in speeds:

            print(f"Speed = {speed}")

            servo.speed(speed)

            time.sleep(2)

    finally:

        servo.disable()

        pi.stop()


if __name__ == "__main__":
    main()
