from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QLabel
import math


class ProgressRing(QLabel):
    """Traces a thin line around the bar's own rounded-rect border, filling
    in anti-clockwise from the top-left as the song plays -- instead of a
    separate linear bar sitting inside the lyrics text.

    `QPainterPath.addRoundedRect`'s path actually starts at the middle of
    the *left* edge (verified empirically, not at the top-left as originally
    assumed) and winds clockwise as t increases. `start_offset` below shifts
    the reference point to the true top-left, and sampling t in the
    *decreasing* direction from there traces anti-clockwise (left edge,
    then bottom, then right, then back across the top). `pointAtPercent(t)`
    samples by *fraction of actual path length*, not by angle, so progress
    moves at a constant visual speed along straight edges and around
    corners alike (a naive QConicalGradient approach would instead move at
    a constant *angular* speed around the rect's center, which looks very
    uneven on a wide, short pill shape).
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

        # QPainterPath.addRoundedRect's path doesn't actually start at the
        # top-left -- it starts at the middle of the left edge (the bottom
        # end of the top-left corner's arc), verified empirically. The true
        # top-left point (top edge, just past that corner) sits one quarter-
        # circle of arc length further along the same path. Pulling back a
        # further fixed few pixels of arc length (CORNER_PULLBACK_PX) lands
        # the actual start a bit before that flat-edge transition, still on
        # the curve -- a purely aesthetic nudge, not the literal corner-end
        # point. percentAtLength converts a fixed physical arc length into
        # the right fraction regardless of this widget's actual size, and
        # this is 0 when radius is 0 (square corners, nothing to pull back
        # into).
        CORNER_PULLBACK_PX = 6
        arc_to_corner_end = max(0.0, (math.pi / 2) * radius - CORNER_PULLBACK_PX)
        start_offset = full_path.percentAtLength(arc_to_corner_end) if radius > 0 else 0.0

        # Sample the revealed portion of the path as a polyline. Capped
        # sample count keeps this cheap even during frequent progress-tick
        # repaints, regardless of how long the actual path is.
        # Anti-clockwise: decreasing t from the top-left start offset traces
        # down the left edge, across the bottom, up the right side, and back
        # across the top to close the loop -- verified empirically, since
        # QPainterPath's own winding direction (increasing t) is clockwise.
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