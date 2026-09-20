import pigpio
from evdev import InputDevice, ecodes, list_devices

from config import LASER
from hardware.laser import Laser


# Xbox A button under Linux / evdev.
LASER_BUTTON = ecodes.BTN_SOUTH


def find_xbox_controller() -> str:
    """
    Find the Xbox controller input device.
    """

    candidates = []

    for path in list_devices():
        device = InputDevice(path)

        try:
            name = device.name
            name_lower = name.lower()

            if (
                "xbox" in name_lower
                or "wireless controller" in name_lower
            ):
                candidates.append(
                    (path, name)
                )

        finally:
            device.close()

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


def main() -> None:
    pi = None
    laser = None
    gamepad = None

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
        # Laser
        # -------------------------------------------------

        laser = Laser(
            pi=pi,
            pin=LASER["gpio"],
        )

        # Laser.__init__() already calls off(), but doing
        # this explicitly makes our safety intention clear.
        laser.off()

        # -------------------------------------------------
        # Xbox controller
        # -------------------------------------------------

        device_path = find_xbox_controller()

        gamepad = InputDevice(
            device_path
        )

        # -------------------------------------------------
        # Safety gate
        # -------------------------------------------------

        print()
        print("==============================")
        print("XBOX LASER TEST")
        print("==============================")
        print()
        print(
            f"Laser GPIO: {LASER['gpio']}"
        )
        print()
        print(
            "Hold the Xbox A button to turn the laser ON."
        )
        print(
            "Release A to turn the laser OFF."
        )
        print()
        print(
            "Keep the laser aimed at a safe, "
            "non-reflective surface."
        )
        print()
        print(
            "Press Ctrl+C at any time to stop."
        )
        print()

        input(
            "Press Enter to enable laser control..."
        )

        print()
        print("LASER CONTROL ENABLED")
        print("Laser is currently OFF.")
        print()

        # -------------------------------------------------
        # Button loop
        # -------------------------------------------------

        for event in gamepad.read_loop():
            if event.type != ecodes.EV_KEY:
                continue

            if event.code != LASER_BUTTON:
                continue

            # evdev key values:
            #
            # 0 = released
            # 1 = pressed
            # 2 = held / repeated

            if event.value == 1:
                laser.on()

                print(
                    "LASER ON ",
                    end="\r",
                    flush=True,
                )

            elif event.value == 0:
                laser.off()

                print(
                    "LASER OFF",
                    end="\r",
                    flush=True,
                )

    except KeyboardInterrupt:
        print()
        print()
        print("Laser test cancelled.")

    except OSError as error:
        print()
        print()
        print(
            f"Controller connection lost: {error}"
        )

    except RuntimeError as error:
        print()
        print()
        print(
            f"TEST FAILED: {error}"
        )

    finally:
        # -------------------------------------------------
        # Fail-safe shutdown
        # -------------------------------------------------

        if laser is not None:
            laser.off()

        if gamepad is not None:
            gamepad.close()

        if pi is not None:
            pi.stop()

        print()
        print("Laser OFF.")
        print("Gamepad closed.")


if __name__ == "__main__":
    main()
