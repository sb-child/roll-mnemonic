from concurrent.futures import ThreadPoolExecutor
import os
import time
import pickle
import random
import ssl
import asyncio
from typing import Callable, Optional
from camera import camera_entropy
from extract import extract, extract_fn
from mousemove import mouse_move_launcher
from options import ExtractAllSourcesOptions
from public_types import Action
from sound import sound_entropy
from tpm_random_client import get_tpm_random
from util import log_err


def urandom() -> bytes:
    r = os.urandom(512)
    assert len(r) == 512
    return r


def tpm_random(endpoint: Optional[str]) -> bytes:
    def get_random() -> bytes:
        r = get_tpm_random() if endpoint is None else get_tpm_random(endpoint)
        assert r is not None
        assert len(r) == 32
        return r

    try:
        r = [get_random() for _ in range(32)]
    except AssertionError as e:
        log_err(f"tpm_random: Is your TPM works? Check server logs: {e}")
        raise e
    except Exception as e:
        log_err(f"tpm_random: Are your server running: {e}")
        raise e
    return b"".join(r)


def mouse_move():
    assert ssl.RAND_status(), "OpenSSL PRNG is not seeded"
    (event_bytes, total_events_count) = asyncio.run(mouse_move_launcher())
    ssl.RAND_add(event_bytes, float(total_events_count))
    assert ssl.RAND_status(), "OpenSSL PRNG is not seeded"
    r = ssl.RAND_bytes(512)
    assert len(r) == 512
    return r


def time_sleep() -> bytes:
    ticks = []

    def record():
        now = time.time()
        now_ns = time.time_ns()
        pc = time.perf_counter()
        pcns = time.perf_counter_ns()
        ticks.append((now, now_ns, pc, pcns))

    record()
    for _ in range(1000):
        r = random.random()  # 0.0 ~ 1.0
        time.sleep(r / 1000.0)
        record()
    r = pickle.dumps(ticks)
    return r


def test_extract(a: Action, c: str):
    r = extract(a, c)
    print(f"hex for {c}:\n{r.hex()}")
    return r


def test_extract_fn(f: Callable[[], bytes], c: str):
    r = extract_fn(f, c)
    print(f"hex for {c}:\n{r.hex()}")
    return r


def process_single_source(comment: str, action: Action | Callable):
    if isinstance(action, Action):
        return extract(action, comment)
    elif isinstance(action, Callable) or callable(action):
        return extract_fn(action, comment)
    else:
        log_err(
            f"process_single_source: Unknown action {comment} type {type(action).__name__}"
        )
        return b""


def extract_all_sources(opts: ExtractAllSourcesOptions):
    sources = {
        "journalctl": Action("journalctl -b 0 --no-pager"),
        "dnf-history": Action("dnf history list"),
        "systemctl-status": Action("systemctl status --no-pager"),
        "systemd-blame": Action("systemd-analyze blame"),
        "top-snapshot": Action("top -b -c -n 1"),
        "lsusb": Action("lsusb -vvv"),
        "lspci": Action("lspci -vvv"),
        "lscpu-info": Action("lscpu -y -J"),
        "lscpu-freq": Action("lscpu -y -J -e"),
        "time-sleep": time_sleep,
        "urandom": urandom,
        "mousemove": mouse_move,
        "tpm-random": lambda: tpm_random(opts.tpm_random_server_endpoint),
        "camera-entropy": camera_entropy,
        "sound": sound_entropy,
    }
    max_workers = len(sources)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_comment = {
            executor.submit(process_single_source, comment, action): comment
            for comment, action in sources.items()
        }
        results = []
        try:
            for future in future_to_comment:
                results.append(future.result())
        except KeyboardInterrupt:
            log_err("extract_all_sources: Ctrl+C detected! Canceling...")
            for f in future_to_comment:
                f.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
    return results


def test():
    o = ExtractAllSourcesOptions(tpm_random_server_endpoint=None)
    r = extract_all_sources(o)
    for i in r:
        print(f"{i.hex()}")


if __name__ == "__main__":
    test()
