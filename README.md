# <img src="resources/icon.ico" alt="LyricBar Logo" width="30"> LyricBar

<!-- Let's show a small lyricsbar icon.ico file at the top as a logo? -->

LyricBar is a small, always-on-top lyric bar for Windows. It follows your current playback, fetches synced lyrics, and shows them in a compact rounded strip with a minimal theme system.

## Features

- Fixed-size floating lyric bar with rounded styling.
- Follows playback from Windows media sessions or Spicetify.
- Synced lyrics with provider fallback and local cache support.
- Theme picker with curated minimal themes.
- Progress bar toggle, timing offset, and tracking-app settings.
- Tray menu for settings, theme reload, and exit.

## Shortcuts

- `Ctrl + Left Drag` - move the bar (persistent across sessions).
- `Double click` on the bar - copy the current lyric line.
- `Shift + Left Click` - move the bar to another screen.
- `Right Click` - fetch lyrics from the next provider.
- `Shift + Mouse Wheel` - change global offset.
- `Mouse Wheel` - change track offset.
- `Middle Click` - reset track offset.
- `Shift + Middle Click` - clear current lyrics.
- `Shift + Esc` - minimize to the floating icon.

## Installation & Usage

#### Run

```bash
python main.py
```

#### Build

```bash
.\build_exe.bat
```

## Spicetify Mode

Copy the webnowplaying.js file from the LyricBar repository into your Spicetify extensions directory. After that, enable the extension using:

> Although, I don't understand why you would want to use LyricBar with Spicetify when it can track all Windows media sessions natively. But if you want to, go ahead.

```bash
spicetify config extensions webnowplaying.js
spicetify apply
```

## License

GPL-3.0 License. See [LICENSE](LICENSE) for more details.
