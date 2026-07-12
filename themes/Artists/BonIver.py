def twotwo_a_million(line):
    original = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    output = "Δв¢dэfgнîJкLми◊pQя$†Ʊv₩Xyz"
    ret = ""
    line = line.upper()
    line.replace("OO", "∞")
    for char in line.upper():
        if char in original:
            ret += output[original.index(char)]
        else:
            ret += char
    return ret
STYLES = {
    "22, a million": {
        "foreground-image": "images/22amillion.png",
        "background-color": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(150,130,190,0), stop:0.15 #b9a1c6, stop:0.5 #a9746e, stop:0.85 #b9a1c6, stop:1 rgba(150,130,190,0))",
        
        "font-color": "#ffffff",
        "font-family": "Times New Roman, sans-serif, Gadugi",
        # "font-family": "Helvetica",
        "font-size": "30px",
        
        "line-width": 0,
        
        "shadow-color": "#ffffff",
        # "shadow-offset": [2, 2],
        "shadow-radius": 5,
        
        "rule": lambda track: (track.artist.lower() == "bon iver" and any([_.lower() in track.title.lower().replace("‘", "'").replace("’", "'") for _ in ["22", "10", "715", "33", "29", "666", "21", "8", "45", "00000"]])),
        
        # "format": twotwo_a_million
    }
}