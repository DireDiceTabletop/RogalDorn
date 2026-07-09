import pigpio


class Servo:

    MIN_PULSE = 500
    MAX_PULSE = 2500

    def __init__(self, pi, gpio):
        self.pi = pi
        self.gpio = gpio

    def pulse(self, pulse):
        pulse = max(self.MIN_PULSE, min(self.MAX_PULSE, pulse))
        self.pi.set_servo_pulsewidth(self.gpio, pulse)

    def disable(self):
        """Completely stop sending PWM."""
        self.pi.set_servo_pulsewidth(self.gpio, 0)
