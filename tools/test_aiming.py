from control.aiming import AimingController


TEST_ERRORS = [
    0,
    10,
    21,
    25,
    25,
    30,
    40,
    60,
    90,
    120,
    20,
    10,
    0,
    -21,
    -25,
    -25,
    -30,
    -40,
    -60,
    -90,
    -120,
    0,
]


def main() -> None:
    aiming = AimingController(
        deadzone=20,
        max_error=120,
        confirm_frames=2,
    )

    print("Aiming controller test")
    print("----------------------")
    print()
    print(
        f"Deadzone       : "
        f"±{aiming.deadzone}px"
    )
    print(
        f"Maximum error  : "
        f"±{aiming.max_error}px"
    )
    print(
        f"Confirm frames : "
        f"{aiming.confirm_frames}"
    )
    print()

    for index, error_x in enumerate(
        TEST_ERRORS,
        start=1,
    ):
        command = aiming.calculate(
            error_x
        )

        print(
            f"{index:02d}  "
            f"error_x={error_x:+4d}  "
            f"aim={command.direction.value:7}  "
            f"strength={command.strength:.2f}  "
            f"active="
            f"{aiming.active_direction.value}"
        )


if __name__ == "__main__":
    main()
