import time

import cv2

from control.aiming import AimingController
from vision.camera import Camera
from vision.detector import FaceDetector
from vision.tracker import TargetTracker


WIDTH = 320
HEIGHT = 180

DEADZONE = 20
TRACKING_SPEED = 0.25

REPORT_INTERVAL = 0.2


def main() -> None:
    camera = Camera(
        width=WIDTH,
        height=HEIGHT,
        frame_rate=30,
        rotation=270,
    )

    detector = FaceDetector(
        score_threshold=0.5,
    )

    target_selector = TargetTracker()

    aiming = AimingController(
        deadzone=DEADZONE,
        tracking_speed=TRACKING_SPEED,
    )

    print("Starting camera...")
    camera.start()

    try:
        # Give the camera time to settle.
        time.sleep(2.0)

        # Discard a few startup frames.
        for _ in range(5):
            camera.capture_array()

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
            print(
                f"No face detected "
                f"({detect_time:.2f}s)"
            )
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

        print()
        print(
            f"Aiming deadzone: ±{aiming.deadzone}px"
        )
        print(
            f"Requested turret speed: "
            f"{aiming.tracking_speed:.2f}"
        )

        print()
        print("Starting MOSSE tracking...")
        print("No turret movement will occur.")
        print("Press Ctrl+C to stop.")
        print()

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

        last_report = 0.0

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

            now = time.perf_counter()

            if now - last_report < REPORT_INTERVAL:
                continue

            last_report = now

            total_time = now - loop_start

            if total_time > 0:
                fps = 1.0 / total_time
            else:
                fps = 0.0

            capture_ms = capture_time * 1000
            track_ms = track_time * 1000

            if not success:
                print(
                    "TRACK LOST -> STOP  "
                    f"FPS={fps:5.1f}  "
                    f"capture={capture_ms:5.1f}ms  "
                    f"track={track_ms:5.1f}ms"
                )

                # For this test we stop rather than
                # attempting automatic reacquisition.
                break

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

            command = aiming.calculate(error_x)

            print(
                f"X={error_x:+4d}  "
                f"Y={error_y:+4d}  "
                f"AIM={command.direction.value.upper():7}  "
                f"SPEED={command.speed:.2f}  "
                f"FPS={fps:5.1f}  "
                f"capture={capture_ms:5.1f}ms  "
                f"track={track_ms:5.1f}ms"
            )

    except KeyboardInterrupt:
        print()
        print("Stopped.")

    finally:
        camera.stop()


if __name__ == "__main__":
    main()
