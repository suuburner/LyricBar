import logging
from PyQt5.QtCore import QMutex
from LyricBar.config import settings, resource_path
from LyricBar.backend.lyricmanager import FromSpotify, FromThirdParty, LyricLine, Lyrics, LyricsManager
from LyricBar.nowplaying import NowPlayingSystem, NowPlayingSpicetify
from LyricBar.utils.dataclasses import PlayingStatusTrigger
from LyricBar.themes import STYLES, get_style

logger = logging.getLogger(__name__)


class LyricsMaintainer():
    def __init__(self, now_playing, update_callback=None):
        super().__init__()
        
        self.update_callback = update_callback

        self.providers = {}
        if settings.use_spotify_lyrics:
            self.providers["Spotify"] = FromSpotify(settings.sp_dc)
        for provider in settings.third_party_lyrics_providers:
            self.providers[provider] = FromThirdParty([provider])

        self.manager = LyricsManager(
            providers=self.providers,
            cache_dir=resource_path(settings.lyric_folder),
        )

        self.lyrics = None
        self.callback_mutex = QMutex()
        self.lyrics_mutex = QMutex()
        
        self.current_line = None
        self._last_blocked_reason = None  # diagnostics: avoid log spam in `line`
        
        self.stopped = False  # MUST be set BEFORE register_callback
        
        self.now_playing = now_playing
        self.now_playing.register_callback(self.manager_callback)
        
    def start(self):
        self.stopped = False
        self.now_playing.activate(self.manager_callback)
    
    def pause(self):
        self.stopped = True
        self.lyrics = None
        self.manager.cleanup()
    
    @property
    def line(self):
        # Never block UI thread here; keep previous line if writer holds lock briefly.
        if not self.lyrics_mutex.tryLock(0):
            return self.current_line
            
        try:
            if not self.now_playing.has_lyrics:
                self._log_blocked_once("has_lyrics is False (no result set yet, or search failed/hasn't started)")
                return None  # Hide bar when no lyrics found
                
            if not self.lyrics:
                # Inconsistent state: has_lyrics=True but lyrics=None/empty.
                logger.warning("Inconsistent lyrics state detected - resetting has_lyrics to False")
                self.now_playing.has_lyrics = False
                return None  # Hide bar instead of showing sync symbol
                
            if not self.now_playing.is_playing:
                self._log_blocked_once("now_playing.is_playing is False")
                return None
                
            if not self.now_playing.current_begin_time:
                self._log_blocked_once("now_playing.current_begin_time is falsy (no timeline yet)")
                return None
                
            try:
                l = self.lyrics.get_line_with_timestamp(self.now_playing.progress)
                if l:
                    self._last_blocked_reason = None
                    self.current_line = l
                    l.end_timestamp = self.lyrics.lines[l.index + 1].timestamp if l.index < len(self.lyrics.lines) - 1 else -1
                    l = self.lyrics.get_real_time(l)
                    l.begin_time = (self.now_playing.current_begin_time or 0) + l.timestamp
                    return l
                else:
                    self._log_blocked_once(
                        f"get_line_with_timestamp({self.now_playing.progress:.0f}) returned None "
                        f"(lyrics has {len(self.lyrics.lines or [])} lines, first starts at "
                        f"{self.lyrics.lines[0].timestamp if self.lyrics.lines else 'n/a'})"
                    )
                    
            except Exception as e:
                logger.error(f"Error getting lyrics line: {e}")
                # Reset lyrics if corrupted
                self.lyrics = None
                self.now_playing.has_lyrics = False
            
            return None  # Hide bar instead of showing ♬ when no valid line found
            
        finally:
            # Always unlock in finally block to prevent deadlocks
            self.lyrics_mutex.unlock()

    def _log_blocked_once(self, reason):
        """Log why `line` returned None, but only on change, so this doesn't spam
        the console at the 16ms UI refresh rate."""
        if reason != self._last_blocked_reason:
            logger.info(f"[lyrics display blocked] {reason}")
            self._last_blocked_reason = reason
    
    def manager_callback(self, value):
        if self.stopped:
            return
        if not self.callback_mutex.tryLock(0):
            return
        if value == PlayingStatusTrigger.NEW_TRACK:
            # Reset lyrics state for the new track. The actual search is triggered
            # once, from the UI layer (handleTrackChange), which also owns the
            # lyrics_search_in_progress flag and needs to know when the result lands.
            self.lyrics = None
            self.current_line = None
            self.now_playing.has_lyrics = False
            self._last_blocked_reason = None  # let diagnostics re-report for the new track
            self.callback_mutex.unlock()
            return
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
        logger.debug("Lyric offset updated: %s", self.lyrics.offset)
        self.manager.save_lyrics(self.lyrics.track, self.lyrics)
        self.lyrics_mutex.unlock()

    
    def set_lyrics(self, value, track=None, check_first=False):
        logger.info(
            f"set_lyrics called: value={'Lyrics(%d lines, source=%s)' % (len(value.lines or []), value.source) if value else None}, "
            f"track={track}, current_track={self.now_playing.current_track}"
        )
        if check_first and not value:
            return
        if track is not None:
            if self.now_playing.current_track != track:
                logger.warning(
                    f"set_lyrics REJECTED: track mismatch. search was for {track!r}, "
                    f"now_playing.current_track is {self.now_playing.current_track!r}"
                )
                return
        
        # Use timeout lock to prevent deadlocks
        if not self.lyrics_mutex.tryLock(500):  # Reduced timeout for faster response
            logger.warning("Could not acquire lyrics mutex in set_lyrics - skipping update")
            return
            
        try:
            self.lyrics = value
            if not self.lyrics:
                logger.info("LYRICS NOT FOUND")
                self.now_playing.has_lyrics = False
            else:
                self.now_playing.has_lyrics = True
                if self.lyrics.source:
                    self.update_callback("Lyrics from " + self.lyrics.source)
        finally:
            self.lyrics_mutex.unlock()
        logger.debug(
            "Lyrics set for %s: %s", self.now_playing.current_track, self.lyrics is not None
        )