"""
core/qimen/zeji.py
==================
奇门遁甲·择吉（与择日打通）——为某事择「时空」之吉。

择日定「日」之吉（建除十二神、黄道黑道、宜忌、神煞），奇门定「时辰+方位」之吉
（用事吉门吉星吉奇、吉格、用神宫旺）。本模块二者合参：

  1. 以 date_selection.select_dates 取本月吉日（已含建除/黄道/宜忌/分数）。
  2. 于每个吉日，扫十二时辰，各起奇门时盘，按 purpose_analysis 评该时辰
     之用事得分（最佳宫之吉门吉星吉奇），再加吉格奖、凶格罚。
  3. 日吉分 + 时辰奇门分 合为总分，排出最佳「日×时辰×方位」之吉。

如此一事既得吉日，又得吉时与吉方，乃奇门「趋吉避凶、择时择方」之实用。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.qimen.algorithm import calculate_qimen
from core.qimen.purpose_analysis import get_purpose_analysis, PURPOSE_LOGIC

# 时辰 → 代表时（取每时辰中点附近整点）
_SHICHEN_HOUR = {
    "子": 0, "丑": 2, "寅": 4, "卯": 6, "辰": 8, "巳": 10,
    "午": 12, "未": 14, "申": 16, "酉": 18, "戌": 20, "亥": 22,
}
_SHICHEN_LABEL = {
    "子": "子时(23-1)", "丑": "丑时(1-3)", "寅": "寅时(3-5)", "卯": "卯时(5-7)",
    "辰": "辰时(7-9)", "巳": "巳时(9-11)", "午": "午时(11-13)", "未": "未时(13-15)",
    "申": "申时(15-17)", "酉": "酉时(17-19)", "戌": "戌时(19-21)", "亥": "亥时(21-23)",
}
_PALACE_DIR = {
    "坎宫": "北", "坤宫": "西南", "震宫": "东", "巽宫": "东南", "中宫": "中",
    "乾宫": "西北", "兑宫": "西", "艮宫": "东北", "离宫": "南",
}

_SEV_BONUS = {
    "auspicious_great": 4, "auspicious": 2, "mixed": 0,
    "inauspicious": -2, "inauspicious_great": -3,
}


def _score_hour_chart(layout: Dict[str, Any], purpose: str) -> Dict[str, Any]:
    """评一时盘对某事之吉：最佳宫用事分 + 吉格奖凶格罚。"""
    pa = get_purpose_analysis(layout, purpose)
    best = (pa.get("best_palaces") or [])
    best_p = best[0] if best else None
    base = best_p.get("purpose_score", 0) if best_p else 0

    pat_bonus = 0
    ji, xiong = [], []
    for pat in layout.get("patterns", []):
        b = _SEV_BONUS.get(pat.get("severity", ""), 0)
        pat_bonus += b
        if b > 0:
            ji.append(pat.get("name", ""))
        elif b < 0:
            xiong.append(pat.get("name", ""))

    score = base + pat_bonus
    return {
        "score": score, "base": base, "pattern_bonus": pat_bonus,
        "best_palace": best_p.get("palace_name", "") if best_p else "",
        "best_dir": _PALACE_DIR.get(best_p.get("palace_name", ""), "") if best_p else "",
        "best_door": best_p.get("door", "") if best_p else "",
        "best_star": best_p.get("star", "") if best_p else "",
        "best_stem": best_p.get("tian_pan", "") if best_p else "",
        "ji_ge": ji[:3], "xiong_ge": xiong[:3],
    }


def select_qimen_times(purpose: str, year: int, month: int,
                       birth_year: Optional[int] = None,
                       top_n: int = 8,
                       day_limit: int = 12) -> Dict[str, Any]:
    """
    为某事择「日×时辰×方位」之吉（奇门 × 择日）。

    purpose : 用事（须在 PURPOSE_LOGIC 内，如 求财/出行/谈判…）
    year/month : 择期之年月
    birth_year : 求测人生年（可选，传给择日避本命冲克）
    top_n : 返回前 N 个最佳时空
    day_limit : 最多扫描的吉日数（控制计算量）
    """
    if purpose not in PURPOSE_LOGIC:
        # 容许择日的近义用事映射到奇门用事
        purpose = {"婚嫁": "婚姻", "搬家": "出行", "开业": "求财",
                   "求职": "事业"}.get(purpose, "谋事")

    # ── 1. 择日取吉日 ──
    from core.date_selection.selector import select_dates
    # 择日 purpose 用近义（择日模块自有 purpose 词表，宽松传入）
    try:
        ds = select_dates(purpose, year, month, birth_year=birth_year)
    except Exception:
        ds = select_dates("祈福", year, month)
    aus_days = ds.get("auspicious_days", []) or ds.get("all_days", [])
    aus_days = sorted(aus_days, key=lambda d: d.get("score", 0), reverse=True)[:day_limit]

    # ── 2. 每吉日扫十二时辰，起奇门时盘评分 ──
    candidates: List[Dict[str, Any]] = []
    for day in aus_days:
        d_num = day.get("day")
        if not d_num:
            continue
        day_score = day.get("score", 0)
        for zhi, hr in _SHICHEN_HOUR.items():
            try:
                lay = calculate_qimen(year, month, int(d_num), hr)
                sc = _score_hour_chart(lay, purpose)
            except Exception:
                continue
            total = day_score + sc["score"]
            candidates.append({
                "date": day.get("date", f"{year}-{month:02d}-{int(d_num):02d}"),
                "day": d_num,
                "ganzhi": day.get("ganzhi", ""),
                "officer": day.get("officer", ""),
                "huangdao": day.get("huangdao", False),
                "shichen": _SHICHEN_LABEL.get(zhi, zhi),
                "shichen_zhi": zhi,
                "best_dir": sc["best_dir"],
                "best_palace": sc["best_palace"],
                "best_door": sc["best_door"],
                "best_star": sc["best_star"],
                "day_score": day_score,
                "qimen_score": sc["score"],
                "total_score": total,
                "ji_ge": sc["ji_ge"],
                "xiong_ge": sc["xiong_ge"],
                "summary": (
                    f"{day.get('date','')} {_SHICHEN_LABEL.get(zhi, zhi)}："
                    f"{day.get('officer','')}日{'·黄道' if day.get('huangdao') else ''}，"
                    f"用事吉方在{sc['best_palace']}（{sc['best_dir']}方·{sc['best_door']}{sc['best_star']}）"
                    + (f"，吉格：{'、'.join(sc['ji_ge'])}" if sc["ji_ge"] else "")
                    + (f"，须防：{'、'.join(sc['xiong_ge'])}" if sc["xiong_ge"] else "")
                    + "。"
                ),
            })

    candidates.sort(key=lambda c: c["total_score"], reverse=True)
    top = candidates[:top_n]

    return {
        "success": True,
        "purpose": purpose,
        "year": year, "month": month,
        "scanned_days": len(aus_days),
        "scanned_times": len(candidates),
        "best_times": top,
        "note": "总分 = 择日吉分（建除/黄道/宜忌）+ 奇门时盘用事分（吉门吉星吉奇+吉格）。"
                "择吉时携用事吉方而行，趋生门、避凶格，则时空俱利。",
        "principle": PURPOSE_LOGIC.get(purpose, {}).get("principle", ""),
    }
