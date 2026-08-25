import base64
import math
from collections import Counter
from blake3 import blake3
from typing import List, Tuple, Union
from util import clamped_pchip, scale_float
import randomness_kit


def frag_score(data: bytes | str):
    data_count = len(data)
    frag_score = 0.0
    frag_score_multiplier = frag_multiplier_curve(data_count)
    frag_score_total_weight = 0
    fragments = find_non_overlapping_fragments(
        data, count=30, t=2, global_non_overlap=True
    )
    fragments_count = len(fragments)
    # 分段范围越小越好，如果文本长度足够，分段数量越少越好。
    for frag in fragments:
        frag_index: int = frag[0]  # type: ignore
        frag_index_multiplier = frag_index_multiplier_curve(
            frag_index / fragments_count
        )
        frag_ranges: List[Tuple[int, int]] = frag[1]  # type: ignore
        frag_range_count = len(frag_ranges)
        frag_range_len = frag_ranges[0][1] - frag_ranges[0][0]
        frag_range_data = data[frag_ranges[0][0] : frag_ranges[0][1]]
        frag_range_count_score = frag_range_count_curve(frag_range_count)
        frag_range_entropy_score = randomness_score(frag_range_data)
        frag_range_score = frag_range_score_curve(frag_range_len)
        # 0.0 ~ 2.0
        frag_range_score_result = frag_range_count_score * (
            min(1.0, (frag_range_entropy_score + frag_range_score))
        )
        # 0.0 ~ 1.0
        frag_range_score_result = (
            frag_range_norm_curve(frag_range_score_result) * frag_index_multiplier
        )
        # print(
        #     "idx",
        #     frag_index,
        #     "mul",
        #     f"{frag_index_multiplier:.06f}",
        #     "cnt",
        #     frag_range_count,
        #     "len",
        #     frag_range_len,
        #     "sc",
        #     f"{frag_range_count_score:.06f}",
        #     "ent",
        #     f"{frag_range_entropy_score:.06f}",
        #     "rs",
        #     f"{frag_range_score:.06f}",
        #     "score",
        #     f"{frag_range_score_result:.06f}",
        #     "data",
        #     frag_range_data,
        # )
        new_total_weight = frag_score_total_weight + frag_index_multiplier
        if new_total_weight != 0:
            new_score = (
                frag_score * frag_score_total_weight
                + frag_range_score_result * frag_index_multiplier
            ) / new_total_weight
            frag_score = min(new_score, 1.0)
            frag_score_total_weight = new_total_weight
        # for rg in frag_ranges:
        #     rg_start, rg_end = rg[0], rg[1]
    frag_final_score = (frag_score + frag_score_multiplier) / 2
    # print(
    #     f"frag_final_score = {frag_final_score} = {frag_score}, {frag_score_multiplier}"
    # )
    return frag_final_score


def frag_index_multiplier_curve(x: float) -> float:
    x_pts = [0.0, 0.1, 0.3, 0.5, 0.8, 1.0]
    y_pts = [1.0, 0.5, 0.15, 0.05, 0.03, 0.0]
    return clamped_pchip(x_pts, y_pts, x)


def frag_range_norm_curve(x: float) -> float:
    x_pts = [0.0, 1.0, 2.0]
    y_pts = [0.0, 0.3, 1.0]
    return clamped_pchip(x_pts, y_pts, x)


def frag_range_count_curve(x: float) -> float:
    x_pts = [0.0, 1.0, 10.0, 15.0, 30.0, 50.0, 100.0, 1000.0]
    y_pts = [1.0, 1.0, 0.2, 0.1, 0.05, 0.03, 0.01, 0.0]
    return clamped_pchip(x_pts, y_pts, x)


def frag_range_score_curve(x: float) -> float:
    x_pts = [0.0, 1.0, 10, 50, 100, 500]
    y_pts = [1.0, 1.0, 0.1, 0.08, 0.001, 0.0]
    return clamped_pchip(x_pts, y_pts, x)


