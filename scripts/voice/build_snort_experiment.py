"""RIFF/PCM helpers retained from the local historical prototype.
No event-local prototype builder is exposed here.
"""
import hashlib
import struct
import wave
import numpy as np

def sha(data):
    return hashlib.sha256(data).hexdigest()


def wave_samples(path):
    with wave.open(str(path)) as f:
        assert (f.getnchannels(), f.getframerate(), f.getsampwidth()) == (1, 48000, 2)
        return np.frombuffer(f.readframes(f.getnframes()), dtype='<i2').astype(np.float64)


def chunks(data):
    """Wwise RIFF: final zero pad from this encoder is permitted explicitly."""
    assert data[:4] == b'RIFF' and data[8:12] == b'WAVE'
    assert struct.unpack_from('<I', data, 4)[0] + 8 == len(data)
    pos = 12
    result = {}
    while pos + 8 <= len(data):
        tag, n = struct.unpack_from('<4sI', data, pos)
        assert tag not in result and pos + 8 + n <= len(data)
        result[tag] = data[pos + 8:pos + 8 + n]
        pos += 8 + n
    assert pos == len(data) or data[pos:] == b'\0'
    return result
