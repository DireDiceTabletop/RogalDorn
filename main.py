import threading
import time

import pigpio

from config import (
    BARREL,
    HALL_SENSORS,
    LASER,
    LEFT_TRACK,
    RIGHT_TRACK,
    TURRET,
)
from control.gamepad import Gamepad, GamepadState
from hardware.barrel import Barrel
from hardware.continuous_servo import ContinuousRotationServo
from hardware.drive import Drive
from hardware.hall_sensor import HallSensor
from hardware.laser import Laser
from hardware.servo import Servo
from hardware.tank_controller import TankController
from hardware.turret import Turret


# =========================================================
# Manual-control configuration
# =========================================================

GAMEPAD_DEADZONE = 0.12

CONTROL_HZ = 50.0
CONTROL_INTERVAL = 1.0 / CONTROL_HZ


# ---------------------------------------------------------
# Drive
#
# Triggers provide proportional forward/reverse throttle.
#
# Shoulder buttons provide fixed-speed steering.
#
# Right turn currently needs more input than left turn
# because of the physical response of the track servos.
# ---------------------------------------------------------

LEFT_TURN_SPEED = 0.50
RIGHT_TURN_SPEED = 0.75


# ---------------------------------------------------------
# Turret
#
# This matches the control method used by the
# known-good tools/test_turret_gamepad.py test.
#
# Stick magnitude is multiplied by this value.
# ---------------------------------------------------------

MAX_TURRET_SPEED = 0.50


# ---------------------------------------------------------
# Barrel
# ---------------------------------------------------------

BARREL_SPEED = 200.0

# Cubic response gives finer movement near the centre of
# the stick while still allowing full-speed movement.
BARREL_USE_CUBIC_RESPONSE = True


# ---------------------------------------------------------
# Homing
# ---------------------------------------------------------

HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0


# =========================================================
# Hardware construction
# =========================================================

def create_drive(
    pi: pigpio.pi,
) -> Drive:
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


def create_turret(
    pi: pigpio.pi,
) -> Turret:
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


def create_barrel(
    pi: pigpio.pi,
) -> Barrel:
    servo = Servo(
        pi=pi,
        gpio=BARREL["gpio"],
    )

    return Barrel(
        servo=servo,
        up_pulse=BARREL["up"],
        centre_pulse=BARREL["centre"],
        down_pulse=BARREL["down"],
    )


def create_laser(
    pi: pigpio.pi,
) -> Laser:
    return Laser(
        pi=pi,
        pin=LASER["gpio"],
    )


# =========================================================
# Controller reader
# =========================================================

def controller_reader(
    gamepad: Gamepad,
    stop_event: threading.Event,
    controller_data: dict,
    lock: threading.Lock,
) -> None:
    """
    Read Xbox events continuously.

    The main control loop always uses the most recently
    received complete GamepadState.
    """

    try:
        for state in gamepad.read_state_loop():
            if stop_event.is_set():
                return

            with lock:
                controller_data["state"] = state

    except OSError as error:
        if not stop_event.is_set():
            with lock:
                controller_data["error"] = (
                    f"Gamepad connection lost: {error}"
                )

            stop_event.set()


# =========================================================
# Turret control
# =========================================================

def control_turret(
    tank: TankController,
    turret_input: float,
) -> float:
    """
    Apply continuous manual turret control.

    Negative stick:
        tank LEFT

    Positive stick:
        tank RIGHT
    """

    speed = (
        abs(turret_input)
        * MAX_TURRET_SPEED
    )

    if turret_input < 0:
        tank.turret_left(
            speed
        )

        return speed

    if turret_input > 0:
        tank.turret_right(
            speed
        )

        return speed

    tank.stop_turret()

    return 0.0


# =========================================================
# Main program
# =========================================================

