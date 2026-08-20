# ---------------------------------------------------------
# Track servos
# ---------------------------------------------------------

LEFT_TRACK = {
    "gpio": 23,
    "stop": 1460,
    "forward": 1750,
    "reverse": 1250,
}


RIGHT_TRACK = {
    "gpio": 24,
    "stop": 1460,
    "forward": 1750,
    "reverse": 1250,
}


# ---------------------------------------------------------
# Turret servo
# ---------------------------------------------------------

TURRET = {
    "gpio": 25,

    # Continuous-rotation servo pulse calibration.
    "stop": 1500,
    "forward": 1800,
    "reverse": 1200,

    # Direction convention:
    #
    # LEFT and RIGHT are ALWAYS from the tank's perspective
    # while driving forwards.
    #
    # 1 has been physically calibrated so:
    #
    # turret.rotate_left()
    #     -> tank LEFT
    #
    # turret.rotate_right()
    #     -> tank RIGHT
    "tank_left_direction": 1,

    # -----------------------------------------------------
    # Tracking speed calibration
    #
    # The assembled turret has significantly different
    # effective speed ranges in each direction.
    # -----------------------------------------------------

    # Tank LEFT:
    # ~0.05 is approximately the lowest useful movement.
    # ~0.10 is approximately the maximum useful tracking
    # speed before movement becomes too aggressive.
    "tracking_left_min": 0.05,
    "tracking_left_max": 0.10,

    # Tank RIGHT:
    # ~0.17 begins movement.
    # ~0.21 roughly matches the useful upper LEFT speed.
    "tracking_right_min": 0.17,
    "tracking_right_max": 0.21,

    # -----------------------------------------------------
    # Right-side startup boost
    #
    # Tank RIGHT requires more breakaway force from rest.
    # Every pulse begins from STOP, so a short stronger
    # command is applied before the normal tracking pulse.
    # -----------------------------------------------------

    "tracking_right_start": 0.21,
    "tracking_right_start_duration": 0.03,

    # -----------------------------------------------------
    # Tracking pulse durations
    #
    # Movement is deliberately pulsed rather than leaving
    # the servo running throughout the vision-processing
    # interval.
    # -----------------------------------------------------

    # Tank LEFT pulse range.
    "tracking_left_pulse_min": 0.010,
    "tracking_left_pulse_max": 0.019,

    # Tank RIGHT normal pulse range.
    # The startup duration above occurs before this pulse.
    "tracking_right_pulse_min": 0.028,
    "tracking_right_pulse_max": 0.040,
}


# ---------------------------------------------------------
# Turret position limits
# ---------------------------------------------------------

TURRET_MIN = -80
TURRET_MAX = 80
TURRET_HOME = 0


# ---------------------------------------------------------
# Hall-effect sensors
#
# LEFT and RIGHT follow the same tank-relative convention:
#
# LEFT  = tank's left while driving forwards
# RIGHT = tank's right while driving forwards
# ---------------------------------------------------------

HALL_SENSORS = {
    "left": 19,
    "home": 20,
    "right": 16,
}


# ---------------------------------------------------------
# Barrel elevation servo
# ---------------------------------------------------------

BARREL = {
    "gpio": 26,
    "home": 45,
    "min_angle": 20,
    "max_angle": 70,
}
