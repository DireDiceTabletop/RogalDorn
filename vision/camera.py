import cv2
from picamera2 import Picamera2


class Camera:
    """Picamera2 wrapper that returns upright OpenCV-ready frames."""

    VALID_ROTATIONS = {0, 90, 180, 270}

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        frame_rate: int = 30,
        rotation: int = 90,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Camera width and height must be positive.")

        if frame_rate <= 0:
            raise ValueError("Camera frame rate must be positive.")

        if rotation not in self.VALID_ROTATIONS:
            raise ValueError(
                "Rotation must be one of: 0, 90, 180, or 270."
            )

        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.rotation = rotation

        self.picamera = Picamera2()

        configuration = self.picamera.create_video_configuration(
            main={
                "size": (self.width, self.height),
                "format": "RGB888",
            },
            controls={
                "FrameRate": self.frame_rate,
            },
            buffer_count=4,
        )

        self.picamera.configure(configuration)

    def start(self) -> None:
        """Start the camera."""

        self.picamera.start()

    def stop(self) -> None:
        """Stop the camera."""

        self.picamera.stop()

    def close(self) -> None:
        """Release the camera completely."""

        self.picamera.close()

    def capture_array(self):
        """
        Capture and return an upright, three-channel frame.

        Picamera2's RGB888 array is suitable for OpenCV processing.
        Rotation is applied here so other vision modules do not need
        to know how the physical camera is mounted.
        """

        frame = self.picamera.capture_array("main")

        if frame is None:
            raise RuntimeError("Camera returned no frame.")

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise RuntimeError(
                f"Unexpected camera frame format: {frame.shape}"
            )

        if self.rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        elif self.rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        elif self.rotation == 270:
            frame = cv2.rotate(
                frame,
                cv2.ROTATE_90_COUNTERCLOCKWISE,
            )

        return frame
