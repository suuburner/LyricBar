STYLES = {
    "cupcakke": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #d34c8f, stop:1 #f36e8f)",

        "font-color": "#dcdac7",
        "font-family": "Feathergraphy Clean, Arial, sans-serif",
        
        "font-size": "40px",
        
        "line-width": 0,
        
        "use-shadow": False,
        
        "rule": lambda track: (track.artist.lower() == "cupcakke")
    }
}