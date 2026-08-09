import pigpio

from config import HALL_SENSORS, TURRET
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret


HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0


def main() -> None:
    pi = None
    turret = None

    try:
        pi = pigpio.pi()

        if not pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio. "
                "Check that the pigpio daemon is running."
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
            left_direction=-1,
            left_limit=left_sensor,
            home_sensor=home_sensor,
            right_limit=right_sensor,
        )

        print("Automatic turret homing test")
        print("----------------------------")
        print()
        print(
            f"Left limit : "
            f"{'ACTIVE' if turret.at_left_limit else 'clear'}"
        )
        print(
            f"Home       : "
            f"{'ACTIVE' if turret.at_home else 'clear'}"
        )
        print(
            f"Right limit: "
            f"{'ACTIVE' if turret.at_right_limit else 'clear'}"
        )
        print()

        input(
            "Press Enter to begin homing, "
            "or Ctrl+C to cancel..."
        )

        print()
        print("Homing turret...")

        turret.home(
            speed=HOMING_SPEED,
            timeout=HOMING_TIMEOUT,
        )

        if turret.at_home:
            print("HOME FOUND")
            print("Turret is centred.")
        else:
            raise RuntimeError(
                "Homing completed but home sensor is not active."
            )

    except KeyboardInterrupt:
        print("\nHoming cancelled.")

    except (RuntimeError, TimeoutError) as error:
        print()
        print(f"HOMING FAILED: {error}")

    finally:
        if turret is not None:
            turret.close()

        if pi is not None:
            pi.stop()

        print("Turret disabled.")


if __name__ == "__main__":
    main()
