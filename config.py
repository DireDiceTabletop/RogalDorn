"""
Rogal Dorn Tank Configuration
"""

# -------------------------------------------------
# Continuous Rotation Servos (FS90R)
# -------------------------------------------------

LEFT_TRACK = {
    "gpio": 23,
    "stop": 1460,
    "forward": 2000,
    "reverse": 1000,
}

RIGHT_TRACK = {
    "gpio": 24,
    "stop": 1460,
    "forward": 2000,
    "reverse": 1000,
}

TURRET = {
    "gpio": 25,
    "stop": 1500,
    "forward": 1800,
    "reverse": 1200,
    # Physical direction convention:
    #
    # LEFT and RIGHT are always from the tank's perspective
    # while driving forwards.
    #
    # We will calibrate this value using the physical
    # direction test.
    "tank_left_direction": 1,

    # Physical tracking-speed calibration.
    #
    # These values represent approximately equivalent
    # usable movement ranges in each physical direction.
    "tracking_left_min": 0.05,
    "tracking_left_max": 0.10,

    "tracking_right_min": 0.17,
    "tracking_right_max": 0.21,
}

# -------------------------------------------------
# Positional Servo (GH-S37D)
# -------------------------------------------------

BARREL = {
    "gpio": 26,
    "home": 45,
    "min_angle": 20,
    "max_angle": 70,
}

# -------------------------------------------------
# GPIO
# -------------------------------------------------

LASER_GPIO = 17
HALL_SENSORS = {
	"left": 19,
	"home": 20,
	"right": 16,
}

# -------------------------------------------------
# Turret Limits
# -------------------------------------------------

TURRET_MIN = -80
TURRET_MAX = 80
TURRET_HOME = 0
