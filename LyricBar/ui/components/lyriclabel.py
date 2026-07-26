from datetime import datetime
from LyricBar.ui.components.utils import convert_to_color
from LyricBar.ui.components.progressring import ProgressRing
from LyricBar.ui.components.pad import Pad
from LyricBar.ui.components.outlinedlabel import OutlinedLabel
from PyQt5.QtWidgets import QLabel
from LyricBar.config import resource_path
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QSequentialAnimationGroup, QAbstractAnimation
from PyQt5.QtGui import QBrush, QColor, QPixmap, QGradient, QPainterPath, QPainter
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtCore import pyqtProperty


class LyricAnimation(QAbstractAnimation):
    def __init__(self, target, duration, parent=None, entering=None, sustaining=None, leaving=None):
        super().__init__(parent)
        self.target = target
        self._duration = -1
        self.setDuration(duration if duration is not None else -1)
        self.entering = self.get_interpolation_function(entering)
        self.sustaining = self.get_interpolation_function(sustaining)
        self.leaving = self.get_interpolation_function(leaving)
        
        # INSTANT appearance - no fade effects for maximum performance
        self.entering_time = 0  # 0ms = instant flash-in
        self.leaving_time = 0   # 0ms = instant flash-out
        self.sustaining_time = 3000
        
        self.last_frame_type = None
        
    def setAnimation(self, **kwargs):
        if "entering" in kwargs:
            self.entering = self.get_interpolation_function(kwargs["entering"])
        if "sustaining" in kwargs:
            self.sustaining = self.get_interpolation_function(kwargs["sustaining"])
        if "leaving" in kwargs:
            self.leaving = self.get_interpolation_function(kwargs["leaving"])
            
    def start(self, direction=1):
        self.currentTime = 0
        self.direction = direction
        self.target.applyValues(reset=True)
        super().start()
        
    def get_interpolation_function(self, props):
        if props is None:
            return lambda x: {}
        def get_stage_value(perc):
            ret = {}
            for property_name, points in props:
                points = sorted(points)
                if perc == 0:
                    ret[property_name] = points[0][1] if points[0][1] is not None else self.target.__getattribute__(property_name)
                for i in range(len(points)):
                    if perc > points[i][0] and perc <= points[i+1][0]:
                        left_v = points[i][1] if points[i][1] is not None else self.target.__getattribute__(property_name)
                        right_v = points[i+1][1] if points[i+1][1] is not None else self.target.__getattribute__(property_name)
                        weight = (perc - points[i][0]) / (points[i+1][0] - points[i][0])
                        ret[property_name] =  weight * right_v + (1 - weight) * left_v
            return ret
        return get_stage_value
    
    def get_value(self, time):
        if self.duration() < 0:
            entering_time = self.entering_time
            if self.entering is not None:
                if time <= self.entering_time:
                    # print("ENTERING", time / self.entering_time)
                    self.last_frame_type = "entering"
                    return self.entering(time / self.entering_time)
                else:
                    entering_time = 0
            if self.sustaining is not None:
                # print("SUSTAINING")
                if self.last_frame_type != "sustaining":
                    self.target.applyValues(reset=True)
                self.last_frame_type = "sustaining"
                return self.sustaining(((time - entering_time) % self.sustaining_time) / (self.sustaining_time))
            else:
                return {}
        entering_time = min(self.entering_time, self.duration() / 3)
        leaving_time = min(self.leaving_time, self.duration() / 3)
        if self.entering is not None:
            if time <= entering_time:
                # print("ENTERING")
                self.last_frame_type = "entering"
                return self.entering(time / entering_time)
        else:
            entering_time = 0
        if self.leaving is not None:
            if time >= self.duration() - leaving_time:
                # print("LEAVING")
                self.last_frame_type = "leaving"
                return self.leaving((time - self.duration() + leaving_time) / leaving_time)
        else:
            leaving_time = 0
        if self.last_frame_type != "sustaining":
            self.target.applyValues(reset=True)
        self.last_frame_type = "sustaining"
        if self.sustaining is not None:
            # print("SUSTAINING", self.sustaining(((time - entering_time) % self.sustaining_time)/ (self.sustaining_time)))
            return self.sustaining(((time - entering_time) % self.sustaining_time)/ (self.sustaining_time))
        return {}
    
    def setDuration(self, duration):
        self._duration = duration
        
    def duration(self):
        return self._duration
    
    def updateCurrentTime(self, currentTime: int) -> None:
        value = self.get_value(currentTime)
        # print(value)
        self.target.applyValues(**value)
        return
      

