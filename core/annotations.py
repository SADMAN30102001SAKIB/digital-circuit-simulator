class Annotation:
    """Base class for UI annotations (non-circuit elements)"""

    def __init__(self, x, y, name="ANNOTATION"):
        self.x = x
        self.y = y
        self.name = name
        self.width = 100
        self.height = 60
        self.rotation = 0


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
