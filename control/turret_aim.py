from config import TURRET
from control.aiming import AimDirection, AimingCommand
from hardware.turret import Turret


def _map_strength(
    strength: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Map a logical correction strength from 0.0–1.0
    onto a physical servo speed range.
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
    Convert a logical aiming command into the calibrated
    physical speed for that tank-relative direction.
    """

    if command.direction is AimDirection.LEFT:
        return _map_strength(
            strength=command.strength,
            minimum=TURRET["tracking_left_min"],
            maximum=TURRET["tracking_left_max"],
        )

    if command.direction is AimDirection.RIGHT:
        return _map_strength(
            strength=command.strength,
            minimum=TURRET["tracking_right_min"],
            maximum=TURRET["tracking_right_max"],
        )

    return 0.0


def apply_aiming_command(
    turret: Turret,
    command: AimingCommand,
) -> float:
    """
    Apply a logical aiming command to the physical turret.

    LEFT and RIGHT are always tank-relative:
        LEFT  = tank's left while driving forwards
        RIGHT = tank's right while driving forwards

    Returns the actual physical speed sent to the turret.
    """

    physical_speed = get_physical_speed(
        command
    )

    if command.direction is AimDirection.LEFT:
        turret.rotate_left(
            physical_speed
        )

    elif command.direction is AimDirection.RIGHT:
        turret.rotate_right(
            physical_speed
        )

    else:
        turret.stop()

    return physical_speed
