STYLES = {
    "weyes blood": {
        "background-color": "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.5, fx:0.3, fy:0.5, stop:0 #0e214c, stop:1 #00000000)",
        # "font-family": "Eckmann",
        "font-family": "Eckmann, Arial, sans-serif",
        "font-color": "#f8e3da55",
        "font-size": "23px",
        
        "line-color": "#dd6678",
        "line-width": 1,
        
        "shadow-color": "#ce848b",
        "shadow-radius": 15,
        
        "rule": lambda track: (track.artist.lower() == "weyes blood")
    }
}