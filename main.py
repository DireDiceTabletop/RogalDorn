import pigpio

import config
from hardware.laser import Laser


def main():

    pi = pigpio.pi()

    if not pi.connected:
        raise RuntimeError("Could not connect to pigpiod")

    laser = Laser(pi, config.LASER)

    print("Laser ON")
    laser.on()

    input("Press Enter to switch off...")

    laser.off()

    pi.stop()


if __name__ == "__main__":
    main()
