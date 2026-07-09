import pigpio

import config
from hardware.continuous_servo import ContinuousRotationServo


def make_servo(pi, cfg):
    return ContinuousRotationServo(
        pi,
        gpio=cfg["gpio"],
        stop=cfg["stop"],
        forward=cfg["forward"],
        reverse=cfg["reverse"],
    )


def calibrate(name, servo):

    pulse = servo.stop_pulse

    servo.pulse(pulse)

    while True:

        print("\n-----------------------------")
        print(f"{name}")
        print(f"Current pulse: {pulse} µs")
        print("-----------------------------")
        print("+  Increase 1")
        print("-  Decrease 1")
        print("]  Increase 10")
        print("[  Decrease 10")
        print("s  Apply current pulse")
        print("x  Disable PWM")
        print("q  Back")

        cmd = input("> ").strip()

        if cmd == "w":
            pulse += 1

        elif cmd == "s":
            pulse -= 1

        elif cmd == "]":
            pulse += 10

        elif cmd == "[":
            pulse -= 10

        elif cmd == "x":
            servo.disable()
            continue

        elif cmd == "q":
            servo.stop()
            return

        else:
            continue

        servo.pulse(pulse)


def main():

    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError("Could not connect to pigpiod")

    left = make_servo(pi, config.LEFT_TRACK)
    right = make_servo(pi, config.RIGHT_TRACK)
    turret = make_servo(pi, config.TURRET)

    while True:

        print("\n==============================")
        print(" FS90R Calibration Tool")
        print("==============================")
        print("1 - Left Track")
        print("2 - Right Track")
        print("3 - Turret")
        print("q - Quit")

        choice = input("> ").strip().lower()

        if choice == "1":
            calibrate("Left Track", left)

        elif choice == "2":
            calibrate("Right Track", right)

        elif choice == "3":
            calibrate("Turret", turret)

        elif choice == "q":
            break

    left.disable()
    right.disable()
    turret.disable()

    pi.stop()


if __name__ == "__main__":
    main()
