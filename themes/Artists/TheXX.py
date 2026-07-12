STYLES = {
    "i see you": {
        "background-image": "images/iseeyou.png",
        "font-image": "images/iseeyou.png",
        "font-weight": "bold",
        
        "line-color": "#adadad",
        "line-width": 0,
        
        "rule": lambda track: (track.artist.lower() in ["the xx"])
    }
}