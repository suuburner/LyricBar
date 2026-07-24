import importlib.util
import os
from pathlib import Path

import regex as re

from LyricBar import globalvariables
from LyricBar.utils.dataclasses import TrackInfo
from LyricBar.utils.tools import hex_to_rgba

STYLES = {}
_theme_cache = {}
_cache_max_size = 50
MINIMAL_FONT_FAMILY = "JetBrains Mono, Segoe UI, Arial, sans-serif"
MINIMAL_FONT_SIZE = 18
MINIMAL_BACKGROUND = "#00000088"
MINIMAL_FONT_COLOR = "#d8d8d8"
MINIMAL_LINE_COLOR = "#5a5a5a"
MINIMAL_PROGRESS_COLOR = "#a8a8a8"
MINIMAL_PROGRESS_LINE_COLOR = "#444444"
MINIMAL_THEME_NAMES = ["Soft", "Catppuccin Mocha", "Everforest", "Gruvbox"]


def replace_all(line, matches, replacement, word_pass=None, cap_first=True):
    line = line.strip()
    if matches is None:
        return line

    characters = list(line)
    for match in matches:
        segment = "".join(characters[match.start() : match.end()])
        if word_pass is not None and any(token in segment for token in word_pass):
            continue

        characters[match.start()] = replacement
        if cap_first:
            if match.start() == 0:
                characters[0] = characters[0][:1].upper() + characters[0][1:]
            else:
                index = match.start() - 1
                while index >= 0 and characters[index] == " ":
                    index -= 1
                if index >= 0 and characters[index] in ".!?":
                    characters[match.start()] = characters[match.start()][:1].upper() + characters[match.start()][1:]

        for index in range(match.start() + 1, match.end()):
            characters[index] = ""

    return "".join(characters)


def uncensor(line):
    uncensor_rules = {
        "fuck": (
            r"(\*\*\*\*(?=( it|ing|er|'s sake| sake|'em | 'em| em| him| her| them)))|((?<=(mother))\*\*\*\*)|((?<=(as ))\*\*\*\*)|((?<= )[Ff][^a-tw-yzA-TW-YZ]?[^abd-yzABD-YZ]?[^a-jl-yzA-JL-YZ]?(?=([ !?'\"]|ed |ing |er |in |in' |ers|ed-up |\.[^a-zA-Z])))",
            ("f", "F"),
        ),
        "shit": (
            r"((?<=(as ))\*\*\*\*)|((?<=(little ))\*\*\*\*)|((?<= )[Ss][^a-gi-yzA-GI-YZ]?[^a-hj-yzA-HJ-YZ]?[^a-su-yzA-SU-YZ]?(?=([ !?'\"]|\.[^a-zA-Z])))",
            ("sit", "si", "st", "s", "S"),
        ),
        "bitch": (
            r"(\*\*\*\*\*(?=(es| ass|-ass|ass| gon)))|((?<= )[Bb][^a-hj-yzA-HJ-YZ]?[^a-su-yzA-SU-YZ]?[^abd-yzABD-YZ]?[^a-gi-yzA-GI-YZ]?(?=([ !?'\"]|es |\.[^a-zA-Z])))",
            ("bit", "b", "B"),
        ),
    }

    for word, (pattern, passes) in uncensor_rules.items():
        line = replace_all(line, re.finditer(pattern, line), word, passes)
    return line


def default_formatter(line):
    if any(
        line.strip().startswith(prefix)
        for prefix in ["作词", "编曲", "制作", "作曲", "混音", "人声", "母带", "监制", "词", "曲", "录", "附加制作", "鼓", "贝斯", "吉他", "音频"]
    ):
        line = ""
    line = uncensor(line)
    return "♬" if line == "" else line


