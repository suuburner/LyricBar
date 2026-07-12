# 🖥️ LyricBar Debug Console

The compiled LyricBar executable now includes a **live debug console** for real-time logging and troubleshooting!

## 🚀 How to Access

### Method 1: Keyboard Shortcut
- **Press `Ctrl + Shift + C`** while LyricBar is running
- Works from anywhere when LyricBar has focus

### Method 2: System Tray Menu
- **Right-click** the LyricBar system tray icon
- Click **"🖥️ Toggle Debug Console (Ctrl+Shift+C)"**

## 📊 What You'll See

When the debug console opens, you'll get:

```
🖥️  LyricBar Debug Console Activated!
📊 Live logging enabled - you'll see all debug info here
🎮 GPU: RTX 4050
⌨️  Press Ctrl+Shift+C to toggle this console
============================================================
INFO:root:=== LYRICBAR STARTING ===
INFO:root:🎯 Setting discrete GPU preference...
INFO:root:🎮 Detected GPU: NVIDIA GeForce RTX 4050 Laptop GPU
INFO:root:✅ NVIDIA RTX GPU available!
INFO:root:🎮 Detected GPU: Intel(R) UHD Graphics
INFO:root:ℹ️  Intel integrated GPU available
INFO:root:Physical DPI: 141.95107844318593
INFO:root:NEW TRACK: Artist - Song [Album] (duration)
INFO:root:Searching for lyrics: Artist - Song from NetEase
INFO:root:✓ LYRICS FOUND from NetEase
INFO:root:SYNCING
...
```

## 🔍 What Gets Logged

- **🎮 GPU Detection**: Which GPU is being used (RTX 4050 vs integrated)
- **🎵 Track Changes**: When songs change and from which app
- **📝 Lyrics Search**: Which providers are being tried and results
- **⚡ Performance Info**: Sync timing, provider switching
- **🐛 Error Messages**: Any crashes or issues in real-time
- **🔧 Settings Changes**: When you change themes, providers, etc.

## 💡 Use Cases

### 🐛 **Debugging Issues**
- Song not detected? Check if app is showing in logs
- Lyrics not loading? See which providers are failing
- App crashing? Get detailed error traces

### ⚡ **Performance Monitoring**
- Verify RTX 4050 is being used
- Check lyrics loading speed
- Monitor provider fallback behavior

### 🎛️ **Settings Verification**
- Confirm provider order changes take effect
- See timing offset adjustments in real-time
- Verify theme caching is working

## 🎯 Tips

1. **Keep Console Open** while using LyricBar to see live updates
2. **Toggle Off** when not needed to save resources
3. **Check GPU Info** on first run to ensure RTX 4050 is active
4. **Monitor Provider Order** when testing settings changes

## 🔄 Toggle Behavior

- **First Press**: Opens debug console window
- **Second Press**: Hides debug console window
- **Toast Notification**: Shows "Debug console toggled!" confirmation

## 🚫 Limitations

- **Only available in compiled executable** (not dev mode)
- **Windows only** (uses Windows console API)
- **Single console** (can't have multiple open)

## 🛠️ Technical Details

- Uses Windows `AllocConsole()` API
- Redirects Python stdout/stderr to console
- Adds console logging handler for real-time output
- Console window is positioned and sized automatically
- Proper cleanup when toggled off

---

**Enjoy debugging with live logging! 🎉**