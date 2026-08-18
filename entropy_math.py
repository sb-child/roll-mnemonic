import base64
import math
from collections import Counter
from blake3 import blake3


def guess_entropy(data: bytes | str) -> float:
    me = min_entropy(data) * 1.5
    sh = shannon(data) * 0.5
    r = sum((me, sh)) / 2
    return r


def min_entropy(data: bytes | str) -> float:
    if not data:
        return 0.0
    byte_counts = Counter(data)
    _most_common_byte, max_count = byte_counts.most_common(1)[0]
    max_probability = max_count / len(data)
    min_entropy = -math.log2(max_probability)
    return min_entropy


# https://www.reddit.com/r/learnpython/comments/g1sdkh/python_programming_challenge_calculating_shannon/
def shannon(data: bytes | str) -> float:
    counts = Counter(data)
    frequencies = ((i / len(data)) for i in counts.values())
    return -sum(f * math.log(f, 2) for f in frequencies)


def curve_1(y: float) -> float:
    if y >= 7.99:
        y = 7.99
    elif y < 0.05:
        y = 0.05
    return 100 - math.log((8 - y) / y) / math.log(1.02)


def curve_2(x):
    return x * 0.02 * x


def recommended_bits(data: bytes | str) -> int:
    s = guess_entropy(data)
    return recommended_bits_from_entropy(s)


def recommended_bits_from_entropy(entropy_bits: float) -> int:
    bits = curve_1(entropy_bits * 1.1)
    bits = curve_2(bits)
    # print(f"entropy_bits={entropy_bits} result={bits}")
    if bits < 32:
        return 0
    if bits > 1024:
        return 1024
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