def frag_multiplier_curve(x: float) -> float:
    x_pts = [0.0, 32, 64, 128, 256]
    y_pts = [0, 0.1, 0.3, 0.9, 1]
    return clamped_pchip(x_pts, y_pts, x)


def randomness_score(data: bytes | str):
    """
    计算随机度分数. 范围 `0.0 ~ 1.0`
    """
    uniq = set(data)
    total = len(data)
    uniqs = len(uniq)
    uniq_ratio = uniqs / total
    uniq_score = uniqs_curve(uniqs) * uniq_ratio
    me = min_entropy(data) * 1
    sh = norm_shannon(data) * 1
    score_me = min_entropy_score_curve(me)
    score_sh = norm_shannon_score_curve(sh)
    r = score_me + score_sh + uniq_score
    r *= norm_shannon_result_curve(score_sh)
    r = randomness_score_curve(r)
    r = ((r * score_me) * 0.5) + (r * 0.5)
    # print(
    #     f"me={me:.06f} sh={sh:.06f} | me={score_me:.06f} sh={score_sh:.06f} uq={uniq_score:.06f} r={r:.06f}"
    # )
    return r


def randomness_score_curve(x: float) -> float:
    x_pts = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0]
    y_pts = [0.0, 0.05, 0.2, 0.4, 0.8, 0.9, 1.0]
    return clamped_pchip(x_pts, y_pts, x)


def uniqs_curve(x: float) -> float:
    x_pts = [0.0, 16, 64, 128, 256]
    y_pts = [0, 0.3, 0.5, 0.9, 1]
    return clamped_pchip(x_pts, y_pts, x)


def min_entropy(data: bytes | str) -> float:
    return randomness_kit.min_entropy.measure_entropy(data)


def shannon(data: bytes | str) -> float:
    return randomness_kit.shannon_entropy.measure_entropy(data)


def norm_shannon(data: bytes | str) -> float:
    return randomness_kit.shannon_entropy.measure_normalized_metric_entropy(data)


def norm_shannon_score_curve(x: float) -> float:
    # 过高的熵很可能是故意的
    x_pts = [0.0, 0.1, 0.3, 0.6, 0.9, 1.0, 1.1, 1.11, 1.15, 1.2, 1.3]
    y_pts = [0.0, 0.1, 0.3, 0.6, 0.9, 1.0, 0.2, 0.1, 0.02, 0.005, 0.0]
    return clamped_pchip(x_pts, y_pts, x)


def min_entropy_score_curve(x: float) -> float:
    x_pts = [0.0, 2.0, 4.0, 6.0, 8.0]
    y_pts = [0.0, 0.2, 0.6, 0.9, 1.0]
    return clamped_pchip(x_pts, y_pts, x)


def norm_shannon_result_curve(x: float) -> float:
    x_pts = [0.0, 0.25, 0.5, 0.75, 1.0]
    y_pts = [0.01, 0.1, 0.5, 0.8, 1.0]
    return clamped_pchip(x_pts, y_pts, x)


def find_non_overlapping_fragments(
    data: Union[str, bytes],
    count: int = 100,
    t: int = 2,
    global_non_overlap: bool = False,
) -> List[List[Union[int, List[Tuple[int, int]]]]]:
    """
    在字符串或字节串 data 中寻找最多 b 个出现次数至少为 c 次的不重叠片段。

    :param data: 输入的 str 或 bytes
    :param count: 最多返回的片段数量 (默认 100)
    :param t: 每个片段在 a 中最少出现的非重叠次数 (默认 2)
    :param global_non_overlap:
        - False (默认): 同一个片段在 data 中的多次出现互不重叠
        - True: 要求不同片段之间在 data 中占据的位置也互不重叠
    :return: 格式为 [[index, [(start1, end1), (start2, end2), ...]], ...]
    """
    res = randomness_kit.strings_frag.find_non_overlapping_fragments(
        data, count, t, global_non_overlap
    )
    ret = []
    for i in res:
        index: int = i["id"]  # type: ignore
        occ: list[dict[str, int]] = i["occurrences"]  # type: ignore
        occs = []
        for n in occ:
            start = n["start"]
            end = n["end"]
            occs.append((start, end))
        r = [index, occs]
        ret.append(r)
    return ret


