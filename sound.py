import numpy
import sounddevice as sd
from typing import cast
from numpy.typing import NDArray
from util import log_err


def record_sound() -> NDArray[numpy.float32]:
    sr = 44100
    channels = 2
    duration = 30.0
    log_err(f"record_sound: Start Recording for {duration} secs.")
    try:
        recording = sd.rec(
            int(duration * sr), samplerate=sr, channels=channels, blocking=True
        )
        if (
            (type(recording) is not numpy.ndarray)
            or (len(recording) == 0)
            or (recording.sum() < 1.0)
        ):
            raise Exception("No Sound recorded")

    except Exception as e:
        raise ExceptionGroup("Could not start record sound. Check your device.", [e])
    recording = cast(NDArray[numpy.float32], recording.astype(numpy.float32))
    """
    > print(recording)
    [[0. 0.]
    [0. 0.]
    [0. 0.]
    ...
    [0. 0.]
    [0. 0.]
    [0. 0.]]
    """
    return recording


def sound_entropy() -> bytes:
    s = record_sound()
    b = s.tobytes()
    return b


def main():
    record_sound()


if __name__ == "__main__":
    main()
