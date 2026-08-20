import time

from config import TURRET
from control.aiming import AimDirection, AimingCommand
from hardware.turret import Turret


RIGHT_START_DURATION = 0.10


def _map_strength(
    strength: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Map a logical correction strength from 0.0–1.0
    onto a calibrated physical range.
    """

    strength = max(
        0.0,
        min(1.0, float(strength)),
    )

    return (
        minimum
        + ((maximum - minimum) * strength)
    )


def get_physical_speed(
    command: AimingCommand,
) -> float:
    """
    Return the calibrated physical speed for the
    requested tank-relative direction.
    """

    if command.direction is AimDirection.LEFT:
        return _map_strength(
            command.strength,
            TURRET["tracking_left_min"],
            TURRET["tracking_left_max"],
        )

    if command.direction is AimDirection.RIGHT:
        return _map_strength(
            command.strength,
            TURRET["tracking_right_min"],
            TURRET["tracking_right_max"],
        )

    return 0.0


def get_pulse_duration(
    command: AimingCommand,
) -> float:
    """
    Return the calibrated movement duration for
    the requested tank-relative direction.
    """

    if command.direction is AimDirection.LEFT:
        return _map_strength(
            command.strength,
            TURRET["tracking_left_pulse_min"],
            TURRET["tracking_left_pulse_max"],
        )

    if command.direction is AimDirection.RIGHT:
        return _map_strength(
            command.strength,
            TURRET["tracking_right_pulse_min"],
            TURRET["tracking_right_pulse_max"],
        )

    return 0.0


def apply_aiming_command(
    turret: Turret,
    command: AimingCommand,
) -> tuple[float, float]:
    """
    Apply one Hall-protected aiming correction.

    LEFT and RIGHT are always tank-relative.

    Tank-right movement receives a brief startup boost
    before the normal calibrated tracking pulse.

    Returns:
        physical_speed,
        pulse_duration
    """

    if command.direction is AimDirection.CENTRED:
        turret.stop()

        return 0.0, 0.0

    physical_speed = get_physical_speed(
        command
    )

    pulse_duration = get_pulse_duration(
        command
    )

    try:
        # -------------------------------------------------
        # Tank LEFT
        # -------------------------------------------------

        if command.direction is AimDirection.LEFT:
            allowed = turret.rotate_left(
                physical_speed
            )

            if not allowed:
                turret.stop()

                return 0.0, 0.0

            time.sleep(
                pulse_duration
            )

        # -------------------------------------------------
        # Tank RIGHT
        # -------------------------------------------------

        elif command.direction is AimDirection.RIGHT:
            # Brief startup boost to overcome the higher
            # breakaway threshold in this direction.
            allowed = turret.rotate_right(
                TURRET["tracking_right_start"]
            )

            if not allowed:
                turret.stop()

                return 0.0, 0.0

            time.sleep(
                RIGHT_START_DURATION
            )

            # Apply the normal calibrated right-side
            # tracking command after startup.
            allowed = turret.rotate_right(
                physical_speed
            )

            if not allowed:
                turret.stop()

                return 0.0, 0.0

            time.sleep(
                pulse_duration
            )

    finally:
        # Every correction ends at STOP before the
        # next camera/tracking update.
        turret.stop()

    return (
        physical_speed,
        pulse_duration,
    )
