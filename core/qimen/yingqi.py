"""
core/qimen/yingqi.py
====================
奇门遁甲·应期推算（事应何时）。

应期不离用神宫：定用神之宫后，依其旺衰、地支、空墓之态，推事应之时——
  · 旺衰定远近：用神宫旺相则近应（应日/应时），休囚死绝则远应（应月/应年）。
  · 地支定其时：用神宫所纳地支「值临」或「逢冲」而动，即应于该支之月/日/时。
  · 逢空待填实：用神宫旬空，则待出空、填实（本支值临）或冲空之时方应。
  · 入墓待冲开：用神入墓，则待冲墓库地支之时，开库而出方应。
  · 符使先后：值符落宫之冲日主先应，值使门到宫主后应（《奇门法穷》符应主先、使应主后）。

复用 yongshen_palaces（用神宫定位）与 palace_layers（每宫层级·旺衰空墓），
将地支译为农历月与时辰，给具体可循之应期。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.qimen.palace_layers import GONG_DIZHI

# 六冲
_CHONG: Dict[str, str] = {
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}
# 地支 → 农历月
ZHI_MONTH: Dict[str, str] = {
    "寅": "正月", "卯": "二月", "辰": "三月", "巳": "四月", "午": "五月", "未": "六月",
    "申": "七月", "酉": "八月", "戌": "九月", "亥": "十月", "子": "十一月", "丑": "十二月",
}
# 地支 → 时辰
ZHI_HOUR: Dict[str, str] = {
    "子": "子时(23-1)", "丑": "丑时(1-3)", "寅": "寅时(3-5)", "卯": "卯时(5-7)",
    "辰": "辰时(7-9)", "巳": "巳时(9-11)", "午": "午时(11-13)", "未": "未时(13-15)",
    "申": "申时(15-17)", "酉": "酉时(17-19)", "戌": "戌时(19-21)", "亥": "亥时(21-23)",
}

# 旺相/休囚 → 远近（用 quality 简判）
_NEAR = {"大吉", "吉", "小吉"}
_FAR = {"凶", "大凶"}


def _zhi_times(zhi: str) -> str:
    m = ZHI_MONTH.get(zhi, "")
    h = ZHI_HOUR.get(zhi, "")
    return f"{zhi}（{m}／{h}）" if (m or h) else zhi


def _palace_yingqi(layout: Dict[str, Any], role: str, symbol: str,
                   palace_name: str) -> Dict[str, Any]:
    """单一用神宫之应期。"""
    palace = next((p for p in layout.get("palaces", [])
                   if p.get("palace_name") == palace_name), None)
    if not palace:
        return {"role": role, "palace": palace_name, "yingqi": "用神不入九宫，应期难定。"}

    zhis = GONG_DIZHI.get(palace_name, [])
    layers = palace.get("layers", {}) or {}
    flags = {f["type"] for f in layers.get("flags", [])}
    quality = palace.get("quality", "")

    # 远近
    if quality in _NEAR:
        far = "近应——应于日、时（用神宫旺相得气，事来速）"
    elif quality in _FAR:
        far = "远应——应于月、年（用神宫休囚无力，事来迟）"
    else:
        far = "中应——应于月、日（用神宫平和，远近适中）"

    parts: List[str] = []
    # 空亡：待填实/出空
    if "空亡" in flags:
        fill = "、".join(_zhi_times(z) for z in zhis)
        chong = "、".join(_zhi_times(_CHONG[z]) for z in zhis if z in _CHONG)
        parts.append(f"用神逢空——待填实（{fill}本支值临）或冲空（{chong}）之时方应，眼下虚而未发。")
    # 入墓：待冲墓开库
    elif "入墓" in flags:
        # 入墓 flag 的 desc 含墓库地支；从 GONG_DIZHI 取本宫支之冲为冲墓
        chong = "、".join(_zhi_times(_CHONG[z]) for z in zhis if z in _CHONG)
        parts.append(f"用神入墓——气闭难发，待冲墓开库（{chong}）之时方应。")
    else:
        zhi_t = "、".join(_zhi_times(z) for z in zhis)
        chong_t = "、".join(_zhi_times(_CHONG[z]) for z in zhis if z in _CHONG)
        parts.append(f"用神宫地支{zhi_t}值临之时引动，或逢冲（{chong_t}）而动，即为应期。")

    return {
        "role": role, "symbol": symbol, "palace": palace_name,
        "quality": quality, "flags": sorted(flags),
        "far_near": far,
        "yingqi": far + "；" + "".join(parts),
    }


def analyze_yingqi(layout: Dict[str, Any]) -> Dict[str, Any]:
    """全局应期推算：就已定之用神宫（值符/值使/日干/时干/年命）逐一推应期。"""
    ys = layout.get("yongshen_palaces", {})
    if not ys.get("items"):
        # 若未定用神宫，尝试即时定位
        try:
            from core.qimen.yongshen import analyze_yongshen_palaces
            ys = analyze_yongshen_palaces(layout)
            layout["yongshen_palaces"] = ys
        except Exception:
            return {"success": False, "error": "用神宫未定，应期无从推算。"}

    rows: List[Dict[str, Any]] = []
    # 应期主取值符（先应）、值使（后应）、日干（求测人之事）
    role_order = {"值符宫": 0, "值使宫": 1, "日干宫": 2, "时干宫": 3, "年命宫": 4}
    for it in sorted(ys["items"], key=lambda x: role_order.get(x["role"], 9)):
        rows.append(_palace_yingqi(layout, it["role"], it.get("symbol", ""), it["palace"]))

    # 符使先后总则
    zhifu_row = next((r for r in rows if r["role"] == "值符宫"), None)
    zhishi_row = next((r for r in rows if r["role"] == "值使宫"), None)
    order_note = "《奇门法穷》：符应主先、使应主后——先以值符落宫定先应之期，后以值使门落宫定后应之期。"

    summary = order_note
    if zhifu_row:
        summary += f"　先应：{zhifu_row['palace']}，{zhifu_row['far_near'].split('——')[0]}。"
    if zhishi_row:
        summary += f"　后应：{zhishi_row['palace']}，{zhishi_row['far_near'].split('——')[0]}。"

    result = {"success": True, "rows": rows, "summary": summary, "method": order_note}
    layout["yingqi"] = result
    return result
