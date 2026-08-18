import hashlib
from dataclasses import dataclass
from typing import Callable
from blake3 import blake3
from execute import execute_action
from public_types import Action
from entropy_math import guess_entropy, recommended_bits_from_entropy
from util import bits_to_bytes, log_err


@dataclass
class ExtractResult:
    comment: str
    entropy: float = 0
    data: bytes = b""
    error: str = ""


def extract(a: Action, comment: str) -> ExtractResult:
    b3 = blake3(derive_key_context=f"extract for {comment}")
    r = execute_action(a)
    if r.error:
        log_err(f"extract({comment}): Failed: {r.error}")
        return ExtractResult(
            comment=comment, error=f"during executing action: {r.error}"
        )
    a_str = a.to_json()
    r_str = r.to_json()
    combined = a_str + r_str
    me = guess_entropy(combined)
    recommend_bytes = bits_to_bytes(recommended_bits_from_entropy(me))
    # log_err(f"extract({comment}): recommend_bytes: {recommend_bytes}")
    if recommend_bytes == 0:
        log_err(f"extract({comment}): entropy not enough")
        return ExtractResult(comment=comment, error="entropy not enough", entropy=me)
    b3.update(combined.encode())
    return ExtractResult(
        comment=comment, data=b3.digest(length=recommend_bytes), entropy=me
    )


def extract_fn(f: Callable[[], bytes], comment: str) -> ExtractResult:
    try:
        r = f()
    except Exception as e:
        log_err(f"extract_fn({comment}): Failed: {e}")
        return ExtractResult(comment=comment, error=f"during executing function: {e}")
    else:
        me = guess_entropy(r)
        recommend_bytes = bits_to_bytes(recommended_bits_from_entropy(me))
        # log_err(f"extract({comment}): recommend_bytes: {recommend_bytes}")
        if recommend_bytes == 0:
            log_err(f"extract({comment}): entropy not enough")
            return ExtractResult(
                comment=comment, error="entropy not enough", entropy=me
            )
        b3 = blake3(derive_key_context=f"extract for {comment}")
        b3.update(r)
        return ExtractResult(
            comment=comment, data=b3.digest(length=recommend_bytes), entropy=me
        )


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
