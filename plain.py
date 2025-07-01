from PyQt5.QtWidgets import QPushButton, QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QPainterPath, QBrush, QPen, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QPointF
import sys
import math

class PolygonButton(QPushButton):
    def __init__(self, sides=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sides = sides  # Number of polygon sides, 0 means circle
        self.setMinimumSize(100, 100)  # Just example size

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2 * 0.8

        path = QPainterPath()

        if self.sides == 0:  # circle
            path.addEllipse(center, radius, radius)
        else:
            # polygon vertices
            angle_step = 2 * math.pi / self.sides
            points = []
            for i in range(self.sides):
                angle = angle_step * i - math.pi / 2  # start at top
                x = center.x() + radius * math.cos(angle)
                y = center.y() + radius * math.sin(angle)
                points.append(QPointF(x, y))

            path.moveTo(points[0])
            for p in points[1:]:
                path.lineTo(p)
            path.closeSubpath()

        # Gradient fill
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(255, 0, 0))  # Orange-ish
        gradient.setColorAt(0.5, QColor(0, 0, 255))  # Yellow
        gradient.setColorAt(1, QColor(0, 255, 0))  # Yellow

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(Qt.black, 2))
        painter.drawPath(path)

        # Optionally draw the button text centered
        # painter.setPen(Qt.black)
        # painter.drawText(rect, Qt.AlignCenter, self.text())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = QWidget()
    layout = QVBoxLayout(w)

    # Triangle
    btn_triangle = PolygonButton(3, text="Triangle")
    # Circle (use 0 sides for circle)
    btn_circle = PolygonButton(0, text="Circle")
    # Pentagon
    btn_pentagon = PolygonButton(5, text="Pentagon")
    # Diamond is basically a 4 sided rotated square, let's use 4 sides
    btn_diamond = PolygonButton(4, text="Diamond")

    layout.addWidget(btn_triangle)
    layout.addWidget(btn_circle)
    layout.addWidget(btn_pentagon)
    layout.addWidget(btn_diamond)

    w.show()
    sys.exit(app.exec_())