class LyricLabel(OutlinedLabel):
    def __init__(self, text=None, parent=None, **kwargs):
        
        self._rounded_radius = 0
        
        
        self.back_imagepad = QLabel("", parent=parent)
        self.back_imagepad.setStyleSheet("background-color: transparent")
        self.back_imagepad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.back_pad = Pad(QBrush(QColor(0,0,0,0)), parent=parent)
        self.back_pad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.animation = None
        self.entering = None
        self.sustaining = None
        self.leaving = None
        
        super().__init__(text=text, relative_outline=False, linewidth=0, brushcolor=QColor(0,0,0,0), linecolor=QColor(0,0,0,0), parent=parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.front_imagepad = QLabel("", parent=parent)
        self.front_imagepad.setStyleSheet("background-color: transparent")
        self.front_imagepad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.front_pad = Pad(QBrush(QColor(0,0,0,0)), parent=parent)
        self.front_pad.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_ring = ProgressRing(parent=parent)
        
        # Create separate timestamp labels with independent height
        self.timestamp_left = QLabel("0:00", parent=parent)
        self.timestamp_left.setStyleSheet("background-color: transparent; color: white;")
        self.timestamp_left.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.timestamp_right = QLabel("0:00", parent=parent)
        self.timestamp_right.setStyleSheet("background-color: transparent; color: white;")
        self.timestamp_right.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.glow_color = QColor(0, 0, 0, 200)
        
        self.setStyle(**kwargs)
        
        self.back_pad.show()
        self.back_imagepad.show()
        self.show()
        self.front_pad.show()
        self.front_imagepad.show()
        self.progress_ring.show()
        self.progress_ring.raise_()
        
    @pyqtProperty(float)
    def rounded_radius(self):
        return self._rounded_radius
    
    @rounded_radius.setter
    def rounded_radius(self, value):
        self._rounded_radius = value
        if value > 0:
            self.back_pad.rounded_radius = value
            self.front_pad.rounded_radius = value
            self.progress_ring.rounded_radius = value
        else:
            self.back_pad.rounded_radius = 0
            self.front_pad.rounded_radius = 0
            self.progress_ring.rounded_radius = 0
        self.back_pad.update()
        self.front_pad.update()
        self.progress_ring.update()
        
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        glow = self.graphicsEffect()
        if glow is not None:
            color = QColor(self.glow_color)
            color.setAlphaF(color.alphaF() * value)
            glow.setColor(color)
        self.update()
        
    def setFixedSize(self, width, height):
        super().setFixedSize(width, height)
        self.back_pad.setGeometry(0, 0, width, height)
        self.back_imagepad.setGeometry(0, 0, width, height)
        self.front_pad.setGeometry(0, 0, width, height)
        self.front_imagepad.setGeometry(0, 0, width, height)
        self.progress_ring.setGeometry(0, 0, width, height)

        # Timestamps now live tucked into the pill's rounded end-caps
        # (the corner space lyric text doesn't reach) rather than flanking
        # a separate linear bar -- the ring itself is the progress display.
        timestamp_height = 14
        timestamp_width = 44
        timestamp_y = (height - timestamp_height) // 2
        end_cap_margin = int(max(6, self.rounded_radius // 2))

        self.timestamp_left.setGeometry(end_cap_margin, timestamp_y, timestamp_width, timestamp_height)
        self.timestamp_right.setGeometry(
            width - end_cap_margin - timestamp_width, timestamp_y, timestamp_width, timestamp_height
        )

    def move(self, x, y):
        super().move(x, y)
        self.back_pad.move(x, y)
        self.back_imagepad.move(x, y)
        self.front_pad.move(x, y)
        self.front_imagepad.move(x, y)
        self.progress_ring.move(x, y)

        timestamp_height = 14
        timestamp_width = 44
        timestamp_y = y + (self.height() - timestamp_height) // 2
        end_cap_margin = int(max(6, self.rounded_radius // 2))

        self.timestamp_left.move(x + end_cap_margin, timestamp_y)
        self.timestamp_right.move(x + self.width() - end_cap_margin - timestamp_width, timestamp_y)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
    def setHidden(self, hidden):
        self.back_pad.setHidden(hidden)
        self.back_imagepad.setHidden(hidden)
        super().setHidden(hidden)
        self.front_pad.setHidden(hidden)
        self.front_imagepad.setHidden(hidden)
        self.progress_ring.setHidden(hidden)
            
    def setStyle(self, **kwargs):
        show_progress = kwargs.get("progress-visible", True)
        self.progress_ring.setVisible(show_progress)
        self.timestamp_left.setVisible(show_progress)
        self.timestamp_right.setVisible(show_progress)

        if "font-size" in kwargs:
            self.setFontSize(int(kwargs["font-size"].replace("px", "")))
        if "font-family" in kwargs:
            self.setFontFamily(kwargs["font-family"])
        if "font-weight" in kwargs:
            self.setFontWeight(kwargs["font-weight"])
        if "font-image" in kwargs:
            self.setBrush(QPixmap(resource_path(kwargs["font-image"])))
        elif "font-color" in kwargs:
            self.setBrush(convert_to_color(kwargs["font-color"], width=self.width(), height=self.height()))
        if "use-italic" in kwargs:
            self.setFontItalic(kwargs["use-italic"])
        if "flip-text" in kwargs:
            self.flip = kwargs["flip-text"]
        else:
            self.flip = False
            
            
        if "line-color" in kwargs:
            self.setPen(convert_to_color(kwargs["line-color"]))
        if "line-width" in kwargs:
            self.setLineWidth(kwargs["line-width"])
        
        for key, ip, p in [("background", self.back_imagepad, self.back_pad), ("foreground", self.front_imagepad, self.front_pad)]:
        
            if f"{key}-image" in kwargs:
                p.setColor(QColor(0,0,0,0))
                px = QPixmap(resource_path(kwargs[f"{key}-image"]))
                px = px.scaledToHeight(self.height(), Qt.SmoothTransformation)
                if px.width() > self.width():
                    px = px.copy((px.width() - self.width()) // 2, 0, self.width(), self.height())
                if self.rounded_radius > 0:
                    path = QPainterPath()
                    path.addRoundedRect(0, 0, self.width(), self.height(), self.rounded_radius, self.rounded_radius)
                    new_px = QPixmap(self.width(), self.height())
                    new_px.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(new_px)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, px)
                    painter.end()
                    px = new_px
                ip.setPixmap(px)

            elif f"{key}-color" in kwargs:
                ip.clear()
                p.setStyleSheet("")
                p.setColor(convert_to_color(kwargs[f"{key}-color"], width=self.width(), height=self.height()))
            else:
                ip.clear()
                p.setStyleSheet("background-color: transparent")

        if "border-color" in kwargs and kwargs.get("border-width", 0):
            self.back_pad.setBorder(
                convert_to_color(kwargs["border-color"]),
                kwargs.get("border-width", 0),
            )
        else:
            self.back_pad.setBorder(None, 0)

        if "progress-color" in kwargs:
            self.progress_ring.color = convert_to_color(kwargs["progress-color"])
        elif "font-color" in kwargs:
            self.progress_ring.color = convert_to_color(kwargs["font-color"])
        
        # Set timestamp label colors from theme (priority: font-color > line-color > shadow-color)
        if "font-color" in kwargs:
            font_color_val = kwargs["font-color"]
            # If font-color is a gradient, use line-color or shadow-color for timestamp
            if isinstance(font_color_val, str) and (font_color_val.strip().startswith("qlineargradient") or font_color_val.strip().startswith("qradialgradient")):
                if "line-color" in kwargs:
                    color = convert_to_color(kwargs["line-color"])
                elif "shadow-color" in kwargs:
                    color = convert_to_color(kwargs["shadow-color"])
                else:
                    color = QColor(255,255,255)  # fallback to white
            else:
                color = convert_to_color(font_color_val)
                if isinstance(color, QColor) and color.alpha() < 128:
                    if "line-color" in kwargs:
                        color = convert_to_color(kwargs["line-color"])
                    elif "shadow-color" in kwargs:
                        color = convert_to_color(kwargs["shadow-color"])
            if isinstance(color, QColor):
                color_str = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
                font_size = kwargs.get("font-size", "30px")
                font_family = kwargs.get("font-family", "Arial, sans-serif")
                # Keep timestamps smaller than lyrics but still readable.
                timestamp_size = max(12, int(float(font_size.replace("px", "")) * 0.85))
                style = f"background-color: transparent; color: {color_str}; font-size: {timestamp_size}px; font-family: {font_family};"
                self.timestamp_left.setStyleSheet(style)
                self.timestamp_right.setStyleSheet(style)
            
        # NOTE: the ring has no separate "track" color to wire up like the
        # old linear ProgressBar did (progress-line-color/line-color) -- it
        # draws directly over the bar's own border, which is already
        # theme-colored, so the border itself doubles as the ring's track.
        self.progress_ring.thickness = float(kwargs.get("border-width", 2.5)) + 0.5
            
        if "use-shadow" in kwargs and kwargs["use-shadow"]:
            glow = QGraphicsDropShadowEffect()
            self.glow_color = convert_to_color(kwargs["shadow-color"])
            glow.setColor(self.glow_color)
            glow.setBlurRadius(kwargs["shadow-radius"])
            glow.setOffset(*kwargs["shadow-offset"])
            self.setGraphicsEffect(glow)
        elif "use-shadow" in kwargs and not kwargs["use-shadow"]:
            self.setGraphicsEffect(None)
        
        if "entering" in kwargs:
            entering = kwargs["entering"]
            if entering == "fadein":
                self.entering = [("opacity", [(0, 0.1), (1, 1.0)])]
            elif entering == "leftslidein":
                self.entering = [("x_pos", [(0, -self.width()), (1, 0)])]
            elif entering == "rightslidein":
                self.entering = [("x_pos", [(0, self.width()), (1, 0)])]
            elif entering == "topslidein":
                self.entering = [("y_pos", [(0, -self.height()), (1, 0)])]
            elif entering == "bottomslidein":
                self.entering = [("y_pos", [(0, self.height()), (1, 0)])]
            elif entering == "zoomin":
                self.entering = [("scale", [(0, 0.1), (1, 1)])]
            elif entering == "zoomin_overscale":
                self.entering = [("scale", [(0, 0.1), (0.6, 1.5), (1, 1)])]
            else:
                self.entering = None
        if "leaving" in kwargs:
            leaving = kwargs["leaving"]
            if leaving == "fadeout":
                self.leaving = [("opacity", [(0, None), (1, 0.1)])]
            elif leaving == "leftslideout":
                self.leaving = [("x_pos", [(0, None), (1, -self.width())])]
            elif leaving == "rightslideout":
                self.leaving = [("x_pos", [(0, None), (1, self.width())])]
            elif leaving == "topslideout":
                self.leaving = [("y_pos", [(0, None), (1, -self.height())])]
            elif leaving == "bottomslideout":
                self.leaving = [("y_pos", [(0, None), (1, self.height())])]
            elif leaving == "zoomout":
                self.leaving = [("scale", [(0, None), (1, 0.1)])]
            else:
                self.leaving = None
        if "sustaining" in kwargs:
            sustaining = kwargs["sustaining"]
            if sustaining == "flickering":
                self.sustaining = [("opacity", [(0, 1.0), (0.5, 0.7), (1, 1.0)])]
            elif sustaining == "hshaking":
                self.sustaining = [("x_pos", [(0, 0), (0.25, 2), (0.75, -2), (1, 0)])]
            elif sustaining == "vshaking":
                self.sustaining = [("y_pos", [(0, 0), (0.25, 2), (0.75, -2), (1, 0)])]
            elif sustaining == "zooming":
                self.sustaining = [("scale", [(0, 1), (0.5, 0.9), (1, 1)])]
            else:
                self.sustaining = None
        

                
    def applyValues(self, reset=False, **kwargs):
        if "scale" in kwargs:
            self.scale = kwargs["scale"]
        elif reset:
            self.scale = 1
        if "opacity" in kwargs:
            self.opacity = kwargs["opacity"]
        elif reset:
            self.opacity = 1
        if "x_pos" in kwargs:
            self.x_pos = kwargs["x_pos"]
        elif reset:
            self.x_pos = 0
        if "y_pos" in kwargs:
            self.y_pos = kwargs["y_pos"]
        elif reset:
            self.y_pos = 0
    
    def adjustLineProgress(self, line_progress):
        if self.animation is not None:
            if self.animation.state() == QPropertyAnimation.Running:
                self.animation.pause()
            else:
                self.animation.start()
                self.animation.pause()
            self.applyValues(reset=True)
            self.animation.setCurrentTime(line_progress)
            self.animation.resume()
                
    def setText(self, text, use_animation=True, duration=None, start_time=None):
        # print(text, use_animation, duration, start_time)
        super().setText(text)
        self.applyValues(reset=True)
        self.update()
        if duration is not None:
            if duration < 0:
                duration = None
            else:
                duration = int(duration)
        else:
            duration = -1
        
        # PYQT5
        # if self.animation is not None and self.animation.state() == QPropertyAnimation.Running:
        #     self.animation.stop()
        # PyQt5
        if self.animation is not None and self.animation.state() == QAbstractAnimation.State.Running:
            self.animation.stop()
        if use_animation:
            if self.animation is None:
                self.animation = LyricAnimation(self, duration, entering=self.entering, sustaining=self.sustaining, leaving=self.leaving)
            else:
                self.animation.setAnimation(entering=self.entering, sustaining=self.sustaining, leaving=self.leaving)
                self.animation.setDuration(duration)
            self.animation.start()
            if start_time is not None:
                current_time = datetime.now().timestamp() * 1000
                safe_start_time = start_time if start_time is not None else current_time
                try:
                    time_offset = int(current_time - safe_start_time)
                    self.animation.setCurrentTime(time_offset)
                except (TypeError, ValueError):
                    # Fallback if arithmetic fails
                    self.animation.setCurrentTime(0)
        else:
            self.animation = None
            
    def setProgress(self, progress, current_ms=0, total_ms=0):
        self.progress_ring.setProgress(progress)
        
        # Update timestamp labels
        if total_ms > 0:
            current_str = self._format_time(current_ms)
            total_str = self._format_time(total_ms)
            self.timestamp_left.setText(current_str)
            self.timestamp_right.setText(total_str)
        else:
            self.timestamp_left.setText("0:00")
            self.timestamp_right.setText("0:00")
    
    def _format_time(self, ms):
        """Convert milliseconds to mm:ss format"""
        seconds = int(ms / 1000)
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"