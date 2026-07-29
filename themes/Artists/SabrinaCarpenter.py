STYLES = {
    "sabrina carpenter": {
        "background-image": "images/sabrina.png",
        "font-family": "Century Old Style, Century, Georgia, serif",
        "font-color": "#ece1b9",
        "font-size": "24px",

        "line-color": "#a08112",
        "line-width": 2,
        
        "rule": lambda track: (track.artist.lower() == "sabrina carpenter"),
        
        "entering": "zoomin"
    }
}