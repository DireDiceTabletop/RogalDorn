from control.aiming import AimingController


TEST_ERRORS = [
    -100,
    -50,
    -21,
    -20,
    -10,
    0,
    10,
    20,
    21,
    50,
    100,
]


def main() -> None:
    aiming = AimingController(
        deadzone=20,
        tracking_speed=0.25,
    )

    print("Aiming controller test")
    print("----------------------")
    print()
    print(
        f"Deadzone: ±{aiming.deadzone} pixels"
    )
    print(
        f"Tracking speed: "
        f"{aiming.tracking_speed:.0%}"
    )
    print()

    for error_x in TEST_ERRORS:
        command = aiming.calculate(error_x)

        print(
            f"error_x={error_x:+4d}  "
            f"direction={command.direction.value:7}  "
            f"speed={command.speed:.2f}"
        )


if __name__ == "__main__":
    main()
