import time
import pigpio

import config
from hardware.continuous_servo import ContinuousRotationServo


def make_servo(pi, cfg):
    return ContinuousRotationServo(
        pi,
        gpio=cfg["gpio"],
        stop=cfg["stop"],
        forward=cfg["forward"],
        reverse=cfg["reverse"]
    )


def test_continuous_servo(name, servo):

    print(f"\nTesting {name}")

    input("Press ENTER for Forward...")
    servo.forward()

    time.sleep(2)

    input("Press ENTER to Stop...")
    servo.stop()

    time.sleep(1)

    input("Press ENTER for Reverse...")
    servo.reverse()

    time.sleep(2)

    input("Press ENTER to Stop...")
    servo.stop()


def main():

    pi = pigpio.pi()

    if not pi.connected:
        print("Could not connect to pigpio")
        return

    left = make_servo(pi, config.LEFT_TRACK)
    right = make_servo(pi, config.RIGHT_TRACK)
    turret = make_servo(pi, config.TURRET)

    while True:

        print("\n==============================")
        print(" Rogal Dorn Hardware Tester")
        print("==============================")
        print("1 - Left Track")
        print("2 - Right Track")
        print("3 - Turret")
        print("q - Quit")

        choice = input("> ").lower()

        if choice == "1":
            test_continuous_servo("Left Track", left)

        elif choice == "2":
            test_continuous_servo("Right Track", right)

        elif choice == "3":
            test_continuous_servo("Turret", turret)

        elif choice == "q":
            break

    left.disable()
    right.disable()
    turret.disable()

    pi.stop()


if __name__ == "__main__":
    main()
