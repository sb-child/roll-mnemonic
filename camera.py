from typing import cast

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


def take_photo(vc: cv2.VideoCapture) -> bytes:
    ret, frame = vc.read()
    if not ret:
        log_err("take_photo: Failed to grab a frame.")
        return b""
    f = cast(NDArray[numpy.uint8], frame)
    b = f.tobytes()
    return b


def close_camera(vc: cv2.VideoCapture):
    vc.release()


def grab_frames() -> list[bytes]:
    c = open_camera()
    log_err("camera: Starting grab frames.")
    n = 30 * 10
    res = []
    for i in range(n):
        f = take_photo(c)
        if len(f) > 0:
            res.append(f)
        else:
            log_err(f"camera: Error grabbing frame {i}.")
    log_err(f"camera: Grabbed {len(res)}/{n} frames.")
    return res


def camera_entropy() -> bytes:
    f = grab_frames()
    b3 = blake3(derive_key_context="camera_entropy")
    for i in f:
        b3.update(i)
    return b3.digest(length=512)
