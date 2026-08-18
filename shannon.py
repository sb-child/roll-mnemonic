import base64
import math
from collections import Counter
from blake3 import blake3


# https://www.reddit.com/r/learnpython/comments/g1sdkh/python_programming_challenge_calculating_shannon/
def shannon(string: str) -> float:
    counts = Counter(string)
    frequencies = ((i / len(string)) for i in counts.values())
    return -sum(f * math.log(f, 2) for f in frequencies)


def shannon_bits(string: str) -> int:
    c = len(string)
    sh = shannon(string)
    total_ent = c * sh
    return int(total_ent)


def curve_1(y: float) -> float:
    if y <= 0 or y >= 8:
        raise ValueError("y value out of range")
    return 100 - math.log((8 - y) / y) / math.log(1.02)


def curve_2(x):
    return x * 0.01 * x


def recommended_bits(string: str) -> int:
    s = shannon(string)
    return recommended_bits_from_shannon(s)


def recommended_bits_from_shannon(s: float) -> int:
    bits = curve_1(s * 1.2)
    bits = curve_2(bits)
    if bits < 64:
        return 0
    if bits > 512:
        return 512
    return int(bits)


def main():
    s = recommended_bits("1515515151515151515515151515151515151515151515155115")
    print(s)
    s = recommended_bits("drrftgyhuji秒iOS啊啊啊啊啊啊啊啊啊")
    print(s)
    s = recommended_bits("drrftgyhuji秒iOS啊啊啊啊啊啊啊啊啊")
    print(s)
    s = recommended_bits(
        "(roll-mnemonic) sbchild@xiaoxin:~/roll-mnemonic$ uv run shannon.py"
    )
    print(s)
    s = recommended_bits("d6g7347gdfh7834g27df83o2d")
    print(s)
    b3 = blake3(b"d6g7347gdfh7834g27df83o2d")
    s = recommended_bits(b3.hexdigest())
    print(s)
    b4 = blake3(b"d6g7347gdfh7834g27df83o2d")
    s = recommended_bits(base64.b64encode(b4.digest()).decode())
    print(s)


if __name__ == "__main__":
    main()
