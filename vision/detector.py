from pathlib import Path

import cv2
import numpy as np

from vision.target import Target


class FaceDetector:
    """Detect faces in OpenCV-compatible camera frames using YuNet."""

    def __init__(
        self,
        score_threshold: float = 0.5,
        nms_threshold: float = 0.3,
        top_k: int = 5000,
    ) -> None:
        model_path = (
            Path(__file__).resolve().parent
            / "models"
            / "face_detection_yunet_2023mar.onnx"
        )

        if not model_path.is_file():
            raise FileNotFoundError(
                f"YuNet model not found: {model_path}"
            )

        self.detector = cv2.FaceDetectorYN.create(
            str(model_path),
            "",
            (1280, 720),
            score_threshold=score_threshold,
            nms_threshold=nms_threshold,
            top_k=top_k,
        )

    def detect(self, frame: np.ndarray) -> list[Target]:
        """Detect faces and return them as Target objects."""

        if frame is None:
            raise ValueError("Cannot detect faces in an empty frame.")

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(
                f"Expected a three-channel image, received {frame.shape}."
            )

        height, width = frame.shape[:2]

        self.detector.setInputSize((width, height))

        _, faces = self.detector.detect(frame)

        if faces is None:
            return []

        targets: list[Target] = []

        for face in faces:
            target = Target(
                x=int(face[0]),
                y=int(face[1]),
                width=int(face[2]),
                height=int(face[3]),
                confidence=float(face[-1]),
            )

            targets.append(target)

        return targets
