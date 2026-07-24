"""Minimal settings dialog for LyricBar."""

import yaml

from PyQt5.QtCore import Qt, pyqtSignal
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
)

from LyricBar import themes
from LyricBar.globalvariables import resource_path


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None, settings_path="settings.yaml"):
        super().__init__(parent)
        self.settings_path = settings_path
        self.settings = {}
        self.load_settings()
        self.init_ui()

    def load_settings(self):
        try:
            with open(self.settings_path, "r", encoding="utf-8") as handle:
                self.settings = yaml.safe_load(handle) or {}
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to load settings: {exc}")
            self.settings = {}

    def init_ui(self):
        self.setWindowTitle("LyricBar Settings")
        self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))
        self.setMinimumWidth(420)
        self.setMaximumWidth(520)
        self.setObjectName("settingsDialog")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        title = QLabel("Settings")
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["System", "Spicetify"])
        self.provider_combo.setCurrentText(self.settings.get("Playing Info", {}).get("Provider", "System"))
        form.addRow("Provider", self.provider_combo)

        self.spicetify_port = QSpinBox()
        self.spicetify_port.setRange(1, 65535)
        self.spicetify_port.setValue(int(self.settings.get("Playing Info", {}).get("Spicetify Port", 8974)))
        form.addRow("Spicetify port", self.spicetify_port)

        self.timing_offset = QSpinBox()
        self.timing_offset.setRange(-5000, 5000)
        self.timing_offset.setSingleStep(50)
        self.timing_offset.setSuffix(" ms")
        self.timing_offset.setValue(int(self.settings.get("Lyrics", {}).get("Timing Offset", 300)))
        form.addRow("Timing offset", self.timing_offset)

        self.theme_combo = QComboBox()
        theme_names = [name for name in themes.MINIMAL_THEME_NAMES if name in themes.STYLES]
        self.theme_combo.addItems(theme_names)
        current_theme = self.settings.get("Themes", {}).get("Default")
        if current_theme in theme_names:
            self.theme_combo.setCurrentText(current_theme)
        elif theme_names:
            self.theme_combo.setCurrentIndex(0)
        form.addRow("Theme", self.theme_combo)

        self.progress_checkbox = QCheckBox("Show progress bar")
        self.progress_checkbox.setChecked(bool(self.settings.get("Display", {}).get("Progress Bar", True)))
        form.addRow("Progress", self.progress_checkbox)

        self.tracking_apps = QLineEdit()
        tracking_app = self.settings.get("Playing Info", {}).get("Tracking App", ["Spotify.exe"])
        if isinstance(tracking_app, list):
            tracking_text = ", ".join(tracking_app)
        else:
            tracking_text = str(tracking_app)
        self.tracking_apps.setText(tracking_text)
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

        hint = QLabel("Provider changes need a restart. Theme and timing apply immediately.")
        hint.setObjectName("hintText")
        hint.setWordWrap(True)
        root.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog#settingsDialog {
                background: #101014;
                color: #e8e8e8;
                font-family: "Segoe UI", "Arial";
                font-size: 10pt;
            }
            QLabel#sectionTitle {
                font-size: 13pt;
                font-weight: 600;
                color: #ffffff;
            }
            QLabel#hintText {
                color: #a0a0a0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #1a1a1f;
                border: 1px solid #2d2d36;
                border-radius: 6px;
                padding: 6px;
                color: #f0f0f0;
            }
            QComboBox QAbstractItemView {
                background: #16161b;
                color: #f0f0f0;
                selection-background-color: #3a3a46;
                selection-color: #ffffff;
                outline: 0;
            }
            QComboBox::drop-down {
                border: 0;
                width: 0;
            }
            QDialogButtonBox QPushButton {
                min-width: 84px;
                border-radius: 6px;
                padding: 6px 12px;
                background: #2a2a33;
                color: #f0f0f0;
                border: 1px solid #3a3a46;
            }
            QDialogButtonBox QPushButton:hover {
                background: #363642;
            }
            """
        )

    def detect_tracking_app(self):
        try:
            from LyricBar.nowplaying.nowplayingsystem import NowPlayingSystem
            import asyncio

            probe = NowPlayingSystem(sync_interval=1, update_callback=None, offset=0, tracking_app=[])
            if probe.manager is None:
                QMessageBox.information(self, "Detection unavailable", "No supported media session manager is available on this system.")
                return

            _, current_app_id, _ = asyncio.run(probe.get_best_session())
            if current_app_id:
                self.tracking_apps.setText(current_app_id)
                QMessageBox.information(self, "Detected app", f"Detected media app: {current_app_id}")
            else:
                QMessageBox.information(self, "No active app", "No currently playing media app was detected.")
        except Exception as exc:
            QMessageBox.warning(self, "Detection failed", f"Unable to detect the current audio app: {exc}")

    def save_settings(self):
        try:
            current_provider = self.settings.get("Playing Info", {}).get("Provider", "System")
            new_provider = self.provider_combo.currentText()
            current_offset = int(self.settings.get("Lyrics", {}).get("Timing Offset", 300))
            new_offset = self.timing_offset.value()
            current_theme = self.settings.get("Themes", {}).get("Default", "Default")
            new_theme = self.theme_combo.currentText()
            current_progress = bool(self.settings.get("Display", {}).get("Progress Bar", True))
            new_progress = self.progress_checkbox.isChecked()
            current_tracking = self.settings.get("Playing Info", {}).get("Tracking App", ["Spotify.exe"])
            if isinstance(current_tracking, str):
                current_tracking = [current_tracking]

            self.settings.setdefault("Playing Info", {})
            self.settings.setdefault("Lyrics", {})
            self.settings.setdefault("Themes", {})
            self.settings.setdefault("Display", {})

            self.settings["Playing Info"]["Provider"] = new_provider
            self.settings["Playing Info"]["Spicetify Port"] = self.spicetify_port.value()
            tracking_apps = [app.strip() for app in self.tracking_apps.text().split(",") if app.strip()]
            if tracking_apps:
                self.settings["Playing Info"]["Tracking App"] = tracking_apps
            self.settings["Lyrics"]["Timing Offset"] = new_offset
            self.settings["Themes"]["Default"] = new_theme
            self.settings["Display"]["Progress Bar"] = new_progress

            with open(self.settings_path, "w", encoding="utf-8") as handle:
                yaml.safe_dump(self.settings, handle, sort_keys=False, allow_unicode=True)

            changes = {
                "provider": new_provider,
                "provider_changed": new_provider != current_provider,
                "timing_offset": new_offset,
                "timing_offset_changed": new_offset != current_offset,
                "theme": new_theme,
                "theme_changed": new_theme != current_theme,
                "progress_bar": new_progress,
                "progress_bar_changed": new_progress != current_progress,
                "tracking_apps": tracking_apps,
                "tracking_apps_changed": tracking_apps != current_tracking,
            }
            self.settings_changed.emit(changes)
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {exc}")