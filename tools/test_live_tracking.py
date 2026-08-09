import time

from vision.camera import Camera
from vision.detector import FaceDetector
from vision.tracker import TargetTracker


HORIZONTAL_DEADZONE = 60


def get_direction(error_x: int) -> str:
    """
    Convert horizontal target error into an aiming direction.

    A dead zone prevents tiny movements around the image centre
    from constantly changing direction.
    """

    if error_x < -HORIZONTAL_DEADZONE:
        return "LEFT"

    if error_x > HORIZONTAL_DEADZONE:
        return "RIGHT"

    return "CENTRED"


def main() -> None:
    camera = Camera(
        width=320,
        height=180,
        frame_rate=30,
        rotation=90,
    )

    detector = FaceDetector(
        score_threshold=0.5,
    )

    tracker = TargetTracker()

    print("Live face tracking performance test")
    print("-----------------------------------")
    print("No turret movement will occur.")
    print()
    print(
        f"Horizontal dead zone: "
        f"±{HORIZONTAL_DEADZONE} pixels"
    )
    print()
    print("Performance values:")
    print("  FPS     = completed processing loops per second")
    print("  capture = time waiting for camera frame")
    print("  detect  = time spent running YuNet")
    print()
    print("Press Ctrl+C to stop.")
    print()

    try:
        print("Starting camera...")
        camera.start()

        print("Waiting for camera to settle...")
        time.sleep(2)

        print("Discarding initial frames...")

        for _ in range(5):
            camera.capture_array()

        print("Tracking started.")
        print()

        while True:
            loop_start = time.monotonic()

            # -----------------------------------------
            # Capture frame
            # -----------------------------------------

            capture_start = time.monotonic()

            frame = camera.capture_array()

            capture_time = (
                time.monotonic() - capture_start
            )

            # -----------------------------------------
            # Detect faces
            # -----------------------------------------

            detection_start = time.monotonic()

            targets = detector.detect(frame)

            detection_time = (
                time.monotonic() - detection_start
            )

            # -----------------------------------------
            # Select target
            # -----------------------------------------

            target = tracker.select_target(targets)

            # -----------------------------------------
            # Calculate total loop speed
            # -----------------------------------------

            loop_time = (
                time.monotonic() - loop_start
            )

            if loop_time > 0:
                fps = 1.0 / loop_time
            else:
                fps = 0.0

            # -----------------------------------------
            # No target
            # -----------------------------------------

            if target is None:
                print(
                    "\r"
                    f"Target: NONE  "
                    f"FPS={fps:4.1f}  "
                    f"capture={capture_time * 1000:4.0f}ms  "
                    f"detect={detection_time * 1000:4.0f}ms     ",
                    end="",
                    flush=True,
                )

                continue

            # -----------------------------------------
            # Calculate target position
            # -----------------------------------------

            frame_height, frame_width = frame.shape[:2]

            frame_centre_x = frame_width // 2
            frame_centre_y = frame_height // 2

            error_x = (
                target.centre_x - frame_centre_x
            )

            error_y = (
                target.centre_y - frame_centre_y
            )

            direction = get_direction(error_x)

            # -----------------------------------------
            # Report
            # -----------------------------------------

            print(
                "\r"
                f"Faces={len(targets)}  "
                f"X={error_x:+4d}  "
                f"Y={error_y:+4d}  "
                f"{direction:7}  "
                f"FPS={fps:4.1f}  "
                f"capture={capture_time * 1000:4.0f}ms  "
                f"detect={detection_time * 1000:4.0f}ms     ",
                end="",
                flush=True,
            )

    except KeyboardInterrupt:
        print()
        print()
        print("Tracking test stopped.")

    finally:
        camera.stop()
        camera.close()

        print("Camera stopped.")


if __name__ == "__main__":
    main()
