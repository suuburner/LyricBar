from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtProperty, QPropertyAnimation, QTimer
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QRadialGradient

from .outlinedlabel import OutlinedLabel


class ToastBubble(QLabel):
    def __init__(self, parent=None):
        super(ToastBubble, self).__init__("", parent)
        self._opacity = 1.0

        # Soft shadow beneath the pill itself (previously only the text had
        # any depth treatment, via its glow) so the badge reads as a
        # floating element rather than a flat color patch.
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(14)
        shadow.setColor(QColor(0, 0, 0, 90))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        painter.setOpacity(self.opacity)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Full pill spanning the widget's actual bounds -- this used to draw
        # a semicircle clipped to a (2*radius x radius) box where
        # radius = min(width//2, height). On a wide, short toast (the
        # normal case here: a short bar, and a toast width sized off the
        # bar's width in _layoutToast), that clip box was nowhere near the
        # widget's real width, so the shape rendered bunched on one side
        # while the text label -- laid out across the *full* widget with
        # center alignment -- centered independently of it.
        radius = h / 2.0
        inset = 0.75  # keeps the outline stroke below fully inside the pill
        path = QPainterPath()
        path.addRoundedRect(inset, inset, w - 2 * inset, h - 2 * inset, radius, radius)

        # More translucent throughout than before (each stop's alpha
        # dropped), with a thin light outline so the pill's edge stays
        # legible against both light and dark theme backgrounds instead of
        # being defined purely by a soft alpha falloff.
        gradient = QRadialGradient(w / 2.0, h / 2.0, max(w, h) / 2.0)
        gradient.setColorAt(0, QColor(255, 225, 235, 175))
        gradient.setColorAt(0.6, QColor(255, 205, 220, 155))
        gradient.setColorAt(1, QColor(219, 150, 172, 130))
        painter.fillPath(path, gradient)

        outline = QPen(QColor(255, 240, 245, 130))
        outline.setWidthF(1.2)
        painter.strokePath(path, outline)
        painter.end()

class ToastTag(QLabel):
    def __init__(self, text_color=QColor(35, 20, 25, 255), parent=None):
        super(ToastTag, self).__init__("", parent)
        self.text_color = text_color

        self.bubble = ToastBubble(parent=self)
        self.bubble.setGeometry(0, 0, self.width(), self.height())

        self.text = OutlinedLabel("", parent=self, brushcolor=text_color, relative_outline=False, linewidth=0)
        self.text.setGeometry(0, 0, self.width(), self.height())
        self.text.setFontFamily("Spotify Mix, Arial, Microsoft YaHei UI")
        self.text.setFontSize(13)
        self.text.setFontWeight("bold")
        self.text.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        # Glow is a light, near-white color rather than matching the (dark)
        # text color -- previously it was the same dark color as the text
        # itself, which adds no contrast. A light halo keeps the text
        # readable at the pill's rounded corners and edges too, where the
        # pink/white bubble gradient thins out toward transparent.
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(10)
        glow.setColor(QColor(255, 255, 255, 200))
        glow.setOffset(0, 0)
        self.text.setGraphicsEffect(glow)


        self._opacity = 1.0
        self.fade_in_animation = QPropertyAnimation(self, b"opacity")
        self.fade_in_animation.setDuration(100)
        self.fade_in_animation.setStartValue(0.1)
        self.fade_in_animation.setEndValue(1.0)

        self.fade_out_animation = QPropertyAnimation(self, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.1)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out_animation.start)

    def setGeometry(self, x, y, w, h):
        super().setGeometry(x, y, w, h)
        self.bubble.setGeometry(0, 0, w, h)
        self.text.setGeometry(0, 0, w, h)

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.bubble.opacity = value
        self.text.opacity = value

    def add_newline(self, text, max_width=34):
        # Higher than it used to be: the toast now auto-sizes its own width
        # to fit the text (see ui.py's _layoutToast), so most short/medium
        # messages ("Lyrics found via Lrclib") no longer need wrapping at
        # all -- they just grow the badge instead. Wrapping is now only for
        # genuinely long text that would otherwise blow past the bar's
        # available width.
        words = text.replace(" ", "\n").split("\n")
        i = 0
        while i + 1 < len(words):
            if len(words[i]) + len(words[i+1]) < max_width:
                words[i] += " " + words.pop(i+1)
            else:
                i += 1
        return "\n".join(words)

    # def setHidden(self, value):
    #     super().setHidden(value)
    #     self.bubble.setHidden(value)
    #     self.text.setHidden(value)

    def start(self, text=None, duration=1000):
        if text is not None:
            self.text.setText(self.add_newline(text))
            self.text.update()
        self.end()
        self.setHidden(False)

        self.show()
        self.fade_in_animation.start()
        self.timer.start(duration)

        self.fade_out_animation.finished.connect(lambda: self.setHidden(True))


    def end(self):
        self.setHidden(True)
        if self.fade_in_animation is not None and self.fade_in_animation.state() == QPropertyAnimation.State.Running:
            self.fade_in_animation.stop()
        if self.timer is not None and self.timer.isActive():
            self.timer.stop()
        if self.fade_out_animation is not None and self.fade_out_animation.state() == QPropertyAnimation.State.Running:
            self.fade_out_animation.stop()



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.resize(400, 400)
    win.setLayout(QVBoxLayout())
    win.layout().addWidget(ToastTag("hiiiii"))
    win.show()

    sys.exit(app.exec_())