def recommended_bits(data: bytes | str) -> int:
    s = randomness_score(data)
    return recommended_bits_from_score(s)


def recommended_bits_from_score(randomness_score: float) -> int:
    bits = recommand_curve(randomness_score)
    # print(f"randomness_score={randomness_score} result={bits}")
    if bits < 32:
        return 0
    if bits > 1024:
        return 1024
    return int(bits)


def recommand_curve(x: float) -> float:
    x_pts = [0.0, 0.08, 0.2, 0.5, 0.8, 0.9, 0.95, 1.0]
    y_pts = [0.0, 32, 48, 64, 256, 819, 921, 1024]
    return clamped_pchip(x_pts, y_pts, x)


def test(data: bytes | str, desc: str):
    ent = randomness_score(data)
    # frag = frag_score(data)
    print(f"{desc}:", f"ent={ent:.10f}")


test_string_1 = """
6月 07 07:00:43 xiaoxin niri[4334]: 2026-06-06T23:00:43.460183Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:44 xiaoxin niri[4334]: 2026-06-06T23:00:44.460482Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:45 xiaoxin niri[4334]: 2026-06-06T23:00:45.460761Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:46 xiaoxin niri[4334]: 2026-06-06T23:00:46.461026Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:47 xiaoxin niri[4334]: 2026-06-06T23:00:47.461334Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:48 xiaoxin niri[4334]: 2026-06-06T23:00:48.461618Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:49 xiaoxin niri[4334]: 2026-06-06T23:00:49.462132Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:50 xiaoxin niri[4334]: 2026-06-06T23:00:50.462359Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:51 xiaoxin niri[4334]: 2026-06-06T23:00:51.462533Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:52 xiaoxin niri[4334]: 2026-06-06T23:00:52.463008Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:53 xiaoxin niri[4334]: 2026-06-06T23:00:53.463179Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:54 xiaoxin niri[4334]: 2026-06-06T23:00:54.463315Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:55 xiaoxin niri[4334]: 2026-06-06T23:00:55.463481Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:56 xiaoxin niri[4334]: 2026-06-06T23:00:56.463718Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:57 xiaoxin niri[4334]: 2026-06-06T23:00:57.464224Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:58 xiaoxin niri[4334]: 2026-06-06T23:00:58.464636Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:00:59 xiaoxin niri[4334]: 2026-06-06T23:00:59.464728Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
6月 07 07:01:00 xiaoxin niri[4334]: 2026-06-06T23:01:00.464839Z  INFO new: smithay::output: Creating new Output name="" name="" physical=PhysicalProperties { size: Size<smithay::>
"""


def main():
    test("1234567890qwertyuiopasdfghjkl", "不重复字符")
    test("drrftgyhuji秒iOS啊啊啊啊啊啊啊啊啊", "乱敲键盘1")
    test("(roll-mnemonic) sbchild@xiaoxin:~/roll-mnemonic$ uv run shannon.py", "终端")
    test("d6g7347gdfh7834g27df83o2d", "乱敲键盘2")
    b3 = blake3(b"d6g7347gdfh7834g27df83o2d")
    test(b3.hexdigest(), "随机hex")
    b4 = blake3(b"d6g7347gdfh7834g27df83o2d")
    test(base64.b64encode(b4.digest()).decode(), "随机base64")
    b5 = blake3(b"d6g7347gdfh7834g27df83o2d")
    test(b5.digest(), "随机字节")
    b6 = blake3(b"d6g7347gdfh7834g27df83o2d")
    test(b6.digest(length=512), "更长的随机字节")
    # test(test_string_1, "重复日志")


if __name__ == "__main__":
    main()
