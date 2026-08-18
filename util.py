import ctypes
import mmap
import platform
import signal
import sys
import os
import qrcode
from dataclasses import dataclass


def handle_sig_exit(sig, frame):
    log_err(f"\n[!] {signal.strsignal(sig)} detected. Exiting immediately...")
    log_err(f"[!] Frame:\n{frame}")
    os._exit(1)


def log_err(s: str):
    sys.stderr.write(s + "\n")


def log_out(s: str):
    sys.stdout.write(s + "\n")


def log_out_flush():
    sys.stdout.flush()


def log_err_flush():
    sys.stderr.flush()


def print_qr(data: str):
    log_err("======QRCode======")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(sys.stderr, tty=True)
    log_err("======QRCode======")


def to_bytes(b) -> bytes:
    if isinstance(b, bytes):
        return b
    elif isinstance(b, str):
        return b.encode("utf-8", errors="replace")
    elif isinstance(b, int):
        return str(b).encode("utf-8")
    raise TypeError(f"Can not convert {type(b)} to bytes.")


@dataclass
class MemFd:
    mem: mmap.mmap
    fd: int
    name: str
    size: int


def create_memfd(name: str, size: int, flags: tuple[int]) -> MemFd:
    """
    memfd_create and mmap helper

    size: capacity in bytes of this buffer
    """
    libc = get_libc()
    combined_flags = 0
    for flag in flags:
        combined_flags |= flag
    fd: int = libc.memfd_create(name, combined_flags)
    if fd < 0:
        errno = ctypes.get_errno()
        libc.close(fd)
        raise OSError(
            f"create_memfd({name}): Failed to create memfd: err={fd}, errno={errno}"
        )
    err: int = libc.ftruncate(fd, size)
    if err != 0:
        errno = ctypes.get_errno()
        libc.close(fd)
        raise OSError(
            f"create_memfd({name}): Failed to resize memfd: fd={fd}, ftruncate={err}, errno: {errno}"
        )
    mem = mmap.mmap(fd, size, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)
    assert mem.size() == size
    memfd = MemFd(mem, fd, name, size)
    return memfd


def resize_memfd(memfd: MemFd, new_size: int):
    """
    resize a memfd inplace

    new_size: new capacity in bytes of this buffer
    """
    libc = get_libc()
    memfd.mem.close()
    err: int = libc.ftruncate(memfd.fd, new_size)
    if err != 0:
        errno = ctypes.get_errno()
        libc.close(memfd.fd)
        raise OSError(
            f"resize_memfd({memfd.name}): Failed to resize memfd: fd={memfd.fd}, ftruncate={err}, errno: {errno}"
        )
    mem = mmap.mmap(
        memfd.fd, new_size, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ
    )
    assert mem.size() == new_size
    memfd.mem = mem
    memfd.size = new_size


def close_memfd(memfd: MemFd):
    libc = get_libc()
    memfd.mem.close()
    libc.close(memfd.fd)


def get_libc() -> ctypes.CDLL:
    system_name = platform.system()
    if system_name in ("Linux", "Darwin"):
        libc_name = "libc.dylib" if system_name == "Darwin" else "libc.so.6"
        try:
            libc = ctypes.CDLL(libc_name, use_errno=True)
        except OSError:
            libc = ctypes.CDLL(None, use_errno=True)
    else:
        raise NotImplementedError("Your platform is not supported.")
    return libc


def _lock_memory():
    system_name = platform.system()
    if system_name in ("Linux", "Darwin"):
        import resource

        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            log_err("lock_memory: setrlimit Success")
        except Exception as e:
            log_err(f"lock_memory: setrlimit Failed: {e}")
        libc = get_libc()
        if hasattr(libc, "mlockall"):
            MCL_CURRENT = 1
            MCL_FUTURE = 2
            result = libc.mlockall(MCL_CURRENT | MCL_FUTURE)
            if result != 0:
                errno = ctypes.get_errno()
                log_err(f"lock_memory: mlockall Failed: {result}, errno={errno}")
                return False
            else:
                log_err("lock_memory: mlockall Success")
                return True
        else:
            log_err("lock_memory: mlockall function not found")
            return False
    else:
        log_err("lock_memory: idk how to lock memory for your platform")
        return False


def lock_memory() -> bool:
    try:
        return _lock_memory()
    except Exception as e:
        log_err(f"lock_memory: Unhandled Error: {e}")
        return False


def wipe_memory(*targets: bytearray | list) -> None:
    for obj in targets:
        if isinstance(obj, bytearray):
            for i in range(len(obj)):
                obj[i] = 0
        elif isinstance(obj, list):
            for i in range(len(obj)):
                if isinstance(obj[i], bytearray):
                    wipe_memory(obj[i])
            obj.clear()
