import os
import importlib.util
import regex as re
import sys
from LyricBar.utils.tools import hex_to_rgba
from LyricBar.utils.dataclasses import TrackInfo
from LyricBar import globalvariables

def replace_all(line, matches, replacement, word_pass=None, cap_first=True):
    line = line.strip()
    if matches is None:
        return line
    c_list = list(line)
    for match in matches:
        if word_pass is not None:
            if any([_ in "".join(c_list[match.start():match.end()]) for _ in word_pass]):
                continue
        c_list[match.start()] = replacement
        if cap_first:
            if match.start() == 0:
                c_list[0] = c_list[0][:1].upper() + c_list[0][1:]
            else:
                i = match.start() - 1
                while i >= 0 and c_list[i] in " ":
                    i -= 1
                if c_list[i] in ".!?":
                    c_list[match.start()] = c_list[match.start()][:1].upper() + c_list[match.start()][1:]
        for i in range(match.start() + 1, match.end()):
            c_list[i] = ""
    return "".join(c_list)

def uncensor(line):
    uncensor_dict = {
        "fuck": (r"(\*\*\*\*(?=( it|ing|er|'s sake| sake|'em | 'em| em| him| her| them)))|((?<=(mother))\*\*\*\*)|((?<=(as ))\*\*\*\*)|((?<= )[Ff][^a-tw-yzA-TW-YZ]?[^abd-yzABD-YZ]?[^a-jl-yzA-JL-YZ]?(?=([ !?'\"]|ed |ing |er |in |in' |ers|ed-up |\.[^a-zA-Z])))", ("f", "F")),
        "shit": (r"((?<=(as ))\*\*\*\*)|((?<=(little ))\*\*\*\*)|((?<= )[Ss][^a-gi-yzA-GI-YZ]?[^a-hj-yzA-HJ-YZ]?[^a-su-yzA-SU-YZ]?(?=([ !?'\"]|\.[^a-zA-Z])))", ("sit", "si", "st", "s", "S")),
        "bitch": (r"(\*\*\*\*\*(?=(es| ass|-ass|ass| gon)))|((?<= )[Bb][^a-hj-yzA-HJ-YZ]?[^a-su-yzA-SU-YZ]?[^abd-yzABD-YZ]?[^a-gi-yzA-GI-YZ]?(?=([ !?'\"]|es |\.[^a-zA-Z])))", ("bit", "b", "B")),
    }
    for k, v in uncensor_dict.items():
        line = replace_all(line, re.finditer(v[0], line), k, v[1])
    return line

def default_formatter(line):
    if any([line.strip().startswith(_) for _ in ["作词", "编曲", "制作", "作曲", "混音", "人声", "母带", "监制", "词", "曲", "录", "附加制作", "鼓", "贝斯", "吉他", "音频"]]):
        line = ""
    line = uncensor(line)
    if line == "":
        return "♬"
    return line

STYLES = dict()

import os
import importlib.util
import regex as re
import sys

from LyricBar.utils.tools import hex_to_rgba
from LyricBar.utils.dataclasses import TrackInfo
from LyricBar import globalvariables
def search_py(rootdir):
    file_list = []
    for root, directories, files in os.walk(rootdir):
        root = root.replace(rootdir, "")[1:]
        for file in files:
            if(file.endswith(".py")):
                file_list.append(os.path.join(root, file))
    return file_list

