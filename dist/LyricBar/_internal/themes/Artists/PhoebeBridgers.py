STYLES = {
    "phoebe bridgers": {
        "background-image": "images/phoebebridgers.png",
        # "font-family": "Garamond",
        "font-family": "Garamond, Arial, sans-serif",
        "font-size": "35px",
        
        "progress-line-color": "#00000000",
        
        "rule": lambda track: (track.artist.lower() == "phoebe bridgers")
    }
}