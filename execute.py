import subprocess
import time
from typing import Optional
from public_types import Action, Result


def execute_action(action: Action, timeout: Optional[float] = None) -> Result:
    if not action or not action.cmdline:
        return Result(
            error="Invalid Action: `cmdline` is empty or None.",
        )
    start_time = time.perf_counter()
    proc: Optional[subprocess.Popen] = None
    try:
        proc = subprocess.Popen(
            action.cmdline,
            env=action.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        pid = proc.pid
        stdout, stderr = proc.communicate(timeout=timeout)
        execution_time = time.perf_counter() - start_time
        return Result(
            stdout=stdout,
            stderr=stderr,
            pid=pid,
            statuscode=proc.returncode,
            execution_time=execution_time,
        )
    except subprocess.TimeoutExpired:
        execution_time = time.perf_counter() - start_time
        pid = proc.pid if proc else None
        stdout_str, stderr_str = None, None
        if proc:
            proc.kill()
            try:
                out, err = proc.communicate()
                stdout_str, stderr_str = out, err
            except Exception:
                pass
        return Result(
            stdout=stdout_str,
            stderr=stderr_str,
            pid=pid,
            statuscode=proc.returncode
            if (proc and proc.returncode is not None)
            else -1,
            execution_time=execution_time,
            error=f"Execution timed out after {timeout} seconds.",
        )
    except FileNotFoundError as e:
        execution_time = time.perf_counter() - start_time
        return Result(
            stdout=None,
            stderr=None,
            pid=None,
            statuscode=127,
            execution_time=execution_time,
            error=f"Command not found: '{action.cmdline[0]}' ({e})",
        )
    except PermissionError as e:
        execution_time = time.perf_counter() - start_time
        return Result(
            stdout=None,
            stderr=None,
            pid=None,
            statuscode=126,
            execution_time=execution_time,
            error=f"Permission denied: '{action.cmdline[0]}' ({e})",
        )
    except Exception as e:
        execution_time = time.perf_counter() - start_time
        pid = proc.pid if proc else None
        return Result(
            stdout=None,
            stderr=None,
            pid=pid,
            statuscode=proc.returncode
            if (proc and proc.returncode is not None)
            else None,
            execution_time=execution_time,
            error=f"Unexpected runner exception: {type(e).__name__}: {str(e)}",
        )
