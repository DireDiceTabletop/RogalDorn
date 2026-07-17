from vision.target import Target


class TargetTracker:
    """Select a target from a collection of detections."""

    def select_target(
        self,
        targets: list[Target],
    ) -> Target | None:
        """
        Select the largest visible target.

        A larger face is assumed to be closer to the camera and therefore
        receives priority.
        """

        return max(
            targets,
            key=lambda target: target.area,
            default=None,
        )
