"""Minimal settings dialog for LyricBar."""

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
from LyricBar.config import resource_path, settings


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        # NOTE: this used to open and parse settings.yaml itself, independently
        # of LyricBar.config.AppSettings -- two separate places understanding
        # the same file's schema, and they'd already drifted apart. Reading
        # from the shared `settings` singleton means there's exactly one
        # place that understands settings.yaml's shape.
        self.init_ui()

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
        self.provider_combo.setCurrentText(settings.playing_info_provider)
        form.addRow("Provider", self.provider_combo)

        self.spicetify_port = QSpinBox()
        self.spicetify_port.setRange(1, 65535)
        self.spicetify_port.setValue(int(settings.spicetify_port))
        form.addRow("Spicetify port", self.spicetify_port)

        self.timing_offset = QSpinBox()
        self.timing_offset.setRange(-5000, 5000)
        self.timing_offset.setSingleStep(50)
        self.timing_offset.setSuffix(" ms")
        self.timing_offset.setValue(int(settings.lyrics_timing_offset))
        form.addRow("Timing offset", self.timing_offset)

        self.theme_combo = QComboBox()
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
            current_offset = settings.lyrics_timing_offset
            new_offset = self.timing_offset.value()
            current_theme = settings.default_theme
            new_theme = self.theme_combo.currentText()
            current_progress = settings.show_progress_bar
            new_progress = self.progress_checkbox.isChecked()
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
                "Lyrics": {"Timing Offset": new_offset},
                "Themes": {"Default": new_theme},
                "Display": {"Progress Bar": new_progress},
            })

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