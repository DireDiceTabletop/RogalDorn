import time

import pigpio

from config import TURRET
from hardware.continuous_servo import ContinuousRotationServo


def main() -> None:
    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError(
            "Could not connect to pigpio."
        )

    servo = ContinuousRotationServo(
        pi=pi,
        gpio=TURRET["gpio"],
        stop=TURRET["stop"],
        forward=TURRET["forward"],
        reverse=TURRET["reverse"],
    )

    print("Turret startup/neutral test")
    print("---------------------------")
    print(
        f"GPIO    : {TURRET['gpio']}"
    )
    print(
        f"Stop    : {TURRET['stop']} µs"
    )
    print(
        f"Forward : {TURRET['forward']} µs"
    )
    print(
        f"Reverse : {TURRET['reverse']} µs"
    )
    print()
    print(
        "Servo should remain completely stationary."
    )
    print("Waiting 10 seconds...")
    print()

    try:
        servo.stop()

        for remaining in range(10, 0, -1):
            print(
                f"\r{remaining}...",
                end="",
                flush=True,
            )
            time.sleep(1)

        print()
        print("Test complete.")

    except KeyboardInterrupt:
        print("\nTest cancelled.")

    finally:
        servo.stop()
        servo.disable()
        pi.stop()

        print("Servo disabled.")


if __name__ == "__main__":
    main()
