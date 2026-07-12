STYLES = {
    "chromakopia": {
        "font-family": "Poleno Bold, Arial Black, Impact, Arial",
        "font-color": "#18a450",
        "font-weight": "bold",
        
        "line-width": 0,
        
        "use-shadow": False,
        
        "background-color": "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #d5d3ba, stop:0.75 #d5d3ba, stop:0.9 #1a1a1a, stop:1 #00000000)",
        
        "rule": lambda track: (track.artist.lower() == "tyler, the creator" and any([_ in track.title.lower().replace("'", "'").replace("'", "'") for _ in ["st. chroma", "rah tah tah", "noid", "darling, i", "hey jane", "i killed you", "judge judy", "sticky", "take your mask off", "tomorrow", "thought i was dead", "like him", "balloon", "puppet", "i hope you find your way home"]])),
    },

    "tyler the creator": {
        "font-family": "Poleno Bold, Arial Black, Impact, Arial",
        "font-color": "#fb3826",
        "font-weight": "bold",
        
        "line-width": 2,
        
        "use-shadow": True,
        "shadow-color": "#000000FF",
        "shadow-radius": 10,
        "shadow-offset": (2, 2),

        "background-color": "qradialgradient(spread:pad, cx:0.5, cy:0.9, radius:0.4, fx:0.5, fy:0.9, stop:0 #ff6f61, stop:0.5 #ffa89e, stop:1 #00000000)",
        "rule": lambda track: track.artist.lower().strip() in ("tyler, the creator", "tyler the creator"),
    }
}