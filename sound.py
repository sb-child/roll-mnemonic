import numpy
import sounddevice as sd
from typing import cast
from numpy.typing import NDArray
from util import log_err, normalize_to_dtype_limits


def record_sound() -> NDArray[numpy.int32]:
    sr = 44100
    channels = 2
    duration = 10.0
    log_err(f"[sound-entropy] Start Recording for {duration} secs.")
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
    log_err("[sound-entropy] Record completed, processing data...")
    recording = cast(NDArray[numpy.float32], recording.astype(numpy.float32))
    raw_count = int(recording.shape[0])
    recording = numpy.unique(recording, axis=0)
    recording = recording[~numpy.all(recording == 0, axis=1)]
    recording = recording[~numpy.isnan(recording).any(axis=1)]
    cleaned_count = int(recording.shape[0])
    if raw_count != cleaned_count:
        log_err(
            f"[sound-entropy] Cleaned {raw_count - cleaned_count} samples, {cleaned_count} left."
        )
    recording_norm = normalize_to_dtype_limits(recording, numpy.int32)
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
    return recording_norm


def sound_entropy() -> bytes:
    s = record_sound()
    # print(s)
    b = s.tobytes()
    log_err(f"[sound-entropy] Data process completed, {len(b)} bytes.")
    return b


def main():
    record_sound()


if __name__ == "__main__":
    main()
