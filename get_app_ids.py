"""
Script to find Windows Media App IDs for tracking in LyricBar
Run this while your media apps are playing music to see their IDs
"""

import asyncio
import sys

# Use winrt instead of winsdk
try:
    from winrt.windows.media.control import \
        GlobalSystemMediaTransportControlsSessionManager as MediaManager
except ImportError:
    print("Error: Required Windows modules not installed!")
    print("Please run: pip install winrt-Windows.Media.Control")
    sys.exit(1)

async def get_media_app_ids():
    manager = await MediaManager.request_async()
    sessions = manager.get_sessions()
    
    if not sessions:
        print("No media apps currently running or playing!")
        print("Start playing music in your app and run this script again.")
        return
    
    print("Found active media sessions:\n")
    print("=" * 80)
    
    for i, session in enumerate(sessions, 1):
        app_id = session.source_app_user_model_id
        
        # Try to get current track info
        try:
            info = await session.try_get_media_properties_async()
            title = info.title if info else "N/A"
            artist = info.artist if info else "N/A"
        except Exception:
            title = "N/A"
            artist = "N/A"
        
        print(f"Session {i}:")
        print(f"  App ID: {app_id}")
        print("  Currently Playing:")
        print(f"    Title:  {title}")
        print(f"    Artist: {artist}")
        print("-" * 80)
    
    print("\nTo add an app to LyricBar:")
    print("1. Copy the 'App ID' from above")
    print("2. Open settings.yaml")
    print("3. Add it to the 'Tracking App' list")
    print("\nExample:")
    print("  Tracking App:")
    print("    - Spotify.exe")
    print("    - YourAppID.exe")

if __name__ == "__main__":
    asyncio.run(get_media_app_ids())
