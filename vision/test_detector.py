import time
from pathlib import Path

import cv2

from vision.camera import Camera
from vision.detector import FaceDetector
from vision.tracker import TargetTracker


def main() -> None:
    output_directory = Path(__file__).resolve().parent / "output"
    output_directory.mkdir(parents=True, exist_ok=True)

    raw_output_file = output_directory / "raw_camera_frame.jpg"
    detected_output_file = output_directory / "detected_faces.jpg"

    camera = Camera(
        width=1280,
        height=720,
        frame_rate=30,
        rotation=90,
    )

    detector = FaceDetector(
        score_threshold=0.5,
    )

    tracker = TargetTracker()

    frame = None

    try:
        print("Starting camera...")
        camera.start()

        print("Waiting for camera to settle...")
        time.sleep(2)

        print("Discarding initial frames...")
        for _ in range(5):
            camera.capture_array()

        print("Capturing test frame...")
        frame = camera.capture_array()

    finally:
        camera.stop()
        camera.close()
        print("Camera stopped.")

    if frame is None:
        raise RuntimeError("Camera returned no frame.")

    print(f"Frame shape: {frame.shape}")

    if not cv2.imwrite(str(raw_output_file), frame):
        raise RuntimeError(
            f"Failed to save raw image: {raw_output_file}"
        )

    targets = detector.detect(frame)
    selected_target = tracker.select_target(targets)

    print(f"Detected {len(targets)} face(s).")

    for target in targets:
        is_selected = target is selected_target

        colour = (
            (0, 0, 255)
            if is_selected
            else (0, 255, 0)
        )

        label = (
            f"TARGET {target.confidence:.2f}"
            if is_selected
            else f"Face {target.confidence:.2f}"
        )

        cv2.rectangle(
            frame,
            (target.x, target.y),
            (target.right, target.bottom),
            colour,
            2,
        )

        cv2.circle(
            frame,
            (target.centre_x, target.centre_y),
            5,
            colour,
            -1,
        )

        cv2.putText(
            frame,
            label,
            (target.x, max(20, target.y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            colour,
            1,
            cv2.LINE_AA,
        )

        print(
            f"{'Selected target' if is_selected else 'Face'}: "
            f"centre=({target.centre_x}, {target.centre_y}), "
            f"size={target.width}x{target.height}, "
            f"area={target.area}, "
            f"confidence={target.confidence:.3f}"
        )

    if selected_target is None:
        print("No target selected.")
    else:
        frame_height, frame_width = frame.shape[:2]

        frame_centre_x = frame_width // 2
        frame_centre_y = frame_height // 2

        horizontal_error = (
            selected_target.centre_x - frame_centre_x
        )

        vertical_error = (
            selected_target.centre_y - frame_centre_y
        )

        print(
            "Target offset from frame centre: "
            f"x={horizontal_error}, y={vertical_error}"
        )

    if not cv2.imwrite(str(detected_output_file), frame):
        raise RuntimeError(
            f"Failed to save detection image: "
            f"{detected_output_file}"
        )

    print(f"Saved raw image: {raw_output_file}")
    print(f"Saved detection image: {detected_output_file}")


if __name__ == "__main__":
    main()
