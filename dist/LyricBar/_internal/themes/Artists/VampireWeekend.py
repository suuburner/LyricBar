STYLES = {
    "vampire weekend": {
        "background-color": "qradialgradient(mode:reflect, spread:reflect, cx:width/2, cy:height/2, radius:3, fx:width/2, fy:height/2, stop:0 #ff7d32, stop:0.4 #ffb74d, stop:1 #ffffff)",
        "font-color": "#ff7d32",
        "font-family": "Futura, Arial, sans-serif",
        
        "line-color": "#ffffff",
        "line-width": 0,
        
        "shadow-color": "#ffffff",
        "shadow-radius": 10,
        
        "rule": lambda track: (track.artist.lower() == "vampire weekend")
    }
}