STYLES = {
    "arca": {
    "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #18181f, stop:0.5 #222228, stop:1 #000000)",
    "font-color": "#000000",
        "font-family": "Kick The Font, Arial, sans-serif",
        "font-size": "38px",
        "line-color": "#858585",
        "line-width": 2,
        "shadow-color": "white",
        "rule": lambda track: (track.artist.lower() == "arca"),
        "format": lambda line: line.replace("ñ", "n").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    }
}