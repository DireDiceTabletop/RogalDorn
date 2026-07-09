"""
Rogal Dorn Tank Configuration
"""

# -------------------------------------------------
# Continuous Rotation Servos (FS90R)
# -------------------------------------------------

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

TURRET = {
    "gpio": 25,
    "stop": 1485,
    "forward": 1600,
    "reverse": 1300,
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
HALL_SENSOR_GPIO = 22

# -------------------------------------------------
# Turret Limits
# -------------------------------------------------

TURRET_MIN = -80
TURRET_MAX = 80
TURRET_HOME = 0
