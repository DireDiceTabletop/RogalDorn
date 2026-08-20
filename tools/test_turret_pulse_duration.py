import time

import pigpio

from config import HALL_SENSORS, TURRET
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret


RIGHT_TEST_SPEED = 0.17

PULSE_DURATIONS = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40,
]

HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0

WAIT_AFTER_HOME = 1.5
WAIT_AFTER_TEST = 1.0


def build_turret(pi: pigpio.pi) -> Turret:
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
    print()
    print("HOME")
    print("----")

    turret.home(
        speed=HOMING_SPEED,
        timeout=HOMING_TIMEOUT,
    )

    if not turret.at_home:
        raise RuntimeError(
            "Home sensor was not active after homing."
        )

    print("HOME FOUND")

    time.sleep(WAIT_AFTER_HOME)


def test_right_pulse(
    turret: Turret,
    duration: float,
) -> None:
    print()
    print(
        f"TANK RIGHT | "
        f"speed={RIGHT_TEST_SPEED:.2f} | "
        f"pulse={duration * 1000:.0f}ms"
    )
    print("-" * 45)

    allowed = turret.rotate_right(
        RIGHT_TEST_SPEED
    )

    if not allowed:
        print("RIGHT movement blocked by limit.")
        turret.stop()
        return

    try:
        time.sleep(duration)

    finally:
        turret.stop()

    print("STOP")

    time.sleep(WAIT_AFTER_TEST)


def main() -> None:
    pi = None
    turret = None

    try:
        pi = pigpio.pi()

        if not pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio."
            )

        turret = build_turret(pi)

        print("Tank-right pulse duration test")
        print("==============================")
        print()
        print(
            f"Right test speed : "
            f"{RIGHT_TEST_SPEED:.2f}"
        )
        print()
        print(
            "The turret will HOME before every test."
        )
        print(
            "Hall protection remains active."
        )
        print()
        print(
            "Watch for the shortest pulse that produces "
            "clear, repeatable tank-right movement."
        )
        print()

        input(
            "Press Enter to begin, "
            "or Ctrl+C to cancel..."
        )

        for duration in PULSE_DURATIONS:
            home_turret(turret)

            test_right_pulse(
                turret=turret,
                duration=duration,
            )

        home_turret(turret)

        print()
        print("==============================")
        print("TEST COMPLETE")
        print("==============================")

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

        print()
        print("Turret disabled.")


if __name__ == "__main__":
    main()
