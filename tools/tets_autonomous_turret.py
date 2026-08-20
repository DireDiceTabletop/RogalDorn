import time

import cv2
import pigpio

from config import HALL_SENSORS, TURRET
from control.aiming import AimDirection, AimingController
from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor
from hardware.turret import Turret
from vision.camera import Camera
from vision.detector import FaceDetector
from vision.tracker import TargetTracker


WIDTH = 320
HEIGHT = 180
CAMERA_ROTATION = 270

DEADZONE = 20
TRACKING_SPEED = 0.25

HOMING_SPEED = 0.25
HOMING_TIMEOUT = 3.0

REPORT_INTERVAL = 0.2


def main() -> None:
    pi = None
    turret = None
    camera = None

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
            left_direction=-1,
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
            tracking_speed=TRACKING_SPEED,
        )

        # ---------------------------------------------------------
        # Initial status
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
            f"Deadzone      : ±{aiming.deadzone}px"
        )
        print(
            f"Tracking speed: "
            f"{aiming.tracking_speed:.2f}"
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
        # Prepare for autonomous operation
        # ---------------------------------------------------------

        print("Place your face in front of the camera.")
        print()

        input(
            "Press Enter to begin autonomous tracking, "
            "or Ctrl+C to cancel..."
        )

        print()
        print("Starting camera...")

        camera.start()

        # Allow camera controls/exposure to settle.
        time.sleep(2.0)

        # Discard startup frames.
        for _ in range(5):
            camera.capture_array()

        # ---------------------------------------------------------
        # YuNet acquisition
        # ---------------------------------------------------------

        print()
        print("Acquiring face with YuNet...")
        print("This may take a few seconds.")
        print()

        frame = camera.capture_array()

        detect_start = time.perf_counter()
        targets = detector.detect(frame)
        detect_time = time.perf_counter() - detect_start

        target = target_selector.select_target(targets)

        if target is None:
            turret.stop()

            print(
                f"No face detected "
                f"({detect_time:.2f}s)."
            )
            print("Turret stopped.")
            return

        print(
            f"Face acquired in {detect_time:.2f}s"
        )

        print(
            "Initial box: "
            f"x={target.x}, "
            f"y={target.y}, "
            f"w={target.width}, "
            f"h={target.height}"
        )

        # ---------------------------------------------------------
        # MOSSE initialization
        # ---------------------------------------------------------

        tracker = cv2.legacy.TrackerMOSSE_create()

        bounding_box = (
            target.x,
            target.y,
            target.width,
            target.height,
        )

        tracker.init(
            frame,
            bounding_box,
        )

        print()
        print("AUTONOMOUS TRACKING ACTIVE")
        print("Press Ctrl+C to stop.")
        print()

        last_report = 0.0

        # ---------------------------------------------------------
        # Tracking / aiming loop
        # ---------------------------------------------------------

        while True:
            loop_start = time.perf_counter()

            capture_start = time.perf_counter()
            frame = camera.capture_array()
            capture_time = (
                time.perf_counter() - capture_start
            )

            track_start = time.perf_counter()
            success, box = tracker.update(frame)
            track_time = (
                time.perf_counter() - track_start
            )

            # -----------------------------------------------------
            # Safety: loss of tracking means immediate STOP
            # -----------------------------------------------------

            if not success:
                turret.stop()

                print()
                print("TRACK LOST -> TURRET STOPPED")
                break

            # -----------------------------------------------------
            # Calculate target position
            # -----------------------------------------------------

            x, y, width, height = box

            target_centre_x = x + (width / 2)
            target_centre_y = y + (height / 2)

            frame_height, frame_width = frame.shape[:2]

            frame_centre_x = frame_width / 2
            frame_centre_y = frame_height / 2

            error_x = int(
                target_centre_x - frame_centre_x
            )

            error_y = int(
                target_centre_y - frame_centre_y
            )

            # -----------------------------------------------------
            # Convert position error into an aiming command
            # -----------------------------------------------------

            command = aiming.calculate(error_x)

            # -----------------------------------------------------
            # Execute command
            #
            # Hall-limit protection remains inside Turret.
            # -----------------------------------------------------

            if command.direction is AimDirection.LEFT:
                turret.rotate_left(
                    command.speed
                )

            elif command.direction is AimDirection.RIGHT:
                turret.rotate_right(
                    command.speed
                )

            else:
                turret.stop()

            # -----------------------------------------------------
            # Reporting
            #
            # Only the printing is rate-limited.
            # Turret control above happens on every frame.
            # -----------------------------------------------------

            now = time.perf_counter()

            if now - last_report >= REPORT_INTERVAL:
                last_report = now

                loop_time = (
                    time.perf_counter() - loop_start
                )

                if loop_time > 0:
                    fps = 1.0 / loop_time
                else:
                    fps = 0.0

                capture_ms = capture_time * 1000
                track_ms = track_time * 1000

                print(
                    f"X={error_x:+4d}  "
                    f"Y={error_y:+4d}  "
                    f"AIM="
                    f"{command.direction.value.upper():7}  "
                    f"SPEED={command.speed:.2f}  "
                    f"FPS={fps:5.1f}  "
                    f"capture={capture_ms:5.1f}ms  "
                    f"track={track_ms:5.1f}ms"
                )

    except KeyboardInterrupt:
        print()
        print("Tracking cancelled.")

    except (RuntimeError, TimeoutError) as error:
        print()
        print(f"TEST FAILED: {error}")

    finally:
        # ---------------------------------------------------------
        # Fail-safe shutdown
        # ---------------------------------------------------------

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
