import pigpio


class Laser:
    def __init__(self, pi, pin):
        self.pi = pi
        self.pin = pin

        self.pi.set_mode(pin, pigpio.OUTPUT)
        self.off()

    def on(self):
        self.pi.write(self.pin, 1)

    def off(self):
        self.pi.write(self.pin, 0)

    def toggle(self):
        current = self.pi.read(self.pin)

        if current:
            self.off()
        else:
            self.on()
