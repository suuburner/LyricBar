import os
import sys
from pathlib import Path

import yaml

TAKSBAR_HEIGHT = 40
LEFTOUT_WIDTH = 500

GLOBAL_OFFSET = 0
LYRICS_TIMING_OFFSET = 0

LYRIC_FOLDER = "lyrics"
THEME_FOLDER = "themes"
DEFAULT_THEME = "Slate"
SHOW_PROGRESS_BAR = True
BORDER_ENABLED = True
SHOW_TIMESTAMPS = True

HTTP_PROXY = ""
HTTPS_PROXY = ""

USE_SPOTIFY_LYRICS = False
SP_DC = ""
THIRD_PARTY_LYRICS_PROVIDERS = ["Lrclib", "NetEase", "Musixmatch", "Deezer", "Megalobiz"]

STT_MODEL_PATH = ""
STT_TRACKING_INPUT = ""

PLAYING_INFO_PROVIDER = "Spicetify"
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
SPOTIPY_REDIRECT_URI = ""
TRACKING_APP = ["Spotify.exe"]
SPICETIFY_PORT = 8974


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return str(base_path / relative_path)


def _read_settings():
    settings_path = Path(resource_path("settings.yaml"))
    if not settings_path.exists():
        return {}

    with settings_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def _as_int(value, fallback):
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _apply_settings(config):
    global TAKSBAR_HEIGHT, LEFTOUT_WIDTH, GLOBAL_OFFSET, LYRICS_TIMING_OFFSET
    global LYRIC_FOLDER, THEME_FOLDER, DEFAULT_THEME, HTTP_PROXY, HTTPS_PROXY
    global USE_SPOTIFY_LYRICS, SP_DC, THIRD_PARTY_LYRICS_PROVIDERS
    global STT_MODEL_PATH, STT_TRACKING_INPUT, PLAYING_INFO_PROVIDER
    global SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
    global TRACKING_APP, SPICETIFY_PORT, SHOW_PROGRESS_BAR
    global BORDER_ENABLED, SHOW_TIMESTAMPS

    appearance = config.get("Apperance", {})
    LEFTOUT_WIDTH = _as_int(appearance.get("Leftout Width"), LEFTOUT_WIDTH)

    lyrics = config.get("Lyrics", {})
    LYRIC_FOLDER = lyrics.get("Folder", LYRIC_FOLDER)
    GLOBAL_OFFSET = _as_int(lyrics.get("Global Offset"), GLOBAL_OFFSET)
    LYRICS_TIMING_OFFSET = _as_int(lyrics.get("Timing Offset"), LYRICS_TIMING_OFFSET)

    providers = lyrics.get("Providers", {})
    spotify_settings = providers.get("Spotify") if isinstance(providers, dict) else None
    if spotify_settings:
        USE_SPOTIFY_LYRICS = True
        SP_DC = spotify_settings.get("DC", SP_DC)

    if isinstance(providers, dict):
        valid_providers = {"musixmatch", "lrclib", "deezer", "netease", "megalobiz"}
        THIRD_PARTY_LYRICS_PROVIDERS = [
            provider for provider in providers.keys() if provider.lower() in valid_providers
        ]

    stt = config.get("STT", {})
    STT_MODEL_PATH = stt.get("Model Path", STT_MODEL_PATH)
    STT_TRACKING_INPUT = stt.get("Tracking Input", STT_TRACKING_INPUT)

    playing_info = config.get("Playing Info", {})
    PLAYING_INFO_PROVIDER = playing_info.get("Provider", PLAYING_INFO_PROVIDER)
    if "Tracking App" in playing_info:
        tracking_app_config = playing_info["Tracking App"]
        TRACKING_APP = tracking_app_config if isinstance(tracking_app_config, list) else [tracking_app_config]
    SPICETIFY_PORT = _as_int(playing_info.get("Spicetify Port"), SPICETIFY_PORT)

    themes = config.get("Themes", {})
    THEME_FOLDER = themes.get("Folder", THEME_FOLDER)
    DEFAULT_THEME = themes.get("Default", DEFAULT_THEME)

    display = config.get("Display", {})
    if "Progress Bar" in display:
        SHOW_PROGRESS_BAR = bool(display.get("Progress Bar"))
    if "Border" in display:
        BORDER_ENABLED = bool(display.get("Border"))
    if "Timestamps" in display:
        SHOW_TIMESTAMPS = bool(display.get("Timestamps"))

    proxy = config.get("Proxy", {})
    host = proxy.get("Host")
    port = proxy.get("Port")
    if host and str(port).isdigit():
        HTTP_PROXY = f"{host}:{port}"
        HTTPS_PROXY = HTTP_PROXY


config = _read_settings()
_apply_settings(config)
THEME_FOLDER = resource_path(THEME_FOLDER)