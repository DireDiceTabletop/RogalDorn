from dataclasses import dataclass

from evdev import InputDevice, InputEvent, ecodes, list_devices


@dataclass(frozen=True, slots=True)
class GamepadAxes:
    left_x: float
    left_y: float
    right_x: float
    right_y: float


@dataclass(frozen=True, slots=True)
class GamepadTriggers:
    left: float
    right: float


@dataclass(frozen=True, slots=True)
class GamepadButtons:
    a: bool
    b: bool
    x: bool
    y: bool

    left_bumper: bool
    right_bumper: bool

    start: bool
    select: bool


@dataclass(frozen=True, slots=True)
class GamepadState:
    axes: GamepadAxes
    triggers: GamepadTriggers
    buttons: GamepadButtons


class Gamepad:
    """
    Read and normalize Xbox controller input.
    """

    AXIS_CODES = {
        "left_x": ecodes.ABS_Y,
        "left_y": ecodes.ABS_X,
        "right_x": ecodes.ABS_Z,
        "right_y": ecodes.ABS_RZ,
    }

    TRIGGER_CODES = {
        "right": ecodes.ABS_GAS,
        "left": ecodes.ABS_BRAKE,
    }

    BUTTON_CODES = {
        "a": ecodes.BTN_SOUTH,
        "b": ecodes.BTN_EAST,
        "x": ecodes.BTN_WEST,
        "y": ecodes.BTN_NORTH,

        "left_bumper": ecodes.BTN_TL,
        "right_bumper": ecodes.BTN_TR,

        "select": ecodes.BTN_SELECT,
        "start": ecodes.BTN_START,
    }

    def __init__(
        self,
        device_path: str,
        deadzone: float = 0.12,
        trigger_deadzone: float = 0.02,
    ) -> None:
        if not 0.0 <= deadzone < 1.0:
            raise ValueError(
                "Deadzone must be between 0.0 and 1.0."
            )

        if not 0.0 <= trigger_deadzone < 1.0:
            raise ValueError(
                "Trigger deadzone must be between 0.0 and 1.0."
            )

        self._device = InputDevice(
            device_path
        )

        self._deadzone = deadzone
        self._trigger_deadzone = trigger_deadzone

        self._values = {
            name: 0.0
            for name in self.AXIS_CODES
        }

        self._trigger_values = {
            name: 0.0
            for name in self.TRIGGER_CODES
        }

        self._buttons = {
            name: False
            for name in self.BUTTON_CODES
        }

        self._ranges: dict[
            str,
            tuple[int, int],
        ] = {}

        self._trigger_ranges: dict[
            str,
            tuple[int, int],
        ] = {}

        # -------------------------------------------------
        # Stick ranges
        # -------------------------------------------------

        for name, code in self.AXIS_CODES.items():
            axis_info = self._device.absinfo(
                code
            )

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

        # -------------------------------------------------
        # Trigger ranges
        # -------------------------------------------------

        for name, code in self.TRIGGER_CODES.items():
            axis_info = self._device.absinfo(
                code
            )

            if axis_info is None:
                self.close()

                raise ValueError(
                    f"{self._device.name} does not provide "
                    f"the required trigger {name}."
                )

            self._trigger_ranges[name] = (
                axis_info.min,
                axis_info.max,
            )

    @classmethod
    def discover(
        cls,
        deadzone: float = 0.12,
        trigger_deadzone: float = 0.02,
    ) -> "Gamepad":
        """
        Find a connected controller with the required
        sticks, triggers and buttons.
        """

        required_axes = set(
            cls.AXIS_CODES.values()
        )

        required_axes.update(
            cls.TRIGGER_CODES.values()
        )

        matches: list[
            tuple[str, str]
        ] = []

        for device_path in list_devices():
            device = InputDevice(
                device_path
            )

            try:
                capabilities = (
                    device.capabilities(
                        absinfo=False
                    )
                )

                available_axes = set(
                    capabilities.get(
                        ecodes.EV_ABS,
                        [],
                    )
                )

                available_buttons = set(
                    capabilities.get(
                        ecodes.EV_KEY,
                        [],
                    )
                )

                has_required_axes = (
                    required_axes.issubset(
                        available_axes
                    )
                )

                has_buttons = bool(
                    available_buttons
                )

                if (
                    has_required_axes
                    and has_buttons
                ):
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
                "More than one compatible gamepad "
                "was found:\n"
                f"{descriptions}\n"
                "Disconnect unused controllers "
                "and try again."
            )

        device_path, _ = matches[0]

        return cls(
            device_path=device_path,
            deadzone=deadzone,
            trigger_deadzone=trigger_deadzone,
        )

    @property
    def name(self) -> str:
        return self._device.name

    @property
    def path(self) -> str:
        return self._device.path

    @property
    def axes(self) -> GamepadAxes:
        return GamepadAxes(
            left_x=self._values["left_x"],
            left_y=self._values["left_y"],
            right_x=self._values["right_x"],
            right_y=self._values["right_y"],
        )

    @property
    def triggers(self) -> GamepadTriggers:
        return GamepadTriggers(
            left=self._trigger_values["left"],
            right=self._trigger_values["right"],
        )

    @property
    def buttons(self) -> GamepadButtons:
        return GamepadButtons(
            a=self._buttons["a"],
            b=self._buttons["b"],
            x=self._buttons["x"],
            y=self._buttons["y"],
            left_bumper=self._buttons[
                "left_bumper"
            ],
            right_bumper=self._buttons[
                "right_bumper"
            ],
            start=self._buttons["start"],
            select=self._buttons["select"],
        )

    @property
    def state(self) -> GamepadState:
        return GamepadState(
            axes=self.axes,
            triggers=self.triggers,
            buttons=self.buttons,
        )

    def read_loop(self):
        """
        Backwards-compatible stick-only loop.

        Existing stick-based test programs can continue
        using this method unchanged.
        """

        stick_codes = set(
            self.AXIS_CODES.values()
        )

        for event in self._device.read_loop():
            changed = self.process_event(
                event
            )

            if (
                changed
                and event.type == ecodes.EV_ABS
                and event.code in stick_codes
            ):
                yield self.axes

    def read_state_loop(self):
        """
        Yield the complete controller state whenever a
        configured stick, trigger or button changes.
        """

        for event in self._device.read_loop():
            if self.process_event(event):
                yield self.state

    def process_event(
        self,
        event: InputEvent,
    ) -> bool:
        """
        Process one Linux input event.

        Return True when a configured control changes.
        """

        if event.type == ecodes.EV_ABS:
            if self._process_axis(
                event
            ):
                return True

            if self._process_trigger(
                event
            ):
                return True

        if event.type == ecodes.EV_KEY:
            return self._process_button(
                event
            )

        return False

    def close(self) -> None:
        self._device.close()

    def _process_axis(
        self,
        event: InputEvent,
    ) -> bool:
        for name, code in self.AXIS_CODES.items():
            if event.code != code:
                continue

            minimum, maximum = (
                self._ranges[name]
            )

            self._values[name] = (
                self._normalize_axis(
                    value=event.value,
                    minimum=minimum,
                    maximum=maximum,
                )
            )

            return True

        return False

    def _process_trigger(
        self,
        event: InputEvent,
    ) -> bool:
        for name, code in self.TRIGGER_CODES.items():
            if event.code != code:
                continue

            minimum, maximum = (
                self._trigger_ranges[name]
            )

            self._trigger_values[name] = (
                self._normalize_trigger(
                    value=event.value,
                    minimum=minimum,
                    maximum=maximum,
                )
            )

            return True

        return False

    def _process_button(
        self,
        event: InputEvent,
    ) -> bool:
        for name, code in self.BUTTON_CODES.items():
            if event.code != code:
                continue

            self._buttons[name] = (
                event.value != 0
            )

            return True

        return False

    def _normalize_axis(
        self,
        value: int,
        minimum: int,
        maximum: int,
    ) -> float:
        """
        Convert a stick axis to -1.0 through +1.0.
        """

        centre = (
            minimum + maximum
        ) / 2

        if value >= centre:
            available_range = (
                maximum - centre
            )
        else:
            available_range = (
                centre - minimum
            )

        if available_range == 0:
            return 0.0

        normalized = (
            value - centre
        ) / available_range

        normalized = max(
            -1.0,
            min(
                1.0,
                normalized,
            ),
        )

        if (
            abs(normalized)
            <= self._deadzone
        ):
            return 0.0

        magnitude = (
            abs(normalized)
            - self._deadzone
        ) / (
            1.0
            - self._deadzone
        )

        if normalized < 0:
            return -magnitude

        return magnitude

    def _normalize_trigger(
        self,
        value: int,
        minimum: int,
        maximum: int,
    ) -> float:
        """
        Convert a trigger from its hardware range to
        0.0 through 1.0.

        Released:
            0.0

        Fully pressed:
            1.0
        """

        available_range = (
            maximum - minimum
        )

        if available_range <= 0:
            return 0.0

        normalized = (
            value - minimum
        ) / available_range

        normalized = max(
            0.0,
            min(
                1.0,
                normalized,
            ),
        )

        if normalized <= self._trigger_deadzone:
            return 0.0

        normalized = (
            normalized
            - self._trigger_deadzone
        ) / (
            1.0
            - self._trigger_deadzone
        )

        return max(
            0.0,
            min(
                1.0,
                normalized,
            ),
        )
