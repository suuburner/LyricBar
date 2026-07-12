
STYLES = {
    "cigarettes after sex": {
    "background-color": "qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 #18181f, stop:0.3 #c0c0c0, stop:0.6 #888888, stop:1 #222228)",
        "font-family": "Canela Light Trial, Georgia, serif",
        "font-size": "46px",
    "font-color": "#222228",
        "line-width": 0,
        "use-shadow": True,
    "shadow-color": "#ececec",
        "shadow-radius": 24,
        "shadow-offset": [0, 2],
        "rule": lambda track: (track.artist.lower() in ["cigarettes after sex", "cas"] and any([_ in track.title.lower() for _ in ["k.", "each time you fall in love", "sunsetz", "affection", "keep on loving you", "truly", "nothing's gonna hurt you baby", "apocalypse", "flash", "young & dumb"]]))
    },
    "cry": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #aeefff, stop:0.2 #b7e2ff, stop:0.4 #e0c3fc, stop:0.6 #f9f9d2, stop:0.8 #b6e2d3, stop:1 #a1c4fd)",
        "font-family": "Wilke LT Std Black, sans-serif",
        "font-size": "48px",
        "font-color": "#3a4a6a",
        "line-width": 0,
        "use-shadow": True,
        "shadow-color": "#b7e2ff",
        "shadow-radius": 28,
        "shadow-offset": [0, 2],
        "format": lambda line: line.title(),
        "rule": lambda track: (track.artist.lower() in ["cigarettes after sex", "cas"] and any([_ in track.title.lower() for _ in ["don't let me go", "cry", "falling in love", "heavenly", "you're the only good thing in my life", "touch", "hentai", "pistol"]]))
    },
    "x's": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 #3a2a2a, stop:0.3 #2a1a1a, stop:0.7 #1a0a0a, stop:1 #2a1a2a)",
    "font-family": "IM FELL DW Pica, Georgia, serif",
        "font-size": "42px",
        "font-color": "#f5f5f5",
        "line-width": 0,
        "use-shadow": True,
        "shadow-color": "#3a2a4a",
        "shadow-radius": 18,
        "shadow-offset": [2, 2],
        "rule": lambda track: (track.artist.lower() in ["cigarettes after sex", "cas"] and any([_ in track.title.lower() for _ in ["x's", "ambien slide", "dreaming of you", "hot", "tejano blue", "sesame syrup", "stop waiting", "baby blue movie", "dark vacay"]]))
    },
    "romantic": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2a1a1a, stop:0.5 #3a2020, stop:0.8 #1a0a0a, stop:1 #ffe6e6)",
        "font-family": "Garamond, serif",
        "font-size": "48px",
        "font-color": "#ffe6e6",
        "line-width": 0,
        "use-shadow": True,
        "shadow-color": "#3a2020",
        "shadow-radius": 14,
        "shadow-offset": [0, 0],
        "rule": lambda track: (track.artist.lower() in ["cigarettes after sex", "cas"] and any([_ in track.title.lower() for _ in ["please don't cry", "pistol", "sweet", "opera house", "you're all i want"]]))
    },
    "dreamy": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #2a2a4a, stop:0.4 #1a1a2a, stop:0.8 #0a0a1a, stop:1 #e0e0ff)",
        "font-family": "Century Gothic, sans-serif",
        "font-size": "40px",
        "font-color": "#e0e0ff",
        "line-width": 0,
        "use-shadow": True,
        "shadow-color": "#1a1a2a",
        "shadow-radius": 16,
        "shadow-offset": [0, 0],
        "rule": lambda track: (track.artist.lower() in ["cigarettes after sex", "cas"])
    }
}
