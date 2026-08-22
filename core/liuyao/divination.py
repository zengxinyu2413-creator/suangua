"""
core/liuyao/divination.py
=========================
Three-coin, yarrow-stalk, and time-based LiuYao divination.
Now self-contained — no missing file imports. (B-02 fixed)
"""
from __future__ import annotations
import random
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

from core.constants import YaoType, LineType, yaotype_to_line, is_changing, TRIGRAMS
from core.liuyao.hexagram_data import HEXAGRAM_DATA, HEXAGRAM_TRIGRAM_MAPPING


# ─────────────────────────────────────────────────────────────
# Trigram + Hexagram helpers
# ─────────────────────────────────────────────────────────────

def _lines_to_trigram_name(lines: List[LineType]) -> str:
    """
    Match a 3-line pattern to a trigram name.
    lines[0]=bottom, lines[1]=middle, lines[2]=top.
    """
    pattern = tuple(lines)
    for name, data in TRIGRAMS.items():
        tg_lines = tuple(
            LineType.YANG if l == "阳" else LineType.YIN
            for l in data["lines"]
        )
        if tg_lines == pattern:
            return name
    raise ValueError(f"No trigram for lines {pattern}")


def _hexagram_number(lower: str, upper: str) -> int:
    """Find the King-Wen hexagram number for (lower, upper) trigram pair."""
    for num, (l, u) in HEXAGRAM_TRIGRAM_MAPPING.items():
        if l == lower and u == upper:
            return num
    raise ValueError(f"No hexagram for ({lower}, {upper})")


def _build_hexagram_dict(num: int) -> Dict[str, Any]:
    """Return a serialisable hexagram dict by King-Wen number."""
    data    = HEXAGRAM_DATA[num]
    lower_n, upper_n = HEXAGRAM_TRIGRAM_MAPPING[num]
    lower   = TRIGRAMS[lower_n]
    upper   = TRIGRAMS[upper_n]
    return {
        "number":   num,
        "name":     data["name"],
        "upper":    {**upper,  "name": upper_n},
        "lower":    {**lower,  "name": lower_n},
        "judgment": data["judgment"],
        "image":    data.get("image", ""),
        "lines":    data.get("lines", {}),
        "interpretation": data.get("interpretation", ""),
    }


def _get_changed_hexagram(
    yaos: List[YaoType],
    orig_lower: str, orig_upper: str,
) -> Optional[Dict[str, Any]]:
    """
    Apply changing lines (老阴/老阳) to produce the changed hexagram.
    Returns None if no lines change.
    """
    if not any(is_changing(y) for y in yaos):
        return None

    changed_lines = []
    for y in yaos:
        line = yaotype_to_line(y)
        if is_changing(y):
            # Flip the line
            line = LineType.YIN if line == LineType.YANG else LineType.YANG
        changed_lines.append(line)

    new_lower_name = _lines_to_trigram_name(changed_lines[:3])
    new_upper_name = _lines_to_trigram_name(changed_lines[3:])
    new_num = _hexagram_number(new_lower_name, new_upper_name)
    return _build_hexagram_dict(new_num)


# ─────────────────────────────────────────────────────────────
# Divination methods
# ─────────────────────────────────────────────────────────────

