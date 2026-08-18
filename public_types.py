import json
import shlex
from typing import Any, Dict, List, Optional, Union


class Action:
    cmdline: List[str]
    env: Optional[Dict[str, str]]

    def __init__(
        self,
        cmdline: Union[str, List[Any]],
        env: Optional[Union[str, Dict[Any, Any]]] = None,
    ) -> None:
        if isinstance(cmdline, str):
            self.cmdline = shlex.split(cmdline)
        elif isinstance(cmdline, (list, tuple)):
            self.cmdline = [str(item) for item in cmdline]
        else:
            raise TypeError(
                f"`cmdline` must be `str`, `list`, or `tuple`. Got: {type(cmdline).__name__}"
            )

        if env is None:
            self.env = None
        elif isinstance(env, str):
            parsed_env: Dict[str, str] = {}
            tokens = shlex.split(env)
            for token in tokens:
                if "=" in token:
                    k, v = token.split("=", 1)
                    parsed_env[str(k)] = str(v)
                else:
                    parsed_env[str(token)] = ""
            self.env = parsed_env
        elif isinstance(env, dict):
            self.env = {str(k): str(v) for k, v in env.items()}
        else:
            raise TypeError(
                f"`env` must be `str`, `dict`, or `None`. Got: {type(env).__name__}"
            )

    def __repr__(self) -> str:
        return f"Action(cmdline={self.cmdline!r}, env={self.env!r})"

    def to_json(self) -> str:
        r = {
            "cmdline": self.cmdline,
            "env": self.env,
        }
        return json.dumps(r, separators=(",", ":"))

    @classmethod
    def from_json(cls, s: str) -> "Action":
        r = json.loads(s)
        return cls(cmdline=r.get("cmdline"), env=r.get("env"))


class Result:
    stdout: Optional[str]
    stderr: Optional[str]
    pid: Optional[int]
    statuscode: Optional[int]
    execution_time: Optional[float]
    error: Optional[str]

    def __init__(
        self,
        stdout: Optional[Any] = None,
        stderr: Optional[Any] = None,
        pid: Optional[Any] = None,
        statuscode: Optional[Any] = None,
        execution_time: Optional[Any] = None,
        error: Optional[Any] = None,
    ) -> None:
        self.stdout = str(stdout) if stdout is not None else None
        self.stderr = str(stderr) if stderr is not None else None
        if pid is not None:
            try:
                self.pid = int(pid)
            except ValueError, TypeError:
                raise TypeError(
                    f"`pid` must be an int-like value. Got: {type(pid).__name__}"
                )
        else:
            self.pid = None
        if statuscode is not None:
            try:
                self.statuscode = int(statuscode)
            except ValueError, TypeError:
                raise TypeError(
                    f"`statuscode` must be an int-like value. Got: {type(statuscode).__name__}"
                )
        else:
            self.statuscode = None
        if execution_time is not None:
            try:
                self.execution_time = float(execution_time)
            except ValueError, TypeError:
                raise TypeError(
                    f"`execution_time` must be a float-like value. Got: {type(execution_time).__name__}"
                )
        else:
            self.execution_time = None
        self.error = str(error) if error is not None else None

    def __repr__(self) -> str:
        return (
            f"Result("
            f"stdout={self.stdout!r}, "
            f"stderr={self.stderr!r}, "
            f"pid={self.pid!r}, "
            f"statuscode={self.statuscode!r}, "
            f"execution_time={self.execution_time!r}, "
            f"error={self.error!r})"
        )

    def to_json(self) -> str:
        r: Dict[str, Any] = {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "pid": self.pid,
            "statuscode": self.statuscode,
            "execution_time": self.execution_time,
            "error": self.error,
        }
        return json.dumps(r, separators=(",", ":"))

    @classmethod
    def from_json(cls, s: str) -> "Result":
        r = json.loads(s)
        return cls(
            stdout=r.get("stdout"),
            stderr=r.get("stderr"),
            pid=r.get("pid"),
            statuscode=r.get("statuscode"),
            execution_time=r.get("execution_time"),
            error=r.get("error"),
        )
