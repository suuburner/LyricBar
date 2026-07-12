STYLES = {
    "the 1975 - notes": {
        # Notes on a Conditional Form era - experimental, diverse, chaotic energy  
        "background-color": "qradialgradient(spread:pad, cx:0.5, cy:0.5, radius:0.7, fx:0.5, fy:0.5, stop:0 #00d4ff, stop:0.5 #7b2cbf, stop:0.8 #ff006e, stop:1 #00000000)",
        
        "font-color": "#ffffff",
        "font-family": "Impact, Arial Black, sans-serif",
        "font-size": "33px",
        "font-weight": "bold",
        
        "line-color": "#00d4ff66",
        "line-width": 0.3,

        "use-shadow": True,
        "shadow-color": "#ff006e",
        "shadow-offset": [0, 0],
        "shadow-radius": 12,
        
        "rule": lambda track: track.artist.lower() == "the 1975" and ("too shy" in track.title.lower() or "people" in track.title.lower() or "frail state" in track.title.lower() or "birthday party" in track.title.lower())
    },
    "the 1975 - being funny": {
        # Being Funny in a Foreign Language era - warm, intimate, 80s inspired
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #ff6b9d, stop:0.5 #c44569, stop:1 #00000000)",
        
        "font-color": "#ffffff",
        "font-family": "CCBiffBamBoom, Impact, Arial Black, sans-serif",
        "font-size": "36px",
        "font-weight": "bold",
        
        "line-color": "#ff6b9d99",
        "line-width": 0.25,

        "use-shadow": True,
        "shadow-color": "#000000",
        "shadow-offset": [3, 3],
        "shadow-radius": 10,
        
        "rule": lambda track: track.artist.lower() == "the 1975" and ("part of the band" in track.title.lower() or "happiness" in track.title.lower() or "looking for somebody" in track.title.lower() or "consumption" in track.title.lower() or "wintering" in track.title.lower() or "all i need to hear" in track.title.lower() or "human too" in track.title.lower() or "about you" in track.title.lower() or "oh caroline" in track.title.lower() or "in love with you" in track.title.lower() or "when we are together" in track.title.lower())
    },
    "the 1975 - brief inquiry": {
        # A Brief Inquiry Into Online Relationships era - neon, digital, emotional
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #ff006e, stop:0.4 #8338ec, stop:0.7 #3a86ff, stop:1 #00000000)",
        
        "font-color": "#ffffff",
        "font-family": "Consolas, Courier New, monospace",
        "font-size": "30px",
        "font-weight": "bold",
        
        "line-color": "#7b2cbf99",
        "line-width": 0.3,

        "use-shadow": True,
        "shadow-color": "#3a86ff",
        "shadow-offset": [0, 0],
        "shadow-radius": 15,
        
        "rule": lambda track: track.artist.lower() == "the 1975" and ("give yourself a try" in track.title.lower() or "tootime" in track.title.lower() or "how to draw" in track.title.lower() or "love it if we made it" in track.title.lower() or "be my mistake" in track.title.lower() or "sincerity is scary" in track.title.lower() or "i like america" in track.title.lower() or "married a robot" in track.title.lower() or "inside your mind" in track.title.lower() or "not living" in track.title.lower() or "surrounded by heads" in track.title.lower() or "mine" in track.title.lower() or "more in love" in track.title.lower() or "always wanna die" in track.title.lower())
    },
    "the 1975 - i like it": {
        # I Like It When You Sleep era - pink, dreamy, maximalist aesthetic
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #ff1493, stop:0.25 #ff69eb, stop:0.5 #9d4edd, stop:0.75 #ff1493, stop:1 #00000000)",
        
        "font-color": "#ffffff",
        "font-family": "Candara, Optima, sans-serif",
        "font-size": "36px",
        "font-weight": "300",
        "font-italic": True,
        
        "line-color": "#ff69ebaa",
        "line-width": 0.2,

        "use-shadow": True,
        "shadow-color": "#9d4edd",
        "shadow-offset": [0, 0],
        "shadow-radius": 22,
        
        "rule": lambda track: track.artist.lower() == "the 1975" and ("the sound" in track.title.lower() or "change of heart" in track.title.lower() or "american" in track.title.lower() or "if i believe you" in track.title.lower() or "please be naked" in track.title.lower() or "lostmyhead" in track.title.lower() or "ballad of me" in track.title.lower() or "somebody else" in track.title.lower() or "loving someone" in track.title.lower() or "when you sleep" in track.title.lower() or "must be my dream" in track.title.lower() or "ugh!" in track.title.lower() or "she lays down" in track.title.lower() or "she way out" in track.title.lower() or "nana" in track.title.lower())
    },
    "the 1975 - self titled": {
        # Self-titled era - monochrome, raw, intimate
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:0.5 #d4d4d4, stop:1 #00000000)",
        
        "font-color": "#0a0a0a",
        "font-family": "Courier New, Consolas, monospace",
        "font-size": "31px",
        "font-weight": "bold",
        
        "line-color": "#000000aa",
        "line-width": 0.3,

        "use-shadow": True,
        "shadow-color": "#ffffff",
        "shadow-offset": [2, 2],
        "shadow-radius": 10,
        
        "rule": lambda track: (track.artist.lower() in ["the 1975"] and track.title.lower().replace("'", "'").replace("'", "'") in ["chocolate", "sex", "talk!", "an encounter", "heart out", "settle down", "robbers", "girls", "you", "medicine", "she way out", "menswear", "pressure", "is there somebody who can watch you"])
    },
    "the 1975": {
        # General theme for any The 1975 song - iconic pink/black neon aesthetic
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #ff0080, stop:0.33 #000000, stop:0.66 #ff0080, stop:1 #000000)",
        
        "font-color": "#ffffff",
        "font-family": "Montserrat ExtraBold, Montserrat, Century Gothic, sans-serif",
        "font-size": "35px",
        "font-weight": "800",
        "font-italic": False,
        
        "line-color": "#ff0080dd",
        "line-width": 0.3,

        "use-shadow": True,
        "shadow-color": "#ff0080",
        "shadow-offset": [2, 2],
        "shadow-radius": 18,
        
        "rule": lambda track: (track.artist.lower() in ["the 1975"])
    }
}
