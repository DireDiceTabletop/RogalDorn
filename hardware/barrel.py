from hardware.servo import Servo


class Barrel:
    """
    Positional barrel-elevation controller.

    The calibrated servo range is:

        UP      -> lower pulse width
        CENTRE  -> middle pulse width
        DOWN    -> higher pulse width

    Right-stick control can therefore treat positive input
    as "raise the barrel" without needing to know about
    servo pulse direction.
    """

    def __init__(
        self,
        servo: Servo,
        up_pulse: int,
        centre_pulse: int,
        down_pulse: int,
    ) -> None:
        if not (
            up_pulse
            < centre_pulse
            < down_pulse
        ):
            raise ValueError(
                "Expected up < centre < down pulse widths."
            )

        self._servo = servo

        self._up_pulse = int(up_pulse)
        self._centre_pulse = int(centre_pulse)
        self._down_pulse = int(down_pulse)

        # This represents our commanded position.
        #
        # The servo is NOT moved during construction.
        self._current_pulse = float(
            self._centre_pulse
        )

    @property
    def up_pulse(self) -> int:
        return self._up_pulse

    @property
    def centre_pulse(self) -> int:
        return self._centre_pulse

    @property
    def down_pulse(self) -> int:
        return self._down_pulse

    @property
    def current_pulse(self) -> int:
        return int(
            round(self._current_pulse)
        )

    def centre(self) -> None:
        """
        Move the barrel to its calibrated centre position.
        """

        self.set_pulse(
            self._centre_pulse
        )

    def set_pulse(
        self,
        pulse: float,
    ) -> int:
        """
        Command an absolute barrel position.

        The requested pulse is always clamped to the
        calibrated mechanical limits.
        """

        pulse = max(
            self._up_pulse,
            min(
                self._down_pulse,
                float(pulse),
            ),
        )

        self._current_pulse = pulse

        commanded_pulse = self.current_pulse

        self._servo.pulse(
            commanded_pulse
        )

        return commanded_pulse

    def update(
        self,
        elevation_input: float,
        delta_time: float,
        speed: float,
    ) -> int:
        """
        Move the barrel according to a velocity-style input.

        elevation_input:
            +1.0 = raise barrel at full speed
             0.0 = hold current position
            -1.0 = lower barrel at full speed

        delta_time:
            Seconds since the previous update.

        speed:
            Servo pulse-width movement in microseconds
            per second at full stick.

        Positive elevation reduces pulse width because our
        calibrated UP position is 1350 us.
        """

        elevation_input = max(
            -1.0,
            min(
                1.0,
                float(elevation_input),
            ),
        )

        delta_time = max(
            0.0,
            float(delta_time),
        )

        speed = max(
            0.0,
            float(speed),
        )

        if abs(elevation_input) < 0.001:
            return self.current_pulse

        movement = (
            elevation_input
            * speed
            * delta_time
        )

        new_pulse = (
            self._current_pulse
            - movement
        )

        return self.set_pulse(
            new_pulse
        )

    def disable(self) -> None:
        """
        Stop sending PWM to the positional servo.
        """

        self._servo.disable()
