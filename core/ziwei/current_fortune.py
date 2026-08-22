"""
core/ziwei/current_fortune.py
=============================
紫微斗数·当前运限（大限流年并入主读盘 — 时间维度）。

原紫微主读盘（六件套）只断本命十二宫，不言「现行何大限、今年流年落何宫」。
然紫微之用，正在以大限流年行运叠盘。本模块据命盘已有之 decadal_range（大限
年龄段）、ages（流年虚岁）、decadal_stem（大限宫干），萃取「当前大限宫 + 当年
流年宫 + 大限四化」，供 overview/synthesis/perspectives 织入。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional


def _star_names(stars) -> List[str]:
    out = []
    for s in stars or []:
        if isinstance(s, dict):
            out.append(s.get("name", ""))
        else:
            out.append(str(s))
    return [x for x in out if x]


def build_ziwei_current_fortune(chart: Dict[str, Any], birth_year: int,
                                current_year: int = 2026) -> Dict[str, Any]:
    palaces = chart.get("palaces", []) or []
    if not palaces or not birth_year:
        return {"available": False}

    age = current_year - birth_year + 1   # 虚岁

    daxian_pal = None
    liunian_pal = None
    for p in palaces:
        dr = p.get("decadal_range")
        if dr and isinstance(dr, (list, tuple)) and len(dr) == 2:
            try:
                if int(dr[0]) <= age <= int(dr[1]):
                    daxian_pal = p
            except Exception as _e1:
                from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e1)
        if age in (p.get("ages", []) or []):
            liunian_pal = p

    if not daxian_pal:
        return {"available": False}

    # 大限四化（若可算）
    decade_sihua = None
    try:
        from core.ziwei.chart import calculate_decade_feihua
        dstem = daxian_pal.get("decadal_stem", "")
        if dstem:
            decade_sihua = calculate_decade_feihua(dstem, palaces)
    except Exception:
        decade_sihua = None

    dx = {
        "palace": daxian_pal.get("name", ""),
        "branch": daxian_pal.get("earthly_branch", ""),
        "stem": daxian_pal.get("decadal_stem", ""),
        "range": daxian_pal.get("decadal_range", []),
        "major_stars": _star_names(daxian_pal.get("major_stars")),
        "minor_stars": _star_names(daxian_pal.get("minor_stars"))[:3],
    }
    ln = None
    if liunian_pal:
        ln = {
            "palace": liunian_pal.get("name", ""),
            "branch": liunian_pal.get("earthly_branch", ""),
            "major_stars": _star_names(liunian_pal.get("major_stars")),
            "year": current_year,
            "age": age,
        }

    # 大限主星吉凶底色（粗略：吉星/煞星）
    _JI = {"紫微", "天府", "天相", "天梁", "太阳", "太阴", "天机", "天同", "武曲", "禄存", "天魁", "天钺", "左辅", "右弼", "文昌", "文曲"}
    _SHA = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫", "化忌"}
    dxs = set(dx["major_stars"]) | set(dx["minor_stars"])
    nj = len(dxs & _JI)
    ns = len(dxs & _SHA)
    if not dxs:
        dx_tone = "大限宫无主星，须借对宫及三方四正之星论之"
    elif nj > ns:
        dx_tone = "大限吉星会聚，此十年运势向上、宜把握进取"
    elif ns > nj:
        dx_tone = "大限煞星较重，此十年宜守成谨慎、防起伏波折"
    else:
        dx_tone = "大限吉煞相参，此十年起落互见，重在趋吉避凶"

    return {
        "available": True,
        "current_year": current_year,
        "age": age,
        "daxian": dx,
        "liunian": ln,
        "decade_sihua": decade_sihua,
        "daxian_tone": dx_tone,
    }
