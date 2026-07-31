from dataclasses import dataclass

from evdev import InputDevice, InputEvent, ecodes, list_devices


@dataclass(frozen=True, slots=True)
class GamepadAxes:
    """Normalized analogue-stick positions."""

    left_x: float
    left_y: float
    right_x: float
    right_y: float


class Gamepad:
    """Read and normalize analogue-stick input from a Linux gamepad."""

    AXIS_CODES = {
        "left_x": ecodes.ABS_Y,
        "left_y": ecodes.ABS_X,
        "right_x": ecodes.ABS_Z,
        "right_y": ecodes.ABS_RZ,
    }

    def __init__(
        self,
        device_path: str,
        deadzone: float = 0.12,
    ) -> None:
        if not 0.0 <= deadzone < 1.0:
            raise ValueError(
                "Deadzone must be between 0.0 and 1.0."
            )

        self._device = InputDevice(device_path)
        self._deadzone = deadzone

        self._values = {
            name: 0.0
            for name in self.AXIS_CODES
        }

        self._ranges: dict[str, tuple[int, int]] = {}

        for name, code in self.AXIS_CODES.items():
            axis_info = self._device.absinfo(code)

            if axis_info is None:
                self.close()

                raise ValueError(
                    f"{self._device.name} does not provide "
                    f"the required axis {name}."
                )

            self._ranges[name] = (
                axis_info.min,
                axis_info.max,
            )

    @classmethod
    def discover(
        cls,
        deadzone: float = 0.12,
    ) -> "Gamepad":
        """
        Find a connected input device with all required gamepad axes.

        Linux event device numbers may change between boots, so the
        controller is identified by its capabilities rather than by
        a fixed path such as /dev/input/event2.
        """

        required_axes = set(cls.AXIS_CODES.values())
        matches: list[tuple[str, str]] = []

        for device_path in list_devices():
            device = InputDevice(device_path)

            try:
                capabilities = device.capabilities(
                    absinfo=False
                )

                available_axes = set(
                    capabilities.get(ecodes.EV_ABS, [])
                )

                available_buttons = set(
                    capabilities.get(ecodes.EV_KEY, [])
                )

                has_required_axes = required_axes.issubset(
                    available_axes
                )

                has_buttons = bool(available_buttons)

                if has_required_axes and has_buttons:
                    matches.append(
                        (
                            device.path,
                            device.name,
                        )
                    )

            finally:
                device.close()

        if not matches:
            raise RuntimeError(
                "No compatible gamepad was found. "
                "Check that the controller is connected."
            )

        if len(matches) > 1:
            descriptions = "\n".join(
                f"  {path}: {name}"
                for path, name in matches
            )

            raise RuntimeError(
                "More than one compatible gamepad was found:\n"
                f"{descriptions}\n"
                "Disconnect unused controllers and try again."
            )

        device_path, _ = matches[0]

        return cls(
            device_path=device_path,
            deadzone=deadzone,
        )

    @property
    def name(self) -> str:
        """Return the controller's reported device name."""

        return self._device.name

    @property
    def path(self) -> str:
        """Return the selected Linux event-device path."""

        return self._device.path

    @property
    def axes(self) -> GamepadAxes:
        """Return the most recently received stick positions."""

        return GamepadAxes(
            left_x=self._values["left_x"],
            left_y=self._values["left_y"],
            right_x=self._values["right_x"],
            right_y=self._values["right_y"],
        )

    def read_loop(self):
        """Yield updated stick positions whenever an axis changes."""

        for event in self._device.read_loop():
            if self.process_event(event):
                yield self.axes

    def process_event(
        self,
        event: InputEvent,
    ) -> bool:
        """
        Process one Linux input event.

        Return True when one of the configured stick axes changed.
        """

        if event.type != ecodes.EV_ABS:
            return False

        for name, code in self.AXIS_CODES.items():
            if event.code != code:
                continue

            minimum, maximum = self._ranges[name]

            self._values[name] = self._normalize(
                value=event.value,
                minimum=minimum,
                maximum=maximum,
            )

            return True

        return False

    def close(self) -> None:
        """Close the Linux input device."""

        self._device.close()

    def _normalize(
        self,
        value: int,
        minimum: int,
        maximum: int,
    ) -> float:
        """
        Convert a raw axis value to the range -1.0 through +1.0.

        Values within the configured deadzone are returned as zero.
        """

        centre = (minimum + maximum) / 2

        if value >= centre:
            available_range = maximum - centre
        else:
            available_range = centre - minimum

        if available_range == 0:
            return 0.0

        normalized = (
            value - centre
        ) / available_range

        normalized = max(
            -1.0,
            min(1.0, normalized),
        )

        if abs(normalized) <= self._deadzone:
            return 0.0

        magnitude = (
            abs(normalized) - self._deadzone
        ) / (
            1.0 - self._deadzone
        )

        if normalized < 0:
            return -magnitude

        return magnitude
