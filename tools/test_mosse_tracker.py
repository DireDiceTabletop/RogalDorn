import time

import cv2

from vision.camera import Camera
from vision.detector import FaceDetector
from vision.tracker import TargetTracker


WIDTH = 320
HEIGHT = 180

REPORT_INTERVAL = 0.2


def main() -> None:
    camera = Camera(
        width=WIDTH,
        height=HEIGHT,
        frame_rate=30,
        rotation=90,
    )

    detector = FaceDetector(
        score_threshold=0.5,
    )

    target_selector = TargetTracker()

    print("Headless MOSSE tracker test")
    print("---------------------------")
    print()
    print("YuNet will acquire the face once.")
    print("MOSSE will then track it frame-to-frame.")
    print("No turret movement will occur.")
    print()
    print("Starting camera...")

    try:
        camera.start()

        print("Waiting for camera to settle...")
        time.sleep(2)

        print("Discarding initial frames...")

        for _ in range(5):
            camera.capture_array()

        # -----------------------------------------
        # Initial face acquisition using YuNet
        # -----------------------------------------

        print()
        print("Looking for face...")
        print("Hold reasonably still during acquisition.")

        frame = camera.capture_array()

        detect_start = time.monotonic()

        targets = detector.detect(frame)

        detect_time = (
            time.monotonic() - detect_start
        )

        target = target_selector.select_target(targets)

        if target is None:
            print()
            print(
                f"No face detected "
                f"({detect_time:.2f} seconds)."
            )
            print("Run the test again.")
            return

        print()
        print(
            f"Face acquired in "
            f"{detect_time:.2f} seconds."
        )

        print(
            f"Initial box: "
            f"x={target.x}, "
            f"y={target.y}, "
            f"w={target.width}, "
            f"h={target.height}"
        )

        # -----------------------------------------
        # Initialise MOSSE from YuNet bounding box
        # -----------------------------------------

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
        print("MOSSE tracking started.")
        print("Move slowly left and right.")
        print("Press Ctrl+C to stop.")
        print()

        last_report = 0.0

        # -----------------------------------------
        # Live MOSSE tracking
        # -----------------------------------------

        while True:
            loop_start = time.monotonic()

            capture_start = time.monotonic()

            frame = camera.capture_array()

            capture_time = (
                time.monotonic() - capture_start
            )

            track_start = time.monotonic()

            success, box = tracker.update(frame)

            track_time = (
                time.monotonic() - track_start
            )

            loop_time = (
                time.monotonic() - loop_start
            )

            if loop_time > 0:
                fps = 1.0 / loop_time
            else:
                fps = 0.0

            current_time = time.monotonic()

            if (
                current_time - last_report
                < REPORT_INTERVAL
            ):
                continue

            last_report = current_time

            if not success:
                print(
                    "\r"
                    f"TRACK LOST  "
                    f"FPS={fps:5.1f}  "
                    f"capture={capture_time * 1000:5.1f}ms  "
                    f"track={track_time * 1000:5.1f}ms     ",
                    end="",
                    flush=True,
                )

                continue

            x, y, width, height = [
                int(value)
                for value in box
            ]

            centre_x = (
                x + width // 2
            )

            centre_y = (
                y + height // 2
            )

            frame_height, frame_width = frame.shape[:2]

            error_x = (
                centre_x - frame_width // 2
            )

            error_y = (
                centre_y - frame_height // 2
            )

            print(
                "\r"
                f"X={error_x:+4d}  "
                f"Y={error_y:+4d}  "
                f"FPS={fps:5.1f}  "
                f"capture={capture_time * 1000:5.1f}ms  "
                f"track={track_time * 1000:5.1f}ms     ",
                end="",
                flush=True,
            )

    except KeyboardInterrupt:
        print()
        print()
        print("Tracker test stopped.")

    finally:
        camera.stop()
        camera.close()

        print("Camera stopped.")


if __name__ == "__main__":
    main()