def coin_divination(yao_values: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Three-coin method. Each coin = 0 (tails) or 1 (heads).
    Sum 3 coins → 6=老阴 7=少阳 8=少阴 9=老阳.

    If yao_values provided (list of 6 ints 6/7/8/9), use directly.
    """
    if yao_values and len(yao_values) == 6:
        _map = {6: YaoType.LAO_YIN, 7: YaoType.SHAO_YANG,
                8: YaoType.SHAO_YIN, 9: YaoType.LAO_YANG}
        yaos = [_map[v] for v in yao_values]
    else:
        yaos = []
        for _ in range(6):
            heads = sum(random.randint(0, 1) for _ in range(3))
            # 0→6老阴 1→7少阳 2→8少阴 3→9老阳
            coin_map = {0: YaoType.LAO_YIN, 1: YaoType.SHAO_YANG,
                        2: YaoType.SHAO_YIN, 3: YaoType.LAO_YANG}
            yaos.append(coin_map[heads])

    return _make_result("coin", yaos)


def yarrow_divination() -> Dict[str, Any]:
    """
    Yarrow-stalk method with correct probability distribution:
    9(老阳)=3/16  8(少阴)=7/16  7(少阳)=5/16  6(老阴)=1/16
    """
    yaos = []
    weights = [1, 5, 7, 3]   # 老阴 少阳 少阴 老阳
    types = [YaoType.LAO_YIN, YaoType.SHAO_YANG, YaoType.SHAO_YIN, YaoType.LAO_YANG]
    for _ in range(6):
        yaos.append(random.choices(types, weights=weights, k=1)[0])
    return _make_result("yarrow", yaos)


def time_divination(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Time-based divination (梅花易数·时间起卦法).
    
    古书《梅花易数》正法 — 用农历年支序、农历月、农历日、时辰序：
      上卦数 = (年支序 + 农历月 + 农历日) % 8 (0 取 8)
      下卦数 = (年支序 + 农历月 + 农历日 + 时辰序) % 8 (0 取 8)
      动爻数 = (年支序 + 农历月 + 农历日 + 时辰序) % 6 (0 取 6)
    
    年支序：子1、丑2、寅3、卯4、辰5、巳6、午7、未8、申9、酉10、戌11、亥12
    时辰序：子1、丑2、寅3、卯4、辰5、巳6、午7、未8、申9、酉10、戌11、亥12
    
    （旧版用公历年/24小时制，是误用；古书严格按农历干支起卦。）
    """
    if dt is None:
        dt = datetime.now()
    
    # 用农历 + 时辰序号（古法）
    try:
        from lunar_python import Solar
        sol = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute or 0, 0)
        lunar = sol.getLunar()
        year_branch = lunar.getYearZhi()
        # 年支 → 序数（子1...亥12）
        ZHI_ORDER = "子丑寅卯辰巳午未申酉戌亥"
        y_num = ZHI_ORDER.index(year_branch) + 1
        m = abs(lunar.getMonth())  # 农历月（处理闰月）
        d = lunar.getDay()
        # 时辰序：23-1 子时=1, 1-3 丑=2, ..., 21-23 亥=12
        # 公式：((hour + 1) // 2) % 12 + 1，但 23 时归子时
        if dt.hour == 23:
            h_num = 1
        else:
            h_num = ((dt.hour + 1) // 2) % 12 + 1
    except Exception:
        # 回退到公历（仅当 lunar-python 不可用）
        y_num, m, d, h_num = dt.year, dt.month, dt.day, dt.hour or 1

    upper_num = (y_num + m + d) % 8 or 8
    lower_num = (y_num + m + d + h_num) % 8 or 8
    change_pos = (y_num + m + d + h_num) % 6 or 6  # 1-based

    # Find trigram names by King-Wen number
    from core.constants import KING_WEN_TRIGRAM
    upper_name = KING_WEN_TRIGRAM[upper_num]
    lower_name = KING_WEN_TRIGRAM[lower_num]

    upper_tg = TRIGRAMS[upper_name]
    lower_tg = TRIGRAMS[lower_name]

    # Build 6 yaos (bottom=lower[0], top=upper[2])
    six_lines = [
        LineType.YANG if l == "阳" else LineType.YIN
        for l in lower_tg["lines"] + upper_tg["lines"]
    ]

    yaos = []
    for i, line in enumerate(six_lines):
        pos = i + 1  # 1-based
        if pos == change_pos:
            yt = YaoType.LAO_YANG if line == LineType.YANG else YaoType.LAO_YIN
        else:
            yt = YaoType.SHAO_YANG if line == LineType.YANG else YaoType.SHAO_YIN
        yaos.append(yt)

    return _make_result("time", yaos)


def manual_divination(yao_values: List[int]) -> Dict[str, Any]:
    """Accept 6 explicit yao values (6/7/8/9) from bottom to top."""
    return coin_divination(yao_values)


# ─────────────────────────────────────────────────────────────
# Internal result builder
# ─────────────────────────────────────────────────────────────

def _make_result(method: str, yaos: List[YaoType]) -> Dict[str, Any]:
    # Bottom 3 → lower trigram; top 3 → upper trigram
    lower_lines = [yaotype_to_line(y) for y in yaos[:3]]
    upper_lines = [yaotype_to_line(y) for y in yaos[3:]]

    lower_name = _lines_to_trigram_name(lower_lines)
    upper_name = _lines_to_trigram_name(upper_lines)
    orig_num   = _hexagram_number(lower_name, upper_name)

    original = _build_hexagram_dict(orig_num)
    changed  = _get_changed_hexagram(yaos, lower_name, upper_name)

    changing_lines = [i + 1 for i, y in enumerate(yaos) if is_changing(y)]

    yao_details = []
    for i, y in enumerate(yaos):
        line_data = HEXAGRAM_DATA[orig_num]["lines"].get(i + 1, "")
        yao_details.append({
            "position":    i + 1,
            "yao_type":    y.value,
            "line":        yaotype_to_line(y).value,
            "is_changing": is_changing(y),
            "description": line_data,
        })

    # ── 六合/六冲/游魂/归魂 卦型判断 ─────────────────────────────────────────
    # 六合卦: 各爻地支两两相合 (需annotate_with_najia后才可完整判断, 此处占卦型)
    # 游魂卦 / 归魂卦: 由八宫分类中的宫位决定 (position 7=游魂, 8=归魂)
    from core.liuyao.najia import HEXAGRAM_PALACE
    palace_info = HEXAGRAM_PALACE.get(orig_num, ("", 0))
    palace_name, palace_pos = palace_info
    palace_pos_name = {
        1: "八纯卦", 2: "一变卦", 3: "二变卦", 4: "三变卦",
        5: "四变卦", 6: "五变卦", 7: "游魂卦", 8: "归魂卦",
    }.get(palace_pos, "")

    # 六合/六冲 detection from branch pairs (requires najia annotation first)
    # Mark as pending — will be set by annotate_with_najia
    hex_type = palace_pos_name  # will be enriched after najia annotation

    return {
        "method":           method,
        "original":         original,
        "changed":          changed,
        "changing_lines":   changing_lines,
        "yaos":             yao_details,
        "hex_type":         hex_type,
        "palace_name":      str(palace_name),
        "palace_position":  palace_pos,
    }
