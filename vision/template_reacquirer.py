import cv2
import numpy as np


class TemplateReacquirer:
    """
    Attempt to recover a recently lost target using
    template matching.

    This is not a general object detector.

    It is intended for short-term recovery when a tracker
    loses an object because the camera moved and the object
    has shifted within the image.
    """

    def __init__(
        self,
        threshold: float = 0.55,
        search_scale: float = 3.0,
    ) -> None:
        self._threshold = threshold
        self._search_scale = search_scale

        self._template = None
        self._last_bbox = None

    @property
    def threshold(self) -> float:
        return self._threshold

    def reset(self) -> None:
        self._template = None
        self._last_bbox = None

    def remember(
        self,
        frame: np.ndarray,
        bbox,
    ) -> None:
        """
        Remember the most recent successfully tracked target.

        bbox:
            (x, y, width, height)
        """

        x, y, width, height = (
            int(value)
            for value in bbox
        )

        frame_height, frame_width = frame.shape[:2]

        x = max(0, x)
        y = max(0, y)

        right = min(
            frame_width,
            x + width,
        )

        bottom = min(
            frame_height,
            y + height,
        )

        if right <= x or bottom <= y:
            return

        template = frame[
            y:bottom,
            x:right,
        ]

        if template.size == 0:
            return

        self._template = self._to_gray(
            template
        ).copy()

        self._last_bbox = (
            x,
            y,
            right - x,
            bottom - y,
        )

    def reacquire(
        self,
        frame: np.ndarray,
    ):
        """
        Search around the last known target position.

        Returns:
            (bbox, score)

        or:
            None
        """

        if (
            self._template is None
            or self._last_bbox is None
        ):
            return None

        frame_gray = self._to_gray(
            frame
        )

        (
            last_x,
            last_y,
            last_width,
            last_height,
        ) = self._last_bbox

        frame_height, frame_width = frame_gray.shape[:2]

        centre_x = (
            last_x
            + last_width / 2
        )

        centre_y = (
            last_y
            + last_height / 2
        )

        search_width = int(
            last_width
            * self._search_scale
        )

        search_height = int(
            last_height
            * self._search_scale
        )

        search_x = int(
            centre_x
            - search_width / 2
        )

        search_y = int(
            centre_y
            - search_height / 2
        )

        search_x = max(
            0,
            search_x,
        )

        search_y = max(
            0,
            search_y,
        )

        search_right = min(
            frame_width,
            search_x + search_width,
        )

        search_bottom = min(
            frame_height,
            search_y + search_height,
        )

        search_region = frame_gray[
            search_y:search_bottom,
            search_x:search_right,
        ]

        template_height, template_width = (
            self._template.shape[:2]
        )

        region_height, region_width = (
            search_region.shape[:2]
        )

        if (
            region_width < template_width
            or region_height < template_height
        ):
            return None

        result = cv2.matchTemplate(
            search_region,
            self._template,
            cv2.TM_CCOEFF_NORMED,
        )

        (
            _min_score,
            max_score,
            _min_location,
            max_location,
        ) = cv2.minMaxLoc(
            result
        )

        if max_score < self._threshold:
            return None

        match_x = (
            search_x
            + max_location[0]
        )

        match_y = (
            search_y
            + max_location[1]
        )

        bbox = (
            match_x,
            match_y,
            template_width,
            template_height,
        )

        return (
            bbox,
            float(max_score),
        )

    @staticmethod
    def _to_gray(
        frame: np.ndarray,
    ) -> np.ndarray:
        if len(frame.shape) == 2:
            return frame

        return cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2GRAY,
        )
