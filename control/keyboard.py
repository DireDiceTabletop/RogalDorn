import threading
import time

from sshkeyboard import listen_keyboard
import pigpio

import config
from hardware.continuous_servo import ContinuousRotationServo
from hardware.drive import Drive
from hardware.tank_controller import TankController

forward = 0.0
turn = 0.0
running = True

pi = pigpio.pi()

left = ContinuousRotationServo(pi, **config.LEFT_TRACK)
right = ContinuousRotationServo(pi, **config.RIGHT_TRACK)

drive = Drive(left, right)
tank = TankController(drive)


def on_press(key):
    global forward, turn, running

    if key == "w":
        forward = 0.6

    elif key == "s":
        forward = -0.6

    elif key == "a":
        turn = -0.4

    elif key == "d":
        turn = 0.4

    elif key == "q":
        forward = 0
        turn = -0.8

    elif key == "e":
        forward = 0
        turn = 0.8

    elif key == "space":
        forward = 0
        turn = 0

    elif key == "esc":
        running = False


def on_release(key):
    global forward, turn

    if key in ("w", "s"):
        forward = 0

    if key in ("a", "d", "q", "e"):
        turn = 0


def control_loop():
    global running

    while running:
        drive.arcade(forward, turn)
        time.sleep(0.05)

    tank.stop()


thread = threading.Thread(target=control_loop)
thread.start()

try:
    print("\n=== Rogal Dorn Keyboard Control ===")
    print("W/S  Forward / Reverse")
    print("A/D  Steer")
    print("Q/E  Pivot")
    print("Space Stop")
    print("Esc Quit\n")

    listen_keyboard(
        on_press=on_press,
        on_release=on_release,
    )

finally:
    running = False
    thread.join()

    tank.stop()
    left.disable()
    right.disable()

    pi.stop()
