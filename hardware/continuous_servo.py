from hardware.servo import Servo


class ContinuousRotationServo(Servo):
    """
    Driver for continuous rotation servos such as the FS90R.

    Speed values range from:
        -1.0 = Full reverse
         0.0 = Stop
        +1.0 = Full forward
    """

    def __init__(self, pi, gpio, stop, forward, reverse):
        super().__init__(pi, gpio)

        self.stop_pulse = stop
        self.forward_pulse = forward
        self.reverse_pulse = reverse

        # Initialise stopped
        self.stop()

    def stop(self):
        """Stop the servo."""
        self.pulse(self.stop_pulse)

    def forward(self):
        """Run at full forward speed."""
        self.pulse(self.forward_pulse)

    def reverse(self):
        """Run at full reverse speed."""
        self.pulse(self.reverse_pulse)

    def speed(self, speed):
        """
        Set servo speed.

        speed:
            -1.0 = Full reverse
             0.0 = Stop
            +1.0 = Full forward
        """

        # Clamp requested speed
        speed = max(-1.0, min(1.0, float(speed)))

        # Small deadband around zero
        if abs(speed) < 0.01:
            self.stop()
            return

        if speed > 0:
            pulse = self.stop_pulse + (
                (self.forward_pulse - self.stop_pulse) * speed
            )
        else:
            pulse = self.stop_pulse + (
                (self.stop_pulse - self.reverse_pulse) * speed
            )

        self.pulse(int(pulse))
