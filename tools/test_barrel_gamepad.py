import threading
import time

import pigpio
from evdev import InputDevice, list_devices

from config import BARREL
from control.gamepad import Gamepad
from hardware.barrel import Barrel
from hardware.servo import Servo


GAMEPAD_DEADZONE = 0.05

# Full-stick barrel movement rate in servo microseconds
# per second.
#
# Our complete calibrated range is only 330 us, so 250
# gives us roughly 1.3 seconds from one extreme to the
# other at full stick.
BARREL_SPEED = 250.0

UPDATE_HZ = 50.0
UPDATE_INTERVAL = 1.0 / UPDATE_HZ


def find_xbox_controller() -> str:
    """
    Find the Xbox controller input device.
    """

    candidates = []

    for path in list_devices():
        device = InputDevice(
            path
        )

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


def controller_reader(
    gamepad: Gamepad,
    stop_event: threading.Event,
    state: dict,
    lock: threading.Lock,
) -> None:
    """
    Continuously read controller events and store the
    latest right-stick vertical position.
    """

    try:
        for axes in gamepad.read_loop():
            if stop_event.is_set():
                return

            with lock:
                state["right_y"] = (
                    axes.right_y
                )

    except OSError:
        if not stop_event.is_set():
            with lock:
                state["error"] = (
                    "Gamepad connection lost."
                )

            stop_event.set()


def main() -> None:
    pi = None
    gamepad = None
    barrel = None
    reader_thread = None

    stop_event = threading.Event()
    state_lock = threading.Lock()

    controller_state = {
        "right_y": 0.0,
        "error": None,
    }

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
        # Barrel servo
        # -------------------------------------------------

        servo = Servo(
            pi=pi,
            gpio=BARREL["gpio"],
        )

        barrel = Barrel(
            servo=servo,
            up_pulse=BARREL["up"],
            centre_pulse=BARREL["centre"],
            down_pulse=BARREL["down"],
        )

        # -------------------------------------------------
        # Xbox controller
        # -------------------------------------------------

        device_path = (
            find_xbox_controller()
        )

        gamepad = Gamepad(
            device_path=device_path,
            deadzone=GAMEPAD_DEADZONE,
        )

        # -------------------------------------------------
        # Controller reader thread
        # -------------------------------------------------

        reader_thread = threading.Thread(
            target=controller_reader,
            args=(
                gamepad,
                stop_event,
                controller_state,
                state_lock,
            ),
            daemon=True,
        )

        reader_thread.start()

        # -------------------------------------------------
        # Safety gate
        # -------------------------------------------------

        print()
        print("==============================")
        print("XBOX BARREL ELEVATION TEST")
        print("==============================")
        print()

        print(
            f"GPIO:   {BARREL['gpio']}"
        )
        print(
            f"UP:     {BARREL['up']} us"
        )
        print(
            f"CENTRE: {BARREL['centre']} us"
        )
        print(
            f"DOWN:   {BARREL['down']} us"
        )

        print()
        print("RIGHT STICK:")
        print()
        print(
            "  UP      = Raise barrel"
        )
        print(
            "  DOWN    = Lower barrel"
        )
        print(
            "  RELEASE = Hold current position"
        )

        print()
        print(
            "The barrel will be commanded to CENTRE "
            "when the test begins."
        )
        print()
        print(
            "Press Ctrl+C at any time to stop."
        )
        print()

        input(
            "Press Enter to centre the barrel and "
            "enable elevation control..."
        )

        # -------------------------------------------------
        # Initial centre
        # -------------------------------------------------

        barrel.centre()

        print()
        print("BARREL CENTRED")
        print("ELEVATION CONTROL ENABLED")
        print()

        previous_time = (
            time.perf_counter()
        )

        next_print_time = (
            previous_time
        )

        # -------------------------------------------------
        # Main control loop
        # -------------------------------------------------

        while not stop_event.is_set():
            now = time.perf_counter()

            delta_time = (
                now
                - previous_time
            )

            previous_time = now

            with state_lock:
                right_y = controller_state[
                    "right_y"
                ]

                controller_error = (
                    controller_state[
                        "error"
                    ]
                )

            if controller_error is not None:
                raise RuntimeError(
                    controller_error
                )

            # Xbox stick UP is negative.
            #
            # Barrel.update() expects positive values
            # to mean UP, so invert right_y.
            elevation_input = (
                -right_y
            )

            pulse = barrel.update(
                elevation_input=elevation_input,
                delta_time=delta_time,
                speed=BARREL_SPEED,
            )

            if now >= next_print_time:
                print(
                    f"ELEVATION="
                    f"{elevation_input:+.2f}  "
                    f"PULSE="
                    f"{pulse:4d} us",
                    end="\r",
                    flush=True,
                )

                next_print_time = (
                    now + 0.1
                )

            time.sleep(
                UPDATE_INTERVAL
            )

    except KeyboardInterrupt:
        print()
        print()
        print(
            "Barrel test cancelled."
        )

    except RuntimeError as error:
        print()
        print()
        print(
            f"TEST FAILED: {error}"
        )

    finally:
        stop_event.set()

        if barrel is not None:
            barrel.disable()

        if gamepad is not None:
            gamepad.close()

        if reader_thread is not None:
            reader_thread.join(
                timeout=1.0
            )

        if pi is not None:
            pi.stop()

        print()
        print("Barrel servo disabled.")
        print("Gamepad closed.")


if __name__ == "__main__":
    main()
