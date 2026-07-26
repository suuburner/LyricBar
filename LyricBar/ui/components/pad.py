from PyQt5.QtGui import QPainter, QBrush, QGradient, QPainterPath, QColor
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtWidgets import QLabel


class Pad(QLabel):
    def __init__(self, color, parent=None):
        super().__init__("", parent)
        self.brush = QBrush(color)
        self.rounded_radius = 0
        self.border_color = None  # QColor; None or fully transparent = no border
        self.border_width = 0.0

    def setColor(self, color):
        self.brush = QBrush(color)
        self.update()

    def setBorder(self, color, width=0.0):
        """Outline drawn around the same shape (rect or rounded rect) this
        Pad already fills. color: QColor or None to clear. width: stroke
        thickness in px."""
        self.border_color = color
        self.border_width = width
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.brush.gradient() is not None and self.brush.gradient().type() == QGradient.Type.RadialGradient and self.brush.gradient().CoordinateMode == QGradient.CoordinateMode.LogicalMode:
            center = QPointF(self.brush.gradient().focalPoint())
            center.setX(center.x() * self.width())
            center.setY(center.y() * self.height())
            path = QPainterPath()
            path.addEllipse(center, 1, 1)
            painter.fillPath(path, self.brush.gradient().stops()[0][1])
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        has_border = (
            self.border_width > 0
            and isinstance(self.border_color, QColor)
            and self.border_color.alpha() > 0
        )

        full_rect = QRectF(self.rect())

        if has_border:
            # Robust border technique: fill the full outer shape with the
            # border color, then fill a smaller inner shape (inset by the
            # border width, with a proportionally smaller radius) with the
            # normal background brush on top. Two solid fills, no stroking -
            # this sidesteps QPen/antialiasing edge cases entirely (uneven
            # sub-pixel rounding under DPI scaling, cosmetic-pen quirks,
            # etc.) that make a thin stroked outline look inconsistent.
            outer_path = QPainterPath()
            if self.rounded_radius > 0:
                outer_path.addRoundedRect(full_rect, self.rounded_radius, self.rounded_radius)
            else:
                outer_path.addRect(full_rect)
            painter.fillPath(outer_path, self.border_color)

            bw = self.border_width
            inner_rect = full_rect.adjusted(bw, bw, -bw, -bw)
            if inner_rect.width() > 0 and inner_rect.height() > 0:
                inner_path = QPainterPath()
                if self.rounded_radius > 0:
                    inner_radius = max(0.0, self.rounded_radius - bw)
                    inner_path.addRoundedRect(inner_rect, inner_radius, inner_radius)
                else:
                    inner_path.addRect(inner_rect)
                painter.fillPath(inner_path, self.brush)
        elif self.rounded_radius > 0:
            path = QPainterPath()
            path.addRoundedRect(full_rect, self.rounded_radius, self.rounded_radius)
            painter.fillPath(path, self.brush)
        else:
            painter.fillRect(self.rect(), self.brush)