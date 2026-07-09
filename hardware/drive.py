class Drive:
    """
    Controls the two drive servos.
    """

    def __init__(self, left_servo, right_servo):
        self.left = left_servo
        self.right = right_servo

    def stop(self):
        self.set_speed(0.0, 0.0)

    def set_speed(self, left_speed, right_speed):

        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))

        self.left.speed(left_speed)
        self.right.speed(right_speed)

    def arcade(self, forward, turn):
        """
        Differential drive mixer.

        forward:
            -1.0 reverse
             0 stop
             1.0 forward

        turn:
            -1.0 left
             0 straight
             1.0 right
        """

        left = forward + turn
        right = forward - turn

        maximum = max(1.0, abs(left), abs(right))

        left /= maximum
        right /= maximum

        self.set_speed(left, right)

    def forward(self, speed=1.0):
        self.arcade(speed, 0)

    def reverse(self, speed=1.0):
        self.arcade(-speed, 0)

    def turn_left(self, speed=1.0):
        self.arcade(0, -speed)

    def turn_right(self, speed=1.0):
        self.arcade(0, speed)
