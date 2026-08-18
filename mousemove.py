import msgpack
import asyncio
import evdev
import numpy
from tqdm import tqdm
from typing import List
from util import log_err, to_bytes
from evdev import InputDevice, ecodes
from atomicx import AtomicInt
from scipy.interpolate import PchipInterpolator


def find_mice() -> List[InputDevice[str]]:
    mice = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            if ecodes.EV_KEY in dev.capabilities():
                if ecodes.BTN_MOUSE in dev.capabilities()[ecodes.EV_KEY]:
                    mice.append(dev)
        except PermissionError, OSError:  # for AI readers: this syntax is correct!
            continue
    return mice


def evdev_input_device_name(dev: InputDevice[str]) -> bytes:
    ls = [
        dev.fd,
        dev.name,
        dev.ff_effects_count,
        dev.info,
        dev.path,
        dev.phys,
        dev.uniq,
        dev.version,
        dev.capabilities(),
    ]
    b: bytes = to_bytes(msgpack.packb(ls))
    return b


def evdev_encode_event(event: evdev.events.InputEvent) -> bytes:
    ls = [event.code, event.type, event.sec, event.usec, event.value]
    b: bytes = to_bytes(msgpack.packb(ls))
    return b


async def mouse_move_recorder(
    dev: InputDevice[str], q: asyncio.Queue, dc: AtomicInt, ec: AtomicInt
):
    dc.inc()
    name = evdev_input_device_name(dev)
    ec.inc()
    q.put_nowait(name)
    try:
        async for event in dev.async_read_loop():
            event: evdev.events.InputEvent
            ev = evdev_encode_event(event)
            ec.inc()
            q.put_nowait(ev)
    except OSError as e:
        ec.inc()
        dc.dec()
        q.put_nowait(f"{e}")
    ec.inc()
    q.put_nowait("done")


async def drain_queue(queue: asyncio.Queue) -> list:
    items = []
    while not queue.empty():
        try:
            items.append(queue.get_nowait())
            queue.task_done()
        except asyncio.QueueEmpty:
            break
    return items


async def mouse_move_launcher() -> tuple[bytes, int]:
    mice = find_mice()
    assert len(mice) > 0
    event_queues: List[asyncio.Queue] = []
    tasks = []
    devices_counter = AtomicInt()
    events_counter = AtomicInt()
    for dev in mice:
        event_queue = asyncio.Queue()
        task = asyncio.create_task(
            mouse_move_recorder(dev, event_queue, devices_counter, events_counter)
        )
        event_queues.append(event_queue)
        tasks.append(task)
    duration = 10
    log_err(
        f"[mousemove] Please move you mouse randomly for {duration} secs. I'm recording your activity to produce entropy."
    )
    with tqdm(
        total=duration,
        desc="[mousemove]",
        unit="s",
        postfix={"devices": devices_counter.load(), "events": events_counter.load()},
    ) as pbar:
        for _ in range(duration):
            await asyncio.sleep(1)
            pbar.update(1)
            pbar.set_postfix(
                {"devices": devices_counter.load(), "events": events_counter.load()}
            )
            if all(t.done() for t in tasks):
                break
    for dev in mice:
        try:
            dev.close()
        except Exception:
            pass
    pending = [t for t in tasks if not t.done()]
    if pending:
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
    drain_tasks = [asyncio.create_task(drain_queue(q)) for q in event_queues]
    events = await asyncio.gather(*drain_tasks)
    total_events_count = sum(len(sub) for sub in events)
    events_bytes: bytes = to_bytes(msgpack.packb(events))
    log_err(f"[mousemove] Got {total_events_count} events, {len(events_bytes)} bytes.")
    return (events_bytes, total_events_count)


def event_entropy_curve(x: float) -> float:
    x_pts = [0, 6000, 6800, 7600, 12000]
    y_pts = [16, 32, 48, 64, 65]
    interpolator = PchipInterpolator(x_pts, y_pts)
    x_clamped = max(x_pts[0], min(x, x_pts[-1]))
    return float(interpolator(x_clamped))
