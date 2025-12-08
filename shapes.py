from config import MIDDLE_CIRCLE_COLOR, RECT_COLOR
from PyQt6.QtGui import QPainter, QColor, QPen
from math import sqrt


class Circle:
    def __init__(self, x: float, y: float, rx: float, ry: float, color=MIDDLE_CIRCLE_COLOR):
        """
        A class representing a circle.

        Args:
            x (float): The x-coordinate of the circle's center.
            y (float): The y-coordinate of the circle's center.
            rx (float): The radius of the circle along the x-axis.
            ry (float): The radius of the circle along the y-axis.
            color: The color of the circle (default: MIDDLE_CIRCLE_COLOR).
        """
        self.x = x
        self.y = y
        self.rx = rx
        self.ry = ry        
        # self.x = int(x)
        # self.y = int(y)
        # self.rx = int(rx)
        # self.ry = int(ry)
        self.color = color

    def draw(self, painter: QPainter) -> None:
        """
        Draws the circle using the provided QPainter.
        """
        tmp_x = self.x - self.rx
        tmp_y = self.y - self.ry
        painter.setPen(QPen(QColor(0, 0, 0)))  # Black border
        painter.setBrush(QColor(*self.color))  # Fill color
        painter.drawEllipse(int(tmp_x), int(tmp_y), int(self.rx) * 2, int(self.ry) * 2)

    def check_hit(self, input_x: float, input_y: float) -> bool:
        """
        Checks if a point (input_x, input_y) is within the circle.

        Args:
            input_x (float): x-coordinate of the point.
            input_y (float): y-coordinate of the point.

        Returns:
            bool: True if the point is within the circle, False otherwise.
        """
        distance = sqrt((self.x - input_x) ** 2 + (self.y - input_y) ** 2)
        return distance <= max(self.rx, self.ry) 

    def check_hit_line_segment(self, x1, y1, x2, y2):
        if x1 == x2 and y1 == y2:
            return 0
        xc, yc, a, b = self.x, self.y, self.rx, self.ry

        # Line segment vector
        dx = x2 - x1
        dy = y2 - y1

        # Quadratic coefficients
        A = (dx**2) / a**2 + (dy**2) / b**2
        B = 2 * ((dx * (x1 - xc)) / a**2 + (dy * (y1 - yc)) / b**2)
        C = ((x1 - xc)**2) / a**2 + ((y1 - yc)**2) / b**2 - 1

        # Discriminant
        discriminant = B**2 - 4 * A * C

        if discriminant < 0:
            return False  # No intersection

        # Solve for t values
        sqrt_discriminant = sqrt(discriminant)
        t1 = (-B + sqrt_discriminant) / (2 * A)
        t2 = (-B - sqrt_discriminant) / (2 * A)

        # Check if t1 or t2 is in [0, 1]
        return 0 <= t1 <= 1 or 0 <= t2 <= 1    
    
    def calc_dist_to_center(self, data, x, y):
        x, y = data.reverse_process_x_and_y_for_record(x, y)
        return sqrt(((self.x-x)*data.dimensions.X_PIXEL_TO_CM)**2 + ((self.y-y)*data.dimensions.Y_PIXEL_TO_CM)**2) 

    def __str__(self) -> str:
        """
        String representation of the circle.
        """
        return f"x: {self.x}, y: {self.y}, rx: {self.rx}, ry: {self.ry}"


class Rectangle:
    def __init__(self, x: float, y: float, w: float, h: float, color=RECT_COLOR):
        """
        A class representing a rectangle.

        Args:
            x (float): The x-coordinate of the rectangle's top-left corner.
            y (float): The y-coordinate of the rectangle's top-left corner.
            w (float): The width of the rectangle.
            h (float): The height of the rectangle.
            dx (float): Horizontal velocity.
            dy (float): Vertical velocity.
            color: The color of the rectangle (default: RECT_COLOR).
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color

    def draw(self, painter: QPainter) -> None:
        """
        Draws the rectangle using the provided QPainter.
        """
        painter.setBrush(QColor(*self.color))
        painter.drawRect(int(self.x), int(self.y), int(self.w), int(self.h))

    def check_hit(self, x, y):
        return self.x <= x and x <= self.x + self.w and self.y <= y and y <= self.y + self.h

    def check_hit_line_segment(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Helper function to check if two line segments intersect."""
        def orientation(xa, ya, xb, yb, xc, yc):
            val = (yb - ya) * (xc - xb) - (xb - xa) * (yc - yb)
            if val == 0:
                return 0  # Collinear
            return 1 if val > 0 else 2  # Clockwise or counterclockwise

        o1 = orientation(x1, y1, x2, y2, x3, y3)
        o2 = orientation(x1, y1, x2, y2, x4, y4)
        o3 = orientation(x3, y3, x4, y4, x1, y1)
        o4 = orientation(x3, y3, x4, y4, x2, y2)

        # General case
        if o1 != o2 and o3 != o4:
            return 1
        return 0

    def check_hit_line_segments(self, x1, y1, x2, y2):
        if x1 == x2 and y1 == y2:
            return 0
        x, y = self.x, self.y
        tmp = 0
        tmp |= self.check_hit_line_segment(x1, y1, x2, y2, x, y, x+self.w, y)
        tmp |= self.check_hit_line_segment(x1, y1, x2, y2, x, y, x, y+self.h)
        tmp |= self.check_hit_line_segment(x1, y1, x2, y2, x+self.w, y, x+self.w, y+self.h)
        tmp |= self.check_hit_line_segment(x1, y1, x2, y2, x, y+self.h, x+self.w, y+self.h)
        return tmp