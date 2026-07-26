import logging
import sys
import time
from PyQt5.QtCore import Qt, QTimer, QCoreApplication, pyqtSignal, QMutex, QSettings
from PyQt5.QtGui import QBitmap, QCursor, QIcon, QPainter, QPainterPath, QRegion
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QWidget,
    QMenu,
    QSystemTrayIcon,
    QPushButton
)

# WindowsWindowEffect import removed - was causing black background with setAeroEffect

from LyricBar.themes import MINIMAL_THEME_NAMES, get_style, load_themes
from LyricBar.ui.components.lyriclabel import LyricLabel
from LyricBar.ui.components.toasttag import ToastTag
from LyricBar.config import settings, resource_path
from LyricBar.backend.lyricsmaintainer import LyricsMaintainer
from LyricBar.nowplaying import NowPlayingSpicetify, NowPlayingSystem
from LyricBar.utils.dataclasses import PlayingStatusTrigger
from LyricBar.utils.tools import check_if_windows_locked

# STT feature is completely disabled to avoid vosk dependency in executable
STTMaintainer = None
STT_AVAILABLE = False


class FloatingIcon(QPushButton):
    """A draggable floating button widget"""
    
    def __init__(self, parent=None):
        super().__init__("♪", parent)
        # Make it a separate top-level window
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(40, 40)
        
        # Styling
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 120),
                    stop:1 rgba(220, 220, 220, 140));
                color: rgba(255, 255, 255, 220);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 160),
                    stop:1 rgba(240, 240, 240, 180));
                border: 1px solid rgba(255, 255, 255, 140);
            }
            QPushButton:pressed {
                background: rgba(200, 200, 200, 160);
            }
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Dragging support
        self._drag_pos = None
        
        # Position at bottom-right by default
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 60, screen.height() - 100)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            # If barely moved, treat as click
            if (event.globalPos() - self.frameGeometry().topLeft() - self._drag_pos).manhattanLength() < 10:
                self.click()  # Trigger the button click
            self._drag_pos = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class LyricsDisplay(QWidget):
    toast_signal = pyqtSignal(str, int)
    hide_later_signal = pyqtSignal()
    cancel_hide_signal = pyqtSignal()
    callback_signal = pyqtSignal(object)
    def __init__(self, app): #, screen_width, screen_height):
        super().__init__()
        self.app = app
        
        # self.desktop = self.app.screens()
        self.screen_id = 0
        self.app.screenAdded.connect(self.screenAdded)
        self.app.screenRemoved.connect(self.screenRemoved)

        
        self.windowConfig()
        self.corner_radius = settings.taskbar_height // 2
        self.setFixedHeight(settings.taskbar_height)
        # Enable rounded window masking so no rectangular edge appears outside the bar.
        self.use_masked_corners = True
        
        self.frame = QFrame(self)
        self.frame.setStyleSheet("background-color: transparent;")  # Ensure frame is transparent
        
        self.faux_taskbar = QLabel(self.frame)
        self.faux_taskbar.setStyleSheet("background-color: rgba(0, 0, 0, 0.06);")
        self.label = LyricLabel(None, parent=self.frame)
        self.label.setLyricsYOffset(10)
        
        # Add minimize button (collapses to small icon)
        self.minimize_button = QPushButton("−", self)
        self.minimize_button.setStyleSheet("QPushButton { background: transparent; color: transparent; border: 0; padding: 0; }")
        self.minimize_button.setFixedSize(18, 18)
        self.minimize_button.clicked.connect(self.minimizeToIcon)
        self.minimize_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.minimize_button.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Ensure button receives clicks
        self.minimize_button.raise_()  # Keep on top
        self.minimize_button.hide()
        
        # Create floating restore icon (initially hidden) - uses a separate window
        self.restore_icon = FloatingIcon(None)  # No parent so it stays independent
        self.restore_icon.clicked.connect(self.restoreFromIcon)
        
        self.toaster = ToastTag(parent=self)
        self.toaster.setHidden(True)
        self.toast_signal.connect(self.toaster.start)
        
        # Dragging support
        self._drag_pos = None
        self._is_dragging = False
        self._is_minimized = False
        self.position_mode = "top"  # "bottom" or "top" or "custom"
        
        # Resizing support (corner-based only for proportional scaling)
        self._is_resizing = False
        self._resize_corner = None  # 'top-left', 'top-right', 'bottom-left', 'bottom-right'
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self._base_height = settings.taskbar_height  # Store original/max height for scaling
        self._base_width = None  # Will be set after position is determined
        self._scale_factor = 1.0  # Current scale factor
        
        # Cursor update timer for Ctrl key
        self._cursor_update_timer = QTimer(self)
        self._cursor_update_timer.timeout.connect(self.updateCursorOnTimer)
        self._cursor_update_timer.setInterval(50)  # 20 FPS for cursor - sufficient for smooth UX
        
        # Load theme preference only
        self.loadThemeSettings()
        
        self.setPosition(use_saved=False)
        self.show()
        self.setMouseTracking(True)
        
        # Apply rounded corners
        self.applyRoundedCorners()
        
        self.displaying_line = None
        self.displaying_begin_time = None
        self.paused = False
        self.minimized_for_no_lyrics = False  # Flag to track auto-minimize vs manual minimize
        self.last_auto_minimize_time = 0  # Prevent rapid auto-minimize cycles
        self.lyrics_search_in_progress = False  # Flag to prevent premature auto-minimize during search
        
        self.bar_hidden = False
        # self.app.installEventFilter(self)
        
        self.style_name = "default"
        self.formatter = lambda x: x
        
        self.reappear_timer = QTimer(self)
        self.reappear_timer.setSingleShot(True)
        self.reappear_timer.timeout.connect(self.reappear)
        
        self.hide_later_timer = QTimer(self)
        self.hide_later_timer.setSingleShot(True)
        self.hide_later_timer.timeout.connect(lambda: self.setHidden(True))
        
        self.hide_later_signal.connect(lambda: self.hide_later_timer.start(1000))
        self.cancel_hide_signal.connect(lambda: self.hide_later_timer.stop() if self.hide_later_timer.isActive() else None)
    

        self.callback_signal.connect(self.maintainer_callback)
        
        if settings.playing_info_provider == "Spicetify":
            self.now_playing = NowPlayingSpicetify(socket_port=settings.spicetify_port, update_callback=self.callback_signal.emit, offset=120)
        else:
            # Reduced sync_interval from 100ms to 50ms for faster lyric updates (less delay)
            self.now_playing = NowPlayingSystem(update_callback=self.callback_signal.emit, sync_interval=50, offset=0)
        
        self.line_mode = 0
        self.lyric_maintainer = LyricsMaintainer(self.now_playing, self.callback_signal.emit) 
        
        # Initialize STT only if available
        if STT_AVAILABLE and STTMaintainer is not None:
            self.sst_maintainer = STTMaintainer(self.now_playing, self.callback_signal.emit)
            self.sst_maintainer.pause()
        else:
            self.sst_maintainer = None
        
        
        self.timer = QTimer(self)
        self.style_mutex = QMutex()
        
        # Debounce timer for track changes to prevent crashes
        self.track_change_timer = QTimer(self)
        self.track_change_timer.setSingleShot(True)
        self.track_change_timer.timeout.connect(self.handleTrackChange)
        self.pending_track_data = None
        
        # Rainbow background animation for black theme
        self.rainbow_hue = 0
        self.rainbow_timer = QTimer(self)
        self.rainbow_timer.timeout.connect(self.updateRainbowBackground)
        self.rainbow_timer.start(50)  # Update every 50ms for smooth rainbow effect
        
        self.timer.timeout.connect(self.update_info)
        # Use ~60 FPS UI updates so progress and lyric transitions feel lock-step.
        self.timer.start(16)
        
        # Initialize progress bar to 0 on startup
        self.label.setProgress(0)
        self.label.progressbar.progress = 0
        logging.info("=== APP INITIALIZED - Progress bar reset to 0 ===")
        self._drag_pos = None
        self._is_dragging = False
        self.setup_debug_console()
        
        self.now_playing.start_loop()
        self.toast("Welcome to LyricBar", 3000)
        
        # self.applyBackgroundEffect()
    
    def setup_debug_console(self):
        """Setup the debug console functionality for compiled executable"""
        self._console_visible = False
        self._console_handler = None
        
        def toggle_console():
            try:
                import sys
                import io

                if not sys.platform.startswith("win"):
                    self.toast("Console toggle is only available on Windows")
                    return

                import ctypes
                kernel32 = ctypes.windll.kernel32
                user32 = ctypes.windll.user32
                
                if not self._console_visible:
                    # Allocate console
                    kernel32.AllocConsole()
                    
                    # Store original handles for restoration
                    self._original_stdout = sys.stdout
                    self._original_stderr = sys.stderr
                    
                    # Redirect stdout/stderr to console for print statements
                    console_out = io.TextIOWrapper(open('CONOUT$', 'wb'), encoding='utf-8')
                    sys.stdout = console_out
                    sys.stderr = console_out
                    
                    # Set console title
                    kernel32.SetConsoleTitleW("LyricBar Debug Console - Live Logging")
                    
                    # Get console window handle and make it nice
                    console_hwnd = kernel32.GetConsoleWindow()
                    if console_hwnd:
                        # Set console window size and position
                        user32.SetWindowPos(console_hwnd, 0, 100, 100, 800, 600, 0x0040)  # SWP_SHOWWINDOW
                        # Make console window topmost briefly to show it
                        user32.SetWindowPos(console_hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_TOPMOST
                        user32.SetWindowPos(console_hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_NOTOPMOST
                    
                    self._console_visible = True
                    print("🖥️  LyricBar Debug Console Activated!")
                    print("📊 Live logging enabled - you'll see all debug info here")
                    print("=" * 60)
                    
                    # Reconfigure existing logging handlers to use the console
                    # Remove any existing handlers that might conflict
                    root_logger = logging.getLogger()
                    for handler in root_logger.handlers[:]:
                        if isinstance(handler, logging.StreamHandler) and hasattr(handler, 'stream'):
                            if handler.stream in (self._original_stdout, self._original_stderr, sys.__stdout__, sys.__stderr__):
                                root_logger.removeHandler(handler)
                    
                    # Add a new console handler using the redirected stdout
                    self._console_handler = logging.StreamHandler(sys.stdout)
                    self._console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s:%(name)s:%(message)s'))
                    self._console_handler.setLevel(logging.INFO)
                    root_logger.addHandler(self._console_handler)
                    
                    # Test the logging
                    print("📊 Logging system configured for console output")
                    logging.info("🖥️ Debug console activated successfully!")
                    logging.info("📊 All future logs will appear here in real-time")
                    
                else:
                    # Remove console handler first
                    if self._console_handler:
                        root_logger = logging.getLogger()
                        root_logger.removeHandler(self._console_handler)
                        self._console_handler = None
                    
                    # Restore original stdout/stderr
                    if hasattr(self, '_original_stdout'):
                        sys.stdout = self._original_stdout
                    if hasattr(self, '_original_stderr'):
                        sys.stderr = self._original_stderr
                    
                    # Hide console
                    kernel32.FreeConsole()
                    self._console_visible = False
                    logging.info("🖥️  Debug console hidden")
                    
            except Exception as e:
                logging.error(f"❌ Failed to toggle console: {e}")
        
        # Store toggle function globally for access from UI
        import builtins
        builtins.toggle_console = toggle_console

    
    @property
    def line_provider(self):
        if self.line_mode == 0:
            return self.lyric_maintainer
        return self.sst_maintainer
    
    @property
    def allowed_to_reappear(self):
        return not ((self.geometry().top() <= QCursor.pos().y() <= self.geometry().bottom()) or check_if_windows_locked() or self.app.screens() == [])
    
    def switch_mode(self):
        logging.info("SWITCHING MODE")
        if self.line_mode == 0:
            if self.sst_maintainer is None:
                self.toast("STT not available")
                return
            self.line_mode = 1
            self.toast("Switching to STT Mode")
            self.label.right_pad = True
            self.label.use_scale = False
            self.lyric_maintainer.pause()
            self.sst_maintainer.start()
        else:
            self.line_mode = 0
            self.toast("Switching to Lyrics Mode")
            self.label.right_pad = False
            self.label.use_scale = True
            self.lyric_maintainer.start()
            if self.sst_maintainer is not None:
                self.sst_maintainer.pause()
            
    def set_stt_mode(self):
        if self.line_mode == 0:
            self.switch_mode()
            
    def set_lyrics_mode(self):
        if self.line_mode == 1:
            self.switch_mode()
    
    # def applyBackgroundEffect(self):
    #     self.windowsEffect.setAeroEffect(self.winId())
    #     # logging.info(getSystemAccentColor().name())
    #     # self.windowsEffect.setAcrylicEffect(self.winId(), gradientColor="271b43ff", enableShadow=False, animationId=0)
    #     # self.windowsEffect.enableBlurBehindWindow(self.winId())
    
    # def clearBackgroundEffect(self):
    #     self.windowsEffect.removeBackgroundEffect(self.winId())
        
    def switchDesktop(self, next=True):
        screen_count = len(self.app.screens())
        if screen_count == 0:
            self.setHidden(True)
        elif screen_count > 0 and self.bar_hidden:
            self.setHidden(False)
        self.screen_id = (self.screen_id + (1 if next else 0)) % screen_count
        self.toast(f"Moving to Screen {self.screen_id}")
        self.setPosition()
        
    def screenAdded(self):
        self.switchDesktop(next=False)
    
    def screenRemoved(self):
        self.switchDesktop(next=False)
    
    def toast(self, text, duration=1000):
        self.toaster.start(text, duration)
        
    def copyLyricsToClipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.line_provider.line.text)
    
    def setPosition(self, use_saved=False):
        if self.screen_id >= len(self.app.screens()):
            self.switchDesktop(next=False)
        screen = self.app.screens()[self.screen_id]
        screen_height = screen.geometry().height()
        screen_width = screen.geometry().width()
        screen_top = screen.geometry().top()
        screen_left = screen.geometry().left()
        
        width = screen_width - 2 * settings.leftout_width
        height = settings.taskbar_height
        x = (screen_width - width) // 2
        
        # Store base/max dimensions for resize limits
        if self._base_width is None:
            self._base_width = width
        
        # Position based on mode
        if self.position_mode == "top":
            y = 0
        else:
            y = screen_height - height
        
        self.setGeometry(screen_left + x, screen_top + y, width, height)
        
        self.faux_taskbar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.faux_taskbar.setGeometry(0, 0, self.width(), self.height())
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(self.width(), self.height())
        toast_width = max(140, (self.height() + 10) * 2)
        self.toaster.setGeometry(max(0, (self.width() - toast_width) // 2), 0, toast_width, self.height() + 6)
        
        # Update rounded corners when resizing
        self.applyRoundedCorners()
    
    def minimizeToIcon(self):
        """Minimize the lyrics window to a floating icon"""
        if self._is_minimized:
            return

        self._is_minimized = True
        
        # Position the restore icon where the minimize button was
        button_global_pos = self.minimize_button.mapToGlobal(self.minimize_button.pos())
        # Center the floating icon over where the minimize button was
        icon_x = button_global_pos.x() + self.minimize_button.width() // 2 - self.restore_icon.width() // 2
        icon_y = button_global_pos.y() + self.minimize_button.height() // 2 - self.restore_icon.height() // 2
        
        # Ensure icon stays within screen bounds
        screen = QApplication.primaryScreen().geometry()
        icon_x = max(0, min(icon_x, screen.width() - self.restore_icon.width()))
        icon_y = max(0, min(icon_y, screen.height() - self.restore_icon.height()))
        
        self.restore_icon.move(icon_x, icon_y)
        self.restore_icon.show()
        self.restore_icon.raise_()
        self.restore_icon.activateWindow()
        
        super().setHidden(True)
    
    def restoreFromIcon(self):
        """Restore the lyrics window from the floating icon"""
        if not self._is_minimized and not self.restore_icon.isVisible():
            return

        self._is_minimized = False
        self.minimized_for_no_lyrics = False  # Reset auto-minimize flag on manual restore
        self.restore_icon.hide()
        self.bar_hidden = False
        super().setHidden(False)
    
    def loadThemeSettings(self):
        """Load saved theme preference"""
        qsettings = QSettings("LyricBar", "WindowSettings")
        saved_theme = qsettings.value("theme", None)
        if saved_theme in MINIMAL_THEME_NAMES:
            settings.default_theme = saved_theme

    def saveThemeSettings(self):
        """Save theme preference"""
        qsettings = QSettings("LyricBar", "WindowSettings")
        qsettings.setValue("theme", settings.default_theme)
    
    def closeEvent(self, event):
        """Handle window close"""
        # Stop all timers before closing
        if hasattr(self, 'rainbow_timer'):
            self.rainbow_timer.stop()
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'track_change_timer'):
            self.track_change_timer.stop()
        if hasattr(self, '_cursor_update_timer'):
            self._cursor_update_timer.stop()
        
        # Clean up lyrics manager threads
        if hasattr(self, 'lyric_maintainer') and self.lyric_maintainer:
            if hasattr(self.lyric_maintainer, 'manager') and self.lyric_maintainer.manager:
                self.lyric_maintainer.manager.cleanup()
        

        
        self.saveThemeSettings()
        super().closeEvent(event)
    
    def getCornerAtPosition(self, pos):
        """Determine which corner (if any) is at the given position"""
        corner_margin = 20  # pixels from corner to detect resize
        
        rect = self.rect()
        corner = None
        
        # Skip if clicking on minimize button
        if self.minimize_button.geometry().contains(pos):
            return None
        
        # Check corners only (not edges)
        at_left = pos.x() <= corner_margin
        at_right = pos.x() >= rect.width() - corner_margin
        at_top = pos.y() <= corner_margin
        at_bottom = pos.y() >= rect.height() - corner_margin
        
        if at_top and at_left:
            corner = 'top-left'
        elif at_top and at_right:
            corner = 'top-right'
        elif at_bottom and at_left:
            corner = 'bottom-left'
        elif at_bottom and at_right:
            corner = 'bottom-right'
        
        return corner
    
    def updateCursor(self, pos):
        """Update cursor based on position"""
        corner = self.getCornerAtPosition(pos)
        
        if corner in ['top-left', 'bottom-right']:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif corner in ['top-right', 'bottom-left']:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def updateChildWidgets(self):
        """Update child widget positions and scale after resize"""
        # Calculate scale factor based on height change
        self._scale_factor = self.height() / self._base_height
        
        # Update child widget sizes
        self.faux_taskbar.setGeometry(0, 0, self.width(), self.height())
        self.label.setFixedSize(self.width(), self.height())
        self.label.setGeometry(0, 0, self.width(), self.height())
        toast_width = max(140, (self.height() + 10) * 2)
        self.toaster.setGeometry(max(0, (self.width() - toast_width) // 2), 0, toast_width, self.height() + 6)
        
        # Apply scale to label (font size)
        self.label.applyScale(self._scale_factor)
        
        # Update rounded corners
        self.applyRoundedCorners()
        
        # Force label to update
        self.label.updatePath()
        self.label.update()
    
    def windowConfig(self):
        self.setAcceptDrops(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # GPU-accelerated rendering optimizations for buttery smooth performance
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        # WA_NoSystemBackground removed - was causing black background
        
        # High DPI and rendering optimizations
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)  # Disable if not needed
        
        # Double buffering for flicker-free rendering
        self.setAttribute(Qt.WA_PaintOnScreen, False)  # Use double buffering
        
        # Optimize paint updates for maximum smoothness
        self.setUpdatesEnabled(True)
        self.setAutoFillBackground(False)  # We handle our own background
        
        # Enable native rendering for better GPU utilization
        self.setAttribute(Qt.WA_NativeWindow, False)  # Use Qt's compositor for smoother blending
        self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)  # Optimize widget hierarchy
    
    def applyRoundedCorners(self):
        """Apply rounded corners to the window"""
        radius = self.corner_radius
        if self.use_masked_corners:
            # Use an antialiased bitmap mask for smoother corner edges than polygon regions.
            mask = QBitmap(self.size())
            mask.fill(Qt.color0)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.color1)
            painter.drawRoundedRect(0, 0, max(0, self.width() - 1), max(0, self.height() - 1), radius, radius)
            painter.end()
            self.setMask(mask)
        else:
            self.clearMask()

        # Keep background visibly rounded regardless of mask mode.
        self.faux_taskbar.setStyleSheet(
            f"""
            background-color: rgba(0, 0, 0, 0.12);
            border-radius: {radius}px;
            """
        )
        
    
    def updateStyle(self, style, force_reload=False):
        # Use tryLock instead of lock to prevent deadlocks
        if not self.style_mutex.tryLock(100):
            # If we can't get the lock quickly, queue it for later
            QTimer.singleShot(100, lambda: self.updateStyle(style, force_reload))
            return
        
        try:
            if not style or "name" not in style:
                return
                
            if style["name"] == self.style_name and not force_reload:
                return
            
            self.label.setStyle(**style)
            self.style_name = style["name"]
            self.formatter = style["format"]
            self.displaying_line = None
            
            # Trigger immediate rainbow update if switching to black theme
            if style["name"] == "black":
                self.updateRainbowBackground()
        except Exception as e:
            logging.error(f"Error updating style: {e}")
        finally:
            self.style_mutex.unlock()
        
        return 
    
    def updateRainbowBackground(self):
        """Update the rainbow gradient background for black theme"""
        if self.style_name != "black":
            # Reset to transparent for other themes
            self.faux_taskbar.setStyleSheet(
                f"""
                background-color: rgba(0, 0, 0, 0.12);
                border-radius: {self.corner_radius}px;
                """
            )
            return
        
        # Increment hue (0-360 degrees)
        self.rainbow_hue = (self.rainbow_hue + 3) % 360  # Faster cycling
        
        # Convert HSV to RGB for multiple gradient stops
        import colorsys
        
        # Create 7 color stops across the rainbow spectrum
        colors = []
        for i in range(7):
            hue = (self.rainbow_hue + i * 51.4) % 360  # ~51.4 degrees apart (360/7)
            rgb = colorsys.hsv_to_rgb(hue / 360.0, 0.85, 0.5)  # 85% saturation, 50% value for vibrant effect
            r, g, b = int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        
        # Create dynamic diagonal gradient stylesheet with higher opacity (no QLabel selector!)
        gradient = f"""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 {colors[0]}F0,
                stop:0.166 {colors[1]}F0,
                stop:0.333 {colors[2]}F0,
                stop:0.5 {colors[3]}F0,
                stop:0.666 {colors[4]}F0,
                stop:0.833 {colors[5]}F0,
                stop:1 {colors[6]}F0);
            border-radius: {self.corner_radius}px;
        """
        
        # Apply to the faux taskbar (background)
        self.faux_taskbar.setStyleSheet(gradient)
    
    def handleTrackChange(self):
        """Handle track change - reset state and fetch new lyrics"""
        try:
            if not self.pending_track_data:
                return
                
            if not self.now_playing or not self.now_playing.current_track:
                return
            
            track = self.now_playing.current_track
            logging.info(f"Track change: {track.title} - {track.artist}")
            
            # Clear logged fonts for new track
            from LyricBar.ui.components.outlinedlabel import LOGGED_FONTS
            LOGGED_FONTS.clear()
            
            # Reset UI state
            self.displaying_line = None
            self.displaying_begin_time = None
            self.paused = False
            
            # Reset lyrics and trigger fetch for new track
            if self.lyric_maintainer:
                self.lyric_maintainer.lyrics = None
                self.lyric_maintainer.current_line = None
            
            # Reset auto-minimize flag for new track (don't auto-restore manual minimization)
            self.minimized_for_no_lyrics = False
            # Set lyrics search in progress flag to prevent premature auto-minimize
            self.lyrics_search_in_progress = True
            
            if track.artist and track.title:
                self.lyric_maintainer.manager.get_lyrics(
                    track,
                    lambda x: self.handleLyricsResult(*x)
                )
            
            # Reset UI display
            self.label.setText("♬", False)
            self.label.setProgress(0)
            
            # Update theme
            style = get_style(track)
            if style:
                self.updateStyle(style, force_reload=True)
            
            # Update UI with fresh data
            self.updateLyrics()
            self.label.setProgress(self.now_playing.percent)
            self.label.update()
            self.update()
            
            self.setHidden(False)
            self.pending_track_data = None

        except Exception as e:
            logging.error(f"!!! ERROR in handleTrackChange: {e}")
            import traceback
            traceback.print_exc()
    
    def handleLyricsResult(self, lyrics, track):
        """Handle lyrics search result and clear search in progress flag"""
        logging.info(f"handleLyricsResult called: lyrics={'found' if lyrics else 'None'}, track={track}")
        # Clear the search in progress flag
        self.lyrics_search_in_progress = False
        # Call the original set_lyrics method
        self.lyric_maintainer.set_lyrics(lyrics, track)
    
    def maintainer_callback(self, value):
        try:
            if value == PlayingStatusTrigger.PAUSE:
                self.paused = True
                if self.now_playing and self.now_playing.current_track:
                    logging.info(f"!!PAUSING: {self.now_playing.current_track}")
                self.hide_later_signal.emit()
                
            elif value == PlayingStatusTrigger.RESUME:
                self.paused = False
                if self.now_playing and self.now_playing.current_track:
                    logging.info(f"!!RESUMING: {self.now_playing.current_track}")
                self.setHidden(False)
                
            elif value == PlayingStatusTrigger.NEW_TRACK:
                self.paused = False
                logging.info("=== RECEIVED NEW_TRACK CALLBACK ===")
                if self.now_playing and self.now_playing.current_track:
                    logging.info(f"!!NEW TRACK: {self.now_playing.current_track.title} - {self.now_playing.current_track.artist}")
                    # Force immediate complete reload on track change
                    self.pending_track_data = value
                    # Stop debounce timer if it's running
                    self.track_change_timer.stop()
                    # Call handleTrackChange immediately
                    self.handleTrackChange()
                else:
                    logging.info("No current track info available")
                    
            elif isinstance(value, str):
                self.toast_signal.emit(value, 2000)
        except Exception as e:
            logging.error(f"Error in maintainer_callback: {e}")


    def updateLyrics(self, anim=True):
        if self.isHidden():
            return
            
        # Safety checks
        if not self.line_provider or not self.formatter:
            return
            
        try:
            self.raise_()
        except Exception:
            pass
        
        try:
            line = self.line_provider.line
            begin_time = None if (line is None or line.begin_time <= 0) else line.begin_time
            
            if line:
                text = line.text
                # NO animations - instant flash appearance only
                formatted = self.formatter(text)
                
                # Check if already displaying this line
                if (line == self.displaying_line and 
                    formatted == self.displaying_line.text and 
                    begin_time == self.displaying_begin_time):
                    return
                
                # Handle special timestamps
                if line.timestamp == -2:
                    formatted = self.formatter("♬")
                elif line.timestamp == -3:
                    formatted = self.formatter("🔄")
                elif line.timestamp == -4:
                    formatted = self.formatter("👂")
                elif line.timestamp == 0:
                    if self.line_mode == 0:
                        formatted = self.formatter("♬")
                    else:
                        formatted = self.formatter("👂") if line.text == self.formatter("") else self.formatter(line.text)
                
                # Restore from icon only if it was auto-minimized for no lyrics
                if self._is_minimized and self.minimized_for_no_lyrics:
                    self.restoreFromIcon()
                    self.minimized_for_no_lyrics = False
                
                # Update label - NO ANIMATIONS for instant appearance
                try:
                    duration = None
                    if (line.end_timestamp is not None and line.end_timestamp != -1 and 
                        line.timestamp is not None and line.timestamp != -1):
                        duration = line.end_timestamp - line.timestamp
                        
                    self.label.setText(formatted, False, duration=duration, start_time=begin_time)  # Always False = no fade
                    self.displaying_line = line
                    self.displaying_line.text = formatted
                    self.displaying_begin_time = begin_time
                    

                            
                except Exception as e:
                    logging.error(f"Error updating lyrics label: {e}")
            else:
                # No line available - check if music is playing but no lyrics found
                self.displaying_line = None
                
                # If music is playing but no lyrics available, minimize to icon once.
                # Skip this when nothing is actually playing or when the bar is already minimized.
                if (self.now_playing and self.now_playing.current_track and getattr(self.now_playing, "is_playing", False) and
                    hasattr(self.now_playing, 'has_lyrics') and not self.now_playing.has_lyrics and
                    not self.lyrics_search_in_progress):
                    if not self._is_minimized:
                        current_time = time.time()
                        if current_time - self.last_auto_minimize_time > 5:
                            self.minimized_for_no_lyrics = True
                            self.last_auto_minimize_time = current_time
                            self.minimizeToIcon()
                    return

                if self._is_minimized and self.restore_icon.isVisible():
                    self.restoreFromIcon()
                
                # Otherwise show pause symbol
                if self.label.text() != "⏸":
                    self.label.setText("⏸", False)

        except Exception as e:
            logging.error(f"Error in updateLyrics: {e}")
    

        
    def updateProgress(self):
        if self.bar_hidden:
            return
        percent = self.now_playing.percent
        progress_ms = self.now_playing.progress
        current_ms = progress_ms if progress_ms > 0 else 0
        total_ms = self.now_playing.current_track_length if self.now_playing.current_track_length else 0
        
        # Fallback: If SMTC doesn't provide song length but we have lyrics, estimate from lyrics
        if total_ms == 0 and self.lyric_maintainer and self.lyric_maintainer.lyrics:
            try:
                lyrics_lines = self.lyric_maintainer.lyrics.lines
                if lyrics_lines and len(lyrics_lines) > 0:
                    # Use the last line's timestamp + 5 seconds as estimated length
                    last_line_timestamp = lyrics_lines[-1].timestamp
                    total_ms = last_line_timestamp + 5000  # Add 5 seconds buffer
                    logging.debug(f"💡 Using lyrics-based length estimate: {total_ms}ms")
                    
                    # Recalculate percent with estimated length
                    if current_ms > 0 and total_ms > 0:
                        percent = current_ms / total_ms
            except Exception as e:
                logging.debug(f"Error estimating length from lyrics: {e}")
        
        self.label.setProgress(percent, current_ms, total_ms)
    
    def update_info(self):
        try:
            self.updateLyrics()
            self.updateProgress()
        except Exception as e:
            logging.error(f"Error in update_info: {e}")
        
    def setHidden(self, hidden):
        # Don't interfere with minimized state
        if self._is_minimized and hidden:
            return
            
        if not hidden:
            self.cancel_hide_signal.emit()
        self.bar_hidden = hidden
        if hidden:
            self.reappear_timer.start(100)
            super().setHidden(True)
        else:
            if not self.allowed_to_reappear:
                self.reappear_timer.start(100)
                return
            super().setHidden(False)
        
    def reappear(self):
        if self.paused:
            return
        self.setHidden(False)  
        
    def enterEvent(self, e):
        pass
    
    def leaveEvent(self, e):
        pass
    
    def mouseDoubleClickEvent(self, e):
        """Handle double-click to copy lyrics"""
        if e.button() == Qt.MouseButton.LeftButton:
            # Don't copy if clicking on minimize button
            if not self.minimize_button.geometry().contains(e.pos()):
                self.copyLyricsToClipboard()
                self.toast("Lyrics Copied to Clipboard")
    
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            if self.minimize_button.geometry().contains(e.pos()):
                return
            self._is_dragging = True
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.switchDesktop()
        elif e.button() == Qt.MouseButton.RightButton:
            if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier == Qt.KeyboardModifier.ShiftModifier:
                self.switch_mode()
            else:
                self.line_provider.get_from_next_source()
                self.toast("Searching from Next Source")
        elif e.button() == Qt.MouseButton.MiddleButton:
            if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier == Qt.KeyboardModifier.ShiftModifier:
                self.line_provider.set_empty_lyrics()        
                self.toast("Lyrics Cleared")
            else:
                self.line_provider.track_offset = 0
                self.toast("Track Offset Reset")
    
    def mouseMoveEvent(self, e):
        if self._is_dragging and self._drag_pos is not None:
            self.move(e.globalPos() - self._drag_pos)
            e.accept()
    
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self._drag_pos = None
    
    def updateCursorOnTimer(self):
        pass
    
    def keyPressEvent(self, e):
        # Minimize the bar when Shift+Esc is pressed
        if e.key() == Qt.Key_Escape and e.modifiers() & Qt.ShiftModifier:
            self.minimizeToIcon()
        

        super().keyPressEvent(e)
    
    def keyReleaseEvent(self, e):
        super().keyReleaseEvent(e)
    
    def wheelEvent(self, e):
        QModifiers = QApplication.keyboardModifiers()
        if QModifiers & Qt.KeyboardModifier.ShiftModifier == Qt.KeyboardModifier.ShiftModifier:
            self.now_playing.global_offset += e.angleDelta().y()
            self.toast("Global Offset:\n" + str(self.now_playing.global_offset))
        else:
            self.line_provider.track_offset += e.angleDelta().y()
            self.toast("Track Offset:\n" + str(self.line_provider.track_offset))


class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.parent = parent
        self.activated.connect(self.onActivated)
        self.createMenu()
        
    def createMenu(self):
        menu = QMenu(self.parent)
        menu.setStyleSheet(
            """
            QMenu {
                font-family: "Segoe UI", "Arial";
                font-size: 12px;
                background-color: #111114;
                border: 1px solid #2a2a33;
                padding: 4px;
                color: #e8e8e8;
            }
            QMenu::item {
                padding: 4px 8px;
                margin: 1px 2px;
            }
            QMenu::item:selected {
                background-color: #2a2a33;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                margin: 4px 6px;
                background: #2a2a33;
            }
            """
        )

        settingsAction = menu.addAction("Settings")
        reloadThemeAction = menu.addAction("Reload Themes")
        consoleAction = menu.addAction("Toggle Console")
        menu.addSeparator()
        restartAction = menu.addAction("Restart")
        exitAction = menu.addAction("Exit")
        
        self.setContextMenu(menu)
        settingsAction.triggered.connect(self.openSettings)
        exitAction.triggered.connect(self.exit)
        restartAction.triggered.connect(self.restart)
        reloadThemeAction.triggered.connect(self.reloadThemes)
        consoleAction.triggered.connect(self.toggleDebugConsole)
    
    def reloadThemes(self):
        """Reload all themes and refresh the menu"""
        load_themes()
        # Recreate the menu with updated themes
        self.createMenu()
        self.parent.updateStyle(get_style(self.parent.now_playing.current_track), force_reload=True)
        self.parent.toast("Themes Reloaded")
    
    def setPosition(self, position):
        """Set the position mode (top/bottom)"""
        self.parent.position_mode = position
        self.parent.setPosition()
        self.createMenu()
        self.parent.toast(f"Position: {position.capitalize()}")
    
    def openSettings(self):
        """Open the settings dialog"""
        from .components.settingsdialog import SettingsDialog

        dialog = SettingsDialog(parent=self.parent)
        dialog.settings_changed.connect(self.onSettingsChanged)
        dialog.exec_()

    def onActivated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.openSettings()
    
    def onSettingsChanged(self, changes):
        """Handle settings changes.

        NOTE: this used to call `importlib.reload(globalvariables)` then
        `importlib.reload(lyricmanager)` here. Reloading a module re-runs its
        top-level code and creates brand-new class objects -- any code
        already holding a reference to the *old* `LyricsManager` class (e.g.
        a running QThread) would silently stop being `isinstance` of the
        reloaded class, and in-flight lyric fetches could end up orphaned.
        It's no longer needed: `SettingsDialog.save_settings()` already wrote
        through to the single shared `settings` object via
        `settings.update_and_persist(...)`, so every module that reads
        `settings.<field>` already sees the new values -- nothing to reload.
        """
        if changes.get("progress_bar_changed"):
            self.parent.updateStyle(get_style(self.parent.now_playing.current_track), force_reload=True)
            self.parent.toast("Progress bar updated")

        if changes.get("tracking_apps_changed") and hasattr(self.parent, "now_playing"):
            if hasattr(self.parent.now_playing, "tracking_apps"):
                self.parent.now_playing.tracking_apps = changes.get("tracking_apps", [])
                self.parent.toast("Tracking apps updated")

        if changes.get("theme_changed"):
            self.parent.saveThemeSettings()
            self.parent.updateStyle(get_style(self.parent.now_playing.current_track), force_reload=True)
            self.parent.toast(f"Theme: {settings.default_theme}")

        if changes.get("provider_changed"):
            self.parent.toast("Provider changed. Restart LyricBar to apply.")

        if changes.get("timing_offset_changed"):
            self.parent.toast(f"Lyrics timing updated to {changes['timing_offset']}ms")
    
    def toggleDebugConsole(self):
        """Toggle the debug console window"""
        try:
            import builtins
            if hasattr(builtins, 'toggle_console'):
                builtins.toggle_console()
                self.parent.toast("Debug console toggled!")
            else:
                self.parent.toast("Console toggle not available in dev mode")
        except Exception as e:
            self.parent.toast(f"Console error: {e}")
            import logging
            logging.error(f"Failed to toggle debug console: {e}")

    def restart(self):
        """Restart LyricBar"""
        import sys
        import os
        import subprocess
        
        # Get the python executable and script path
        python = sys.executable
        script = sys.argv[0]
        
        # Close the current application
        QCoreApplication.quit()
        
        # Start a new instance
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            # Running as script (hide console window)
            subprocess.Popen([python, script] + sys.argv[1:], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)

    def exit(self):
        # Clean up threads before exiting
        if hasattr(self, 'lyric_maintainer') and self.lyric_maintainer:
            if hasattr(self.lyric_maintainer, 'manager') and self.lyric_maintainer.manager:
                self.lyric_maintainer.manager.cleanup()
        QCoreApplication.exit()

def main():
    # Configure logging FIRST
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s',
        force=True
    )
    logging.info("=== LYRICBAR STARTING ===")
    
    # Enable hardware acceleration and smooth rendering
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)  # Use desktop OpenGL for hardware acceleration
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)  # Use high DPI pixmaps
    QApplication.setAttribute(Qt.AA_SynthesizeMouseForUnhandledTouchEvents, False)  # Improve touch performance
    QApplication.setAttribute(Qt.AA_SynthesizeTouchForUnhandledMouseEvents, False)  # Improve mouse performance
    
    # GPU-specific optimizations for NVIDIA RTX 4050
    import os
    os.environ['QSG_RENDER_LOOP'] = 'threaded'  # Use threaded render loop for better GPU utilization
    os.environ['QT_OPENGL'] = 'desktop'  # Force desktop OpenGL
    os.environ['QT_QUICK_BACKEND'] = 'opengl'  # Use OpenGL backend
    
    # Force NVIDIA RTX 4050 usage (discrete GPU over integrated)
    os.environ['__NV_PRIME_RENDER_OFFLOAD'] = '1'  # NVIDIA Optimus
    os.environ['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'  # Force NVIDIA driver
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Use first GPU (usually discrete)
    
    # Windows-specific GPU selection
    os.environ['GPU_FORCE_64BIT_PTR'] = '1'  # Enable 64-bit pointers for large VRAM
    os.environ['GPU_MAX_HEAP_SIZE'] = '100'  # Use 100% of GPU memory if needed
    os.environ['GPU_USE_SYNC_OBJECTS'] = '1'  # Enable GPU sync objects for better performance
    
    # Try to set discrete GPU preference programmatically (Windows 10+)
    try:
        import ctypes
        
        # Load d3d11.dll and set GPU preference
        d3d11 = ctypes.windll.d3d11
        if hasattr(d3d11, 'D3D11CreateDevice'):
            # Set preference for high-performance GPU (RTX 4050)
            logging.info("🎯 Setting discrete GPU preference...")
    except Exception as e:
        logging.info(f"ℹ️  Could not set GPU preference programmatically: {e}")
        logging.info("ℹ️  Make sure LyricBar.exe is set to 'High Performance' in Windows Graphics Settings")
    

    
    app = QApplication(sys.argv)
    
    # Detect GPU without failing startup when the Windows probing tools are
    # unavailable or noisy on the host.
    try:
        from LyricBar.utils.gpu import log_gpu_status

        log_gpu_status()
    except Exception as exc:
        logging.info("ℹ️  GPU detection failed: %s", exc)
        logging.info("ℹ️  Make sure to set LyricBar to 'High Performance' in Windows Graphics Settings")
    
    # Set smooth rendering hints
    app.setStyle('Fusion')  # Use Fusion style for smoother, modern rendering
    
    logging.info(f"Physical DPI: {app.primaryScreen().physicalDotsPerInch()}")
    ui = LyricsDisplay(app)
    # we = WindowsWindowEffect(ui)
    # ptr = int(ui.winId())
    # we.setAeroEffect(ptr)  # Commented out - was causing black background instead of transparent
    trayIcon = SystemTrayIcon(QIcon(resource_path("resources/icon.ico")), parent=ui)
    trayIcon.show()
    sys.exit(app.exec())