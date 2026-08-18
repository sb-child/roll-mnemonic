import base64
import hashlib
from typing import Callable
from blake3 import blake3
from execute import execute_action
from public_types import Action
from shannon import recommended_bits
from util import bits_to_bytes, log_err


def extract(a: Action, comment: str) -> bytes:
    b3 = blake3(derive_key_context=f"extract for {comment}")
    r = execute_action(a)
    if r.error:
        log_err(f"extract({comment}): Failed: {r.error}")
    a_str = a.to_json()
    r_str = r.to_json()
    combined = a_str + r_str
    recommend_bytes = bits_to_bytes(recommended_bits(combined))
    # log_err(f"extract({comment}): recommend_bytes: {recommend_bytes}")
    if recommend_bytes == 0:
        log_err(f"extract({comment}): entropy not enough")
        return b""
    b3.update(combined.encode())
    return b3.digest(length=recommend_bytes)


def extract_fn(f: Callable[[], bytes], comment: str) -> bytes:
    b3 = blake3(derive_key_context=f"extract for {comment}")
    try:
        r = f()
    except Exception as e:
        log_err(f"extract_fn({comment}): Failed: {e}")
        b3.update(b"FUNCTION RAISED EXCEPTION")
    else:
        r_str = base64.b64encode(r).decode()
        recommend_bytes = bits_to_bytes(recommended_bits(r_str))
        # log_err(f"extract({comment}): recommend_bytes: {recommend_bytes}")
        if recommend_bytes == 0:
            log_err(f"extract({comment}): entropy not enough")
            return b""
        b3.update(r)
        return b3.digest(length=recommend_bytes)
    return b3.digest(length=16)


def extract_from_entropy_list(
    entropy_list: list[bytes], target_bytes: int
) -> bytearray:
    hasher = hashlib.shake_256()
    for chunk in entropy_list:
        hasher.update(chunk)
    return bytearray(hasher.digest(target_bytes))


def test():
    pass


if __name__ == "__main__":
    test()
