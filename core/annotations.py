import math


class Annotation:
    """Base class for UI annotations (non-circuit elements)"""

    def __init__(self, x, y, name="ANNOTATION"):
        self.x = x
        self.y = y
        self.name = name
        self.width = 100
        self.height = 60
        self.rotation = 0

    def contains_point(self, x, y):
        """Check if point is inside annotation (accounts for rotation)"""
        if self.rotation == 0:
            return (
                self.x <= x <= self.x + self.width
                and self.y <= y <= self.y + self.height
            )

        # For rotated annotations, transform the point to local coordinates
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        dx = x - cx
        dy = y - cy

        angle_rad = math.radians(-self.rotation)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a

        return (
            -self.width / 2 <= local_x <= self.width / 2
            and -self.height / 2 <= local_y <= self.height / 2
        )


class TextAnnotation(Annotation):
    """Text label annotation for writing on canvas"""

    def __init__(self, x, y):
        super().__init__(x, y, "TEXT")
        self.text = "Text"
        self.font_family = "Segoe UI"
        self.font_size = 14
        self.font_bold = False
        self.font_italic = False
        self.text_color = "#DCDCE1"
        self.width = 80
        self.height = 30


class RectangleAnnotation(Annotation):
    """Transparent rectangle with border only"""

    def __init__(self, x, y):
        super().__init__(x, y, "RECT")
        self.border_width = 2
        self.border_color = "#5096FF"
        self.border_radius = 0
        self.width = 100
        self.height = 80


class CircleAnnotation(Annotation):
    """Transparent circle with border only"""

    def __init__(self, x, y):
        super().__init__(x, y, "CIRCLE")
        self.border_width = 2
        self.border_color = "#5096FF"
        self._diameter = 80  # Use private variable first
        self.width = 80
        self.height = 80

    @property
    def diameter(self):
        return self._diameter

    @diameter.setter
    def diameter(self, value):
        self._diameter = value
        # Keep width and height in sync with diameter
        self.width = value
        self.height = value

