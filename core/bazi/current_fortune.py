"""
core/bazi/current_fortune.py
============================
八字·当前运程（大运流年并入主读盘 — 时间维度之命根）。

原八字主读盘（六件套）只断先天静盘，不言「现走何运、今年如何、何时应验」。
然真实命理之用，正在以大运流年引动命局。本模块据已有 forecaster 之大运流年，
萃取「当前大运 + 当年流年 + 近年运势 + 岁运组合」，供 overview/synthesis/
perspectives 织入，使读盘有先天之体、亦有后天之时。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.bazi.forecaster import calculate_dayun, calculate_liunian


def build_current_fortune(chart: Dict[str, Any], gender: str,
                          birth_year: int, current_year: int = 2026) -> Dict[str, Any]:
    if not birth_year:
        return {"available": False}

    try:
        dayun = calculate_dayun(chart, gender, birth_year) or []
        liunian = calculate_liunian(chart, gender, birth_year,
                                    current_year, current_year + 5) or []
    except Exception:
        return {"available": False}

    if not dayun:
        return {"available": False}

    # 当前大运：start_year ≤ 今年 < end_year
    cur_dy = None
    for d in dayun:
        if d.get("start_year", 0) <= current_year < d.get("end_year", 0):
            cur_dy = d
            break
    if cur_dy is None:
        # 未交运（幼年）或超出排运：取第一/末运
        cur_dy = dayun[0] if current_year < dayun[0].get("start_year", 0) else dayun[-1]
        pre_yun = current_year < dayun[0].get("start_year", 0)
    else:
        pre_yun = False

    # 当年流年
    cur_ln = next((l for l in liunian if l.get("year") == current_year), liunian[0] if liunian else None)

    # 岁运组合（当前大运 × 当年流年）
    suiyun = None
    if cur_dy and cur_ln:
        try:
            from core.bazi.combos import analyze_suiyun
            suiyun = analyze_suiyun(chart, cur_dy.get("tiangan", ""), cur_dy.get("dizhi", ""),
                                    cur_ln.get("tiangan", ""), cur_ln.get("dizhi", ""))
        except Exception:
            suiyun = None

    # 近年运势（今年起 5 年）
    recent = [{"year": l.get("year"), "ganzhi": f"{l.get('tiangan','')}{l.get('dizhi','')}",
               "quality": l.get("quality", ""), "shishen": l.get("shishen_gan", "")}
              for l in liunian[:5]]

    # 当前大运十神吉凶（与命局用神比对）
    _GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
               "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
    yong_wx = (chart.get("yong_shen", {}) or {}).get("yong_shen_wx", "")
    ji_wx = (chart.get("yong_shen", {}) or {}).get("ji_shen_wx", "")
    dy_wx = _GAN_WX.get(cur_dy.get("tiangan", ""), "")
    dy_help = None
    if yong_wx and dy_wx:
        if dy_wx == yong_wx:
            dy_help = "扶用"
        elif dy_wx == ji_wx:
            dy_help = "助忌"
        else:
            dy_help = "中性"

    suiyun_brief = ""
    if isinstance(suiyun, dict):
        tags = suiyun.get("tags", []) or []
        notes = suiyun.get("notes", []) or []
        suiyun_brief = ("、".join(tags) + "：" + (notes[0] if notes else "")) if (tags or notes) else ""

    return {
        "available": True,
        "current_year": current_year,
        "pre_yun": pre_yun,
        "current_dayun": {
            "ganzhi": f"{cur_dy.get('tiangan','')}{cur_dy.get('dizhi','')}",
            "tiangan": cur_dy.get("tiangan", ""), "dizhi": cur_dy.get("dizhi", ""),
            "start_age": cur_dy.get("start_age", ""), "end_age": cur_dy.get("end_age", ""),
            "start_year": cur_dy.get("start_year", ""), "end_year": cur_dy.get("end_year", ""),
            "shishen": cur_dy.get("dm_shishen", ""), "quality": cur_dy.get("quality", ""),
            "help": dy_help, "warning": cur_dy.get("warning", ""),
        },
        "current_liunian": {
            "year": cur_ln.get("year") if cur_ln else current_year,
            "ganzhi": f"{cur_ln.get('tiangan','')}{cur_ln.get('dizhi','')}" if cur_ln else "",
            "shishen": cur_ln.get("shishen_gan", "") if cur_ln else "",
            "quality": cur_ln.get("quality", "") if cur_ln else "",
            "summary": cur_ln.get("summary", "") if cur_ln else "",
        } if cur_ln else None,
        "suiyun": suiyun,
        "suiyun_brief": suiyun_brief,
        "recent_years": recent,
    }
