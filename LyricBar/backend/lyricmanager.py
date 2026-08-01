from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)
import os
import re
from pathlib import Path
import syncedlyrics
from PyQt5.QtCore import Qt, QThread, QMutex, pyqtSignal
from pylrc.parser import synced_line_regex, validateTimecode
from syrics.api import Spotify as LyricsSpotify

from ..config import settings
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
        text = text.replace(u"е", "e")  # Cyrillic 'е' (U+0435) -> Latin 'e'
        text = text.replace(u"а", "a")  # Cyrillic 'а' (U+0430) -> Latin 'a'
        return text

    def copy(self):
        return LyricLine(self.timestamp, self.text, self.end_timestamp, self.index)

@dataclass
class Lyrics:
    lines: list = None
    offset: int = 0
    track_offset: int = 0
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

        # Read live from settings (positive = earlier, negative = later) so a
        # timing-offset change from the settings dialog takes effect immediately,
        # instead of the value being frozen to whatever it was at import time.
        adjusted_timestamp = timestamp + settings.global_offset + self.track_offset

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
        line.timestamp += self.offset - self.track_offset
        if line.end_timestamp != -1:
            line.end_timestamp += self.offset - self.track_offset
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
        except Exception:
            logger.exception("FromSpotify lyrics lookup failed")
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
        except Exception:
            logger.exception("Third-party lyrics search failed")
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
        self.finished.connect(self._remove_from_holder, type=Qt.QueuedConnection)
        self.finished.connect(self.deleteLater, type=Qt.QueuedConnection)

    def _forward_result(self, payload):
        if self.callback is None:
            return
        try:
            self.callback(payload)
        except Exception:
            logger.exception("Lyrics callback failed")

    def cancel(self):
        self.cancelled = True

    def gracefully_out(self):
        # Just marks intent to stop; NOT safe to touch self.holder here since
        # this runs on the worker thread, inside run() itself. Removing self
        # from self.holder here would drop the only Python reference keeping
        # this QThread alive, deallocating it mid-run() (a real source of the
        # "crash on thread destruction" issue) and silently dropping any
        # already-queued result_ready signal before it can be delivered.
        # The actual holder cleanup happens in _remove_from_holder, once
        # `finished` fires on the main thread after run() has truly ended.
        if self._cleanup_started:
            return
        self._cleanup_started = True
        return

    def _remove_from_holder(self):
        if self.holder is None:
            return
        self.holder_lock.lock()
        try:
            if self in self.holder:
                self.holder.remove(self)
        finally:
            self.holder_lock.unlock()

    def run(self):
        try:
            self._run()
        except Exception:
            logger.exception(
                f"LyricsThread crashed while searching for {self.track.artist} - {self.track.title}"
            )
            self.gracefully_out()

    def _run(self):
        logger.debug("LyricsThread started for %s - %s (source=%s)", self.track.artist, self.track.title, self.source)
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
                        logger.debug("LyricsThread cancelled after cache hit, before emit")
                        self.gracefully_out()
                        return
                    logger.info("Lyrics found for %s - %s (cached, %d lines)", self.track.artist, self.track.title, len(ret.lines or []))
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
        tried = []
        for name in self.source:
            if self.cancelled:
                self.gracefully_out()
                return
            provider = self.maintainer.providers[name]
            logger.debug("Searching for lyrics: %s - %s from %s", self.track.artist, self.track.title, name)
            tried.append(name)
            lyrics = provider.get_lyrics(self.track)
            if lyrics is not None:
                self.maintainer.save_lyrics(self.track, lyrics)
                lyrics.source = name
                ret = lyrics
            if ret is not None:
                break

        if ret is not None:
            logger.info("Lyrics found for %s - %s (via %s)", self.track.artist, self.track.title, ret.source)
        else:
            logger.info(
                "No lyrics found for %s - %s (tried: %s)",
                self.track.artist, self.track.title, ", ".join(tried) or "no providers configured",
            )

        if self.cancelled:
            logger.debug("LyricsThread cancelled for %s - %s, before emit", self.track.artist, self.track.title)
            self.gracefully_out()
            return
        logger.debug(
            "LyricsThread emitting result for %s - %s: %s",
            self.track.artist, self.track.title,
            f"found ({len(ret.lines or [])} lines)" if ret else "not found",
        )
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
                logger.debug(
                    f"Cancelling in-flight lyrics search for {lg.track.artist} - {lg.track.title} "
                    f"(source={lg.source}) in favor of new request for {track.artist} - {track.title} (source={source})"
                )
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
                logger.warning("Lyrics thread did not stop in time; terminating it")
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
