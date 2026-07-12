# 🚀 Creating a Standalone Executable for LyricBar

## Option 1: Using PyInstaller (Recommended)

PyInstaller bundles your Python application into a standalone executable with all dependencies included.

### Step 1: Install PyInstaller

```powershell
C:/Users/Swopnil/Downloads/Compressed/LyricBar/.venv/Scripts/python.exe -m pip install pyinstaller
```

### Step 2: Create the Executable

Navigate to the LyricBar folder and run:

```powershell
cd C:\Users\Swopnil\Downloads\Compressed\LyricBar
.venv\Scripts\python.exe -m PyInstaller --name="LyricBar" --onefile --windowed --icon="resources/icon.ico" main.py
```

**Parameters explained:**
- `--name="LyricBar"` - Name of the executable
- `--onefile` - Creates a single .exe file (easier to distribute)
- `--windowed` - No console window (cleaner for GUI apps)
- `--icon="resources/icon.ico"` - Sets the application icon

### Step 3: Include Required Files

PyInstaller might miss some files. Create a file called `LyricBar.spec` with this content:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('themes', 'themes'),
        ('resources', 'resources'),
        ('images', 'images'),
        ('settings.yaml', '.'),
        ('webnowplaying.js', '.'),
    ],
    hiddenimports=[
        'winrt.windows.media.control',
        'winrt.windows.foundation',
        'winrt.windows.foundation.collections',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LyricBar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)
```

Then build with the spec file:

```powershell
.venv\Scripts\python.exe -m PyInstaller LyricBar.spec
```

### Step 4: Find Your Executable

After building, you'll find:
- **Single file version**: `dist/LyricBar.exe`

### Step 5: Test the Executable

1. Copy `LyricBar.exe` from the `dist` folder to wherever you want
2. Make sure `settings.yaml`, `themes/`, and `images/` folders are in the same directory
3. Double-click `LyricBar.exe` to run!

---

## Option 2: Auto-Start with Windows

Once you have the executable, make it start automatically:

### Method 1: Windows Startup Folder

1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. Create a shortcut to `LyricBar.exe` in this folder
4. Done! It will start automatically when Windows starts

### Method 2: Task Scheduler (More Control)

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Task** (not Basic Task)
3. **General Tab:**
   - Name: "LyricBar"
   - Check "Run with highest privileges"
4. **Triggers Tab:**
   - New → Begin task: "At log on"
   - Click OK
5. **Actions Tab:**
   - New → Action: "Start a program"
   - Program/script: Browse to `LyricBar.exe`
   - Start in: The folder containing LyricBar.exe
6. **Conditions Tab:**
   - Uncheck "Start the task only if the computer is on AC power"
7. Click OK

---

## Troubleshooting

### Issue: "Failed to execute script"
**Solution:** The .exe might be missing data files. Make sure these are in the same folder:
- `settings.yaml`
- `themes/` folder
- `images/` folder
- `resources/` folder (if using icons)

### Issue: Antivirus flags the .exe
**Solution:** PyInstaller executables are sometimes flagged. Add an exception in your antivirus or:
1. Use `--debug` flag to see what's wrong
2. Try building without `--onefile` (creates a folder with dependencies)

### Issue: Application crashes silently
**Solution:** Build without `--windowed` to see error messages:
```powershell
.venv\Scripts\python.exe -m PyInstaller --name="LyricBar" --onefile --icon="resources/icon.ico" main.py
```

---

## Advanced: Distribution Package

To share with others, create a folder structure:

```
LyricBar/
├── LyricBar.exe
├── settings.yaml
├── themes/
│   ├── Default.py
│   └── Artists/
│       └── (all artist themes)
├── images/
│   └── (all image files)
└── README.txt
```

Zip this folder and share! Users just extract and run `LyricBar.exe`.

---

## Performance Tips

### Faster Startup
Use `--onefile` for convenience, but for faster startup, use `--onedir`:
```powershell
.venv\Scripts\python.exe -m PyInstaller --name="LyricBar" --onedir --windowed --icon="resources/icon.ico" main.py
```

This creates a folder with the .exe and dependencies. Startup is much faster.

### Reduce File Size
Add to the spec file to exclude unused modules:
```python
excludes=['matplotlib', 'scipy', 'pandas', 'notebook', 'IPython']
```

---

## Next Steps

Once you have a working .exe:

1. ✅ Create a desktop shortcut
2. ✅ Add to Windows startup
3. ✅ Customize your settings.yaml
4. ✅ Enjoy automatic lyrics!

Would you like me to create the actual build script for you?
