"""Minimal settings dialog for LyricBar."""

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QCheckBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QListView,
)

from LyricBar import themes
from LyricBar.config import resource_path, settings


class SettingsComboBox(QComboBox):
    def showPopup(self):
        super().showPopup()
        QTimer.singleShot(0, self._raise_popup)

    def _raise_popup(self):
        popup = self.view().window()
        if popup is None:
            return
        popup.setStyleSheet(
            """
            QFrame {
                background: #17171d;
                border: 1px solid #343442;
                border-radius: 8px;
            }
            QListView {
                background: #17171d;
                color: #f8f8fa;
                border: none;
                outline: 0;
                selection-background-color: #4a4a5c;
                selection-color: #ffffff;
            }
            QListView::item {
                min-height: 26px;
                padding: 4px 10px;
            }
            QListView::item:selected {
                background: #4a4a5c;
                color: #ffffff;
            }
            """
        )
        popup.setAutoFillBackground(True)
        popup.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        popup.setWindowFlag(Qt.WindowType.ToolTip, True)
        popup.raise_()
        popup.activateWindow()


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        # NOTE: this used to open and parse settings.yaml itself, independently
        # of LyricBar.config.AppSettings -- two separate places understanding
        # the same file's schema, and they'd already drifted apart. Reading
        # from the shared `settings` singleton means there's exactly one
        # place that understands settings.yaml's shape.
        self._fixed_dialog_size = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("LyricBar Settings")
        self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setObjectName("settingsDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        self.setFontFamilyStack()

        title = QLabel("Settings")
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)

        self.provider_combo = SettingsComboBox()
        self._style_combo_box(self.provider_combo)
        self.provider_combo.addItems(["System", "Spicetify"])
        self.provider_combo.setCurrentText(settings.playing_info_provider)
        form.addRow("Provider", self.provider_combo)

        self.spicetify_port = QSpinBox()
        self.spicetify_port.setRange(1, 65535)
        self.spicetify_port.setValue(int(settings.spicetify_port))
        form.addRow("Spicetify port", self.spicetify_port)

        self.global_offset = QSpinBox()
        self.global_offset.setRange(-5000, 5000)
        self.global_offset.setSingleStep(50)
        self.global_offset.setSuffix(" ms")
        self.global_offset.setValue(int(settings.global_offset))
        form.addRow("Global offset", self.global_offset)

        self.theme_combo = SettingsComboBox()
        self._style_combo_box(self.theme_combo)
        theme_names = [name for name in themes.MINIMAL_THEME_NAMES if name in themes.STYLES]
        self.theme_combo.addItems(theme_names)
        if settings.default_theme in theme_names:
            self.theme_combo.setCurrentText(settings.default_theme)
        elif theme_names:
            self.theme_combo.setCurrentIndex(0)
        form.addRow("Theme", self.theme_combo)

        self.progress_checkbox = QCheckBox("Show progress ring")
        self.progress_checkbox.setChecked(bool(settings.show_progress_bar))
        form.addRow("Progress ring", self.progress_checkbox)

        self.border_checkbox = QCheckBox("Show bar border")
        self.border_checkbox.setChecked(bool(settings.border_enabled))
        form.addRow("Border", self.border_checkbox)

        self.timestamps_checkbox = QCheckBox("Show timestamps")
        self.timestamps_checkbox.setChecked(bool(settings.show_timestamps))
        form.addRow("Timestamps", self.timestamps_checkbox)

        # The ring is drawn traced over the bar's own border -- with no
        # border, there's nothing underneath for the "unfilled" portion of
        # the ring to show against, so the two are kept in sync both ways:
        # turning the ring on with the border off turns the border on too,
        # and turning the border off with the ring on turns the ring off too.
        self.progress_checkbox.toggled.connect(self._on_progress_toggled)
        self.border_checkbox.toggled.connect(self._on_border_toggled)

        self.tracking_apps = QLineEdit()
        tracking_app = settings.tracking_app
        self.tracking_apps.setText(", ".join(tracking_app) if isinstance(tracking_app, list) else str(tracking_app))
        self.tracking_apps.setPlaceholderText("Spotify.exe, other-app.exe")

        tracking_row = QWidget(self)
        tracking_layout = QHBoxLayout(tracking_row)
        tracking_layout.setContentsMargins(0, 0, 0, 0)
        tracking_layout.setSpacing(6)
        tracking_layout.addWidget(self.tracking_apps)
        self.detect_button = QPushButton("Detect")
        self.detect_button.clicked.connect(self.detect_tracking_app)
        tracking_layout.addWidget(self.detect_button)
        form.addRow("Tracking apps", tracking_row)

        root.addLayout(form)

        hint = QLabel("Provider changes need a restart. Theme and offsets apply immediately.")
        hint.setObjectName("hintText")
        hint.setWordWrap(True)
        root.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.setSizeGripEnabled(False)

        self.setStyleSheet(
            """
            QDialog#settingsDialog {
                background: #101014;
                color: #e8e8e8;
                font-family: "JetBrains Mono", "Segoe UI", "Consolas", monospace;
                font-size: 10.5pt;
            }
            QLabel#sectionTitle {
                font-size: 14pt;
                font-weight: 700;
                color: #f7f7f7;
                padding-bottom: 2px;
            }
            QLabel#hintText {
                color: #b6b6bf;
                padding-top: 2px;
            }
            QFormLayout QLabel {
                color: #f0f0f5;
                padding-right: 4px;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #17171d;
                border: 1px solid #2f2f39;
                border-radius: 8px;
                padding: 8px 10px;
                color: #f5f5f7;
                selection-background-color: #4a4a5c;
                selection-color: #ffffff;
            }
            QComboBox QAbstractItemView {
                background: #17171d;
                color: #f8f8fa;
                border: 1px solid #343442;
                border-radius: 8px;
                padding: 4px;
                outline: 0;
                selection-background-color: #4a4a5c;
                selection-color: #ffffff;
            }
            QComboBox QAbstractItemView::item {
                min-height: 26px;
                padding: 4px 10px;
            }
            QComboBox::drop-down {
                border: 0;
                width: 18px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
            }
            QDialogButtonBox QPushButton {
                min-width: 88px;
                border-radius: 8px;
                padding: 7px 14px;
                background: #24242d;
                color: #f4f4f6;
                border: 1px solid #353545;
            }
            QDialogButtonBox QPushButton:hover {
                background: #30303b;
            }
            """
        )

        # Lock the dialog to the final layout size so it cannot be resized.
        self.adjustSize()
        self._fixed_dialog_size = self.sizeHint()
        self.setMinimumSize(self._fixed_dialog_size)
        self.setMaximumSize(self._fixed_dialog_size)
        self.resize(self._fixed_dialog_size)

    def setFontFamilyStack(self):
        from PyQt5.QtGui import QFont, QFontDatabase

        font_candidates = ["JetBrains Mono", "Segoe UI", "Consolas", "Arial"]
        available_fonts = set(QFontDatabase().families())
        family = next((name for name in font_candidates if name in available_fonts), "Segoe UI")
        font = QFont(family)
        font.setPointSizeF(10.5)
        self.setFont(font)

    def _style_combo_box(self, combo_box):
        combo_box.setView(QListView(combo_box))
        combo_box.view().setUniformItemSizes(True)
        combo_box.setMaxVisibleItems(10)
        combo_box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo_box.setMinimumWidth(180)
        combo_box.view().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        combo_box.view().viewport().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        combo_box.view().setStyleSheet(
            """
            QListView {
                background: #17171d;
                color: #f8f8fa;
                border: none;
                outline: 0;
            }
            QListView::viewport {
                background: #17171d;
                border: none;
            }
            QListView::item {
                min-height: 26px;
                padding: 4px 10px;
            }
            QListView::item:selected {
                background: #4a4a5c;
                color: #ffffff;
            }
            """
        )

    def resizeEvent(self, event):
        if self._fixed_dialog_size is not None and event.size() != self._fixed_dialog_size:
            self.setMinimumSize(self._fixed_dialog_size)
            self.setMaximumSize(self._fixed_dialog_size)
            if self.size() != self._fixed_dialog_size:
                self.resize(self._fixed_dialog_size)
        super().resizeEvent(event)

    def _on_progress_toggled(self, checked):
        if checked and not self.border_checkbox.isChecked():
            self.border_checkbox.setChecked(True)

    def _on_border_toggled(self, checked):
        if not checked and self.progress_checkbox.isChecked():
            self.progress_checkbox.setChecked(False)

    def detect_tracking_app(self):
        try:
            from LyricBar.nowplaying.nowplayingsystem import NowPlayingSystem
            import asyncio

            probe = NowPlayingSystem(sync_interval=1, update_callback=None, offset=0, tracking_app=[])
            if probe.manager is None:
                QMessageBox.information(self, "Detection unavailable", "No supported media session manager is available on this system.")
                return

            # NOTE: this used to call probe.get_best_session(), which only
            # matches sessions against the *already configured* tracking-app
            # list -- with tracking_app=[] that match loop has nothing to
            # iterate, so it always returned nothing, no matter what was
            # actually playing. list_available_sessions() lists every live
            # session with no filtering, same idea as the standalone
            # get_app_ids.py diagnostic script.
            sessions = asyncio.run(probe.list_available_sessions())

            if not sessions:
                QMessageBox.information(
                    self,
                    "No active app",
                    "No media sessions were found. Start playing something and try again.",
                )
                return

            # Prefer a session that's actually playing; among those (or if
            # none are playing) prefer one with track info attached.
            def rank(s):
                return (s["is_playing"], bool(s["title"]))

            best = max(sessions, key=rank)

            # Append to whatever is already in the field instead of
            # overwriting it -- this used to call setText(best["app_id"])
            # directly, which wiped out any apps already listed there.
            existing = [app.strip() for app in self.tracking_apps.text().split(",") if app.strip()]
            if best["app_id"] not in existing:
                existing.append(best["app_id"])
            self.tracking_apps.setText(", ".join(existing))

            lines = []
            for s in sessions:
                marker = "▶" if s["is_playing"] else " "
                track = f"{s['artist']} - {s['title']}" if s["title"] else "no track info"
                lines.append(f"{marker} {s['app_id']}  ({track})")
            QMessageBox.information(
                self,
                "Detected apps",
                "Added: " + best["app_id"] + "\n\nAll sessions found:\n" + "\n".join(lines),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Detection failed", f"Unable to detect the current audio app: {exc}")

    def save_settings(self):
        try:
            current_provider = settings.playing_info_provider
            new_provider = self.provider_combo.currentText()
            current_offset = settings.global_offset
            new_offset = self.global_offset.value()
            current_theme = settings.default_theme
            new_theme = self.theme_combo.currentText()
            current_progress = settings.show_progress_bar
            new_progress = self.progress_checkbox.isChecked()
            current_border = settings.border_enabled
            new_border = self.border_checkbox.isChecked()
            current_timestamps = settings.show_timestamps
            new_timestamps = self.timestamps_checkbox.isChecked()
            current_tracking = settings.tracking_app

            tracking_apps = [app.strip() for app in self.tracking_apps.text().split(",") if app.strip()]
            if not tracking_apps:
                tracking_apps = current_tracking

            # Single write path: persist to disk AND update the shared
            # `settings` object in place, so every module holding a reference
            # to it sees the new values immediately.
            settings.update_and_persist({
                "Playing Info": {
                    "Provider": new_provider,
                    "Spicetify Port": self.spicetify_port.value(),
                    "Tracking App": tracking_apps,
                },
                "Lyrics": {
                    "Global Offset": new_offset,
                    "Timing Offset": new_offset,
                },
                "Themes": {"Default": new_theme},
                "Display": {
                    "Progress Bar": new_progress,
                    "Border": new_border,
                    "Timestamps": new_timestamps,
                },
            })

            changes = {
                "provider": new_provider,
                "provider_changed": new_provider != current_provider,
                "global_offset": new_offset,
                "timing_offset_changed": new_offset != current_offset,
                "global_offset_changed": new_offset != current_offset,
                "theme": new_theme,
                "theme_changed": new_theme != current_theme,
                "progress_bar": new_progress,
                "progress_bar_changed": new_progress != current_progress,
                "border": new_border,
                "border_changed": new_border != current_border,
                "timestamps": new_timestamps,
                "timestamps_changed": new_timestamps != current_timestamps,
                "tracking_apps": tracking_apps,
                "tracking_apps_changed": tracking_apps != current_tracking,
            }
            self.settings_changed.emit(changes)
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {exc}")
