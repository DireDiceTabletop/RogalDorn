from dataclasses import dataclass
from enum import Enum


class AimDirection(Enum):
    """Possible horizontal aiming directions."""

    LEFT = "left"
    CENTRED = "centred"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class AimingCommand:
    """
    Logical aiming command.

    strength:
        0.0 = smallest correction
        1.0 = maximum correction
    """

    direction: AimDirection
    strength: float
    error_x: int

    @property
    def is_centred(self) -> bool:
        """Return True when no movement is required."""

        return self.direction is AimDirection.CENTRED


class AimingController:
    """
    Convert horizontal image error into a logical correction.

    The controller does not know anything about servo calibration.

    Inside the deadzone:
        stop immediately.

    Outside the deadzone:
        require consecutive confirmation frames before movement
        starts or changes direction.

    Correction strength increases from 0.0 to 1.0 as the
    target moves farther from image centre.
    """

    def __init__(
        self,
        deadzone: int = 20,
        max_error: int = 120,
        confirm_frames: int = 2,
    ) -> None:
        if deadzone < 0:
            raise ValueError(
                "Deadzone must be zero or greater."
            )

        if max_error <= deadzone:
            raise ValueError(
                "max_error must be greater than deadzone."
            )

        if confirm_frames < 1:
            raise ValueError(
                "confirm_frames must be at least 1."
            )

        self._deadzone = deadzone
        self._max_error = max_error
        self._confirm_frames = confirm_frames

        self._pending_direction: AimDirection | None = None
        self._pending_frames = 0

        self._active_direction = AimDirection.CENTRED

    @property
    def deadzone(self) -> int:
        return self._deadzone

    @property
    def max_error(self) -> int:
        return self._max_error

    @property
    def confirm_frames(self) -> int:
        return self._confirm_frames

    @property
    def active_direction(self) -> AimDirection:
        return self._active_direction

    def reset(self) -> None:
        """Return the controller to a stopped state."""

        self._pending_direction = None
        self._pending_frames = 0
        self._active_direction = AimDirection.CENTRED

    def calculate(
        self,
        error_x: int,
    ) -> AimingCommand:
        """Calculate the next logical aiming command."""

        # Absolute stop zone.
        if abs(error_x) <= self._deadzone:
            self.reset()

            return AimingCommand(
                direction=AimDirection.CENTRED,
                strength=0.0,
                error_x=error_x,
            )

        desired_direction = (
            AimDirection.LEFT
            if error_x < 0
            else AimDirection.RIGHT
        )

        # Already moving in the correct direction.
        if self._active_direction is desired_direction:
            return self._movement_command(
                direction=desired_direction,
                error_x=error_x,
            )

        # New movement or direction reversal.
        if self._pending_direction is desired_direction:
            self._pending_frames += 1
        else:
            self._pending_direction = desired_direction
            self._pending_frames = 1

        if self._pending_frames < self._confirm_frames:
            return AimingCommand(
                direction=AimDirection.CENTRED,
                strength=0.0,
                error_x=error_x,
            )

        self._active_direction = desired_direction
        self._pending_direction = None
        self._pending_frames = 0

        return self._movement_command(
            direction=desired_direction,
            error_x=error_x,
        )

    def _movement_command(
        self,
        direction: AimDirection,
        error_x: int,
    ) -> AimingCommand:
        """Create a proportional correction-strength command."""

        magnitude = abs(error_x)

        usable_error = (
            self._max_error - self._deadzone
        )

        current_error = (
            magnitude - self._deadzone
        )

        strength = (
            current_error / usable_error
        )

        strength = max(
            0.0,
            min(1.0, strength),
        )

        return AimingCommand(
            direction=direction,
            strength=strength,
            error_x=error_x,
        )
