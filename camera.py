import base64
from typing import cast
from shannon import shannon, recommended_bits_from_shannon
from blake3 import blake3
import cv2
import numpy
from numpy.typing import NDArray

from util import log_err


def open_camera() -> cv2.VideoCapture:
    idx = 0
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        log_err(f"open_camera: Could not open camera {idx}.")
        raise FileNotFoundError(f"Could not open camera {idx}")
    return cap


def take_photo(vc: cv2.VideoCapture) -> tuple[float, bytes]:
    ret, frame = vc.read()
    if not ret:
        log_err("take_photo: Failed to grab a frame.")
        return (0, b"")
    f = cast(NDArray[numpy.uint8], frame)
    b = f.tobytes()
    b_str = base64.b64encode(b).decode()
    b_entropy = shannon(b_str)
    return (b_entropy, b)


def close_camera(vc: cv2.VideoCapture):
    vc.release()


def grab_frames() -> tuple[list[bytes], float]:
    c = open_camera()
    log_err("camera: Starting grab frames.")
    n = 30 * 10
    res = []
    ent = 1.0
    for i in range(n):
        f = take_photo(c)
        if len(f[1]) > 0 and f[0] > 1:
            res.append(f[1])
            ent = (ent + f[0]) / 2
        else:
            log_err(f"camera: Error grabbing frame {i}.")
    log_err(f"camera: Grabbed {len(res)}/{n} frames.")
    return (res, ent)


def camera_entropy() -> bytes:
    (f, ent) = grab_frames()
    recommend = recommended_bits_from_shannon(ent)
    if recommend == 0:
        log_err("camera_entropy: entropy not enough")
        return b""
    b3 = blake3(derive_key_context="camera_entropy")
    for i in f:
        b3.update(i)
    return b3.digest(length=recommend)