def load_themes():
    global STYLES
    STYLES = {
        "default": {
            "background-color": "#00000000",
            
            "font-color": "#bbbbbb",
            "font-family": "Spotify Mix, Arial, Microsoft YaHei UI",
            "font-size": "30px",
            "font-weight": "normal",
            "font-italic": False,
            
            
            "line-color": "#7c7a77",
            "line-width": 0.3,

            "use-shadow": False,  # Disabled for performance
            "shadow-color": "#ffff97",
            "shadow-offset": [0, 0],
            "shadow-radius": 4,
            
            "flip-text": False,
            
            "format": default_formatter,
            
            "entering": "fadein",
            "sustaining": None,  # Disabled for performance (no flickering)
            "leaving": "fadeout"
        }
    }
    
    # Load all themes including artist-specific themes
    theme_files = search_py(globalvariables.THEME_FOLDER)
    theme_files = list(filter(lambda x: x.endswith(".py"), theme_files))
    print(f"Loaded {len(theme_files)} themes.")

    for theme_file in theme_files:
        theme_name = theme_file[:-3]
        if theme_name not in STYLES:
            spec = importlib.util.spec_from_file_location("styles", os.path.join(globalvariables.THEME_FOLDER, theme_file))
            styles_module = importlib.util.module_from_spec(spec)
            sys.modules["styles"] = styles_module
            spec.loader.exec_module(styles_module)
            new_styles = styles_module.STYLES
            for k in list(new_styles.keys()):
                # Don't add prefix for Default.py themes - use clean names
                if theme_file == "Default.py":
                    pass  # Keep the original theme name
                else:
                    new_styles[theme_file.replace(".py", "").replace("\\", "/") + " - " + k] = new_styles.pop(k)
            STYLES.update(new_styles)

    # Only show theme count, not names

load_themes()

# Theme cache to improve performance
_theme_cache = {}
_cache_max_size = 50

def get_style(track: TrackInfo):
    # Create cache key
    cache_key = None
    if track is not None:
        # Handle missing album attribute safely
        album = getattr(track, 'album', None) or 'Unknown'
        cache_key = f"{track.artist}:{track.title}:{album}"
        if cache_key in _theme_cache:
            return _theme_cache[cache_key]
    
    stl = STYLES["default"].copy()
    stl_name = "default"
    
    # Apply default theme from settings even when track is None (startup)
    if globalvariables.DEFAULT_THEME is not None and globalvariables.DEFAULT_THEME in STYLES:
        stl_name = globalvariables.DEFAULT_THEME.replace("\\", "/")
        style = STYLES[stl_name]
        stl.update(STYLES[stl_name])
        if "format" in style:
            stl["format"] = lambda line: (style["format"](STYLES["default"]["format"](line)))
    
    # Only check for matching themes if track is not None
    if track is not None:
        for name, style in STYLES.items():
            if name == "default" or "rule" not in style:
                continue
            if "rule" in style and style["rule"](track):
                stl_name = name
                # Only log essential info elsewhere
                stl.update(style)
                if "format" in style:
                    stl["format"] = lambda line: (style["format"](STYLES["default"]["format"](line)))
                if "font-family" in style:
                    if any([_ in style["font-family"].lower() for _ in [".ttf", ".otf"]]) and os.path.exists(style["font-family"]):
                            stl["font-family"] = style["font-family"]
                    else:
                        stl["font-family"] = ", ".join(list(filter(lambda x: x != " ", [_.strip() for _ in style["font-family"].split(",") + STYLES["default"]["font-family"].split(",")])))
                break
    
    # Dynamic background: Use semi-transparent black for better performance and readability
    # 70% opacity provides good contrast without being too opaque
    if "background-color" not in stl or stl.get("use-dynamic-bg", False):
        stl["background-color"] = "#000000B3"  # 70% black - universal contrast
    
    for key, value in stl.items():
        if 'color' in key:
            if isinstance(value, str) and re.match(r'^#[0-9a-fA-F]{3}([0-9a-fA-F]{3,5})?$', value):
                stl[key] = hex_to_rgba(value)
    stl.update({"name": stl_name})
    
    # Cache the result for better performance
    if cache_key is not None:
        # Keep cache size under control
        if len(_theme_cache) >= _cache_max_size:
            # Remove oldest entry (first in, first out)
            oldest_key = next(iter(_theme_cache))
            del _theme_cache[oldest_key]
        _theme_cache[cache_key] = stl
    
    return stl