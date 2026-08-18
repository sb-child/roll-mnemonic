import hashlib
from typing import Callable
from blake3 import blake3
from execute import execute_action
from public_types import Action
from util import log_err


def extract(a: Action, comment: str) -> bytes:
    b3 = blake3(derive_key_context=f"extract for {comment}")
    r = execute_action(a)
    if r.error:
        log_err(f"extract({comment}): Failed: {r.error}")
    b3.update(a.to_json().encode())
    b3.update(r.to_json().encode())
    return b3.digest(length=256)


def extract_fn(f: Callable[[], bytes], comment: str):
    b3 = blake3(derive_key_context=f"extract for {comment}")
    try:
        r = f()
    except Exception as e:
        log_err(f"extract_fn({comment}): Failed: {e}")
        b3.update(b"FUNCTION RAISED EXCEPTION")
    else:
        b3.update(r)
    return b3.digest(length=256)


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