def _load_theme_module(theme_root: Path, theme_path: Path):
    relative_name = theme_path.relative_to(theme_root).with_suffix("").as_posix().replace("/", "_")
    module_name = f"lyricbar_theme_{relative_name}"
    spec = importlib.util.spec_from_file_location(module_name, theme_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load theme module: {theme_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _compose_format(base_format, theme_format):
    return lambda line: theme_format(base_format(line))


def _normalize_font_family(font_family):
    if any(extension in font_family.lower() for extension in (".ttf", ".otf")) and os.path.exists(font_family):
        return font_family

    fonts = [part.strip() for part in font_family.split(",")]
    defaults = [part.strip() for part in STYLES["default"]["font-family"].split(",")]
    return ", ".join(font for font in fonts + defaults if font)


def _parse_font_size(value, fallback=MINIMAL_FONT_SIZE):
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip().rstrip("px")
        try:
            return int(float(cleaned))
        except ValueError:
            return fallback
    return fallback


def _normalize_minimal_style(style):
    normalized = dict(style)

    normalized["font-family"] = MINIMAL_FONT_FAMILY
    normalized["font-size"] = "18px"
    normalized["font-weight"] = "bold"
    normalized["font-italic"] = False
    normalized["use-shadow"] = False
    normalized["shadow-radius"] = 0
    normalized["shadow-offset"] = [0, 0]
    normalized["shadow-color"] = "#00000000"
    normalized["background-color"] = normalized.get("background-color", MINIMAL_BACKGROUND)
    normalized["font-color"] = normalized.get("font-color", MINIMAL_FONT_COLOR)
    normalized["line-color"] = normalized.get("line-color", MINIMAL_LINE_COLOR)
    normalized["progress-color"] = normalized.get("progress-color", MINIMAL_PROGRESS_COLOR)
    normalized["progress-line-color"] = normalized.get("progress-line-color", MINIMAL_PROGRESS_LINE_COLOR)

    line_width = normalized.get("line-width", 0)
    if isinstance(line_width, (int, float)):
        normalized["line-width"] = min(float(line_width), 0.5)
    else:
        normalized["line-width"] = 0.25

    normalized["entering"] = None
    normalized["sustaining"] = None
    normalized["leaving"] = None
    return normalized


def load_themes():
    STYLES.clear()
    STYLES.update(
        {
            "default": {
                "background-color": MINIMAL_BACKGROUND,
                "font-color": MINIMAL_FONT_COLOR,
                "font-family": MINIMAL_FONT_FAMILY,
                "font-size": "18px",
                "font-weight": "bold",
                "font-italic": False,
                "line-color": MINIMAL_LINE_COLOR,
                "line-width": 0.25,
                "use-shadow": False,
                "shadow-color": "#00000000",
                "shadow-offset": [0, 0],
                "shadow-radius": 0,
                "flip-text": False,
                "format": default_formatter,
                "entering": None,
                "sustaining": None,
                "leaving": None,
                "progress-color": MINIMAL_PROGRESS_COLOR,
                "progress-line-color": MINIMAL_PROGRESS_LINE_COLOR,
            }
        }
    )

    theme_root = Path(globalvariables.THEME_FOLDER)
    if not theme_root.exists():
        print("Loaded 0 themes.")
        return

    loaded_count = 0
    for theme_path in sorted(theme_root.rglob("*.py")):
        module = _load_theme_module(theme_root, theme_path)
        styles = dict(module.STYLES)
        if theme_path.name != "Default.py":
            prefix = theme_path.relative_to(theme_root).with_suffix("").as_posix()
            styles = {f"{prefix} - {name}": style for name, style in styles.items()}
        STYLES.update(styles)
        loaded_count += 1

    print(f"Loaded {loaded_count} themes.")


def get_style(track: TrackInfo):
    cache_key = None
    if track is not None:
        album = getattr(track, "album", None) or "Unknown"
        cache_key = (
            track.artist,
            track.title,
            album,
            globalvariables.DEFAULT_THEME,
            globalvariables.SHOW_PROGRESS_BAR,
        )
        cached_style = _theme_cache.get(cache_key)
        if cached_style is not None:
            return cached_style

    style_name = "default"
    style = STYLES["default"].copy()

    default_theme = globalvariables.DEFAULT_THEME
    if default_theme is not None and default_theme in STYLES:
        style_name = default_theme.replace("\\", "/")
        default_style = STYLES[style_name]
        style.update(default_style)
        if "format" in default_style:
            style["format"] = _compose_format(STYLES["default"]["format"], default_style["format"])

    if track is not None:
        for name, candidate in STYLES.items():
            if name == "default" or "rule" not in candidate:
                continue
            if candidate["rule"](track):
                style_name = name
                style.update(candidate)
                if "format" in candidate:
                    style["format"] = _compose_format(STYLES["default"]["format"], candidate["format"])
                if "font-family" in candidate:
                    style["font-family"] = _normalize_font_family(candidate["font-family"])
                break

    if "background-color" not in style or style.get("use-dynamic-bg", False):
        style["background-color"] = "#000000B3"

    for key, value in list(style.items()):
        if "color" in key and isinstance(value, str) and re.match(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3,5})?$", value):
            style[key] = hex_to_rgba(value)

    style = _normalize_minimal_style(style)

    style["name"] = style_name
    style["progress-visible"] = globalvariables.SHOW_PROGRESS_BAR

    if cache_key is not None:
        if len(_theme_cache) >= _cache_max_size:
            _theme_cache.pop(next(iter(_theme_cache)))
        _theme_cache[cache_key] = style

    return style


load_themes()