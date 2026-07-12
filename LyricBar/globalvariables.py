##### APPEARANCE
TAKSBAR_HEIGHT = 70
LEFTOUT_WIDTH = 500

##### OFFSET
GLOBAL_OFFSET = 0

##### LYRICS TIMING OFFSET (milliseconds - positive = earlier, negative = later)
LYRICS_TIMING_OFFSET = 300

##### LYRIC FOLDER
LYRIC_FOLDER = "lyrics"

##### THEME FOLDER
THEME_FOLDER = "themes"

##### DEFAULT THEME
DEFAULT_THEME = "Bubblegum"

##### PROXY

### If you need to use proxy, like vpn......(iykyk)
HTTP_PROXY = ""
HTTPS_PROXY = ""

##### LYRIC PROVIDER

### Track ID is needed to get lyrics from Spotify
### Spotify lyrics can be out of sync at a lot of times, but it prevents mixing up lyrics from different versions
USE_SPOTIFY_LYRICS = False
# If True, you need to set SP_DC
SP_DC = ""

### Third party lyrics providers
### AVAILABLE PROVIDERS (from syncedlyrics): Musixmatch, Lrclib, Deezer, NetEase, Megalobiz, Genius
### Netease DOES NOT PROVIDE BJORK SONGS!!!!!
THIRD_PARTY_LYRICS_PROVIDERS = ["Lrclib", "NetEase", "Musixmatch", "Deezer", "Megalobiz"]

### DOES NOT conflict with each other, but spotify lyrics are prioritized, then third party lyrics providers in the list order

##### STT PROVIDER
STT_MODEL_PATH = ""
STT_TRACKING_INPUT = ""


##### PLAYIING INFO PROVIDER

### AVAILABLE OPTIONS: Spotify, System, Mixed

### Spotify: (Not Recommended) Uses Spotify API to get the current playing track. If the interval is set too long, it's much irresponsive to playstate changes (e.g. pause, next track, progress). If the interval is set too short, too much request can lead to rate limiting :( . DOES PROVIDE TRACK ID.
### System: (Not Available Now) Use Windows Runtime API to get the current playing track. You can call them as frequently as you want, but the actual song progress information is updated every four second (at least on my pc, you are welcomed to test it on yours. I dont know whether its a winsdk thing). Song changes are instant, pausing can sometimes be delayed for whatever reason. DOES NOT PROVIDE TRACK ID.
### Mixed: (Not Available Now) Uses Spotify API to get the current playing track id, then uses System to get all the rest information. Spotify API is only called on track change. DOES PROVIDE TRACK ID.
### Spicetify: (Recommended) Uses Spicetify websocket to get the current playing track. It's much more responsive than Spotify API, but it's only available for Spotify desktop client with Spicetify installed. DOES PROVIDE TRACK ID.
PLAYING_INFO_PROVIDER = "Spicetify"

### If you are using Spotify as the playing info provider, you need to set the Spotify API information (or not? I did remember there is a login popup, anyway chi....)
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
SPOTIPY_REDIRECT_URI = ""

##### TRACKING APP (Only works for System Playing Info Provider)

### I also tried "PotPlayerMini64.exe" and it kinda works?!?!
# Can be a single string or a list of apps to track
# TRACKING_APP = ["TheBrowserCompany.Arc_ttt1ap7aakyb4!Arc", "Spotify.exe"]
TRACKING_APP = ["Spotify.exe"]

##### SPICETIFY PORT (Only works for Spicetify Playing Info Provider)

SPICETIFY_PORT = 8974


import yaml
import os
import sys

# Helper function to get the correct resource path for PyInstaller
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

config = dict()
settings_file = resource_path("settings.yaml")
if os.path.exists(settings_file):
    config = yaml.safe_load(open(settings_file, "r"))

if "Apperance" in config:
    if "Taksbar Height" in config["Apperance"] and str(config["Apperance"]["Taksbar Height"]).isdigit():
        TAKSBAR_HEIGHT = int(config["Apperance"]["TaksbarHeight"])
    if "Leftout Width" in config["Apperance"] and str(config["Apperance"]["Leftout Width"]).isdigit():
        LEFTOUT_WIDTH = int(config["Apperance"]["Leftout Width"])

if "Lyrics" in config:
    if "Folder" in config["Lyrics"]:
        LYRIC_FOLDER = config["Lyrics"]["Folder"]
    if "Global Offset" in config["Lyrics"] and str(config["Lyrics"]["Global Offset"]).isdigit():
        GLOBAL_OFFSET = int(config["Lyrics"]["Global Offset"])
    if "Timing Offset" in config["Lyrics"]:
        try:
            LYRICS_TIMING_OFFSET = int(config["Lyrics"]["Timing Offset"])
        except (ValueError, TypeError):
            LYRICS_TIMING_OFFSET = 300  # Default to 300ms
    if "Providers" in config["Lyrics"]:
        if "Spotify" in config["Lyrics"]["Providers"] and config["Lyrics"]["Providers"]["Spotify"]:
            USE_SPOTIFY_LYRICS = True
            if "SP_DC" in config["Lyrics"]["Providers"]["Spotify"]:
                SP_DC = config["Lyrics"]["Providers"]["Spotify"]["DC"]
        # Filter providers to only include valid ones, preserving order from settings
        valid_providers = ["musixmatch", "lrclib", "deezer", "netease", "megalobiz"]
        THIRD_PARTY_LYRICS_PROVIDERS = [p for p in config["Lyrics"]["Providers"] if p.lower() in valid_providers]

if "STT" in config:
    if "Model Path" in config["STT"]:
        STT_MODEL_PATH = config["STT"]["Model Path"]
    if "Tracking Input" in config["STT"]:
        STT_TRACKING_INPUT = config["STT"]["Tracking Input"]

if "Playing Info" in config:
    if "Provider" in config["Playing Info"]:
        PLAYING_INFO_PROVIDER = config["Playing Info"]["Provider"]
    if "Tracking App" in config["Playing Info"]:
        tracking_app_config = config["Playing Info"]["Tracking App"]
        # Support both single string and list of apps
        if isinstance(tracking_app_config, list):
            TRACKING_APP = tracking_app_config
        else:
            TRACKING_APP = [tracking_app_config]  # Convert single string to list
    if "Spicetify Port" in config["Playing Info"] and str(config["Playing Info"]["Spicetify Port"]).isdigit():
        SPICETIFY_PORT = int(config["Playing Info"]["Spicetify Port"])

if "Themes" in config:
    if "Folder" in config["Themes"]:
        THEME_FOLDER = config["Themes"]["Folder"]
    if "Default" in config["Themes"]:
        DEFAULT_THEME = config["Themes"]["Default"]

# Update THEME_FOLDER to use resource_path for exe compatibility
THEME_FOLDER = resource_path(THEME_FOLDER)

if "Proxy" in config:
    if "Host" in config["Proxy"] and config["Proxy"]["Host"] != "" and config["Proxy"]["Host"] is not None and "Port" in config["Proxy"] and str(config["Proxy"]["Port"]).isdigit():
        HTTP_PROXY = config["Proxy"]["Host"] + ":" + str(config["Proxy"]["Port"])
        HTTPS_PROXY = config["Proxy"]["Host"] + ":" + str(config["Proxy"]["Port"])
