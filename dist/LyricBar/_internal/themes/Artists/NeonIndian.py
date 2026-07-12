STYLES = {
    "neonindian": {
        "background-color": "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #0f1944, stop:1 #00000000)",
        
        "font-color": "#e0eef5aa",
        "font-family": "Hor, serif",
        "font-size": "35px",
        "font-weight": "bold",
        "font-italic": False,
        
        
        "line-color": "#e0eef5aa",
        "line-width": 0.5,

        "use-shadow": True,
        "shadow-color": "#0e98de",
        "shadow-offset": [0, 0],
        "shadow-radius": 20,
        
        "rule": lambda track: (track.artist.lower() == "neon indian")
    }
}