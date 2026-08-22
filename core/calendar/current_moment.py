"""
core/calendar/current_moment.py
===============================
当下时空（此刻四柱）——任何解读皆须纳入「当下时辰」与分析结果合参。

提供：当前年月日时四柱、时辰地支/名/五行、当前节气；并提供「此刻五行 vs 用神/忌神」
之扶抑判断，供各模块 master_synthesis 织入「当下时辰」一层：
  「此刻为 X 年 Y 月 Z 日 时辰干支，时令五行于本命用神为扶/为抑，故此时宜/忌……」
全部基于历法底座（节气历），与排盘同源。
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, Optional, List

# 五行常量一律取自 core.constants（单一真源，杜绝重复定义）
from core.constants import (
    TIANGAN_WUXING as _GAN_WX,
    DIZHI_WUXING as _ZHI_WX,
    WUXING_SHENG as _SHENG,
    WUXING_KE as _KE,
)
# 时辰名
_ZHI_HOUR_NAME = {
    "子": "子时(23-1)", "丑": "丑时(1-3)", "寅": "寅时(3-5)", "卯": "卯时(5-7)",
    "辰": "辰时(7-9)", "巳": "巳时(9-11)", "午": "午时(11-13)", "未": "未时(13-15)",
    "申": "申时(15-17)", "酉": "酉时(17-19)", "戌": "戌时(19-21)", "亥": "亥时(21-23)",
}


def current_sizhu(now: Optional[datetime] = None) -> Dict[str, Any]:
    """当前此刻四柱（年/月/日/时干支）+ 时辰 + 节气。"""
    now = now or datetime.now()
    out: Dict[str, Any] = {"datetime": now.strftime("%Y-%m-%d %H:%M")}
    try:
        from lunar_python import Solar
        lun = Solar.fromYmdHms(now.year, now.month, now.day, now.hour, now.minute, 0).getLunar()
        year_gz = lun.getYearInGanZhiByLiChun()   # 立春换年
        month_gz = lun.getMonthInGanZhi()
        day_gz = lun.getDayInGanZhi()
        hour_gz = lun.getTimeInGanZhi()
        hour_zhi = lun.getTimeZhi()
    except Exception:
        from core.calendar.solar_terms import day_ganzhi_at, month_ganzhi_at, month_dizhi_at
        year_gz = ""
        month_gz = month_ganzhi_at(now)
        day_gz = day_ganzhi_at(now)
        hour_gz = ""
        hour_zhi = ""
    from core.calendar.solar_terms import current_solar_term
    out.update({
        "year_gz": year_gz, "month_gz": month_gz, "day_gz": day_gz, "hour_gz": hour_gz,
        "hour_zhi": hour_zhi,
        "hour_name": _ZHI_HOUR_NAME.get(hour_zhi, ""),
        "hour_wuxing": _ZHI_WX.get(hour_zhi, ""),
        "day_gan": day_gz[0] if day_gz else "",
        "day_gan_wuxing": _GAN_WX.get(day_gz[0], "") if day_gz else "",
        "solar_term": current_solar_term(now) or "",
    })
    # 此刻当令五行（月令 + 时辰）
    out["seasonal_wx"] = _ZHI_WX.get(month_gz[1], "") if month_gz and len(month_gz) > 1 else ""
    return out


def _wx_relation(src: str, tgt: str) -> str:
    """src 五行 对 tgt 五行 的关系。"""
    if not src or not tgt:
        return ""
    if src == tgt:
        return "比和"
    if _SHENG.get(src) == tgt:
        return "生"   # src 生 tgt
    if _KE.get(src) == tgt:
        return "克"   # src 克 tgt
    if _SHENG.get(tgt) == src:
        return "被生"  # tgt 生 src（即 src 泄于…实为 tgt 之子）
    if _KE.get(tgt) == src:
        return "被克"
    return ""


def moment_vs_yongshen(moment: Dict[str, Any],
                       yong_wx: List[str] | str,
                       ji_wx: List[str] | str = "") -> Dict[str, Any]:
    """
    此刻时令五行（时辰 + 月令）对本命用神/忌神之扶抑。
    返回 {tone: 扶用/助忌/中性, quality: 吉/中/凶, note}。
    """
    yong = [yong_wx] if isinstance(yong_wx, str) else list(yong_wx or [])
    ji = [ji_wx] if isinstance(ji_wx, str) else list(ji_wx or [])
    yong = [w for w in yong if w]
    ji = [w for w in ji if w]

    hour_wx = moment.get("hour_wuxing", "")
    seas_wx = moment.get("seasonal_wx", "")
    cur_wxs = [w for w in (hour_wx, seas_wx) if w]

    score = 0
    hits = []
    for w in cur_wxs:
        if w in yong:
            score += 1
            hits.append(f"{w}扶用")
        elif w in ji:
            score -= 1
            hits.append(f"{w}助忌")
        else:
            # 生用神者亦为助；克用神者为抑
            for y in yong:
                if _SHENG.get(w) == y:
                    score += 1; hits.append(f"{w}生用神{y}")
                elif _KE.get(w) == y:
                    score -= 1; hits.append(f"{w}克用神{y}")

    if score > 0:
        tone, quality = "扶用", "吉"
    elif score < 0:
        tone, quality = "助忌", "凶"
    else:
        tone, quality = "中性", "中"

    yong_s = "、".join(yong) or "—"
    note = (f"此刻{moment.get('hour_name', '')}（{hour_wx}），月令{seas_wx}，"
            f"于本命用神（{yong_s}）为{tone}"
            + (f"（{('，'.join(hits[:3]))}）" if hits else "") + "。")
    return {"tone": tone, "quality": quality, "note": note,
            "hour_wuxing": hour_wx, "seasonal_wx": seas_wx}


def moment_brief(moment: Dict[str, Any]) -> str:
    """当下时空一句话。"""
    return (f"此刻 {moment.get('datetime', '')}，"
            f"{moment.get('year_gz', '')}年{moment.get('month_gz', '')}月"
            f"{moment.get('day_gz', '')}日{moment.get('hour_gz', '')}时"
            f"（{moment.get('hour_name', '')}），节气{moment.get('solar_term', '')}。")


def moment_dimension(kind: str = "general", now: Optional[datetime] = None) -> Dict[str, Any]:
    """
    生成各模块通用之「当下」维度 + 段落。
    kind: divination(六爻/奇门-占时即基准) | static(玄空/阳宅-流时辅参) |
          dateref(择日-当下为基准) | general。
    """
    mo = current_sizhu(now)
    brief = moment_brief(mo)
    notes = {
        "divination": ("中", "此卦/局即依此刻而起，所断即应此当下之时空，故占时与断语本为一体。"),
        "static": ("中", "宅为静、时为动；此刻时辰之气加临，为流时辅参——当下行事，宜合此时令之吉方吉时。"),
        "dateref": ("中", "以此刻为基准向后择吉，故所选之日皆自当下起算。"),
        "general": ("中", "此刻时空为解读之当下背景，宜与上述分析合参。"),
    }
    q, tail = notes.get(kind, notes["general"])
    return {
        "dimension": {"dim": "当下", "domain": "当下", "quality": q,
                      "verdict": brief + tail},
        "paragraph": "再合当下之时：" + brief + tail,
        "moment": mo,
    }
