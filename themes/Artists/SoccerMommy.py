STYLES = {
    "color theory": {
        "background-image": "images/soccermommy.png",

        "font-family": "Pixelon, Arial, sans-serif",
        "font-color": "#af8484c0",
        "font-size": "21px",

        "line-color": "#8e0d1d88",
        "line-width": 0.5,
        
        "shadow-color": "#2d7879",
        "shadow-radius": 5,
        "shadow-offset": [-2, -2],
        
        "format": lambda line: "".join([_ for _ in line if _ in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ♬"]),
        "rule": lambda track: (track.artist.lower() == "soccer mommy")
    }
}