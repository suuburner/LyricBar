from LyricBar.backend.lyricmanager import LyricsManager
from LyricBar.utils.dataclasses import TrackInfo
from LyricBar.globalvariables import resource_path, LYRIC_FOLDER
import os

track = TrackInfo(artist='Daniel Seavey', title='Fall into You', length=158602.0)
manager = LyricsManager(providers={}, cache_dir=resource_path(LYRIC_FOLDER))
print('cache_dir', manager.cache_dir)
print('candidate', os.path.join(manager.cache_dir, track.hash_id + '.json'))
print('exists', os.path.exists(os.path.join(manager.cache_dir, track.hash_id + '.json')))

result = []

def cb(payload):
    result.append(payload)
    print('callback called', payload[0].source if payload[0] else None, payload[0].lines[0].text if payload[0] and payload[0].lines else None)

manager.get_lyrics(track, cb)
print('done queued')
