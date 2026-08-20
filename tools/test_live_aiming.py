import time

import cv2

from control.aiming import AimingController
from control.turret_aim import get_physical_speed
from vision.camera import Camera
from vision.detector import FaceDetector
from vision.tracker import TargetTracker


WIDTH = 320
HEIGHT = 180
CAMERA_ROTATION = 270

CAMERA_X_OFFSET = 52

DEADZONE = 20
MAX_TRACKING_ERROR = 120
CONFIRM_FRAMES = 2

REPORT_INTERVAL = 0.2


def main() -> None:
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

    print("Live aiming controller test")
    print("---------------------------")
    print()
    print("No turret movement will occur.")
    print()
    print(
        f"Camera X offset : "
        f"{CAMERA_X_OFFSET:+d}px"
    )
    print(
        f"Deadzone        : "
        f"±{aiming.deadzone}px"
    )
    print(
        f"Maximum error   : "
        f"±{aiming.max_error}px"
    )
    print(
        f"Confirm frames  : "
        f"{aiming.confirm_frames}"
    )
    print()

    try:
        print("Starting camera...")
        camera.start()

        time.sleep(2.0)

        for _ in range(5):
            camera.capture_array()

        print()
        print("Acquiring face with YuNet...")

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
            print(
                f"No face detected "
                f"({detect_time:.2f}s)."
            )
            return

        print(
            f"Face acquired in "
            f"{detect_time:.2f}s."
        )

        tracker = cv2.legacy.TrackerMOSSE_create()

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
        print("MOSSE tracking started.")
        print("No turret movement will occur.")
        print()

        last_report = 0.0

        while True:
            loop_start = time.perf_counter()

            capture_start = time.perf_counter()
            frame = camera.capture_array()

            capture_time = (
                time.perf_counter()
                - capture_start
            )

            track_start = time.perf_counter()

            success, box = tracker.update(
                frame
            )

            track_time = (
                time.perf_counter()
                - track_start
            )

            if not success:
                aiming.reset()

                print()
                print(
                    "TRACK LOST -> "
                    "AIMING STOPPED"
                )
                break

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

            raw_error_x = int(
                target_centre_x
                - frame_width / 2
            )

            error_x = (
                raw_error_x
                - CAMERA_X_OFFSET
            )

            error_y = int(
                target_centre_y
                - frame_height / 2
            )

            command = aiming.calculate(
                error_x
            )

            physical_speed = (
                get_physical_speed(command)
            )

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
                f"FPS={fps:5.1f}  "
                f"capture="
                f"{capture_time * 1000:5.1f}ms  "
                f"track="
                f"{track_time * 1000:5.1f}ms"
            )

    except KeyboardInterrupt:
        print()
        print("Aiming test stopped.")

    finally:
        aiming.reset()
        camera.stop()

        print("Camera stopped.")


if __name__ == "__main__":
    main()
