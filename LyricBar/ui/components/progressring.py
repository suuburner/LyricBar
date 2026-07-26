from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QLabel


class ProgressRing(QLabel):
    """Traces a thin line around the bar's own rounded-rect border, filling
    in clockwise from the top-left as the song plays -- instead of a
    separate linear bar sitting inside the lyrics text.

    `QPainterPath.addRoundedRect` starts its path at the top edge, just past
    the top-left corner, and always winds clockwise -- which is exactly the
    "starts top-left, goes clockwise" behavior wanted, with no manual angle
    math needed. `pointAtPercent(t)` samples the path by *fraction of actual
    path length*, not by angle, so progress moves at a constant visual speed
    along straight edges and around corners alike (a naive QConicalGradient
    approach would instead move at a constant *angular* speed around the
    rect's center, which looks very uneven on a wide, short pill shape).
    """

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

        # Sample the revealed portion of the path as a polyline. Capped
        # sample count keeps this cheap even during frequent progress-tick
        # repaints, regardless of how long the actual path is.
        num_samples = max(2, min(300, int(300 * self.progress) + 2))
        reveal_path = QPainterPath()
        for i in range(num_samples):
            t = self.progress * i / (num_samples - 1)
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