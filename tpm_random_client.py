import time
from typing import Any, Dict, Optional
import requests
from util import log_err


def get_tpm_random(
    url: str = "http://127.0.0.1:7900/get_tpm_random",
    max_retries: int = 5,
    initial_delay: float = 0.2,
    backoff_factor: float = 1.1,
    timeout: float = 3.0,
) -> Optional[bytes]:
    """调用 TPM 随机数 API

    :param url: API 接口地址
    :param max_retries: 最大重试次数（针对网络波动/服务不可用）
    :param initial_delay: 首次重试等待时间（秒）
    :param backoff_factor: 退避系数
    :param timeout: 单次请求超时时间（秒）
    :return: 成功返回 bytes; 若 TPM 硬件故障/不存在则立即返回 None; 网络彻底失败则抛出异常
    """
    current_delay = initial_delay

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            if not data.get("success", False):
                log_err("get_tpm_random: TPM failure or not exist.")
                return None
            hex_str = data.get("random_hex", "").strip()
            if not hex_str:
                log_err("get_tpm_random: No byte retrived.")
                return None
            return bytes.fromhex(hex_str)
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"get_tpm_random: Attmpt {attempt}/{max_retries}: {e}")
            if attempt == max_retries:
                log_err("get_tpm_random: Retried many times. Request failed.")
                raise ExceptionGroup(f"Retried {max_retries} times but failed", [e])
            log_err(f"get_tpm_random: Waiting for {current_delay:.1f}s")
            time.sleep(current_delay)
            current_delay *= backoff_factor
    return None


if __name__ == "__main__":
    target_url = "http://127.0.0.1:7900/get_tpm_random"
    for i in range(0, 10):
        try:
            result = get_tpm_random(url=target_url)
            if result is None:
                print(f"({i}) data: None")
            else:
                print(f"({i}) data: {result.hex()}")
        except Exception as err:
            print(f"({i}) failed:", err)
