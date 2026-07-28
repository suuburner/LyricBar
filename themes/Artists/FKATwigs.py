STYLES = {
    "eusexua": {
        "background-image": "images/eusexua.png",
        "background-color": "#734E4E64",
        
        "font-family": "OBG EUSEXUA 2024",
        "font-size": "21px",
        "font-color": "#ffffff",
        
        "line-color": "#000000",
        "line-width": 0,
        
        "use-shadow": False,
        
        "rule": lambda track: (track.artist.lower() == "fka twigs" and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["eusexua", "perfect stranger", "drums of death"]])),
        
        "format": lambda line: line.upper().replace("‘", "").replace("’", "").replace("'", "")
    }
}