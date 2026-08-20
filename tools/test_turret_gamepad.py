import pigpio

from config import HALL_SENSORS, TURRET
from control.gamepad import Gamepad
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret


MAX_TURRET_SPEED = 0.50
GAMEPAD_DEADZONE = 0.12


def control_turret(
    turret: Turret,
    right_stick_x: float,
) -> tuple[str, float]:
    """Convert right-stick horizontal movement into turret movement."""

    speed = (
        min(abs(right_stick_x), 1.0)
        * MAX_TURRET_SPEED
    )

    if right_stick_x < 0:
        allowed = turret.rotate_left(speed)

        if not allowed:
            return "LEFT LIMIT", 0.0

        return "LEFT", speed

    if right_stick_x > 0:
        allowed = turret.rotate_right(speed)

        if not allowed:
            return "RIGHT LIMIT", 0.0

        return "RIGHT", speed

    turret.stop()

    return "STOPPED", 0.0


def main() -> None:
    gamepad = None
    pi = None
    turret = None
    report_callbacks = []

    try:
        print("Searching for compatible gamepad...")

        gamepad = Gamepad.discover(
            deadzone=GAMEPAD_DEADZONE,
        )

        print(f"Controller: {gamepad.name}")
        print(f"Device: {gamepad.path}")
        print()

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
            left_direction=TURRET["tank_left_direction"],
            left_limit=left_sensor,
            home_sensor=home_sensor,
            right_limit=right_sensor,
        )

        report_callbacks.append(
            left_sensor.add_activation_callback(
                lambda: print(
                    "\nLEFT LIMIT DETECTED",
                    flush=True,
                )
            )
        )

        report_callbacks.append(
            home_sensor.add_activation_callback(
                lambda: print(
                    "\nHOME DETECTED",
                    flush=True,
                )
            )
        )

        report_callbacks.append(
            right_sensor.add_activation_callback(
                lambda: print(
                    "\nRIGHT LIMIT DETECTED",
                    flush=True,
                )
            )
        )

        print("Turret Hall-limit gamepad test")
        print("------------------------------")
        print("Right stick left/right controls turret.")
        print("Hall limit sensors prevent outward movement.")
        print("Home sensor reports centre position.")
        print("Ctrl+C quits.")
        print()
        print(
            f"Maximum test speed: "
            f"{MAX_TURRET_SPEED:.0%}"
        )
        print()

        previous_status = None

        for axes in gamepad.read_loop():
            direction, speed = control_turret(
                turret=turret,
                right_stick_x=axes.right_x,
            )

            status = (
                direction,
                round(speed, 2),
            )

            if status != previous_status:
                print(
                    "\r"
                    f"Turret: {direction:11} "
                    f"speed={speed:.2f}",
                    end="",
                    flush=True,
                )

                previous_status = status

    except KeyboardInterrupt:
        print("\nController test stopped.")

    except OSError as error:
        print(
            "\nController disconnected or became unavailable: "
            f"{error}"
        )

    finally:
        if turret is not None:
            try:
                turret.close()
            except Exception as error:
                print(
                    "\nWarning: could not fully disable turret: "
                    f"{error}"
                )

        for callback in report_callbacks:
            try:
                callback.cancel()
            except Exception:
                pass

        if pi is not None:
            pi.stop()

        if gamepad is not None:
            try:
                gamepad.close()
            except OSError:
                pass

        print("\nTurret disabled.")


if __name__ == "__main__":
    main()
