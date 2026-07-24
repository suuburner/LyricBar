from dataclasses import dataclass
import json
import logging
import os
import re
from pathlib import Path
import syncedlyrics
from PyQt5.QtCore import Qt, QThread, QMutex, pyqtSignal
from pylrc.parser import synced_line_regex, validateTimecode
from syrics.api import Spotify as LyricsSpotify

from ..globalvariables import SP_DC, LYRICS_TIMING_OFFSET
from ..utils.dataclasses import TrackInfo
from ..utils.syncedlyricspatch import *

@dataclass
class LyricLine:
    timestamp: int
    text: str
    end_timestamp: int = -1
    index: int = -1
    begin_time: float = -1

    def __init__(self, timestamp, text, end_timestamp=None, index=None, begin_time=-1):
        self.timestamp = timestamp
        self.text = self.clean_text(text)
        self.end_timestamp = end_timestamp
        self.index = index
        self.begin_time = begin_time
        
    def __lt__(self, other: "LyricLine"):
        return self.timestamp < other.timestamp

    def __eq__(self, other: "LyricLine"):
        if other is None:
            return False
        return self.timestamp == other.timestamp

    def __str__(self):
        return f"{self.timestamp} {self.text}"

    def shift(self, milliseconds=0):
        self.timestamp += milliseconds
        
    @classmethod
    def from_formatted_time(cls, time, text):
        if "." in time:
            minutes, seconds = re.match(r"\[(\d+):(\d+\.\d+)\]", time).groups()
            return cls(int(minutes) * 60000 + float(seconds) * 1000, text)
        else:
            minutes, seconds = re.match(r"\[(\d+):(\d+)\]", time).groups()
            return cls(int(minutes) * 60000 + int(seconds) * 1000, text)
         
    def clean_text(self, text):
        text = text.strip()
        text = text.replace(u"е", "e")
        text = text.replace(u"a", "a")
        return text
    
    def copy(self):
        return LyricLine(self.timestamp, self.text, self.end_timestamp, self.index)
        
@dataclass
class Lyrics:
    lines: list = None
    offset: int = 0
    artist: str = None
    title: str = None
    track_id: str = None
    track: TrackInfo = None
    source: str = None
    _cursor_index: int = -1
    # album: str = ""
    # length: int = 0
    
    def get_line_with_timestamp(self, timestamp):
        if not self.lines:
            self._cursor_index = -1
            return None

        # Use global LYRICS_TIMING_OFFSET (positive = earlier, negative = later)
        adjusted_timestamp = timestamp + LYRICS_TIMING_OFFSET

        # Cursor-based lookup avoids full scans every frame and keeps UI updates tight.
        idx = self._cursor_index
        if idx < 0 or idx >= len(self.lines):
            idx = -1

        # Handle backward seek or rewind.
        if idx >= 0 and int(self.lines[idx].timestamp + self.offset) > adjusted_timestamp:
            while idx >= 0 and int(self.lines[idx].timestamp + self.offset) > adjusted_timestamp:
                idx -= 1
            self._cursor_index = idx
            return self.lines[idx] if idx >= 0 else None

        # Move forward as playback advances.
        while idx + 1 < len(self.lines) and int(self.lines[idx + 1].timestamp + self.offset) <= adjusted_timestamp:
            idx += 1

        self._cursor_index = idx
        return self.lines[idx] if idx >= 0 else None
    
    def get_real_time(self, line):
        line = line.copy()
        line.timestamp += self.offset
        if line.end_timestamp != -1:
            line.end_timestamp += self.offset
        return line
    
    @classmethod
    def from_json(cls, jsn, track: TrackInfo = None):
        lyrics = cls()
        items = []
        
        for idx, line in enumerate(jsn["lyrics"]["lines"]):
            start_time = int(line["startTimeMs"])
            items.append(LyricLine(start_time, line["words"], index=idx))
        lyrics.lines = sorted(items)
        if "offset" in jsn:
            lyrics.offset = jsn["offset"]
        if "source" in jsn:
            lyrics.source = jsn["source"]
        lyrics.track = track
        return lyrics
    
    @classmethod
    def from_lrc(cls, lrc, track: TrackInfo = None):
        lyrics = cls()
        items = []

        for line in lrc.split("\n"):
            if not line:
                continue
            elif line.startswith('[ar:'):
                lyrics.artist = line.rstrip()[4:-1].lstrip()
            elif line.startswith('[ti:'):
                lyrics.title = line.rstrip()[4:-1].lstrip()
            # elif line.startswith('[al:'):
            #     lyrics.album = line.rstrip()[4:-1].lstrip()
            # elif line.startswith('[length:'):
            #     lyrics.length = int(line.rstrip()[8:-1].lstrip())
            elif line.startswith('[offset:'):
                lyrics.offset = int(line.rstrip()[8:-1].lstrip())
            elif synced_line_regex.match(line):
                text = ""
                first = True
                for split in reversed(line.split(']')):
                    if validateTimecode(split + "]"):
                        lyric_line = LyricLine.from_formatted_time(split + "]", text=text)
                        items.append(lyric_line)
                    else:
                        if not first:
                            split += "]"
                        else:
                            first = False
                        text = split + text

        lyrics.lines = sorted(items)
        for idx, l in enumerate(lyrics.lines):
            l.index = idx
        lyrics.track = track
        return lyrics
    
    def to_json_file(self, jsn_file_path):
        jsn = {
            "lyrics": {
                "syncType": "LINE_SYNCED", 
                "lines": [{"startTimeMs": l.timestamp, "words": l.text, "endTimeMs": "0"} for l in self.lines]
            }, 
            "offset": self.offset
        }
        if self.source:
            jsn["source"] = self.source
        json.dump(jsn, open(jsn_file_path, "w", encoding="utf-8"), ensure_ascii=False)


