import time

from config import TURRET
from control.aiming import AimDirection, AimingCommand
from hardware.turret import Turret


def _map_strength(
    strength: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Map a logical correction strength from 0.0-1.0
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
    Return the calibrated physical servo speed for the
    requested tank-relative aiming direction.
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


def get_pulse_duration(
    command: AimingCommand,
) -> float:
    """
    Return the total movement duration for one aiming pulse.
    """

    if command.direction is AimDirection.LEFT:
        return _map_strength(
            strength=command.strength,
            minimum=TURRET["tracking_left_pulse_min"],
            maximum=TURRET["tracking_left_pulse_max"],
        )

    if command.direction is AimDirection.RIGHT:
        return _map_strength(
            strength=command.strength,
            minimum=TURRET["tracking_right_pulse_min"],
            maximum=TURRET["tracking_right_pulse_max"],
        )

    return 0.0


def apply_aiming_command(
    turret: Turret,
    command: AimingCommand,
) -> tuple[float, float]:
    """
    Apply one short Hall-protected aiming correction.

    LEFT and RIGHT are always tank-relative.

    Tank LEFT:
        Move at the calibrated proportional speed for the
        entire pulse.

    Tank RIGHT:
        Use the stronger startup speed for the beginning
        of the pulse, then switch to the normal proportional
        speed for the remainder.

    The right startup boost is INCLUDED in the total pulse
    duration. It is not added on top.

    Every correction ends at STOP before the next camera
    and tracker update.

    Returns:
        physical_speed
        total_pulse_duration
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
        # TANK LEFT
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
        # TANK RIGHT
        # -------------------------------------------------

        elif command.direction is AimDirection.RIGHT:
            startup_speed = TURRET[
                "tracking_right_start"
            ]

            startup_duration = TURRET[
                "tracking_right_start_duration"
            ]

            # Startup is part of the total pulse rather
            # than additional movement.
            startup_duration = min(
                startup_duration,
                pulse_duration,
            )

            allowed = turret.rotate_right(
                startup_speed
            )

            if not allowed:
                turret.stop()

                return 0.0, 0.0

            time.sleep(
                startup_duration
            )

            remaining_duration = (
                pulse_duration
                - startup_duration
            )

            if remaining_duration > 0:
                allowed = turret.rotate_right(
                    physical_speed
                )

                if not allowed:
                    turret.stop()

                    return 0.0, 0.0

                time.sleep(
                    remaining_duration
                )

    finally:
        # Always stop before the next vision update.
        turret.stop()

    return (
        physical_speed,
        pulse_duration,
    )
