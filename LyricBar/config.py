"""Compatibility layer for the legacy LyricBar.config import path.

Several modules in this workspace still import ``settings`` from
``LyricBar.config``. The runtime settings live in LyricBar.globalvariables,
so this module acts as a small adapter that preserves the old API while
writing back to settings.yaml through the existing global settings loader.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from LyricBar import globalvariables as _globalvariables


class SettingsProxy:
    """Proxy that exposes the legacy dot-access settings API."""

    _ATTRIBUTE_MAP = {
        "taskbar_height": "TAKSBAR_HEIGHT",
        "leftout_width": "LEFTOUT_WIDTH",
        "global_offset": "GLOBAL_OFFSET",
        "lyrics_timing_offset": "LYRICS_TIMING_OFFSET",
        "lyric_folder": "LYRIC_FOLDER",
        "theme_folder": "THEME_FOLDER",
        "default_theme": "DEFAULT_THEME",
        "show_progress_bar": "SHOW_PROGRESS_BAR",
        "use_spotify_lyrics": "USE_SPOTIFY_LYRICS",
        "sp_dc": "SP_DC",
        "third_party_lyrics_providers": "THIRD_PARTY_LYRICS_PROVIDERS",
        "playing_info_provider": "PLAYING_INFO_PROVIDER",
        "spicetify_port": "SPICETIFY_PORT",
        "tracking_app": "TRACKING_APP",
        "lyrics_folder": "LYRIC_FOLDER",
    }

    def __getattr__(self, name: str) -> Any:
        target_name = self._ATTRIBUTE_MAP.get(name)
        if target_name is not None:
            return getattr(_globalvariables, target_name)
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        target_name = self._ATTRIBUTE_MAP.get(name)
        if target_name is not None:
            setattr(_globalvariables, target_name, value)
            return

        object.__setattr__(self, name, value)

    def update_and_persist(self, updates: dict[str, Any]) -> dict[str, Any]:
        settings_path = Path(_globalvariables.resource_path("settings.yaml"))
        config: dict[str, Any] = {}
        if settings_path.exists():
            try:
                loaded = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
            except Exception:
                loaded = {}
            if isinstance(loaded, dict):
                config = loaded

        merged_config = _deep_merge(config, updates)
        settings_path.write_text(yaml.safe_dump(merged_config, sort_keys=False), encoding="utf-8")
        _globalvariables._apply_settings(merged_config)
        return merged_config


def _deep_merge(base: Any, updates: Any) -> Any:
    if isinstance(base, dict) and isinstance(updates, dict):
        result = copy.deepcopy(base)
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = _deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result
    return copy.deepcopy(updates)


settings = SettingsProxy()
resource_path = _globalvariables.resource_path
