import pigpio

from config import TURRET
from control.gamepad import Gamepad
from hardware.continuous_servo import ContinuousRotationServo
from hardware.turret import Turret


MAX_TURRET_SPEED = 0.25
GAMEPAD_DEADZONE = 0.12


def control_turret(
    turret: Turret,
    right_stick_x: float,
) -> tuple[str, float]:
    """
    Convert the right-stick horizontal position into turret movement.

    The controller reports:
        negative = left
        positive = right
    """

    speed = min(abs(right_stick_x), 1.0) * MAX_TURRET_SPEED

    if right_stick_x < 0:
        turret.rotate_left(speed)
        return "LEFT", speed

    if right_stick_x > 0:
        turret.rotate_right(speed)
        return "RIGHT", speed

    turret.stop()
    return "STOPPED", 0.0


def main() -> None:
    gamepad = None
    pi = None
    turret = None

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

        print("Gamepad turret test")
        print("-------------------")
        print("Right stick left  : rotate turret left")
        print("Right stick right : rotate turret right")
        print("Release stick     : stop turret")
        print("Ctrl+C             : quit")
        print()
        print(
            f"Maximum turret speed: "
            f"{MAX_TURRET_SPEED:.0%}"
        )
        print()
        print("Keep the turret away from its physical limits.")

        previous_status: tuple[str, float] | None = None

        for axes in gamepad.read_loop():
            status = control_turret(
                turret=turret,
                right_stick_x=axes.right_x,
            )

            direction, speed = status

            rounded_status = (
                direction,
                round(speed, 2),
            )

            if rounded_status != previous_status:
                print(
                    "\r"
                    f"Turret: {direction:7} "
                    f"speed={speed:.2f}",
                    end="",
                    flush=True,
                )

                previous_status = rounded_status

    except KeyboardInterrupt:
        print("\nController test stopped.")

    except OSError as error:
        print(
            "\nThe controller input device was disconnected "
            f"or became unavailable: {error}"
        )

    finally:
        if turret is not None:
            try:
                turret.stop()
                turret.disable()
            except Exception as error:
                print(
                    f"\nWarning: could not fully disable turret: "
                    f"{error}"
                )

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
