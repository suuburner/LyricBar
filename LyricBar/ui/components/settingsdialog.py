"""
Settings Dialog for LyricBar
Allows configuring providers and tracking apps from the UI
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QListWidget, QPushButton, QLineEdit,
    QMessageBox, QWidget, QSpinBox, QAbstractItemView, QListView
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPalette
import yaml
from LyricBar.globalvariables import resource_path


class SettingsDialog(QDialog):
    """Dialog for configuring LyricBar settings"""
    
    settings_changed = pyqtSignal(dict)  # Emits dict of changed settings
    
    def __init__(self, parent=None, settings_path="settings.yaml"):
        super().__init__(parent)
        self.settings_path = settings_path
        self.settings = {}
        self.load_settings()
        self.init_ui()
        
    def load_settings(self):
        """Load current settings from settings.yaml"""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                self.settings = yaml.safe_load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load settings: {e}")
            self.settings = {}
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("LyricBar Settings")
        self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))
        self.setMinimumWidth(620)
        self.setMinimumHeight(480)
        self.setObjectName("settingsDialog")
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(14, 12, 14, 12)

        provider_heading = QLabel("Playback Provider")
        provider_heading.setObjectName("sectionHeading")
        layout.addWidget(provider_heading)

        provider_label = QLabel("Source for now-playing information")
        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("providerCombo")
        self.provider_combo.addItems(["System", "Spicetify"])
        self.provider_combo.setMaxVisibleItems(8)
        provider_view = QListView(self)
        provider_view.setObjectName("comboPopup")
        provider_view.setAlternatingRowColors(False)
        self.provider_combo.setView(provider_view)

        current_provider = self.settings.get("Playing Info", {}).get("Provider", "System")
        self.provider_combo.setCurrentText(current_provider)
        layout.addWidget(provider_label)
        layout.addWidget(self.provider_combo)

        spicetify_layout = QHBoxLayout()
        spicetify_label = QLabel("Spicetify Port:")
        self.spicetify_port = QLineEdit()
        current_port = self.settings.get("Playing Info", {}).get("Spicetify Port", 8974)
        self.spicetify_port.setText(str(current_port))
        self.spicetify_port.setPlaceholderText("Default: 8974")
        self.spicetify_port.setMaximumWidth(120)
        spicetify_layout.addWidget(spicetify_label)
        spicetify_layout.addWidget(self.spicetify_port)
        spicetify_layout.addStretch()

        self.spicetify_widget = QWidget()
        self.spicetify_widget.setLayout(spicetify_layout)
        layout.addWidget(self.spicetify_widget)

        info_label = QLabel(
            "System = Windows media sessions | Spicetify = websocket extension"
        )
        info_label.setObjectName("hintText")
        layout.addWidget(info_label)

        timing_heading = QLabel("Lyrics Timing")
        timing_heading.setObjectName("sectionHeading")
        layout.addWidget(timing_heading)

        offset_layout = QHBoxLayout()
        offset_description = QLabel("Timing offset")
        self.timing_offset = QSpinBox()
        self.timing_offset.setRange(-5000, 5000)
        self.timing_offset.setSingleStep(50)
        self.timing_offset.setSuffix(" ms")
        self.timing_offset.setButtonSymbols(QSpinBox.NoButtons)
        self.timing_offset.setToolTip(
            "Positive values make lyrics appear earlier.\n"
            "Negative values make lyrics appear later.\n"
            "0 means exact file timing"
        )

        current_offset = self.settings.get("Lyrics", {}).get("Timing Offset", 200)
        self.timing_offset.setValue(current_offset)

        offset_layout.addWidget(offset_description)
        offset_layout.addWidget(self.timing_offset)
        offset_layout.addStretch()
        layout.addLayout(offset_layout)

        timing_info = QLabel(
            "Positive = earlier, Zero = exact, Negative = delayed"
        )
        timing_info.setObjectName("hintText")
        layout.addWidget(timing_info)

        provider_order_heading = QLabel("Lyrics Provider Order")
        provider_order_heading.setObjectName("sectionHeading")
        layout.addWidget(provider_order_heading)

        self.lyrics_provider_list = QListWidget()
        self.lyrics_provider_list.setObjectName("lyricsProviderList")
        self.lyrics_provider_list.setDragDropMode(QListWidget.InternalMove)
        self.lyrics_provider_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lyrics_provider_list.setAlternatingRowColors(True)
        self.lyrics_provider_list.setToolTip(
            "Drag and drop to reorder providers.\n"
            "Top provider will be tried first, if it fails, the next one will be used."
        )
        
        current_providers = self.settings.get("Lyrics", {}).get("Providers", ["Lrclib", "NetEase", "Musixmatch"])
        for provider in current_providers:
            self.lyrics_provider_list.addItem(provider)
        layout.addWidget(self.lyrics_provider_list)

        button_layout = QHBoxLayout()
        self.move_up_btn = QPushButton("Move Up")
        self.move_down_btn = QPushButton("Move Down")
        self.reset_order_btn = QPushButton("Reset to Default")
        
        self.move_up_btn.clicked.connect(self.move_provider_up)
        self.move_down_btn.clicked.connect(self.move_provider_down)
        self.reset_order_btn.clicked.connect(self.reset_provider_order)
        
        button_layout.addWidget(self.move_up_btn)
        button_layout.addWidget(self.move_down_btn)
        button_layout.addWidget(self.reset_order_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        provider_info = QLabel(
            "• Lrclib: Best coverage for most songs\n"
            "• NetEase: Great for Asian music and popular tracks\n"
            "• Musixmatch: Large database, very reliable"
        )
        provider_info.setObjectName("hintText")
        layout.addWidget(provider_info)

        tracking_heading = QLabel("Tracking Apps")
        tracking_heading.setObjectName("sectionHeading")
        layout.addWidget(tracking_heading)

        self.tracking_group = QWidget()
        tracking_layout = QVBoxLayout()

        tracking_label = QLabel("Apps to track when provider is System")
        tracking_layout.addWidget(tracking_label)

        self.tracking_list = QListWidget()
        self.tracking_list.setObjectName("trackingAppList")
        self.tracking_list.setAlternatingRowColors(True)
        self.tracking_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.populate_tracking_apps()
        tracking_layout.addWidget(self.tracking_list)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add App")
        self.remove_button = QPushButton("Remove Selected")
        self.detect_button = QPushButton("Auto-Detect Playing Apps")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.detect_button)
        tracking_layout.addLayout(button_layout)

        instructions = QLabel(
            "Use Auto-Detect while music is playing, then remove generic host apps if needed"
        )
        instructions.setObjectName("hintText")
        instructions.setWordWrap(True)
        tracking_layout.addWidget(instructions)

        self.tracking_group.setLayout(tracking_layout)
        layout.addWidget(self.tracking_group)
        
        # Update visibility based on provider
        self.update_tracking_visibility()
        self.provider_combo.currentTextChanged.connect(self.update_tracking_visibility)
        
        # Save/Cancel buttons
        button_box = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.setDefault(True)
        save_button.setAutoDefault(True)
        save_button.setObjectName("primaryButton")
        
        save_button.clicked.connect(self.save_settings)
        cancel_button.clicked.connect(self.reject)
        
        button_box.addStretch()
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        
        layout.addLayout(button_box)
        
        self.setLayout(layout)
        
        # Connect buttons
        self.add_button.clicked.connect(self.add_tracking_app)
        self.remove_button.clicked.connect(self.remove_tracking_app)
        self.detect_button.clicked.connect(self.auto_detect_apps)

        self._apply_list_palette(self.lyrics_provider_list)
        self._apply_list_palette(self.tracking_list)
        self._apply_list_palette(provider_view)

        self.setStyleSheet(
            """
            QDialog#settingsDialog {
                background-color: #11111b;
                color: #cdd6f4;
                font-family: "Segoe UI Variable Text", "Segoe UI", "Inter", "Roboto";
                font-size: 10pt;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLabel#sectionHeading {
                color: #f5e0dc;
                font-size: 11.5pt;
                font-weight: 600;
                margin-top: 8px;
            }
            QLabel#hintText {
                color: #a6adc8;
                font-size: 9pt;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 7px;
                padding: 6px;
                color: #cdd6f4;
            }
            QComboBox#providerCombo {
                min-height: 30px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 0px;
                border: 0px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
            }
            QListWidget {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 7px;
                padding: 4px;
                color: #cdd6f4;
                outline: none;
            }
            QComboBox QAbstractItemView, QListWidget, QListView#comboPopup {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #313244;
                outline: 0;
                border-radius: 0px;
                padding: 1px;
            }
            QComboBox QAbstractItemView::item, QListView#comboPopup::item {
                background: #1e1e2e;
                color: #cdd6f4;
                border: 0;
                padding: 6px 8px;
                margin: 0;
            }
            QListWidget::item:selected, QComboBox QAbstractItemView::item:selected {
                background-color: #313244;
                color: #cdd6f4;
            }
            QListWidget::item:selected:active, QComboBox QAbstractItemView::item:selected:active {
                background-color: #89b4fa;
                color: #11111b;
            }
            QListWidget::item:selected:!active, QComboBox QAbstractItemView::item:selected:!active {
                background-color: #74c7ec;
                color: #11111b;
            }
            QComboBox QAbstractItemView::item:hover, QListView#comboPopup::item:hover {
                background: #313244;
                color: #cdd6f4;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 5px;
                background: transparent;
            }
            QListWidget::item:alternate {
                background: rgba(255, 255, 255, 0.01);
            }
            QListWidget::item:hover {
                background: rgba(137, 180, 250, 0.2);
            }
            QPushButton {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 7px;
                padding: 5px 12px;
                color: #cdd6f4;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:pressed {
                background-color: #313244;
            }
            QPushButton#primaryButton {
                background-color: #f5c2e7;
                border: 1px solid #f5c2e7;
                color: #1e1e2e;
                font-weight: 700;
            }
            QPushButton#primaryButton:hover {
                background-color: #f9d4ef;
            }
            QScrollBar:vertical {
                background: #181825;
                width: 10px;
                margin: 2px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #585b70;
                min-height: 28px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6c7086;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
                border: none;
                height: 0px;
            }
            QScrollBar:horizontal {
                background: #181825;
                height: 10px;
                margin: 2px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #585b70;
                min-width: 28px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #6c7086;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal,
            QScrollBar::left-arrow:horizontal,
            QScrollBar::right-arrow:horizontal,
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: none;
                border: none;
                width: 0px;
            }
            QToolTip {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #313244;
                padding: 6px;
            }
            """
        )

    def _apply_list_palette(self, widget):
        palette = widget.palette()
        palette.setColor(QPalette.Base, QColor("#1e1e2e"))
        palette.setColor(QPalette.AlternateBase, QColor("#181825"))
        palette.setColor(QPalette.Text, QColor("#cdd6f4"))
        palette.setColor(QPalette.Window, QColor("#1e1e2e"))
        palette.setColor(QPalette.Highlight, QColor("#89b4fa"))
        palette.setColor(QPalette.HighlightedText, QColor("#11111b"))
        palette.setColor(QPalette.Active, QPalette.Highlight, QColor("#89b4fa"))
        palette.setColor(QPalette.Inactive, QPalette.Highlight, QColor("#74c7ec"))
        palette.setColor(QPalette.Active, QPalette.HighlightedText, QColor("#11111b"))
        palette.setColor(QPalette.Inactive, QPalette.HighlightedText, QColor("#11111b"))
        widget.setPalette(palette)
    
    def update_tracking_visibility(self):
        """Show/hide tracking apps section and spicetify port based on provider"""
        provider = self.provider_combo.currentText()
        is_system = provider == "System"
        is_spicetify = provider == "Spicetify"
        
        self.tracking_group.setVisible(is_system)
        self.spicetify_widget.setVisible(is_spicetify)
    
    def populate_tracking_apps(self):
        """Populate the tracking apps list"""
        self.tracking_list.clear()
        tracking_app = self.settings.get("Playing Info", {}).get("Tracking App", [])
        
        # Handle both string and list format
        if isinstance(tracking_app, str):
            tracking_app = [tracking_app]
        elif not isinstance(tracking_app, list):
            tracking_app = []
        
        for app in tracking_app:
            self.tracking_list.addItem(app)
    
    def move_provider_up(self):
        """Move selected provider up in the priority list"""
        current_row = self.lyrics_provider_list.currentRow()
        if current_row > 0:
            item = self.lyrics_provider_list.takeItem(current_row)
            self.lyrics_provider_list.insertItem(current_row - 1, item)
            self.lyrics_provider_list.setCurrentRow(current_row - 1)
    
    def move_provider_down(self):
        """Move selected provider down in the priority list"""
        current_row = self.lyrics_provider_list.currentRow()
        if current_row < self.lyrics_provider_list.count() - 1 and current_row >= 0:
            item = self.lyrics_provider_list.takeItem(current_row)
            self.lyrics_provider_list.insertItem(current_row + 1, item)
            self.lyrics_provider_list.setCurrentRow(current_row + 1)
    
    def reset_provider_order(self):
        """Reset provider order to default (Lrclib, NetEase, Musixmatch)"""
        self.lyrics_provider_list.clear()
        default_providers = ["Lrclib", "NetEase", "Musixmatch"]
        for provider in default_providers:
            self.lyrics_provider_list.addItem(provider)
    
    def add_tracking_app(self):
        """Add a new tracking app manually"""
        from PyQt5.QtWidgets import QInputDialog
        
        app_id, ok = QInputDialog.getText(
            self, 
            "Add Tracking App",
            "Enter the app ID (e.g., Spotify.exe or com.github.th-ch.youtube-music):"
        )
        
        if ok and app_id.strip():
            # Check if already exists
            items = [self.tracking_list.item(i).text() for i in range(self.tracking_list.count())]
            if app_id.strip() not in items:
                self.tracking_list.addItem(app_id.strip())
            else:
                QMessageBox.information(self, "Info", "This app is already in the list.")
    
    def remove_tracking_app(self):
        """Remove selected tracking app"""
        current_item = self.tracking_list.currentItem()
        if current_item:
            self.tracking_list.takeItem(self.tracking_list.row(current_item))
        else:
            QMessageBox.information(self, "Info", "Please select an app to remove.")
    
    def auto_detect_apps(self):
        """Auto-detect currently playing media apps"""
        try:
            import asyncio
            from winrt.windows.media.control import \
                GlobalSystemMediaTransportControlsSessionManager as MediaManager
            
            async def get_apps():
                manager = await MediaManager.request_async()
                sessions = manager.get_sessions()
                return [session.source_app_user_model_id for session in sessions]
            
            # Run async detection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            app_ids = loop.run_until_complete(get_apps())
            loop.close()
            
            if not app_ids:
                QMessageBox.information(
                    self, 
                    "No Apps Found", 
                    "No media apps are currently playing.\n\nStart playing music in an app and try again."
                )
                return
            
            # Get existing apps
            existing_apps = [self.tracking_list.item(i).text() for i in range(self.tracking_list.count())]
            
            # Add new apps
            added_count = 0
            for app_id in app_ids:
                if app_id not in existing_apps:
                    self.tracking_list.addItem(app_id)
                    added_count += 1
            
            if added_count > 0:
                QMessageBox.information(
                    self,
                    "Apps Detected",
                    f"Added {added_count} new app(s):\n\n" + "\n".join(app_ids)
                )
            else:
                QMessageBox.information(
                    self,
                    "No New Apps",
                    "All detected apps are already in your tracking list."
                )
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Detection Failed",
                f"Failed to detect apps: {e}\n\nMake sure music is playing in an app."
            )
    
    def save_settings(self):
        """Save settings to settings.yaml and emit signal"""
        try:
            # Update provider
            if "Playing Info" not in self.settings:
                self.settings["Playing Info"] = {}
            
            new_provider = self.provider_combo.currentText()
            old_provider = self.settings.get("Playing Info", {}).get("Provider", "System")
            
            self.settings["Playing Info"]["Provider"] = new_provider
            
            # Update Spicetify port
            if new_provider == "Spicetify":
                try:
                    port = int(self.spicetify_port.text())
                    self.settings["Playing Info"]["Spicetify Port"] = port
                except ValueError:
                    # Use default port if invalid
                    self.settings["Playing Info"]["Spicetify Port"] = 8974
            
            # Update lyrics timing offset
            if "Lyrics" not in self.settings:
                self.settings["Lyrics"] = {}
            
            old_offset = self.settings.get("Lyrics", {}).get("Timing Offset", 200)
            new_offset = self.timing_offset.value()
            self.settings["Lyrics"]["Timing Offset"] = new_offset
            
            # Update lyrics provider order from the list widget
            new_providers = []
            for i in range(self.lyrics_provider_list.count()):
                new_providers.append(self.lyrics_provider_list.item(i).text())
            
            old_providers = self.settings.get("Lyrics", {}).get("Providers", ["Lrclib", "NetEase", "Musixmatch"])
            self.settings["Lyrics"]["Providers"] = new_providers
            provider_changed = (old_providers != new_providers) if old_providers else True
            
            # Update tracking apps
            tracking_apps = [
                self.tracking_list.item(i).text() 
                for i in range(self.tracking_list.count())
            ]
            
            if tracking_apps:
                self.settings["Playing Info"]["Tracking App"] = tracking_apps
            
            # Write to file
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.settings, f, default_flow_style=False, allow_unicode=True)
            
            # Emit signal with changes
            primary_provider = new_providers[0] if new_providers else "Unknown"
            changes = {
                'provider': new_provider,
                'provider_changed': new_provider != old_provider,
                'tracking_apps': tracking_apps,
                'timing_offset': new_offset,
                'timing_offset_changed': new_offset != old_offset,
                'lyrics_provider': primary_provider,
                'lyrics_provider_changed': provider_changed,
                'lyrics_providers_order': new_providers
            }
            self.settings_changed.emit(changes)
            
            # Show appropriate message
            if changes['provider_changed']:
                QMessageBox.information(
                    self,
                    "Restart Required",
                    f"Provider changed from '{old_provider}' to '{new_provider}'.\n\n"
                    "Please restart LyricBar for changes to take effect."
                )
            elif changes['lyrics_provider_changed']:
                QMessageBox.information(
                    self,
                    "Setting Updated",
                    f"Lyrics provider order updated. Primary provider: '{primary_provider}'.\n\n"
                    "The change will take effect for new lyrics fetches."
                )
            elif changes['timing_offset_changed']:
                QMessageBox.information(
                    self,
                    "Setting Updated",
                    f"Lyrics timing offset changed to {new_offset}ms.\n\n"
                    "The change will take effect immediately."
                )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
