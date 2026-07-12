# 🎯 Quick Setup Guide - LyricBar Standalone

## Goal
Run LyricBar without typing commands every time, and optionally auto-start with Spotify!

---

## 📦 Option 1: Create Standalone Executable (RECOMMENDED)

### Simple 3-Step Process:

#### Step 1: Build the Executable
Double-click: **`build_exe.bat`**

That's it! Wait a few minutes for the build to complete.

#### Step 2: Test It
Your executable will be at: `dist\LyricBar.exe`

Double-click it to test!

#### Step 3: Move It (Optional)
Copy `LyricBar.exe` to wherever you want. Just make sure these are in the same folder:
- `settings.yaml`
- `themes/` folder
- `images/` folder

---

## 🚀 Option 2: Auto-Start with Spotify

### Method A: Auto-Launcher Script (BEST)

1. **Build the executable first** (see Option 1 above)

2. **Edit `spotify_launcher.ps1`:**
   - Right-click → Edit
   - Update line 5 with your LyricBar.exe path:
     ```powershell
     $lyricBarPath = "C:\Path\To\Your\LyricBar.exe"
     ```

3. **Test the launcher:**
   - Right-click `spotify_launcher.ps1`
   - Select "Run with PowerShell"
   - Start Spotify - LyricBar should auto-start!

4. **Add to Windows Startup:**
   - Press `Win + R`
   - Type: `shell:startup`
   - Press Enter
   - Create a shortcut in the folder that opens:
     - Right-click → New → Shortcut
     - Target: `powershell.exe -WindowStyle Hidden -File "C:\Path\To\spotify_launcher.ps1"`
     - Name: "Spotify LyricBar Launcher"
   - Done! It will auto-start when Windows starts

### Method B: Windows Startup Folder (SIMPLER)

1. **Build the executable**
2. Press `Win + R`, type `shell:startup`, press Enter
3. Copy `LyricBar.exe` shortcut into that folder
4. Done! LyricBar starts with Windows

---

## 📚 Detailed Guides

- **`CREATE_EXECUTABLE.md`** - Full PyInstaller guide with troubleshooting
- **`SPICETIFY_INTEGRATION.md`** - Advanced Spicetify integration options
- **`HOW_TO_CHANGE_THEMES.md`** - Theme customization guide

---

## 🛠️ Files Included

### Build Scripts:
- **`build_exe.bat`** - Double-click to build (Windows batch file)
- **`build_exe.ps1`** - PowerShell build script (alternative)
- **`LyricBar.spec`** - PyInstaller configuration

### Launcher Scripts:
- **`spotify_launcher.ps1`** - Auto-start LyricBar with Spotify

---

## ⚡ Quick Troubleshooting

### Build fails
- Make sure you're in the LyricBar folder
- Make sure `.venv` folder exists
- Run: `.venv\Scripts\python.exe -m pip install -r requirements.txt`

### Executable doesn't run
- Make sure `settings.yaml`, `themes/`, and `images/` are in the same folder as the .exe
- Try running from command line to see errors

### Antivirus blocks the .exe
- PyInstaller executables are sometimes flagged as false positives
- Add an exception in your antivirus

### Launcher doesn't find Spotify
- Make sure Spotify is actually running
- Check the PowerShell window for error messages

---

## 🎉 Recommended Setup

For the best experience:

1. ✅ Build the executable using `build_exe.bat`
2. ✅ Move `LyricBar.exe` to a permanent location (e.g., `C:\Program Files\LyricBar\`)
3. ✅ Copy `settings.yaml`, `themes/`, and `images/` to the same folder
4. ✅ Setup auto-launcher with `spotify_launcher.ps1`
5. ✅ Add launcher to Windows startup
6. ✅ Customize themes in `settings.yaml`

Result: 🎵 Automatic synced lyrics every time you play Spotify! No commands needed!

---

Need help? Check the detailed guides or the console output for error messages.
