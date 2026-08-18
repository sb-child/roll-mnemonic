import argparse
import asyncio
import os
import signal
import subprocess
import sys
from util import get_libc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from aiologger import Logger

logger = Logger.with_default_handlers()
libc = get_libc()


def set_pdeathsig():
    PR_SET_PDEATHSIG = 1
    libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)


app = FastAPI(
    title="TPM2 Random Generator API",
    description="TPM2 随机数生成服务",
    version="1.0.0",
)

tpm_lock = asyncio.Lock()


class RandomResponse(BaseModel):
    success: bool = Field(examples=[True])
    random_hex: str = Field(
        examples=["2d2868aeb75792f705f3ac3a8bf0dc863bd3c91aa1046c1a4a3a85a08ffec1a8"]
    )


def cleanup_child_processes(signum=None, frame=None):
    try:
        pgid = os.getpgrp()
        os.killpg(pgid, signal.SIGTERM)
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup_child_processes)
signal.signal(signal.SIGTERM, cleanup_child_processes)


@app.get(
    "/get_tpm_random",
    response_model=RandomResponse,
    summary="获取 TPM2 随机数",
    description="从 TPM2 获取 32 字节 hex 编码随机数",
)
async def get_tpm_random():
    async with tpm_lock:
        try:
            process = await asyncio.to_thread(
                subprocess.run,
                ["tpm2_getrandom", "32", "--hex"],
                capture_output=True,
                text=True,
                check=False,
                preexec_fn=set_pdeathsig,
            )
            if process.returncode != 0:
                await logger.warn(f"tpm2_getrandom: returncode={process.returncode}")
                await logger.warn(f"tpm2_getrandom: stdout={process.stdout.strip()}")
                await logger.warn(f"tpm2_getrandom: stderr={process.stderr.strip()}")
                return RandomResponse(success=False, random_hex="")
            hex_output = process.stdout.strip()
            return RandomResponse(success=True, random_hex=hex_output)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            raise HTTPException(
                status_code=500,
                detail=f"TPM2 command execution failed: {error_msg}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="TPM2 OpenAPI Server")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=7900,
        help="指定 API 服务监听的端口号",
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="127.0.0.1",
        help="指定 API 服务监听的 IP 地址",
    )
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
