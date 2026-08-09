import pigpio


class HallSensor:
    """Active-low A3144 Hall-effect position sensor."""

    def __init__(
        self,
        pi: pigpio.pi,
        gpio: int,
    ) -> None:
        self._pi = pi
        self._gpio = gpio

        self._pi.set_mode(
            self._gpio,
            pigpio.INPUT,
        )

        self._pi.set_pull_up_down(
            self._gpio,
            pigpio.PUD_UP,
        )

    @property
    def gpio(self) -> int:
        """Return the BCM GPIO number used by this sensor."""

        return self._gpio

    @property
    def raw_value(self) -> int:
        """
        Return the raw GPIO value.

        1 = sensor inactive
        0 = magnet detected
        """

        return self._pi.read(self._gpio)

    @property
    def is_active(self) -> bool:
        """Return True when the magnet is detected."""

        return self.raw_value == 0

    def add_activation_callback(self, callback):
        """
        Run callback whenever the sensor changes from inactive to active.

        The A3144 is active-low, so activation is a falling GPIO edge.
        """

        def _handle_activation(gpio, level, tick):
            callback()

        return self._pi.callback(
            self._gpio,
            pigpio.FALLING_EDGE,
            _handle_activation,
        )
