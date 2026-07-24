import logging
import sys
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QMutex
from LyricBar.globalvariables import (
    GLOBAL_OFFSET,
    PLAYING_INFO_PROVIDER,
    SP_DC,
    SPICETIFY_PORT,
    THIRD_PARTY_LYRICS_PROVIDERS,
    USE_SPOTIFY_LYRICS,
    LYRIC_FOLDER,
    resource_path,
)
from LyricBar.backend.lyricmanager import FromSpotify, FromThirdParty, LyricLine, Lyrics, LyricsManager
from LyricBar.nowplaying import NowPlayingSystem, NowPlayingSpicetify
from LyricBar.utils.dataclasses import PlayingStatusTrigger
from LyricBar.themes import STYLES, get_style


# class debugQMutex(QMutex):
#     def tryLock(self, timeout=0):
#         ret = super().tryLock(timeout)
#         print("TRY LOCK: ", ret)
#         return ret
#     def unlock(self):
#         print("UNLOCK")
#         return super().unlock()


class LyricsMaintainer():
    def __init__(self, now_playing, update_callback=None):
        super().__init__()
        
        self.update_callback = update_callback

        # if PLAYING_INFO_PROVIDER == "Spotify":
        #     self.now_playing = NowPlayingSpotify(update_callback=self.update_lyrics)
        # elif PLAYING_INFO_PROVIDER == "System":
        #     self.now_playing = NowPlayingSystem(update_callback=self.update_lyrics)
        # else:
        #     NowPlayingMixed(update_callback=self.update_lyrics)
        
        self.providers = {}
        if USE_SPOTIFY_LYRICS:
            self.providers["Spotify"] = FromSpotify(SP_DC)
        if THIRD_PARTY_LYRICS_PROVIDERS and THIRD_PARTY_LYRICS_PROVIDERS != []:
            for provider in THIRD_PARTY_LYRICS_PROVIDERS:
                self.providers[provider] = FromThirdParty([provider])
        
        self.manager = LyricsManager(
            providers=self.providers,
            cache_dir=resource_path(LYRIC_FOLDER),
        )
        
        
        
        self.lyrics = None
        # self.style = STYLES["default"]
        # self.style["name"] = "default"
        
        self.callback_mutex = QMutex()
        self.lyrics_mutex = QMutex()
        
        self.current_line = None
        
        self.stopped = False  # MUST be set BEFORE register_callback
        
        self.now_playing = now_playing
        self.now_playing.register_callback(self.manager_callback)
        
    # def start(self):
    #     self.now_playing.start_loop()
    
    def start(self):
        self.stopped = False
        self.now_playing.activate(self.manager_callback)
    
    def pause(self):
        self.stopped = True
        self.lyrics = None
        self.manager.cleanup()
    
    @property
    def line(self):
        # # print(self.now_playing.__dict__)
        # print("has lyrics?", self.now_playing.has_lyrics)
        
        # Never block UI thread here; keep previous line if writer holds lock briefly.
        if not self.lyrics_mutex.tryLock(0):
            return self.current_line
            
        try:
            if not self.now_playing.has_lyrics:
                return None  # Hide bar when no lyrics found
                
            if not self.lyrics and self.now_playing.has_lyrics:
                # Inconsistent state: has_lyrics=True but lyrics=None
                # This causes infinite sync symbol - reset the state
                logging.warning("Inconsistent lyrics state detected - resetting has_lyrics to False")
                self.now_playing.has_lyrics = False
                return None  # Hide bar instead of showing sync symbol
                
            if not self.lyrics:
                return None  # Hide bar when no lyrics found (was showing ♬ before)
                
            if not self.now_playing.is_playing:
                return None
                
            if not self.now_playing.current_begin_time:
                return None
                
            try:
                l = self.lyrics.get_line_with_timestamp(self.now_playing.progress)
                if l:
                    self.current_line = l
                    l.end_timestamp = self.lyrics.lines[l.index + 1].timestamp if l.index < len(self.lyrics.lines) - 1 else -1
                    l = self.lyrics.get_real_time(l)
                    l.begin_time = (self.now_playing.current_begin_time or 0) + l.timestamp
                    return l
                    
            except Exception as e:
                logging.error(f"Error getting lyrics line: {e}")
                # Reset lyrics if corrupted
                self.lyrics = None
                self.now_playing.has_lyrics = False
            
            return None  # Hide bar instead of showing ♬ when no valid line found
            
        finally:
            # Always unlock in finally block to prevent deadlocks
            self.lyrics_mutex.unlock()
    
    def manager_callback(self, value):
        if self.stopped:
            return
        if not self.callback_mutex.tryLock(0):
            # print("UPDATING SKIPPED")
            return
        if value == PlayingStatusTrigger.NEW_TRACK:
            self.lyrics = None
            self.current_line = None
            self.now_playing.has_lyrics = False
            if self.now_playing.current_track.artist == "" or self.now_playing.current_track.title == "":
                self.callback_mutex.unlock()
                return
            # if self.update_callback is not None:
            #     self.update_callback(value)
            self.manager.get_lyrics(self.now_playing.current_track, lambda x: self.set_lyrics(*x))
            self.callback_mutex.unlock()
            return
        # if self.update_callback is not None:
        #     self.update_callback(value)
        self.callback_mutex.unlock()
        return
        
    def next_source(self):
        self.now_playing.has_lyrics = True
        if not self.now_playing.is_playing:
            return
        current_source = self.lyrics.source if self.lyrics else None
        next_source = None
        if current_source is None or current_source == "Cache":
            # If no source or from cache, start with first provider
            next_source = list(self.providers.keys())
        else:
            try:
                current_idx = list(self.providers.keys()).index(current_source)
                next_source = list(self.providers.keys())
                next_source = next_source[(current_idx + 1) % len(self.providers):] + next_source[:(current_idx + 1) % len(self.providers)]
            except ValueError:
                # Source not in list (shouldn't happen but just in case)
                next_source = list(self.providers.keys())
        return next_source
    
    def get_from_next_source(self):
        next_source = self.next_source()
        # Force refresh to skip cache when switching providers manually
        self.manager.get_lyrics(self.now_playing.current_track, lambda x: self.set_lyrics(*x, check_first=True), force_refresh=True, source=next_source)
        
    def set_empty_lyrics(self):
        self.lyrics = Lyrics([])
        self.lyrics.track = self.now_playing.current_track
        self.now_playing.has_lyrics = True
        self.manager.save_lyrics(self.now_playing.current_track, self.lyrics)
    
    @property
    def track_offset(self):
        if not self.lyrics_mutex.tryLock(100):
            return 0
        try:
            if not self.now_playing.has_lyrics or not self.lyrics:
                return 0
            offset = self.lyrics.offset
            return offset
        finally:
            self.lyrics_mutex.unlock()
    
    @track_offset.setter
    def track_offset(self, value):
        if not self.lyrics_mutex.tryLock(0):
            return
        if not self.now_playing.has_lyrics or not self.lyrics:
            self.lyrics_mutex.unlock()
            return
        self.lyrics.offset = value
        # print("LYRIC OFFSET UPDATED: ", self.lyrics.offset)
        self.manager.save_lyrics(self.lyrics.track, self.lyrics)
        self.lyrics_mutex.unlock()

    
    def set_lyrics(self, value, track=None, check_first=False):
        if check_first and not value:
            return
        if track is not None:
            if self.now_playing.current_track != track:
                return
        
        # Use timeout lock to prevent deadlocks
        if not self.lyrics_mutex.tryLock(500):  # Reduced timeout for faster response
            logging.warning("Could not acquire lyrics mutex in set_lyrics - skipping update")
            return
            
        try:
            self.lyrics = value
            if not self.lyrics:
                logging.info("LYRICS NOT FOUND")
                self.now_playing.has_lyrics = False
            else:
                self.now_playing.has_lyrics = True
                if self.lyrics.source:
                    self.update_callback("Lyrics from " + self.lyrics.source)
        finally:
            self.lyrics_mutex.unlock()
        # print("SET LYRICS: ", self.now_playing.current_track, self.lyrics is not None)

        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    lm = LyricsMaintainer()
    breakpoint()
    sys.exit(app.exec_())