class LyricsProvider:
    def __init__(self):
        pass
    def get_lyrics(self, track: TrackInfo) -> Lyrics:
        pass
    
class FromSpotify(LyricsProvider):
    def __init__(self, sp_dc):
        self._pvd = None
        self.sp_dc = sp_dc
        
    @property
    def pvd(self):
        if self._pvd is None:
            self._pvd = LyricsSpotify(self.sp_dc)
        return self._pvd
    
    def get_lyrics(self, track: TrackInfo) -> Lyrics:
        if track.id is None:
            return None
        lyrics = None
        try:
            lyrics = self.pvd.get_lyrics(track.id)
        except Exception as e:
            logging.error(e)
        if (lyrics is None) or ("lyrics" not in lyrics) or ("syncType" not in lyrics["lyrics"]) or (lyrics["lyrics"]["syncType"] != "LINE_SYNCED"):
            return None
        return Lyrics.from_json(lyrics, track)
        
class FromThirdParty(LyricsProvider):
    def __init__(self, third_parties=["Lrclib", "NetEase", "Musixmatch"]):
        self.third_parties = third_parties
    
    def get_lyrics(self, track: TrackInfo) -> Lyrics:
        lrc = None
        try:
            lrc = syncedlyrics.search(track, allow_plain_format=False, providers=self.third_parties, enhanced=False)
        except Exception as e:
            logging.error(e)
        if lrc is None:
            return None
        lyrics = Lyrics.from_lrc(lrc, track)
        if lyrics.artist is not None and lyrics.artist!= track.artist or lyrics.title is not None and lyrics.title!= track.title:
            return None
        return lyrics

