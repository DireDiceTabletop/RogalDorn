from control.gamepad import Gamepad


def main() -> None:
    print("Searching for compatible gamepad...")

    gamepad = Gamepad.discover(
        deadzone=0.12,
    )

    print(f"Controller: {gamepad.name}")
    print(f"Device: {gamepad.path}")
    print()
    print("Move both sticks.")
    print("Press Ctrl+C to stop.")
    print()

    try:
        for axes in gamepad.read_loop():
            print(
                "\r"
                f"LX={axes.left_x:+.2f}  "
                f"LY={axes.left_y:+.2f}  "
                f"RX={axes.right_x:+.2f}  "
                f"RY={axes.right_y:+.2f}",
                end="",
                flush=True,
            )

    except KeyboardInterrupt:
        print("\nController test stopped.")

    finally:
        gamepad.close()


if __name__ == "__main__":
    main()
