class TankController:
    """
    High-level interface for controlling the tank.

    Everything else in the project should communicate with this class
    rather than directly controlling hardware.
    """

    def __init__(self, drive):
        self.drive = drive

    # -----------------------------
    # Driving
    # -----------------------------

    def stop(self):
        self.drive.stop()

    def forward(self, speed=1.0):
        self.drive.forward(speed)

    def reverse(self, speed=1.0):
        self.drive.reverse(speed)

    def turn_left(self, speed=1.0):
        self.drive.turn_left(speed)

    def turn_right(self, speed=1.0):
        self.drive.turn_right(speed)
