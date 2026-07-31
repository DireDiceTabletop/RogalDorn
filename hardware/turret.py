from hardware.continuous_servo import ContinuousRotationServo


class Turret:
    """
    Controls horizontal turret rotation.

    Higher-level code uses left and right directions without needing
    to know about servo forward/reverse directions or pulse widths.
    """

    def __init__(
        self,
        servo: ContinuousRotationServo,
        left_direction: int = -1,
    ) -> None:
        if left_direction not in (-1, 1):
            raise ValueError("left_direction must be either -1 or 1.")

        self._servo = servo
        self._left_direction = left_direction

    def rotate_left(self, speed: float = 1.0) -> None:
        """Rotate the turret left at a speed from 0.0 to 1.0."""
        speed = self._validate_speed(speed)
        self._servo.speed(self._left_direction * speed)

    def rotate_right(self, speed: float = 1.0) -> None:
        """Rotate the turret right at a speed from 0.0 to 1.0."""
        speed = self._validate_speed(speed)
        self._servo.speed(-self._left_direction * speed)

    def stop(self) -> None:
        """Stop turret rotation."""
        self._servo.stop()

    def disable(self) -> None:
        """Stop sending PWM pulses to the turret servo."""
        self._servo.disable()

    @staticmethod
    def _validate_speed(speed: float) -> float:
        speed = float(speed)

        if not 0.0 <= speed <= 1.0:
            raise ValueError(
                "Turret speed must be between 0.0 and 1.0."
            )

        return speed
