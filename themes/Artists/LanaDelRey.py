STYLES = {
    "honeymoon": {
        "background-color": "qradialgradient(spread:pad, cx:0.3, cy:0.3, radius:1.2, fx:0.3, fy:0.3, stop:0 #4a3428, stop:0.4 #2d1f1a, stop:0.8 #1a1210, stop:1 #000000dd)",
        
        "font-family": "Cg, Georgia, serif",
        "font-size": "23px",
        "font-color": "#f5e6d3",
        
        "line-width": 0,
        
        "use-shadow": True,
        "shadow-color": "#000000",
        "shadow-offset": [2, 2],
        "shadow-radius": 8,
        
        "rule": lambda track: (track.artist.lower() == "lana del rey" and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["honeymoon", "music to watch boys to", "terrence loves you", "god knows i tried", "high by the beach", "art deco", "burnt norton", "religion", "salvatore", "the blackest day", "24", "swan song", "don't let me be misunderstood"]]) or track.title.lower().replace("‘", "'").replace("’", "'") in ["freak"])
    },
    "lfl": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #ff6b9d, stop:0.5 #c44569, stop:1 #00000000)",
        
    "font-family": "LTCCaslonLongSwash, serif",
        "font-color": "#ffffff",
        "font-size": "22px",
        
        "line-color": "#ff6b9d99",
        "line-width": 0.2,
        
        "use-shadow": True,
        "shadow-color": "#c44569",
        "shadow-offset": [0, 0],
        "shadow-radius": 10,
        
        "rule": lambda track: (track.artist.lower() == "lana del rey" and (any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["lust for life", "13 beaches", "cherry", "white mustang", "summer bummer", "groupie love", "in my feelings", "coachella - woodstock in my mind", "god bless america - and all the beautiful people in it", "when the world was at war we kept dancing", "beautiful people beautiful problems", "tomorrow never came", "get free"]]) or track.title.lower().replace("‘", "'").replace("’", "'") in ["love", "change", "heroin"]))
    },
    "nfr": {
        "background-image": "images/nfr.png",
        
        "font-family": "CCBiffBamBoom, Arial, sans-serif",
        "font-color": "#ffffff00",
        
        "line-color": "#030101",
        "line-width": 1.5,
        
        "shadow-color": "#030101",
        "shadow-offset": [2, 2],
        "shadow-radius": 5,
        
        "entering": "zoomin_overscale",
        "sustaining": "zooming",
        "leaving": "topslideout",
        
        "rule": lambda track: (track.artist.lower() == "lana del rey" and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["norman fucking rockwell", "mariners apartment complex", "venice bitch", "fuck it i love you", "doin' time", "love song", "cinnamon girl", "how to disappear", "california", "the next best american record", "the greatest", "bartender", "happiness is a butterfly", "hope is a dangerous thing for a woman like me to have - but i have it"]]))
    },
    "cotc": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #f5f5dc, stop:0.5 #d4c5b9, stop:1 #00000000)",
        
        # "font-family": "Marons",
    "font-family": "Marons, serif",
        "font-color": "#5d4e37",
        "font-size": "23px",
        
        "line-color": "#8b7355aa",
        "line-width": 0.2,
        
        "shadow-color": "#000000",
        "shadow-offset": [3, 3],
        "shadow-radius": 6,
        
        "rule": lambda track: (track.artist.lower() == "lana del rey" and any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["white dress", "chemtrails over the country club", "tulsa jesus freak", "let me love you like a woman", "wild at heart", "dark but just a game", "not all who wander are lost", "yosemite", "breaking up slowly", "dance till we die", "for free"]]))
    },
    "bb": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #4a5a6a, stop:0.5 #8fa8c5, stop:1 #00000000)",
        
        # "font-family": "Modern No. 216 Heavy",
        "font-family": "Modern No. 216 Heavy, Arial, sans-serif",
        "font-color": "#ffffff",
        "font-size": "21px",
        
        "line-color": "#8fa8c5aa",
        "line-width": 0.2,
        
        "use-shadow": True,
        "shadow-color": "#2c3e50",
        "shadow-offset": [2, 2],
        "shadow-radius": 8,
        
        "rule": lambda track: (track.artist.lower() == "lana del rey" and (any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["text book", "blue banisters", "arcadia", "interlude - the trio", "black bathing suit", "if you lie down with me", "violets for roses", "dealer", "thunder", "wildflower wildfire", "nectar of the gods", "living legend", "cherry blossom", "sweet carolina"]]) or track.title.lower().replace("‘", "'").replace("’", "'") in ["beautiful"]))
    },
    "blvd": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1a4d7a, stop:0.5 #2d6fa8, stop:1 #00000000)",
        
        "font-family": "Futura Display BQ, Futura, Arial, sans-serif",
        "font-color": "#f2db78",
        "font-size": "23px",
        
        "line-color": "#f2db78aa",
        "line-width": 0.2,
        
        "use-shadow": True,
        "shadow-color": "#1a4d7a",
        "shadow-offset": [0, 0],
        "shadow-radius": 10,
        
        "rule": lambda track: (track.artist.lower() == "lana del rey" and (any([_ in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["the grants", "did you know that there's a tunnel under ocean blvd", "sweet", "a&w", "judah smith interlude", "candy necklace", "jon batiste interlude", "kintsugi", "fingertips", "paris, texas", "grandfather please stand on the shoulders of my father while he's deep-sea fishing", "let the light in", "margaret", "fishtail", "peppers", "taco truck x vb"]]) or track.title.lower().replace("‘", "'").replace("’", "'") in ["sweet"]))
    },
    "lana del rey": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 #8b7355, stop:0.5 #a0826d, stop:1 #00000000)",
        
        # "font-family": "Rainbow",
    "font-family": "Rainbow, serif",
        "font-size": "25px",
        "font-color": "qlineargradient(spread:pad, x1:0, y1:1, x2:1, y2:0, stop:0 #998a4b, stop:0.3 #9f904d, stop:1 #fdf9dc)",
        
        "line-width": 0,
        "use-shadow": False,
        
        "rule": lambda track: (track.artist.lower() == "lana del rey")
    }
}