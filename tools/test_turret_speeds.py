import time

import pigpio

from config import HALL_SENSORS, TURRET
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret


TEST_SPEEDS = [
    0.15,
    0.16,
    0.17,
    0.18,
    0.19,
    0.20,
]

TEST_DURATION = 0.75

HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0

WAIT_AFTER_HOME = 1.5
WAIT_AFTER_MOVEMENT = 1.0


def build_turret(pi: pigpio.pi) -> Turret:
    """Create the Hall-protected turret."""

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

    return Turret(
        servo=servo,
        left_direction=TURRET["tank_left_direction"],
        left_limit=left_sensor,
        home_sensor=home_sensor,
        right_limit=right_sensor,
    )


def home_turret(turret: Turret) -> None:
    """Home the turret and verify the home sensor."""

    print()
    print("HOME")
    print("----")
    print("Homing...")

    turret.home(
        speed=HOMING_SPEED,
        timeout=HOMING_TIMEOUT,
    )

    if not turret.at_home:
        raise RuntimeError(
            "Homing completed without the home sensor being active."
        )

    print("HOME FOUND")


def run_movement(
    turret: Turret,
    direction: str,
    speed: float,
) -> None:
    """Run a short Hall-protected movement."""

    print()
    print(
        f"{direction.upper()} at speed {speed:.2f}"
    )
    print("-" * 30)

    start = time.monotonic()

    while time.monotonic() - start < TEST_DURATION:
        if direction == "left":
            allowed = turret.rotate_left(speed)
        else:
            allowed = turret.rotate_right(speed)

        if not allowed:
            print("LIMIT REACHED")
            turret.stop()
            return

        time.sleep(0.02)

    turret.stop()

    print("Movement complete.")


def main() -> None:
    pi = None
    turret = None

    try:
        pi = pigpio.pi()

        if not pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio. "
                "Check that pigpio is running."
            )

        turret = build_turret(pi)

        print("Low-speed turret smoothness test")
        print("================================")
        print()
        print(
            f"Stop    : {TURRET['stop']}"
        )
        print(
            f"Forward : {TURRET['forward']}"
        )
        print(
            f"Reverse : {TURRET['reverse']}"
        )
        print()
        print("Each speed is tested left and right.")
        print("The turret homes between every movement.")
        print("Hall limits remain active.")
        print()
        print("Watch for:")
        print("  - smooth continuous rotation")
        print("  - pulsing / start-stop movement")
        print("  - significant left/right differences")
        print()

        input(
            "Press Enter to begin, or Ctrl+C to cancel..."
        )

        for speed in TEST_SPEEDS:
            print()
            print("=" * 40)
            print(f"TEST SPEED {speed:.2f}")
            print("=" * 40)

            home_turret(turret)

            print(
                f"Waiting {WAIT_AFTER_HOME:.1f}s..."
            )
            time.sleep(WAIT_AFTER_HOME)

            run_movement(
                turret=turret,
                direction="left",
                speed=speed,
            )

            print(
                f"Waiting {WAIT_AFTER_MOVEMENT:.1f}s..."
            )
            time.sleep(WAIT_AFTER_MOVEMENT)

            home_turret(turret)

            print(
                f"Waiting {WAIT_AFTER_HOME:.1f}s..."
            )
            time.sleep(WAIT_AFTER_HOME)

            run_movement(
                turret=turret,
                direction="right",
                speed=speed,
            )

            print(
                f"Waiting {WAIT_AFTER_MOVEMENT:.1f}s..."
            )
            time.sleep(WAIT_AFTER_MOVEMENT)

            home_turret(turret)

            print(
                f"Waiting {WAIT_AFTER_HOME:.1f}s..."
            )
            time.sleep(WAIT_AFTER_HOME)

        print()
        print("LOW-SPEED TEST COMPLETE")

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
