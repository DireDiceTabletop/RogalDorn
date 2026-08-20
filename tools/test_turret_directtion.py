import time

import pigpio

from config import HALL_SENSORS, TURRET
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret


TEST_SPEED = 0.15
TEST_DURATION = 0.75

HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0

WAIT_TIME = 1.5


def main() -> None:
    pi = None
    turret = None

    try:
        pi = pigpio.pi()

        if not pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio."
            )

        left_sensor = HallSensor(
            pi=pi,
            gpio=HALL_SENSORS["left"],
        )

        home_sensor = HallSensor(
            pi=pi,
            gpio=HALL_SENSORS["home"],
        )

        right_sensor = HallSensor(
            pi=pi,
            gpio=HALL_SENSORS["right"],
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
            left_direction=TURRET["tank_left_direction"],
            left_limit=left_sensor,
            home_sensor=home_sensor,
            right_limit=right_sensor,
        )

        print("Tank-relative turret direction test")
        print("-----------------------------------")
        print()
        print(
            "LEFT and RIGHT are from the tank's "
            "perspective while driving forwards."
        )
        print()
        print(
            f"Configured tank_left_direction: "
            f"{TURRET['tank_left_direction']}"
        )
        print()

        input(
            "Press Enter to begin, "
            "or Ctrl+C to cancel..."
        )

        # -------------------------------------------------
        # HOME
        # -------------------------------------------------

        print()
        print("HOME")

        turret.home(
            speed=HOMING_SPEED,
            timeout=HOMING_TIMEOUT,
        )

        print("HOME FOUND")
        time.sleep(WAIT_TIME)

        # -------------------------------------------------
        # TANK LEFT
        # -------------------------------------------------

        print()
        print("TANK LEFT")
        print(
            "The turret should physically rotate "
            "toward the tank's LEFT."
        )

        turret.rotate_left(TEST_SPEED)
        time.sleep(TEST_DURATION)
        turret.stop()

        print("STOP")
        time.sleep(WAIT_TIME)

        # -------------------------------------------------
        # HOME
        # -------------------------------------------------

        print()
        print("HOME")

        turret.home(
            speed=HOMING_SPEED,
            timeout=HOMING_TIMEOUT,
        )

        print("HOME FOUND")
        time.sleep(WAIT_TIME)

        # -------------------------------------------------
        # TANK RIGHT
        # -------------------------------------------------

        print()
        print("TANK RIGHT")
        print(
            "The turret should physically rotate "
            "toward the tank's RIGHT."
        )

        turret.rotate_right(TEST_SPEED)
        time.sleep(TEST_DURATION)
        turret.stop()

        print("STOP")
        time.sleep(WAIT_TIME)

        # -------------------------------------------------
        # FINAL HOME
        # -------------------------------------------------

        print()
        print("HOME")

        turret.home(
            speed=HOMING_SPEED,
            timeout=HOMING_TIMEOUT,
        )

        print("HOME FOUND")

        print()
        print("Direction test complete.")

    except KeyboardInterrupt:
        print()
        print("Test cancelled.")

    except (RuntimeError, TimeoutError) as error:
        print()
        print(
            f"TEST FAILED: {error}"
        )

    finally:
        if turret is not None:
            turret.close()

        if pi is not None:
            pi.stop()

        print("Turret disabled.")


if __name__ == "__main__":
    main()
