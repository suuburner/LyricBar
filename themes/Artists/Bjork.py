STYLES = {
    "post": {
        "font-color": "#d58fe8",
        # "font-family": "Bjork",
        "font-family": "Bjork, Arial, sans-serif",
        "font-size": "40px",
        
        "line-color": "#a22929",
        "line-width": 1,
        
        "shadow-color": "#a22929",
        "shadow-offset": [2, 2],
        "shadow-radius": 8,
        
        "rule": lambda track: (track.artist.lower() in ["bjork", "björk"] and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["army of me", "hyperballad", "hyper-ballad", "the modern things", "it's oh so quiet", "enjoy", "you've been flirting again", "isobel", "possibly maybe", "i miss you", "cover me", "headphones"]])),
        
        "format": lambda line: "".join([_ for _ in line if _ in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ♬"]),
        "background-color": "qlineargradient(spread:pad, x1:0.5, y1:0, x2:1, y2:0, stop:0 #e6c6f700, stop:0.2 #d1a3e6cc, stop:0.5 #d58fe8, stop:0.8 #f7b3e6cc, stop:1 #e6c6f700)"
    },
    "vespertine": {
        "font-color": "#ffffff",
        "font-family": "Vespertine, Georgia, serif",
        "font-size": "50px",
        
        "line-width": 0.75,
        "line-color": "#ffffff",
        
        "use-shadow": False,
        
        "rule": lambda track: (track.artist.lower() in ["bjork", "björk"] and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["hidden place", "cocoon", "it's not up to you", "undo", "pagan poetry", "frosti", "aurora", "an echo, a stain", "sun in my mouth", "heirloom", "harm of will", "unison", "stonemilker", "lionsong", "history of touches", "black lake", "family", "notget", "atom dance", "mouth mantra", "quicksand"]])),
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a1a, stop:0.5 #3e5c6e, stop:1 #ffffff)"
    }
}