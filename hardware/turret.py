import time
from threading import RLock

from hardware.continuous_servo import ContinuousRotationServo
from hardware.hall_sensor import HallSensor


class Turret:
    """
    Controls horizontal turret rotation.

    The turret owns horizontal movement, Hall-effect limits,
    and automatic homing.
    """

    def __init__(
        self,
        servo: ContinuousRotationServo,
        left_direction: int = -1,
        left_limit: HallSensor | None = None,
        home_sensor: HallSensor | None = None,
        right_limit: HallSensor | None = None,
    ) -> None:
        if left_direction not in (-1, 1):
            raise ValueError(
                "left_direction must be either -1 or 1."
            )

        self._servo = servo
        self._left_direction = left_direction

        self._left_limit = left_limit
        self._home_sensor = home_sensor
        self._right_limit = right_limit

        self._movement: str | None = None
        self._homing = False

        self._lock = RLock()
        self._callbacks = []

        if self._left_limit is not None:
            self._callbacks.append(
                self._left_limit.add_activation_callback(
                    self._handle_left_limit
                )
            )

        if self._home_sensor is not None:
            self._callbacks.append(
                self._home_sensor.add_activation_callback(
                    self._handle_home_sensor
                )
            )

        if self._right_limit is not None:
            self._callbacks.append(
                self._right_limit.add_activation_callback(
                    self._handle_right_limit
                )
            )

    @property
    def at_left_limit(self) -> bool:
        """Return True when the left limit sensor is active."""

        return (
            self._left_limit is not None
            and self._left_limit.is_active
        )

    @property
    def at_home(self) -> bool:
        """Return True when the home sensor is active."""

        return (
            self._home_sensor is not None
            and self._home_sensor.is_active
        )

    @property
    def at_right_limit(self) -> bool:
        """Return True when the right limit sensor is active."""

        return (
            self._right_limit is not None
            and self._right_limit.is_active
        )

    def rotate_left(
        self,
        speed: float = 1.0,
    ) -> bool:
        """
        Rotate left.

        Return False when movement is blocked by the left limit.
        """

        speed = self._validate_speed(speed)

        with self._lock:
            if speed == 0:
                self._stop_locked()
                return True

            if self.at_left_limit:
                self._stop_locked()
                return False

            self._movement = "left"

            self._servo.speed(
                self._left_direction * speed
            )

            return True

    def rotate_right(
        self,
        speed: float = 1.0,
    ) -> bool:
        """
        Rotate right.

        Return False when movement is blocked by the right limit.
        """

        speed = self._validate_speed(speed)

        with self._lock:
            if speed == 0:
                self._stop_locked()
                return True

            if self.at_right_limit:
                self._stop_locked()
                return False

            self._movement = "right"

            self._servo.speed(
                -self._left_direction * speed
            )

            return True

    def home(
        self,
        speed: float = 0.25,
        timeout: float = 3.0,
    ) -> None:
        """
        Find the turret's centre Hall sensor.

        The turret initially searches right. If the right limit is
        reached first, it reverses and searches left for home.

        Each search phase has a timeout as a secondary safety measure.
        """

        speed = self._validate_speed(speed)

        if speed == 0:
            raise ValueError(
                "Homing speed must be greater than zero."
            )

        if timeout <= 0:
            raise ValueError(
                "Homing timeout must be greater than zero."
            )

        if self._home_sensor is None:
            raise RuntimeError(
                "Cannot home turret without a home sensor."
            )

        if (
            self._left_limit is None
            or self._right_limit is None
        ):
            raise RuntimeError(
                "Automatic homing requires both limit sensors."
            )

        if self.at_left_limit and self.at_right_limit:
            raise RuntimeError(
                "Both turret limit sensors are active."
            )

        self.stop()

        if self.at_home:
            return

        self._homing = True

        try:
            # If already at the right limit, there is no point
            # trying to move farther right.
            if not self.at_right_limit:
                self.rotate_right(speed)

                result = self._wait_for_home_or_limit(
                    home=self._home_sensor,
                    limit=self._right_limit,
                    timeout=timeout,
                )

                if result == "home":
                    return

            # Home was not found while travelling right.
            # Move back left until the centre sensor is found.
            self.rotate_left(speed)

            result = self._wait_for_home_or_limit(
                home=self._home_sensor,
                limit=self._left_limit,
                timeout=timeout,
            )

            if result == "home":
                return

            raise RuntimeError(
                "Left limit reached without finding home."
            )

        finally:
            self.stop()
            self._homing = False

    def stop(self) -> None:
        """Stop turret rotation."""

        with self._lock:
            self._stop_locked()

    def disable(self) -> None:
        """Stop the turret and disable its PWM signal."""

        with self._lock:
            self._stop_locked()
            self._servo.disable()

    def close(self) -> None:
        """Stop the turret and clean up Hall callbacks."""

        self.disable()

        for callback in self._callbacks:
            callback.cancel()

        self._callbacks.clear()

    def _wait_for_home_or_limit(
        self,
        home: HallSensor,
        limit: HallSensor,
        timeout: float,
    ) -> str:
        """
        Wait until either home or the current travel limit is reached.
        """

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if home.is_active:
                self.stop()
                return "home"

            if limit.is_active:
                self.stop()
                return "limit"

            time.sleep(0.01)

        self.stop()

        raise TimeoutError(
            "Turret homing timed out before reaching a sensor."
        )

    def _handle_left_limit(self) -> None:
        """Immediately stop outward movement at the left limit."""

        with self._lock:
            if self._movement == "left":
                self._stop_locked()

    def _handle_home_sensor(self) -> None:
        """Immediately stop when home is detected during homing."""

        with self._lock:
            if self._homing:
                self._stop_locked()

    def _handle_right_limit(self) -> None:
        """Immediately stop outward movement at the right limit."""

        with self._lock:
            if self._movement == "right":
                self._stop_locked()

    def _stop_locked(self) -> None:
        """Stop the servo while the turret lock is already held."""

        self._movement = None
        self._servo.stop()

    @staticmethod
    def _validate_speed(speed: float) -> float:
        """Validate a turret speed from 0.0 through 1.0."""

        speed = float(speed)

        if not 0.0 <= speed <= 1.0:
            raise ValueError(
                "Turret speed must be between 0.0 and 1.0."
            )

        return speed
