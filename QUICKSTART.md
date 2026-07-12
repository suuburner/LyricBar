# LyricBar - Quick Start Guide

## Running the Application

### Using the Virtual Environment (Recommended)
```powershell
C:/Users/Swopnil/Downloads/Compressed/LyricBar/.venv/Scripts/python.exe main.py
```

### Or Activate Virtual Environment First
```powershell
.venv\Scripts\Activate.ps1
python main.py
```

## Troubleshooting

### If you get "Module not found" errors:
1. Make sure you're in the LyricBar directory
2. Run: `.venv\Scripts\python.exe -m pip install -r requirements.txt`

### If winsdk installation fails:
- This has been fixed! The application now uses `winrt` packages instead
- If you still see issues, make sure you installed from the updated `requirements.txt`

### Current Warnings (Safe to Ignore):
- **QFont::setPixelSize**: Font configuration warning - doesn't affect functionality
- **Failed to load STT model**: Optional feature - only needed for speech-to-text
- **Failed to find System Loopback device**: Optional feature - only needed for audio capture

## Configuration

Edit `settings.yaml` to customize:
- Default theme
- Now playing provider (System/Spotify/Spicetify)
- Lyrics providers
- Offset timing
- And more...

## Features Working:
✅ Lyrics display
✅ Theme system with artist-specific themes
✅ Multiple now playing providers
✅ Multiple lyrics sources
✅ Customizable styling
✅ Frameless window with transparency

## Need Help?
Check `FIXES_APPLIED.md` for detailed information about all fixes and improvements.
