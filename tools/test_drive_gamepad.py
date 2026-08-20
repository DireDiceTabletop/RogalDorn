import pigpio
from evdev import InputDevice, list_devices

from config import LEFT_TRACK, RIGHT_TRACK
from control.gamepad import Gamepad
from hardware.continuous_servo import ContinuousRotationServo
from hardware.drive import Drive


# ---------------------------------------------------------
# Gamepad
# ---------------------------------------------------------

GAMEPAD_DEADZONE = 0.12


def find_xbox_controller() -> str:
    """
    Find the Xbox controller input device.

    We prefer devices whose name contains Xbox or
    Wireless Controller.
    """

    candidates = []

    for path in list_devices():
        device = InputDevice(path)

        name = device.name.lower()

        if (
            "xbox" in name
            or "wireless controller" in name
        ):
            candidates.append(
                (path, device.name)
            )

    if not candidates:
        raise RuntimeError(
            "Could not find Xbox controller."
        )

    path, name = candidates[0]

    print(
        f"Gamepad found: {name}"
    )
    print(
        f"Device: {path}"
    )

    return path


def create_drive(
    pi: pigpio.pi,
) -> Drive:
    """
    Create the left and right track servos
    and return the Drive abstraction.
    """

    left_servo = ContinuousRotationServo(
        pi=pi,
        gpio=LEFT_TRACK["gpio"],
        stop=LEFT_TRACK["stop"],
        forward=LEFT_TRACK["forward"],
        reverse=LEFT_TRACK["reverse"],
    )

    right_servo = ContinuousRotationServo(
        pi=pi,
        gpio=RIGHT_TRACK["gpio"],
        stop=RIGHT_TRACK["stop"],
        forward=RIGHT_TRACK["forward"],
        reverse=RIGHT_TRACK["reverse"],
    )

    return Drive(
        left_servo=left_servo,
        right_servo=right_servo,
    )


def main() -> None:
    pi = None
    gamepad = None
    drive = None

    try:
        # -------------------------------------------------
        # pigpio
        # -------------------------------------------------

        pi = pigpio.pi()

        if not pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio."
            )

        # -------------------------------------------------
        # Drive
        # -------------------------------------------------

        drive = create_drive(
            pi
        )

        # Make absolutely sure we begin stationary.
        drive.arcade(
            forward=0.0,
            turn=0.0,
        )

        # -------------------------------------------------
        # Gamepad
        # -------------------------------------------------

        device_path = find_xbox_controller()

        gamepad = Gamepad(
            device_path=device_path,
            deadzone=GAMEPAD_DEADZONE,
        )

        # -------------------------------------------------
        # Safety gate
        # -------------------------------------------------

        print()
        print("==============================")
        print("XBOX DRIVE TEST")
        print("==============================")
        print()
        print(
            "LEFT STICK:"
        )
        print(
            "  Up / Down   = Forward / Reverse"
        )
        print(
            "  Left / Right = Steering"
        )
        print()
        print(
            "For the first test, raise the tank so "
            "both tracks can spin freely."
        )
        print()
        print(
            "Press Ctrl+C at any time to stop."
        )
        print()

        input(
            "Press Enter to enable track control..."
        )

        print()
        print("DRIVE ENABLED")
        print()

        # -------------------------------------------------
        # Main controller loop
        # -------------------------------------------------

        for axes in gamepad.read_loop():

            # Xbox sticks normally report:
            #
            # stick UP   = negative Y
            # stick DOWN = positive Y
            #
            # Drive.arcade() expects:
            #
            # positive forward = forwards
            #
            # so invert left_y.
            forward = -axes.left_y

            turn = axes.left_x

            drive.arcade(
                forward=forward,
                turn=turn,
            )

            print(
                f"FORWARD={forward:+.2f}  "
                f"TURN={turn:+.2f}",
                end="\r",
                flush=True,
            )

    except KeyboardInterrupt:
        print()
        print()
        print("Drive test cancelled.")

    except RuntimeError as error:
        print()
        print(
            f"TEST FAILED: {error}"
        )

    finally:
        # -------------------------------------------------
        # Safe shutdown
        # -------------------------------------------------

        if drive is not None:
            drive.arcade(
                forward=0.0,
                turn=0.0,
            )

        if gamepad is not None:
            gamepad.close()

        if pi is not None:
            pi.stop()

        print()
        print("Tracks stopped.")
        print("Gamepad closed.")


if __name__ == "__main__":
    main()
