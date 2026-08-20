import time

import cv2
import pigpio

from config import HALL_SENSORS, TURRET
from control.aiming import AimingController
from control.turret_aim import apply_aiming_command
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret
from vision.camera import Camera
from vision.detector import FaceDetector
from vision.tracker import TargetTracker


# ---------------------------------------------------------
# Camera
# ---------------------------------------------------------

WIDTH = 320
HEIGHT = 180
CAMERA_ROTATION = 270

# Calibrated optical centre offset.
CAMERA_X_OFFSET = 52


# ---------------------------------------------------------
# Aiming
# ---------------------------------------------------------

DEADZONE = 20
MAX_TRACKING_ERROR = 120
CONFIRM_FRAMES = 2


# ---------------------------------------------------------
# Homing
# ---------------------------------------------------------

HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0


# ---------------------------------------------------------
# Reporting
# ---------------------------------------------------------

REPORT_INTERVAL = 0.2


def main() -> None:
    pi = None
    turret = None
    camera = None
    aiming = None

    try:
        # ---------------------------------------------------------
        # Connect to pigpio
        # ---------------------------------------------------------

        pi = pigpio.pi()

        if not pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio. "
                "Check that the pigpio daemon is running."
            )

        # ---------------------------------------------------------
        # Hall sensors
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Turret servo
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Vision
        # ---------------------------------------------------------

        camera = Camera(
            width=WIDTH,
            height=HEIGHT,
            frame_rate=30,
            rotation=CAMERA_ROTATION,
        )

        detector = FaceDetector(
            score_threshold=0.5,
        )

        target_selector = TargetTracker()

        aiming = AimingController(
            deadzone=DEADZONE,
            max_error=MAX_TRACKING_ERROR,
            confirm_frames=CONFIRM_FRAMES,
        )

        # ---------------------------------------------------------
        # Startup information
        # ---------------------------------------------------------

        print("Autonomous turret tracking test")
        print("-------------------------------")
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
        print(
            f"Camera resolution : "
            f"{WIDTH}x{HEIGHT}"
        )

        print(
            f"Camera rotation   : "
            f"{CAMERA_ROTATION}"
        )

        print(
            f"Camera X offset   : "
            f"{CAMERA_X_OFFSET:+d}px"
        )

        print()
        print(
            f"Deadzone          : "
            f"±{aiming.deadzone}px"
        )

        print(
            f"Maximum error     : "
            f"±{aiming.max_error}px"
        )

        print(
            f"Confirm frames    : "
            f"{aiming.confirm_frames}"
        )

        print()
        print(
            f"Left tracking     : "
            f"{TURRET['tracking_left_min']:.2f}"
            f"–{TURRET['tracking_left_max']:.2f}"
        )

        print(
            f"Right tracking    : "
            f"{TURRET['tracking_right_min']:.2f}"
            f"–{TURRET['tracking_right_max']:.2f}"
        )

        print()
        print(
            f"Servo stop        : "
            f"{TURRET['stop']} µs"
        )

        print(
            f"Servo forward     : "
            f"{TURRET['forward']} µs"
        )

        print(
            f"Servo reverse     : "
            f"{TURRET['reverse']} µs"
        )

        print()

        input(
            "Press Enter to home the turret, "
            "or Ctrl+C to cancel..."
        )

        # ---------------------------------------------------------
        # Home turret
        # ---------------------------------------------------------

        print()
        print("Homing turret...")

        turret.home(
            speed=HOMING_SPEED,
            timeout=HOMING_TIMEOUT,
        )

        if not turret.at_home:
            raise RuntimeError(
                "Homing completed but home sensor "
                "is not active."
            )

        print("HOME FOUND")
        print("Turret centred.")
        print()

        # ---------------------------------------------------------
        # Prepare for face tracking
        # ---------------------------------------------------------

        input(
            "Place your face in view and press Enter "
            "to begin tracking..."
        )

        print()
        print("Starting camera...")

        camera.start()

        time.sleep(2.0)

        for _ in range(5):
            camera.capture_array()

        # ---------------------------------------------------------
        # Initial YuNet face acquisition
        # ---------------------------------------------------------

        print()
        print("Acquiring face with YuNet...")
        print("This may take a few seconds.")
        print()

        frame = camera.capture_array()

        detect_start = time.perf_counter()

        targets = detector.detect(frame)

        detect_time = (
            time.perf_counter()
            - detect_start
        )

        target = target_selector.select_target(
            targets
        )

        if target is None:
            aiming.reset()
            turret.stop()

            print(
                f"No face detected "
                f"({detect_time:.2f}s)."
            )

            return

        print(
            f"Face acquired in "
            f"{detect_time:.2f}s."
        )

        print(
            "Initial box: "
            f"x={target.x}, "
            f"y={target.y}, "
            f"w={target.width}, "
            f"h={target.height}"
        )

        # ---------------------------------------------------------
        # Initialise KCF
        # ---------------------------------------------------------

        tracker = cv2.legacy.TrackerKCF_create()

        tracker.init(
            frame,
            (
                target.x,
                target.y,
                target.width,
                target.height,
            ),
        )

        print()
        print("AUTONOMOUS TRACKING ACTIVE")
        print("--------------------------")
        print("Move slowly left and right.")
        print("LEFT/RIGHT are tank-relative.")
        print("Press Ctrl+C to stop.")
        print()

        last_report = 0.0

        # ---------------------------------------------------------
        # Tracking loop
        # ---------------------------------------------------------

        while True:
            loop_start = time.perf_counter()

            # -----------------------------------------------------
            # Capture frame
            # -----------------------------------------------------

            capture_start = time.perf_counter()

            frame = camera.capture_array()

            capture_time = (
                time.perf_counter()
                - capture_start
            )

            # -----------------------------------------------------
            # MOSSE update
            # -----------------------------------------------------

            track_start = time.perf_counter()

            success, box = tracker.update(
                frame
            )

            track_time = (
                time.perf_counter()
                - track_start
            )

            # -----------------------------------------------------
            # Lost target
            # -----------------------------------------------------

            if not success:
                aiming.reset()
                turret.stop()

                print()
                print(
                    "TRACK LOST -> "
                    "TURRET STOPPED"
                )

                break

            # -----------------------------------------------------
            # Target coordinates
            # -----------------------------------------------------

            x, y, width, height = box

            target_centre_x = (
                x + width / 2
            )

            target_centre_y = (
                y + height / 2
            )

            frame_height, frame_width = (
                frame.shape[:2]
            )

            # Raw target error relative to image centre.
            raw_error_x = int(
                target_centre_x
                - frame_width / 2
            )

            # Correct the camera's optical centre relative
            # to the tank's calibrated forward centreline.
            error_x = (
                raw_error_x
                - CAMERA_X_OFFSET
            )

            error_y = int(
                target_centre_y
                - frame_height / 2
            )

            # -----------------------------------------------------
            # Logical aiming command
            # -----------------------------------------------------

            command = aiming.calculate(
                error_x
            )

            # -----------------------------------------------------
            # Physical turret command
            #
            # This maps logical correction strength onto the
            # independently calibrated left/right speed ranges.
            # -----------------------------------------------------

            physical_speed, pulse_duration = apply_aiming_command(
                turret=turret,
                command=command,
            )

            # -----------------------------------------------------
            # Reporting
            # -----------------------------------------------------

            now = time.perf_counter()

            if (
                now - last_report
                < REPORT_INTERVAL
            ):
                continue

            last_report = now

            loop_time = (
                time.perf_counter()
                - loop_start
            )

            fps = (
                1.0 / loop_time
                if loop_time > 0
                else 0.0
            )

            print(
                f"RAW={raw_error_x:+4d}  "
                f"X={error_x:+4d}  "
                f"Y={error_y:+4d}  "
                f"AIM="
                f"{command.direction.value.upper():7}  "
                f"STRENGTH="
                f"{command.strength:.2f}  "
                f"SERVO="
                f"{physical_speed:.2f}  "
                f"PULSE"
                f"PULSE={pulse_duration * 1000:4.0f}ms  "
                f"ACTIVE="
                f"{aiming.active_direction.value.upper():7}  "
                f"FPS={fps:5.1f}  "
                f"capture="
                f"{capture_time * 1000:5.1f}ms  "
                f"track="
                f"{track_time * 1000:5.1f}ms"
            )

    except KeyboardInterrupt:
        print()
        print("Tracking cancelled.")

    except (RuntimeError, TimeoutError) as error:
        print()
        print(
            f"TEST FAILED: {error}"
        )

    finally:
        # ---------------------------------------------------------
        # Fail-safe shutdown
        # ---------------------------------------------------------

        if aiming is not None:
            aiming.reset()

        if turret is not None:
            turret.stop()

        if camera is not None:
            camera.stop()

        if turret is not None:
            turret.close()

        if pi is not None:
            pi.stop()

        print()
        print("Turret stopped and disabled.")


if __name__ == "__main__":
    main()
