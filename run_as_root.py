from __future__ import annotations
import argparse
import json
import os
import sys
import shlex
from public_types import Action, Result
from util import lock_memory, get_libc, create_memfd
from pathlib import Path
from typing import Any, Dict, Optional, List, Union


def run_as_root(
    cmdline: Union[str, List[Any]], env: Union[str, Dict[Any, Any]]
) -> Result:
    """
    for client: call this function to run your command as root
    """
    action = Action(cmdline, env)
    action_json = action.to_json().encode()
    action_len = len(action_json)
    action_fd = create_memfd("run_as_root_action", 1, (os.MFD_CLOEXEC,))
    os.write(action_fd, action_json)
    print(f"fd: {action_fd}")
    self_path = Path(__file__).absolute()
    python_path = Path(sys.executable).absolute()
    pass


def execute_action_as_root():
    pass


def main():
    lock_memory()
    parser = argparse.ArgumentParser(description="run-as-root Helper")
    parser.add_argument(
        "-a",
        type=int,
        required=True,
        metavar="ACTION_FD",
        help="Action file descriptor",
    )
    parser.add_argument(
        "-al",
        type=int,
        required=True,
        metavar="NUMBER",
        help="Action data length",
    )
    parser.add_argument(
        "-r",
        type=int,
        required=True,
        metavar="RESULT_FD",
        help="Result file descriptor",
    )
    parser.add_argument(
        "-s",
        type=int,
        required=True,
        metavar="SOCK_FD",
        help="Notification Socket file descriptor",
    )
    args = parser.parse_args()
    # action_file_path: Path = args.s
    # result_file_path: Path = args.r
    # os.memfd_create("fd1_secret", os.MFD_CLOEXEC)
    action_fd = create_memfd("run_as_root_action", 1, (os.MFD_CLOEXEC,))
    os.write(action_fd, b"sssssssssss")
    print(f"fd: {action_fd}")


if __name__ == "__main__":
    main()
