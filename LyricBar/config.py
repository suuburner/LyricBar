from __future__ import annotations

import copy
import logging
import sys
from pathlib import Path
from typing import List, Optional
import yaml

logger = logging.getLogger(__name__)

VALID_THIRD_PARTY_PROVIDERS = {"lrclib", "netease", "musixmatch", "deezer", "megalobiz"}
DEFAULT_THIRD_PARTY_PROVIDERS = ["Lrclib", "NetEase", "Musixmatch", "Deezer", "Megalobiz"]


def resource_path(relative_path: str) -> str:
    """Resolve a path relative to the app root -- works both in dev and
    when frozen into a PyInstaller executable (which unpacks to sys._MEIPASS)."""
    base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return str(base_path / relative_path)


def _deep_merge(base, updates):
    if isinstance(base, dict) and isinstance(updates, dict):
        result = copy.deepcopy(base)
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = _deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result
    return copy.deepcopy(updates)


class AppSettings:
    def __init__(self) -> None:
        self.taskbar_height: int = 40
        self.leftout_width: int = 500

        self.lyric_folder: str = "lyrics"
        self.global_offset: int = 0
        self.lyrics_timing_offset: int = 0
        self.use_spotify_lyrics: bool = False
        self.sp_dc: str = ""
        self.third_party_lyrics_providers: List[str] = list(DEFAULT_THIRD_PARTY_PROVIDERS)

        self.stt_model_path: str = ""
        self.stt_tracking_input: str = ""

        self.playing_info_provider: str = "Spicetify"
        self.spotipy_client_id: str = ""
        self.spotipy_client_secret: str = ""
        self.spotipy_redirect_uri: str = ""
        self.tracking_app: List[str] = ["Spotify.exe"]
        self.spicetify_port: int = 8974

        self.theme_folder: str = "themes"
        self.default_theme: str = "Slate"
        self.show_progress_bar: bool = True
        self.border_enabled: bool = True
        self.show_timestamps: bool = True

        self.http_proxy: str = ""
        self.https_proxy: str = ""

        self._settings_path: Optional[Path] = None

    @classmethod
    def load(cls, settings_path: str = "settings.yaml") -> "AppSettings":
        instance = cls()
        instance._settings_path = Path(resource_path(settings_path))
        instance._apply(instance._read_raw())
        instance.theme_folder = resource_path(instance.theme_folder)
        return instance

    def reload(self) -> None:
        """Re-read settings.yaml and update this same instance in place."""
        raw = self._read_raw()
        theme_folder_relative = raw.get("Themes", {}).get("Folder", "themes")
        self._apply(raw)
        self.theme_folder = resource_path(theme_folder_relative)

    def _read_raw(self) -> dict:
        if self._settings_path is None or not self._settings_path.exists():
            return {}
        try:
            with self._settings_path.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        except (OSError, yaml.YAMLError) as exc:
            logger.warning("Could not read settings file %s: %s", self._settings_path, exc)
            return {}

    @staticmethod
    def _as_int(value, fallback):
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def _apply(self, config: dict) -> None:
        appearance = config.get("Apperance", {})
        self.leftout_width = self._as_int(appearance.get("Leftout Width"), self.leftout_width)
        self.taskbar_height = self._as_int(appearance.get("Taskbar Height"), self.taskbar_height)

        lyrics = config.get("Lyrics", {})
        self.lyric_folder = lyrics.get("Folder", self.lyric_folder)
        self.global_offset = self._as_int(lyrics.get("Global Offset"), self.global_offset)
        self.lyrics_timing_offset = self._as_int(lyrics.get("Timing Offset"), self.lyrics_timing_offset)

        self.sp_dc = lyrics.get("SP_DC", self.sp_dc)
        self.use_spotify_lyrics = bool(self.sp_dc)

        providers = lyrics.get("Providers")
        if isinstance(providers, list):
            self.third_party_lyrics_providers = [
                p for p in providers if str(p).lower() in VALID_THIRD_PARTY_PROVIDERS
            ]
        elif isinstance(providers, dict):
            # Back-compat with the older {"Musixmatch": {...}} style config.
            self.third_party_lyrics_providers = [
                p for p in providers.keys() if str(p).lower() in VALID_THIRD_PARTY_PROVIDERS
            ]

        stt = config.get("STT", {})
        self.stt_model_path = stt.get("Model Path", self.stt_model_path)
        self.stt_tracking_input = stt.get("Tracking Input", self.stt_tracking_input)

        playing_info = config.get("Playing Info", {})
        self.playing_info_provider = playing_info.get("Provider", self.playing_info_provider)
        if "Tracking App" in playing_info:
            tracking_app = playing_info["Tracking App"]
            self.tracking_app = tracking_app if isinstance(tracking_app, list) else [tracking_app]
        self.spicetify_port = self._as_int(playing_info.get("Spicetify Port"), self.spicetify_port)

        themes = config.get("Themes", {})
        self.theme_folder = themes.get("Folder", "themes")  # resolved to absolute path by caller
        self.default_theme = themes.get("Default", self.default_theme)

        display = config.get("Display", {})
        if "Progress Bar" in display:
            self.show_progress_bar = bool(display.get("Progress Bar"))
        if "Border" in display:
            self.border_enabled = bool(display.get("Border"))
        if "Timestamps" in display:
            self.show_timestamps = bool(display.get("Timestamps"))

        proxy = config.get("Proxy", {})
        host, port = proxy.get("Host"), proxy.get("Port")
        if host and str(port).isdigit():
            self.http_proxy = f"{host}:{port}"
            self.https_proxy = self.http_proxy


    def update_and_persist(self, changes: dict) -> None:
        raw = self._read_raw()
        merged = _deep_merge(raw, changes)
        if self._settings_path is not None:
            try:
                with self._settings_path.open("w", encoding="utf-8") as handle:
                    yaml.safe_dump(merged, handle, sort_keys=False, allow_unicode=True)
            except OSError as exc:
                logger.error("Could not write settings file %s: %s", self._settings_path, exc)
                raise
        theme_folder_relative = merged.get("Themes", {}).get("Folder", "themes")
        self._apply(merged)
        self.theme_folder = resource_path(theme_folder_relative)


# Shared singleton. Import this, not the class, from everywhere else in the app:
settings = AppSettings.load()
