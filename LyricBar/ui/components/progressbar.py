from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QLabel


class ProgressBar(QLabel):
    def __init__(self, parent=None, progress_color=QColor(255, 255, 255, 200), background_color=QColor(0, 0, 0, 48), line_color=QColor(0, 0, 0, 0)):
        super().__init__("", parent)
        self.progress = 0
        self.progress_color = QColor(176, 176, 176, 220) if isinstance(progress_color, QColor) else progress_color
        self.background_color = QColor(255, 255, 255, 18) if isinstance(background_color, QColor) else background_color
        self.line_color = QColor(85, 85, 85, 180) if isinstance(line_color, QColor) else line_color
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        radius = max(3.0, (self.height() - 1) / 2.0)
        
        # Draw background
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), radius, radius)
        painter.fillPath(path, self.background_color)
        
        # Draw progress
        progress = max(0, self.progress)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, max(0.0, (self.width() - 1) * progress), self.height() - 1), radius, radius)
        painter.fillPath(path, QBrush(self.progress_color))
        
        # Draw outline
        pen = QPen(self.line_color)
        pen.setWidth(1)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.strokePath(path, pen)
