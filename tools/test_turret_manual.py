import sys
import termios
import tty

import pigpio

from config import TURRET
from hardware.continuous_servo import ContinuousRotationServo
from hardware.turret import Turret


TEST_SPEED = 0.2


def read_key() -> str:
    """Read one keypress without requiring Enter."""

    file_descriptor = sys.stdin.fileno()
    previous_settings = termios.tcgetattr(file_descriptor)

    try:
        tty.setraw(file_descriptor)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(
            file_descriptor,
            termios.TCSADRAIN,
            previous_settings,
        )


def main() -> None:
    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError(
            "Could not connect to pigpio. "
            "Check that the pigpio daemon is running."
        )

    servo = ContinuousRotationServo(
        pi=pi,
        gpio=TURRET["gpio"],
        stop=TURRET["stop"],
        forward=TURRET["forward"],
        reverse=TURRET["reverse"],
    )

    turret = Turret(
        servo=servo,
        left_direction=-1,
    )

    print("Manual turret test")
    print("------------------")
    print(f"A     rotate left at {TEST_SPEED:.0%} speed")
    print(f"D     rotate right at {TEST_SPEED:.0%} speed")
    print("Space stop")
    print("Q     quit")
    print()
    print("Press A or D once to start movement.")
    print("Press Space to stop.")
    print("Stay clear of the turret limits.")

    try:
        while True:
            key = read_key().lower()

            if key == "a":
                turret.rotate_left(TEST_SPEED)
                print("\rRotating left   ", end="", flush=True)

            elif key == "d":
                turret.rotate_right(TEST_SPEED)
                print("\rRotating right  ", end="", flush=True)

            elif key == " ":
                turret.stop()
                print("\rStopped         ", end="", flush=True)

            elif key == "q":
                break

    except KeyboardInterrupt:
        pass

    finally:
        turret.stop()
        turret.disable()
        pi.stop()
        print("\nTurret disabled.")


if __name__ == "__main__":
    main()
