from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QLabel
import math

class ProgressRing(QLabel):
    def __init__(self, parent=None, color=QColor(255, 255, 255, 220), thickness=2.5):
        super().__init__("", parent)
        self.rounded_radius = 0
        self.progress = 0.0
        self.color = color if isinstance(color, QColor) else QColor(color)
        self.thickness = thickness

    def setProgress(self, value):
        self.progress = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        if self.progress <= 0 or self.thickness <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Match Pad's own inset convention exactly so this traces the same
        # visual edge the border/mask sit on, not a slightly different one.
        inset = self.thickness / 2.0
        rect = QRectF(inset, inset, max(0.0, self.width() - 1 - 2 * inset), max(0.0, self.height() - 1 - 2 * inset))
        radius = max(0.0, self.rounded_radius - inset)

        full_path = QPainterPath()
        if radius > 0:
            full_path.addRoundedRect(rect, radius, radius)
        else:
            full_path.addRect(rect)

        total_length = full_path.length()
        if total_length <= 0:
            return

        CORNER_PULLBACK_PX = 6
        arc_to_corner_end = max(0.0, (math.pi / 2) * radius - CORNER_PULLBACK_PX)
        start_offset = full_path.percentAtLength(arc_to_corner_end) if radius > 0 else 0.0

        num_samples = max(2, min(300, int(300 * self.progress) + 2))
        reveal_path = QPainterPath()
        for i in range(num_samples):
            s = self.progress * i / (num_samples - 1)
            t = (start_offset - s) % 1.0
            point = full_path.pointAtPercent(t)
            if i == 0:
                reveal_path.moveTo(point)
            else:
                reveal_path.lineTo(point)

        pen = QPen(self.color, self.thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(reveal_path)
