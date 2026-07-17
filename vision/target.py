from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Target:
    """A detected target within a camera frame."""

    x: int
    y: int
    width: int
    height: int
    confidence: float

    @property
    def centre_x(self) -> int:
        return self.x + self.width // 2

    @property
    def centre_y(self) -> int:
        return self.y + self.height // 2

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height
