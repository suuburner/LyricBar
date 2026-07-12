#### Default Theme
STYLES = {
    "Glow": {
        "background-color": "#0A0A0AB3",  # 70% very dark background
        "font-color": "#E6E6E6",  # Slightly darker for more contrast
        "font-family": "Marons, Spotify Mix, Arial, Microsoft YaHei UI",
        "font-size": "40px",
        "font-weight": "900",  # Extra bold for more concrete look
        "font-italic": False,
        "line-color": "#00000000",  # No outline
        "line-width": 0,
        "use-shadow": True,  # Enable shadow for glow effect
        "shadow-color": "#FFFFFF",  # White glow for glowy wordart effect
        "shadow-offset": [0, 0],  # Centered glow
        "shadow-radius": 8,  # Lower radius for sharper, less faded glow
        "flip-text": False,
        "entering": "fadein",
        "sustaining": None,  # Optimized for performance
        "leaving": "fadeout"
    },
    
    "Shadow": {
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #232136, stop:0.4 #2a273f, stop:0.7 #44415a99, stop:1 #18182566)",  # Muted Catppuccin gradient, complements #909090 text
        "font-color": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #cdd1ce, stop:1 #505050)",  # Gradient gray for subtle depth
        "font-family": "Vespertine, Spotify Mix, Arial Black, Microsoft YaHei UI",
        "font-size": "40px",
        "font-weight": "900",  # Extra bold/black weight
        "font-italic": True,
        
        "line-width": 0,

        "use-shadow": True,  # Enable shadow for 3D effect
        "shadow-color": "#000000",  # Black shadow for depth
        "shadow-offset": [2, 2],  # Offset shadow down and right for 3D effect
        "shadow-radius": 2,  # Slightly softer shadow
        
        "progress-color": "#909090",  # Medium gray progress bar (matches text - 50/50 black-white)
        "progress-line-color": "#303030",  # Dark gray/almost black outline
        
        "flip-text": False,
        
        "entering": "fadein",
        "sustaining": "zooming",  # Use predefined flickering animation
        "leaving": "fadeout"
    },
    
    "Bubblegum": {
        "background-color": "#1A0D1AB3",  # 70% dark purple background (contrasts with pink text)

        "font-color": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFB6D9, stop:0.6 #FF69B4, stop:1 #FF66B3)",  # Gradient pink for bubblegum effect
        "font-family": "Gerline Demo, Eurostar, Spotify Mix, Microsoft YaHei UI",
        "font-size": "40px",
        "font-weight": "bold",
        "font-italic": False,
        
        "progress-line-color": "#FFB6D9AA",

        "line-color": "#E180C9CD",
        "line-width": 0,

        "use-shadow": False,  # Optimized for performance
        "shadow-color": "#e3a0b7",
        "shadow-offset": [0, 0],
        "shadow-radius": 9,
        
        "flip-text": False,

        "entering": "fadein",
        "sustaining": None,  # Optimized for performance
        "leaving": "fadeout"
    },
    
    "Crimson": {
        "background-color": "#000000B3",  # 70% black background (contrasts with red outline)
        
        "font-color": "#00000000",  # Transparent fill
        "font-family": "CCBiffBamBoom, Impact, Arial Black, sans-serif",
        "font-size": "38px",
        "font-weight": "bold",
        "font-italic": False,
        
        "line-color": "#FF4757",  # Brighter red for better visibility
        "line-width": 1.5,  # Thicker line for better visibility

        "use-shadow": False,  # Optimized for performance
        
        "progress-line-color": "#FF4757AA",
        
        "flip-text": False,

        "entering": "fadein",
        "sustaining": None,  # Optimized for performance
        "leaving": "fadeout"
    }
}