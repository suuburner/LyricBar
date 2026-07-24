from datetime import datetime, timedelta
import logging
import asyncio

try:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    )
except Exception:  # pragma: no cover - platform fallback for non-Windows environments
    MediaManager = None

from LyricBar.nowplaying.nowplaying import NowPlaying
from LyricBar.globalvariables import TRACKING_APP
from LyricBar.utils.dataclasses import PlayingInfo, PlayingStatusTrigger, TrackInfo



class NowPlayingSystem(NowPlaying):
    def __init__(self, sync_interval=50, update_callback=None, offset=0, tracking_app=TRACKING_APP):
        super().__init__(sync_interval, update_callback)
        self.manager = None
        try:
            self.manager = asyncio.run(self.get_media_manager())
        except Exception as exc:
            logging.debug("Media manager unavailable: %s", exc)
        # Support both single app and list of apps
        if isinstance(tracking_app, list):
            self.tracking_apps = tracking_app
        else:
            self.tracking_apps = [tracking_app]
        self.app_id = None
        self.session = None
        self.is_initialized = False
        self.last_matched_tracking_app = None
        self.offset = offset
        self.sync_animation_frame = 0  # Track animation frame for SYNCING message

    def _match_tracking_app_score(self, session_id, tracking_app):
        session_id_l = (session_id or "").lower()
        tracking_app_l = (tracking_app or "").lower()
        if not session_id_l or not tracking_app_l:
            return None

        # Exact match is the most reliable for both Win32 and UWP app ids.
        if session_id_l == tracking_app_l:
            return 100

        # Common Win32 case: source id ends with executable name.
        if tracking_app_l.endswith(".exe") and session_id_l.endswith(tracking_app_l):
            return 90

        # Controlled fallback for long/specific ids only.
        if len(tracking_app_l) >= 16 and ("!" in tracking_app_l or "." in tracking_app_l):
            if tracking_app_l in session_id_l:
                return 50

        return None

    def _is_session_playing(self, session):
        try:
            playback_info = session.get_playback_info()
            return playback_info is not None and playback_info.playback_status == 4
        except Exception:
            return False

    def update_check(self, old_playing_info, new_playing_info):
        if old_playing_info is None:
            return True
        if new_playing_info.is_playing != old_playing_info.is_playing:
            return True
        if new_playing_info.current_track != old_playing_info.current_track:
            return True
        if new_playing_info.last_updated_time != old_playing_info.last_updated_time: 
            # print("Time Gap: %.9f"%(new_playing_info.last_updated_time - old_playing_info.last_updated_time))
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
        logging.debug("TRY SYNC WITH SYSTEM")
        if not self.sync_mutex.tryLock(0):
            logging.debug("SYNCING SKIPPED")
            return
        info = asyncio.run(self.get_now_playing_info())
        
        if not self.is_initialized and (info is None or not info.is_playing):
            # More generic message when waiting for any music session
            logging.info("WAITING FOR MUSIC")
            self.is_initialized = True
            self.playing_info = None
            if self.update_callback is not None:
                self.update_callback(PlayingStatusTrigger.PAUSE)
            self.sync_mutex.unlock()
            return
        if info is None and self.playing_info is not None:
            logging.info(f"{self.last_matched_tracking_app or self.app_id} DOWN")
            self.is_initialized = True
            self.playing_info = None
            if self.update_callback is not None:
                self.update_callback(PlayingStatusTrigger.PAUSE)
            self.sync_mutex.unlock()
            return
        if info is None:
            self.sync_mutex.unlock()
            return
        if not info.is_playing and (self.playing_info is not None and self.playing_info.is_playing):
            logging.info("PAUSING")
            self.playing_info.is_playing = False
            if self.update_callback is not None:
                self.update_callback(PlayingStatusTrigger.PAUSE)
            self.sync_mutex.unlock()
            return
        if info.is_playing and (self.playing_info is None or self.track_check(self.playing_info, info)):
            logging.info(f"NEW TRACK: {info.current_track}")
            logging.info(f"OLD TRACK: {self.playing_info.current_track if self.playing_info else None}")
            logging.info(f"NEW TRACK FULL INFO: Artist={info.current_track_artist}, Title={info.current_track_title}")
            logging.info(f"PLAYING ON: {self.last_matched_tracking_app or self.app_id}")
            
            # Reset sync animation counter for new track
            self.sync_animation_frame = 0
            
            # Fix for Windows Media API bug: When track changes, API sends new metadata but with old position
            # Reset begin time to current time (position 0) to avoid timestamp carryover from previous track
            if self.playing_info is not None and info.current_track != self.playing_info.current_track:
                from datetime import datetime
                logging.info("Track changed - resetting begin time to now (fixing Windows API timestamp bug)")
                info.current_begin_time = datetime.now().timestamp() * 1000
            
            # Replace the old playing_info with the new one
            if self.playing_info is not None:
                self.playing_info.update(info)
            else:
                self.playing_info = info
            
            if self.update_callback is not None and (self.playing_info.current_track_artist != "" or self.playing_info.current_track_title != ""):
                logging.info("TRIGGERING NEW_TRACK CALLBACK")
                self.update_callback(PlayingStatusTrigger.NEW_TRACK)
            self.sync_mutex.unlock()
            return
        if info.is_playing and not self.playing_info.is_playing:
            logging.info(f"RESUMING on {self.last_matched_tracking_app or self.app_id}")
            if self.playing_info is not None:
                self.playing_info.update(info)
            else:
                self.playing_info = info
            if self.update_callback is not None:
                self.update_callback(PlayingStatusTrigger.RESUME)
        if info.is_playing and self.playing_info and self.update_check(self.playing_info, info):
            # Animated SYNCING message with cycling dashes on same line
            dash_patterns = ["", ".", "..", "..."]
            pattern = dash_patterns[self.sync_animation_frame % len(dash_patterns)]
            if self.sync_animation_frame == 0:
                # First sync shows "SYNCING" normally
                logging.info("SYNCING")
            else:
                # Use print with carriage return to update same line
                import sys
                print(f"\rINFO:root:SYNCING{pattern}   ", end='', flush=True, file=sys.stderr)
            self.sync_animation_frame += 1
            
            if self.playing_info is not None:
                self.playing_info.update(info)
            else:
                self.playing_info = info
        self.sync_mutex.unlock()

    async def get_media_manager(self):
        if MediaManager is None:
            raise RuntimeError("winrt media control is unavailable on this platform")
        return await MediaManager.request_async()

    async def get_best_session(self):
        logging.debug("GETTING APP ID")
        if self.manager is None:
            return None, None, None
        sessions = list(self.manager.get_sessions())
        session_ids = [session.source_app_user_model_id for session in sessions]
        logging.debug("Available sessions: %s", session_ids)

        matched_sessions = []
        for priority, tracking_app in enumerate(self.tracking_apps):
            for session in sessions:
                score = self._match_tracking_app_score(
                    session.source_app_user_model_id, tracking_app
                )
                if score is None:
                    continue
                matched_sessions.append(
                    (
                        self._is_session_playing(session),
                        score,
                        -priority,
                        tracking_app,
                        session.source_app_user_model_id,
                        session,
                    )
                )

        if not matched_sessions:
            self.last_matched_tracking_app = None
            return None, None, None

        # Prefer playing sessions first, then stronger matches, then user-configured app order.
        matched_sessions.sort(reverse=True)
        best = matched_sessions[0]
        self.last_matched_tracking_app = best[3]
        return best[3], best[4], best[5]

    async def get_now_playing_info(self):
        # Always refresh the selected session to follow the currently playing tracked app.
        _, current_app_id, current_session = await self.get_best_session()

        if current_app_id is None or current_session is None:
            logging.debug("No tracking app found")
            self.app_id = None
            self.session = None
            return None

        # If the active app/session changed, swap to the newly selected session.
        if current_app_id != self.app_id or current_session != self.session:
            logging.debug(f"Switching from {self.app_id} to {current_app_id}")
            self.app_id = current_app_id
            self.session = current_session
            
        if self.session is not None:
            info_dict = dict()
            try:
                info = await self.session.try_get_media_properties_async()
            except Exception as e:
                logging.debug(e)
                self.session = None
                return None
            if info is not None:
                # Filter out MediaPlaybackType which causes AttributeError
                for song_attr in dir(info):
                    if not song_attr.startswith("_") and song_attr not in ['media_playback_type']:
                        try:
                            info_dict[song_attr] = info.__getattribute__(song_attr)
                        except AttributeError:
                            # Skip attributes that cause errors
                            pass
            info = self.session.get_timeline_properties()
            if info is not None:
                info_dict.update(
                    {
                        song_attr: info.__getattribute__(song_attr)
                        for song_attr in dir(info)
                        if not song_attr.startswith("_")
                    }
                )
            info = self.session.get_playback_info()
            if info is not None:
                # Filter out MediaPlaybackType which causes AttributeError
                for song_attr in dir(info):
                    if not song_attr.startswith("_") and song_attr not in ['media_playback_type']:
                        try:
                            info_dict[song_attr] = info.__getattribute__(song_attr)
                        except AttributeError:
                            # Skip attributes that cause errors
                            pass
            # print(info_dict)
            # if self.playing_info and self.playing_info.current_begin_time is not None:
            #     print("Progress: ", datetime.now() - datetime.fromtimestamp(self.playing_info.current_begin_time))
            if "playback_status" not in info_dict:
                return None
            return PlayingInfo(
                current_track=TrackInfo(
                    artist=info_dict["artist"] if "artist" in info_dict else None,
                    id=info_dict["track_id"] if "track_id" in info_dict else None,
                    title=info_dict["title"] if "title" in info_dict else None,
                    length=(
                        (info_dict["max_seek_time"] / timedelta(milliseconds=1))
                        if "max_seek_time" in info_dict
                        else None
                    ),
                ),
                # current_begin_time=(
                #     (datetime.timestamp(info_dict["last_updated_time"]) - info_dict["position"]/ timedelta(milliseconds=1) + self.offset)
                #     if "position" in info_dict
                #     else None
                # ),
                current_begin_time=(
                    ((info_dict["last_updated_time"] - info_dict["position"]).timestamp()*1000 + self.offset) if ("position" in info_dict and "last_updated_time" in info_dict) else None
                ),
                is_playing=(info_dict["playback_status"] == 4),
                last_updated_time=datetime.timestamp(info_dict["last_updated_time"]) if "last_updated_time" in info_dict else None,
            )
        return None
    
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    def callback(trigger):
        if trigger == PlayingStatusTrigger.PAUSE:
            print("PAUSE")
        elif trigger == PlayingStatusTrigger.RESUME:
            print("RESUME")
        elif trigger == PlayingStatusTrigger.NEW_TRACK:
            print("NEW TRACK")
    
    app = QApplication(sys.argv)
    np = NowPlayingSystem(update_callback=callback, offset=100)
    np.start_loop()
    breakpoint()
    sys.exit(app.exec_())