class TankController:
    """
    High-level interface for controlling the tank.

    Application code should communicate with this class
    rather than directly manipulating individual hardware
    devices.
    """

    def __init__(
        self,
        drive,
        turret=None,
        barrel=None,
        laser=None,
    ):
        self.drive = drive
        self.turret = turret
        self.barrel = barrel
        self.laser = laser

    # -----------------------------------------------------
    # Driving
    # -----------------------------------------------------

    def drive_arcade(
        self,
        forward: float,
        turn: float,
    ) -> None:
        self.drive.arcade(
            forward=forward,
            turn=turn,
        )

    def stop_drive(self) -> None:
        self.drive.stop()

    def forward(
        self,
        speed: float = 1.0,
    ) -> None:
        self.drive.forward(
            speed
        )

    def reverse(
        self,
        speed: float = 1.0,
    ) -> None:
        self.drive.reverse(
            speed
        )

    def turn_left(
        self,
        speed: float = 1.0,
    ) -> None:
        self.drive.turn_left(
            speed
        )

    def turn_right(
        self,
        speed: float = 1.0,
    ) -> None:
        self.drive.turn_right(
            speed
        )

    # -----------------------------------------------------
    # Turret rotation
    # -----------------------------------------------------

    def turret_left(
        self,
        speed: float,
    ) -> bool:
        if self.turret is None:
            return False

        return self.turret.rotate_left(
            speed
        )

    def turret_right(
        self,
        speed: float,
    ) -> bool:
        if self.turret is None:
            return False

        return self.turret.rotate_right(
            speed
        )

    def stop_turret(self) -> None:
        if self.turret is not None:
            self.turret.stop()

    def home_turret(
        self,
        speed: float,
        timeout: float,
    ) -> None:
        if self.turret is None:
            return

        self.turret.home(
            speed=speed,
            timeout=timeout,
        )

    # -----------------------------------------------------
    # Barrel
    # -----------------------------------------------------

    def centre_barrel(self) -> None:
        if self.barrel is not None:
            self.barrel.centre()

    def update_barrel(
        self,
        elevation_input: float,
        delta_time: float,
        speed: float,
    ) -> int | None:
        if self.barrel is None:
            return None

        return self.barrel.update(
            elevation_input=elevation_input,
            delta_time=delta_time,
            speed=speed,
        )

    # -----------------------------------------------------
    # Laser
    # -----------------------------------------------------

    def laser_on(self) -> None:
        if self.laser is not None:
            self.laser.on()

    def laser_off(self) -> None:
        if self.laser is not None:
            self.laser.off()

    # -----------------------------------------------------
    # Safety
    # -----------------------------------------------------

    def stop(self) -> None:
        """
        Put moving/output systems into their safe state.

        The positional barrel is deliberately left holding
        its current position.
        """

        self.stop_drive()
        self.stop_turret()
        self.laser_off()

    def disable(self) -> None:
        """
        Final shutdown.

        Stop everything and disable the barrel servo PWM.
        """

        self.stop()

        if self.barrel is not None:
            self.barrel.disable()