class LyricsThread(QThread):
    result_ready = pyqtSignal(object)

    def __init__(self, maintainer, track, holder, callback=None, holder_lock=None, force_refresh=False, source=None):
        super().__init__()
        self.maintainer = maintainer
        self.track = track
        self.force_refresh = force_refresh
        self.source = source
        self.callback = callback
        self.holder = holder
        self.holder_lock = holder_lock
        self.get_lock = False
        self.cancelled = False
        self._cleanup_started = False
        self.result_ready.connect(self._forward_result, type=Qt.QueuedConnection)
        self.finished.connect(self.deleteLater, type=Qt.QueuedConnection)

    def _forward_result(self, payload):
        if self.callback is None:
            return
        try:
            self.callback(payload)
        except Exception as exc:
            logging.exception("Lyrics callback failed: %s", exc)
        
    def cancel(self):
        self.cancelled = True
        
    def gracefully_out(self):
        if self._cleanup_started:
            return
        self._cleanup_started = True

        if self.holder is not None:
            self.holder_lock.lock()
            try:
                if self in self.holder:
                    self.holder.remove(self)
            finally:
                self.holder_lock.unlock()
        return

    def run(self):
        # print("TRYING SEARCH", self.track)
        # while self.waiting_counter < 50 and not self.lock.tryLock(100):
        #     self.waiting_counter += 1
        #     if self.cancelled:
        #         self.gracefully_out()
        #         return
        # if self.waiting_counter >= 50:
        #     self.gracefully_out()
        #     return
        # print("STARTING SEARCH", self.track)
        # self.get_lock = True
        if self.cancelled:
            self.gracefully_out()
            return
        cache_dir = Path(self.maintainer.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        ret = None
        if not self.force_refresh and not self.source:
            cache_candidates = []
            if self.track.id is not None:
                cache_candidates.append(cache_dir / f"{self.track.id}.json")
            cache_candidates.append(cache_dir / f"{self.track.hash_id}.json")
            for cache_path in cache_candidates:
                if not cache_path.exists():
                    continue
                try:
                    with cache_path.open("r", encoding="utf-8") as handle:
                        jsn = json.load(handle)
                except Exception as exc:
                    logging.warning("Failed to load cached lyrics from %s: %s", cache_path, exc)
                    continue
                if jsn is not None and "lyrics" in jsn and "syncType" in jsn["lyrics"] and jsn["lyrics"]["syncType"] == "LINE_SYNCED":
                    ret = Lyrics.from_json(jsn, self.track)
                    if ret and not ret.source:
                        ret.source = "Cache"
                    if self.cancelled:
                        self.gracefully_out()
                        return
                    if self.callback is not None:
                        self.result_ready.emit((ret, self.track))
                        self.gracefully_out()
                    return
                if jsn is not None and "lyrics" in jsn and "syncType" in jsn["lyrics"] and jsn["lyrics"]["syncType"] == "LINE_SYNCED":
                    ret = Lyrics.from_json(jsn, self.track)
                    if ret and not ret.source:
                        ret.source = "Cache"
                    if self.cancelled:
                        self.gracefully_out()
                        return
                    if self.callback is not None:
                        self.result_ready.emit((ret, self.track))
                        self.gracefully_out()
                    return
        if self.cancelled:
            self.gracefully_out()
            return
        if self.source is None:
            self.source = list(self.maintainer.providers.keys())
        elif isinstance(self.source, str):
            self.source = [self.source if self.source in self.maintainer.providers else None]
        else:
            self.source = [s if s in self.maintainer.providers else None for s in self.source]
        for name in self.source:
            if self.cancelled:
                self.gracefully_out()
                return
            provider = self.maintainer.providers[name]
            logging.info(f"Searching for lyrics: {self.track.artist} - {self.track.title} from {name}")
            lyrics = provider.get_lyrics(self.track)
            if lyrics is not None:
                self.maintainer.save_lyrics(self.track, lyrics)
                lyrics.source = name
                ret = lyrics
            if ret is not None:
                logging.info(f"✓ LYRICS FOUND from {name}")
                break
            else:
                logging.info(f"✗ No lyrics found from {name}, trying next provider...")
        
        if ret is None:
            logging.warning(f"✗ No lyrics found for '{self.track.artist} - {self.track.title}' from any provider")
        
        if self.cancelled:
            self.gracefully_out()
            return
        if self.callback is not None:
            self.result_ready.emit((ret, self.track))
        self.gracefully_out()
        
        
class LyricsManager():
    def __init__(self, cache_dir="lyrics", providers=[]):
        self.cache_dir = str(Path(cache_dir).expanduser())
        if not Path(self.cache_dir).is_absolute():
            self.cache_dir = str((Path.cwd() / self.cache_dir).resolve())
        self.providers = providers
        self.getter = None
        
        self.lyrics_gripper = set()
        self.lyrics_track = None
        self.last_search_track = None
        self.last_search_time = 0
        
        self.gripper_lock = QMutex()
    
    def get_lyrics(self, track: TrackInfo, callback: callable = None, force_refresh=False, source=None):
        # print("GETTING LYRICS FOR ", str(track), "FROM ", source)
        
        # Prevent duplicate searches within 500ms for same track
        import time
        current_time = time.time() * 1000
        if (not force_refresh and 
            self.last_search_track == track and 
            current_time - self.last_search_time < 500):
            return
        
        found = False
        for lg in self.lyrics_gripper:
            if lg.track == track and lg.source == source and not lg.cancelled:
                found = True
            else:
                lg.cancel()
        if found:
            return
        
        # Update search tracking
        self.last_search_track = track
        self.last_search_time = current_time
        
        lg = LyricsThread(self, track, self.lyrics_gripper, callback, self.gripper_lock, force_refresh, source)
        self.lyrics_gripper.add(lg)
        # lg.start_signal.emit()
        lg.start()
        # print("command sent")
    
    def cleanup(self):
        """Cancel all running threads and clean up resources"""
        self.gripper_lock.lock()
        threads_to_cleanup = list(self.lyrics_gripper)
        self.lyrics_gripper.clear()  # Clear the set first
        self.gripper_lock.unlock()

        for lg in threads_to_cleanup:
            lg.cancel()

        for lg in threads_to_cleanup:
            if lg.isRunning():
                lg.wait(1000)

        for lg in threads_to_cleanup:
            if lg.isRunning():
                logging.warning("Lyrics thread did not stop in time; terminating it")
                lg.terminate()
                lg.wait(1000)

        self.last_search_track = None
        self.last_search_time = 0
        
    def save_lyrics(self, track: TrackInfo, lyrics: Lyrics):
        cache_dir = Path(self.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        if lyrics is None:
            with (cache_dir / f"{track.hash_id}.json").open("w", encoding="utf-8") as handle:
                json.dump({}, handle, ensure_ascii=False)
            return
        if track.id is not None:
            lyrics.to_json_file(str(cache_dir / f"{track.id}.json"))
        lyrics.to_json_file(str(cache_dir / f"{track.hash_id}.json"))
        # pass
    # def get_lyrics_async(self, track: TrackInfo, callback: callable = None, force_refresh=False, source=None):
    #     while self.gripper_cancelled:
    #         asyncio.sleep(0.5)
    #     if not os.path.exists(self.cache_dir):
    #         os.makedirs(self.cache_dir)
    #     ret = None
    #     if not force_refresh and not source:
    #         if track.id is not None and os.path.exists(f"{self.cache_dir}/{track.id}.json"):
    #             jsn = json.load(open(f"{self.cache_dir}/{track.id}.json", "r", encoding="utf-8"))
    #             if jsn is not None and "lyrics" in jsn and "syncType" in jsn["lyrics"] and jsn["lyrics"]["syncType"] == "LINE_SYNCED":
    #                 ret = Lyrics.from_json(jsn, track)    
    #                 if callback is not None:
    #                     callback(ret)
    #                 return ret
    #         if os.path.exists(f"{self.cache_dir}/{track.hash_id}.json"):
    #             jsn = json.load(open(f"{self.cache_dir}/{track.hash_id}.json", "r", encoding="utf-8"))
    #             if jsn is not None and "lyrics" in jsn and "syncType" in jsn["lyrics"] and jsn["lyrics"]["syncType"] == "LINE_SYNCED":
    #                 ret = Lyrics.from_json(jsn, track)
    #                 if callback is not None:
    #                     callback(ret)
    #                 return ret
    #     if self.gripper_cancelled:
    #         self.gripper_cancelled = False
    #         return
    #     if source is None:
    #         source = list(self.providers.keys())
    #     elif isinstance(source, str):
    #         source = [source if source in self.providers else None]
    #     else:
    #         source = [s if s in self.providers else None for s in source]
    #     print("Fetching lyrics from ", source)
    #     for name in source:
    #         if self.gripper_cancelled:
    #             self.gripper_cancelled = False
    #             return
    #         print("Trying ", name)
    #         provider = self.providers[name]
    #         lyrics = provider.get_lyrics(track)
    #         if lyrics is not None:
    #             self.save_lyrics(track, lyrics)
    #             lyrics.source = name
    #             ret = lyrics
    #         if ret is not None:
    #             logging.info(f"LYRICS FOUND: {track.artist} - {track.title} from {provider.__class__.__name__}")
    #             break
    #     if self.gripper_cancelled:
    #         self.gripper_cancelled = False
    #         return
    #     if callback is not None:
    #         callback(ret)
    #     return ret
                
if __name__ == "__main__":
    lm = LyricsManager(providers=[FromSpotify(SP_DC), FromThirdParty()])
    breakpoint()