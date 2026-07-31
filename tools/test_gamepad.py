from evdev import InputDevice, ecodes, list_devices


def event_code_name(event_type: int, event_code: int) -> str:
    """Return a readable Linux input-event code name."""

    code_table = ecodes.bytype.get(event_type, {})
    name = code_table.get(event_code, f"UNKNOWN_{event_code}")

    if isinstance(name, list):
        return "/".join(name)

    return str(name)


def find_controller_devices() -> list[InputDevice]:
    """
    Find input devices that expose both buttons and absolute axes.

    This filters out ordinary keyboards and mice while retaining
    typical gamepads and joysticks.
    """

    controllers: list[InputDevice] = []

    for path in list_devices():
        device = InputDevice(path)
        capabilities = device.capabilities(absinfo=False)

        has_buttons = ecodes.EV_KEY in capabilities
        has_axes = ecodes.EV_ABS in capabilities

        if has_buttons and has_axes:
            controllers.append(device)
        else:
            device.close()

    return controllers


def choose_controller(
    controllers: list[InputDevice],
) -> InputDevice:
    """Ask the user which detected controller node to monitor."""

    print("Detected controller-like input devices:\n")

    for index, device in enumerate(controllers):
        print(f"{index}: {device.name}")
        print(f"   {device.path}")
        print(f"   {device.phys}\n")

    while True:
        response = input("Select device number: ").strip()

        try:
            index = int(response)
            return controllers[index]
        except (ValueError, IndexError):
            print("Please enter one of the displayed device numbers.")


def main() -> None:
    controllers = find_controller_devices()

    if not controllers:
        raise RuntimeError(
            "No controller-like input devices were found. "
            "Check that the controller is connected."
        )

    device = choose_controller(controllers)

    print()
    print(f"Reading events from: {device.name}")
    print(f"Device path: {device.path}")
    print()
    print("Move each stick and press some buttons.")
    print("Press Ctrl+C to stop.\n")

    try:
        for event in device.read_loop():
            if event.type not in (
                ecodes.EV_ABS,
                ecodes.EV_KEY,
            ):
                continue

            event_type = (
                "AXIS"
                if event.type == ecodes.EV_ABS
                else "BUTTON"
            )

            code_name = event_code_name(
                event.type,
                event.code,
            )

            print(
                f"{event_type:6} "
                f"{code_name:24} "
                f"value={event.value}"
            )

    except KeyboardInterrupt:
        print("\nController test stopped.")

    finally:
        for controller in controllers:
            controller.close()


if __name__ == "__main__":
    main()
