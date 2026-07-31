STYLES = {
    "solar power": {
        "background-color": "qradialgradient(spread:pad, mode:logical, cx:width/2, cy:height/2, radius:height/2+width/3, fx:width/2, fy:height/2, stop:0 #e2f2f3, stop:0.3 #a9cde6, stop:0.76 #77addb, stop:0.8 #4686cb, stop:1 #00000000)",
        
        "font-family": "Helvetica",
        "font-color": "#d7daa1",
        "font-weight": "black",

        "line-color": "#db6a1a",
        "line-width": 1,
        
        "shadow-color": "#ced45e",
        "shadow-radius": 20,
        
        "rule": lambda track: (track.artist.lower() == "lorde" and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["the path", "solar power", "california", "stoned at the nail salon", "fallen fruit", "secrets from a girl", "the man with the axe", "dominoes", "big star", "leader of a new regime", "mood ring", "oceanic feeling", "helen of troy", "hold no grudge"]]))
    },
    "melodrama": {
        "background-image": "images/melodrama.png",
        "font-family": "Canela Light Trial, Arial, sans-serif",
        "font-color": "#e7b75e",
        "font-size": "22px",

        "line-color": "#003395",
        "line-width": 2,
        
        "shadow-color": "#e34345",
        "shadow-radius": 20,
        
        "rule": lambda track: (track.artist.lower() == "lorde" and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["green light", "sober", "homemade dynamite", "the louvre", "liability", "hard feelings/loveless", "sober ii (melodrama)", "writer in the dark", "supercut", "liability (reprise)", "perfect places"]])),

        "format": lambda x: " ".join(x.upper()).replace("   ", "  ")
    },
    "pure heroine": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #000000, stop:0.4 #1a1a1a, stop:0.6 #1a1a1a, stop:1 #000000)",

        "font-family": "Futura, Arial, sans-serif",
        "font-size": "20px",
        "font-color": "qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5, stop:0 #ffffff, stop:0.9 #ffffff, stop:1 #b7b5b6)",
        
        "line-width": 0,
        
        "shadow-color": "#ffffff",
        
        "rule": lambda track: (track.artist.lower() == "lorde" and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["tennis court", "400 lux", "royals", "ribs", "buzzcut season", "team", "glory and gore", "still sane", "white teeth teens", "a world alone"]])),
        
        "format": lambda x: " ".join(x.upper()).replace("   ", "  ")
    }
}