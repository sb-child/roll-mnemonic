import cv2
import numpy
from typing import cast
from randomness_math import randomness_score, recommended_bits_from_score
from blake3 import blake3
from numpy.typing import NDArray
from util import log_err, normalize_to_dtype_limits


def open_camera() -> cv2.VideoCapture:
    idx = 0
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        log_err(f"open_camera: Could not open camera {idx}.")
        raise FileNotFoundError(f"Could not open camera {idx}")
    return cap


def take_photo(vc: cv2.VideoCapture) -> tuple[float, bytes]:
    ret, frame1 = vc.read()
    if not ret:
        log_err("take_photo: Failed to grab frame A.")
        return (0, b"")
    f1 = cast(NDArray[numpy.uint8], frame1).astype(numpy.int16)
    ret, frame2 = vc.read()
    if not ret:
        log_err("take_photo: Failed to grab frame B.")
        return (0, b"")
    f2 = cast(NDArray[numpy.uint8], frame2).astype(numpy.int16)
    diff = f2 - f1
    norm = normalize_to_dtype_limits(diff, numpy.int16)
    b = norm.tobytes()
    b_randomness = randomness_score(b)
    return (b_randomness, b)


def close_camera(vc: cv2.VideoCapture):
    vc.release()


def grab_frames() -> tuple[list[bytes], float]:
    c = open_camera()
    log_err("[camera-entropy] Starting grab frames.")
    n = 100
    res = []
    ent = 1.0
    for i in range(n):
        f = take_photo(c)
        if len(f[1]) > 0 and f[0] > 0.2:
            res.append(f[1])
            ent = (ent + f[0]) / 2
        else:
            reason = (
                ", see reason above."
                if len(f[1]) == 0
                else f": randomness_score={f[0]:.08f} not enough."
            )
            log_err(f"camera: Error grabbing frame {i}{reason}")
    log_err(f"[camera-entropy] Grabbed {len(res)}/{n} frames, processing data...")
    return (res, ent)


def camera_entropy() -> bytes:
    (f, ent) = grab_frames()
    recommend = recommended_bits_from_score(ent)
    if recommend == 0:
        log_err("camera_entropy: entropy not enough")
        return b""
    b3 = blake3(derive_key_context="camera_entropy")
    for i in f:
        b3.update(i)
    log_err("[camera-entropy] Data process completed.")
    return b3.digest(length=recommend)
