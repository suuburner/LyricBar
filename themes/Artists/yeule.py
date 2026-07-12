def yeule_style(line):
    original = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    output = "ѧ𝛃ℂᴰ∃ፑᏀਮ𝕀لԟᒶṂℕ❍𝕡ℚ℟ᎦT⨿ᐺሡㄨ𝕐Ꮓ𝖆ƀ𝘤Ժ𝘦𝖋ցħɨڵꝂ╽₥դØᵱᒅ𝐫ક𝕥նᏤ⍵𝕏Ỿ𝐳"
    ret = ""
    line = line.replace("Softscars", "ₛof̷̢̨̛̙̦̮͖̘͍͆♰ꙅᶜà̵̡͈̥͚́̽͛̍̕͘ ̺ ̝ ʳₛ").replace("softscars", "ₛof̷̢̨̛̙̦̮͖̘͍͆♰ꙅᶜà̵̡͈̥͚́̽͛̍̕͘ ̺ ̝ ʳₛ")
    for char in line:
        if char in original:
            ret += output[original.index(char)]
        elif char == " ":
            ret += "  "
        else:
            ret += char
    return ret

STYLES = {
    "yeule": {
        "background-color": "qlineargradient(mode:reflect, spread:reflect, x1:0, y1:0, x2:1, y2:1, radius:0.5, fx:0.5, fy:0.5, stop:0 #000000, stop:0.5 #876ccc, stop:1 #000000)",
        "font-color": "#97befc",
        "font-family": "Times New Roman, sans-serif, Gadugi",
        
        "rule": lambda track: (track.artist.lower() == "yeule"),
        
        "format": yeule_style
    }
}