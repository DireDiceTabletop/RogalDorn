import time

import cv2

from vision.camera import Camera


HAAR_MODEL = (
    "/usr/share/opencv4/haarcascades/"
    "haarcascade_frontalface_default.xml"
)

LBP_MODEL = (
    "/usr/share/opencv4/lbpcascades/"
    "lbpcascade_frontalface.xml"
)

WIDTH = 320
HEIGHT = 180

WARMUP_RUNS = 2
BENCHMARK_RUNS = 10


def load_cascade(path: str) -> cv2.CascadeClassifier:
    detector = cv2.CascadeClassifier(path)

    if detector.empty():
        raise RuntimeError(
            f"Could not load cascade: {path}"
        )

    return detector


def detect_faces(
    detector: cv2.CascadeClassifier,
    gray_frame,
):
    return detector.detectMultiScale(
        gray_frame,
        scaleFactor=1.2,
        minNeighbors=3,
        minSize=(16, 16),
    )


def benchmark(
    name: str,
    detector: cv2.CascadeClassifier,
    gray_frame,
) -> None:
    print()
    print(f"Testing {name}...")

    # Warm up OpenCV before measuring.
    for _ in range(WARMUP_RUNS):
        detect_faces(
            detector,
            gray_frame,
        )

    times = []
    faces = []

    for _ in range(BENCHMARK_RUNS):
        start = time.monotonic()

        faces = detect_faces(
            detector,
            gray_frame,
        )

        elapsed = time.monotonic() - start

        times.append(elapsed)

    average_time = sum(times) / len(times)

    fps = (
        1.0 / average_time
        if average_time > 0
        else 0.0
    )

    print(f"Faces detected : {len(faces)}")
    print(
        f"Average detect : "
        f"{average_time * 1000:.1f} ms"
    )
    print(f"Equivalent FPS : {fps:.1f}")

    if len(faces) > 0:
        for index, (x, y, w, h) in enumerate(
            faces,
            start=1,
        ):
            centre_x = x + w // 2
            centre_y = y + h // 2

            print(
                f"Face {index}: "
                f"centre=({centre_x}, {centre_y}), "
                f"size={w}x{h}"
            )


def main() -> None:
    print("Face cascade benchmark")
    print("----------------------")
    print()
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    print()

    haar = load_cascade(HAAR_MODEL)
    lbp = load_cascade(LBP_MODEL)

    camera = Camera(
        width=WIDTH,
        height=HEIGHT,
        frame_rate=30,
        rotation=90,
    )

    try:
        print("Starting camera...")
        camera.start()

        print("Waiting for camera to settle...")
        time.sleep(2)

        print("Discarding initial frames...")

        for _ in range(5):
            camera.capture_array()

        print()
        print(
            "Look directly at the camera and remain "
            "still for the test."
        )

        time.sleep(2)

        frame = camera.capture_array()

    finally:
        camera.stop()
        camera.close()

    # Camera returns an OpenCV-ready colour frame.
    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY,
    )

    gray = cv2.equalizeHist(gray)

    benchmark(
        name="Haar",
        detector=haar,
        gray_frame=gray,
    )

    benchmark(
        name="LBP",
        detector=lbp,
        gray_frame=gray,
    )

    print()
    print("Benchmark complete.")


if __name__ == "__main__":
    main()
