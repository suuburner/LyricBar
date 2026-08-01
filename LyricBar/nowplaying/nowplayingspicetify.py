import asyncio
import json
import logging
import threading

from websocket_server import WebsocketServer

from LyricBar.config import settings
from LyricBar.nowplaying.nowplaying import NowPlaying
from LyricBar.utils.dataclasses import PlayingInfo, PlayingStatusTrigger, TrackInfo
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
)

logger = logging.getLogger(__name__)


class NowPlayingSpicetify(NowPlaying):
    def __init__(self, socket_port=8974, update_callback=None, offset=0, sync_interval=50):
        super().__init__(sync_interval=-1, update_callback=update_callback)
        self.manager = asyncio.run(self.get_media_manager())
        self.server = WebsocketServer(host='127.0.0.1', port=socket_port)
        self.server.set_fn_message_received(self.message_received)
        self.offset = offset
        self.sync_interval = sync_interval

    async def get_media_manager(self):
        return await MediaManager.request_async()

    def start_loop(self):
        self.started = True
        self.update_callback(PlayingStatusTrigger.PAUSE)
        self.thread = threading.Thread(target=self.server.run_forever, daemon=True).start()
        self.sync_timer.start(self.sync_interval)

    def sync(self):
        # NOTE: this used to hard-filter on "Spotify.exe" only, ignoring the
        # configured tracking-app list entirely -- fixed to check against
        # every app the user actually has configured, same as NowPlayingSystem.
        sessions = self.manager.get_sessions()
        tracking_apps_lower = {app.lower() for app in settings.tracking_app}
        session = next(
            (s for s in sessions if (s.source_app_user_model_id or "").lower() in tracking_apps_lower),
            None,
        )
        if session is None:
            if self.playing_info is not None:
                self.update_callback(PlayingStatusTrigger.PAUSE)
                self.playing_info = None

    def message_received(self, client, server, message):
        info = json.loads(message)
        new_playing_info = None
        try:
            new_playing_info = PlayingInfo(
                current_track=TrackInfo(
                    artist=info["ARTIST"],
                    title=info["TITLE"],
                    length=int(info["DURATION"]),
                    id=info["UID"],
                    is_music=info["TYPE"] == "track",
                ),
                current_begin_time=info["BEGINTIME"] + self.offset,
                is_playing=info["STATE"] == 1,
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.debug("Malformed Spicetify websocket message, ignoring: %s", exc)
            return
        if ((self.playing_info is not None and self.playing_info.current_track.id != new_playing_info.current_track.id) or self.playing_info is None) and new_playing_info.is_playing:
            if self.playing_info is not None:
                self.playing_info.update(new_playing_info)
            else:
                self.playing_info = new_playing_info
            self.update_callback(PlayingStatusTrigger.NEW_TRACK)
            return
        elif self.playing_info is not None and self.playing_info.is_playing != new_playing_info.is_playing:
            if new_playing_info.is_playing:
                self.update_callback(PlayingStatusTrigger.RESUME)
            else:
                self.playing_info.is_playing = False
                self.update_callback(PlayingStatusTrigger.PAUSE)
                return
        elif self.playing_info is None or self.playing_info.is_playing == False:
            return
        if self.playing_info is not None:
            self.playing_info.update(new_playing_info)
        else:
            self.playing_info = new_playing_info
        return