def main() -> None:
    pi = None
    gamepad = None

    drive = None
    turret = None
    barrel = None
    laser = None
    tank = None

    reader_thread = None

    stop_event = threading.Event()
    state_lock = threading.Lock()

    controller_data = {
        "state": None,
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
        # Hardware
        # -------------------------------------------------

        drive = create_drive(
            pi
        )

        turret = create_turret(
            pi
        )

        barrel = create_barrel(
            pi
        )

        laser = create_laser(
            pi
        )

        tank = TankController(
            drive=drive,
            turret=turret,
            barrel=barrel,
            laser=laser,
        )

        # Start in a safe state.
        tank.stop()

        # -------------------------------------------------
        # Xbox controller
        # -------------------------------------------------

        print()
        print("Searching for Xbox controller...")

        gamepad = Gamepad.discover(
            deadzone=GAMEPAD_DEADZONE,
        )

        print(
            f"Controller: {gamepad.name}"
        )

        print(
            f"Device:     {gamepad.path}"
        )

        controller_data["state"] = (
            gamepad.state
        )

        # -------------------------------------------------
        # Controller reader thread
        # -------------------------------------------------

        reader_thread = threading.Thread(
            target=controller_reader,
            args=(
                gamepad,
                stop_event,
                controller_data,
                state_lock,
            ),
            daemon=True,
        )

        reader_thread.start()

        # -------------------------------------------------
        # Startup information
        # -------------------------------------------------

        print()
        print("======================================")
        print("ROGAL DORN MANUAL CONTROL")
        print("======================================")
        print()

        print("DRIVING")
        print("  Right Trigger   Forward")
        print("  Left Trigger    Reverse")
        print("  Right Bumper    Turn right")
        print("  Left Bumper     Turn left")
        print()

        print("RIGHT STICK")
        print("  Left / Right    Rotate turret")
        print("  Up / Down       Barrel elevation")
        print()

        print("A")
        print("  Hold            Laser ON")
        print("  Release         Laser OFF")
        print()

        print("START")
        print("  Reserved for face tracking")
        print()

        print("Ctrl+C")
        print("  Stop and exit")
        print()

        # -------------------------------------------------
        # Stage 1: turret homing
        # -------------------------------------------------

        print("STAGE 1: TURRET HOMING")
        print("----------------------")
        print()

        print(
            "Make sure the turret can rotate safely."
        )
        print()

        input(
            "Press Enter to home the turret..."
        )

        print()
        print("Homing turret...")

        tank.home_turret(
            speed=HOMING_SPEED,
            timeout=HOMING_TIMEOUT,
        )

        if not turret.at_home:
            raise RuntimeError(
                "Turret failed to reach HOME."
            )

        tank.stop_turret()

        print("HOME FOUND")
        print()

        # -------------------------------------------------
        # Stage 2: manual mode
        # -------------------------------------------------

        print("STAGE 2: MANUAL CONTROL")
        print("-----------------------")
        print()

        print(
            "The barrel will move to its centre position."
        )
        print()

        input(
            "Press Enter to enable manual control..."
        )

        tank.centre_barrel()

        time.sleep(
            0.25
        )

        print()
        print("======================================")
        print("MANUAL CONTROL ENABLED")
        print("======================================")
        print()

        previous_time = (
            time.perf_counter()
        )

        next_print_time = (
            previous_time
        )

        laser_was_on = False

        # -------------------------------------------------
        # Main control loop
        # -------------------------------------------------

        while not stop_event.is_set():
            loop_start = (
                time.perf_counter()
            )

            delta_time = (
                loop_start
                - previous_time
            )

            previous_time = (
                loop_start
            )

            # ---------------------------------------------
            # Latest controller state
            # ---------------------------------------------

            with state_lock:
                state: GamepadState = (
                    controller_data["state"]
                )

                controller_error = (
                    controller_data["error"]
                )

            if controller_error is not None:
                raise RuntimeError(
                    controller_error
                )

            if state is None:
                time.sleep(
                    CONTROL_INTERVAL
                )

                continue

            axes = state.axes
            triggers = state.triggers
            buttons = state.buttons

            # ---------------------------------------------
            # DRIVE
            #
            # Right trigger:
            #     forward throttle
            #
            # Left trigger:
            #     reverse throttle
            #
            # Both pressed:
            #     values oppose each other
            # ---------------------------------------------

            forward = (
                triggers.right
                - triggers.left
            )

            # ---------------------------------------------
            # STEERING
            #
            # Right and left turns have separate calibrated
            # speeds because the physical servo response is
            # different in each turning direction.
            #
            # Both bumpers held:
            #     no steering
            # ---------------------------------------------

            right_turn = (
                buttons.right_bumper
            )

            left_turn = (
                buttons.left_bumper
            )

            if (
                right_turn
                and not left_turn
            ):
                turn = RIGHT_TURN_SPEED

            elif (
                left_turn
                and not right_turn
            ):
                turn = -LEFT_TURN_SPEED

            else:
                turn = 0.0

            tank.drive_arcade(
                forward=forward,
                turn=turn,
            )

            # ---------------------------------------------
            # TURRET ROTATION
            # ---------------------------------------------

            turret_input = (
                axes.right_x
            )

            turret_speed = control_turret(
                tank=tank,
                turret_input=turret_input,
            )

            # ---------------------------------------------
            # BARREL ELEVATION
            # ---------------------------------------------

            # Xbox stick UP is negative, so invert Y.
            elevation_input = (
                -axes.right_y
            )

            if BARREL_USE_CUBIC_RESPONSE:
                elevation_input = (
                    elevation_input ** 3
                )

            barrel_pulse = tank.update_barrel(
                elevation_input=elevation_input,
                delta_time=delta_time,
                speed=BARREL_SPEED,
            )

            # ---------------------------------------------
            # LASER
            # ---------------------------------------------

            laser_requested = (
                buttons.a
            )

            if (
                laser_requested
                and not laser_was_on
            ):
                tank.laser_on()

                laser_was_on = True

            elif (
                not laser_requested
                and laser_was_on
            ):
                tank.laser_off()

                laser_was_on = False

            # ---------------------------------------------
            # Diagnostics
            # ---------------------------------------------

            if loop_start >= next_print_time:
                if turret_input < 0:
                    turret_direction = (
                        "LEFT"
                    )

                elif turret_input > 0:
                    turret_direction = (
                        "RIGHT"
                    )

                else:
                    turret_direction = (
                        "STOP"
                    )

                laser_text = (
                    "ON"
                    if laser_was_on
                    else "OFF"
                )

                print(
                    f"RT={triggers.right:.2f}  "
                    f"LT={triggers.left:.2f}  "
                    f"DRIVE={forward:+.2f}  "
                    f"TURN={turn:+.2f}  "
                    f"TURRET={turret_direction:5s} "
                    f"{turret_speed:.2f}  "
                    f"BARREL={barrel_pulse}  "
                    f"LASER={laser_text}",
                    end="\r",
                    flush=True,
                )

                next_print_time = (
                    loop_start + 0.10
                )

            # ---------------------------------------------
            # Maintain approximately 50 Hz
            # ---------------------------------------------

            elapsed = (
                time.perf_counter()
                - loop_start
            )

            sleep_time = (
                CONTROL_INTERVAL
                - elapsed
            )

            if sleep_time > 0:
                time.sleep(
                    sleep_time
                )

        # If the controller reader stopped us, surface the
        # reason rather than exiting silently.
        with state_lock:
            controller_error = (
                controller_data["error"]
            )

        if controller_error is not None:
            raise RuntimeError(
                controller_error
            )

    except KeyboardInterrupt:
        print()
        print()
        print("Manual control stopped.")

    except (RuntimeError, TimeoutError) as error:
        print()
        print()

        print(
            f"ERROR: {error}"
        )

    finally:
        # =================================================
        # Safe shutdown
        # =================================================

        stop_event.set()

        if tank is not None:
            tank.stop()

        if gamepad is not None:
            try:
                gamepad.close()
            except OSError:
                pass

        if reader_thread is not None:
            reader_thread.join(
                timeout=1.0
            )

        if tank is not None:
            tank.disable()

        if turret is not None:
            turret.close()

        if pi is not None:
            pi.stop()

        print()
        print()
        print("======================================")
        print("TANK SAFE")
        print("======================================")
        print()

        print("Tracks stopped.")
        print("Turret stopped.")
        print("Laser off.")
        print("Barrel PWM disabled.")
        print("Controller closed.")


if __name__ == "__main__":
    main()
