import asyncio
import logging

from .nowplaying import NowPlaying
from .nowplayingspotify import NowPlayingSpotify
from .nowplayingsystem import NowPlayingSystem

logger = logging.getLogger(__name__)


class NowPlayingMixed(NowPlaying):
    def __init__(self, sync_interval=50, update_callback=None):
        super().__init__(sync_interval, update_callback)
        self.system = NowPlayingSystem(-1, update_callback)
        self.spotify = NowPlayingSpotify(-1, update_callback)
        self.system_begin_time = None
        self.synced_with_spotify = False

    def update_check(self, old_playing_info, new_playing_info):
        if old_playing_info is None:
            return True
        if new_playing_info.is_playing != old_playing_info.is_playing:
            return True
        if (
            new_playing_info.current_track_artist
            != old_playing_info.current_track_artist
        ):
            return True
        if new_playing_info.current_track_title != old_playing_info.current_track_title:
            return True
        if new_playing_info.progress != old_playing_info.progress:
            return True
        return False

    def track_check(self, old_playing_info, new_playing_info):
        if old_playing_info is None or new_playing_info is None:
            return True
        if old_playing_info.current_track == new_playing_info.current_track:
            if old_playing_info.current_track_id is not None:
                new_playing_info.current_track_id = old_playing_info.current_track_id
            return False
        return True

    def sync(self):
        logger.debug("Attempting sync with system media session")
        if not self.sync_mutex.tryLock(0):
            logger.debug("Sync skipped: previous sync still in progress")
            return
        info = asyncio.run(self.system.get_now_playing_info())
        if info is None:
            self.sync_mutex.unlock()
            return
        if not info.is_playing:
            logger.debug("Playback paused")
            self.playing_info = info
            if self.update_callback is not None:
                self.update_callback(self.playing_info)
            self.sync_mutex.unlock()
            return
        if self.track_check(self.playing_info, info):
            logger.debug("New track: %s", info.current_track)
            self.playing_info = info
            self.synced_with_spotify = False
        if not self.synced_with_spotify:
            logger.debug("Trying to sync with Spotify Web API to get track id")
            onlineinfo = asyncio.run(self.spotify.get_now_playing_info())
            if onlineinfo is None or onlineinfo.current_track_id is None:
                self.synced_with_spotify = False
                logger.debug("Failed to sync with Spotify Web API")
                self.sync_mutex.unlock()
                return
            if self.playing_info.current_track != onlineinfo.current_track:
                self.synced_with_spotify = False
                logger.debug("Spotify Web API not updated yet")
                self.sync_mutex.unlock()
                return
            self.playing_info.current_track_id = onlineinfo.current_track_id
            self.synced_with_spotify = True
            logger.debug("Synced track id via Spotify Web API: %s", info.current_track)
            if self.update_callback is not None:
                self.update_callback(self.playing_info)
        elif self.system.update_check(self.playing_info, info):
            logger.debug("Syncing")
            self.playing_info = info
        self.sync_mutex.unlock()