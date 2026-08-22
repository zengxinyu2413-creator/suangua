"""
core/ziwei/classical.py
=======================
紫微·传统断语收集（古籍原文层）。

surfaced 命宫主星之《紫微斗数全书》深度释义（多层）+ 庙旺断 + 格局典籍，
呈于「传统断语」层，亦可喂 AI。仿八字 collect_classical_statements。
"""
from __future__ import annotations
from typing import Dict, Any, List


def collect_classical_statements(chart: Dict[str, Any]) -> Dict[str, Any]:
    out: List[Dict[str, str]] = []
    palaces = chart.get("palaces", []) or []
    ming = next((p for p in palaces if p.get("is_soul")), None)
    if not ming:
        return {"available": False, "statements": [], "count": 0}

    # 命宫主星深度释义（《紫微斗数全书》十四主星）
    try:
        from knowledge.ziwei_classical_deep import ZIWEI_14_FULL
        for s in ming.get("major_stars", []) or []:
            star = s.get("name", "")
            full = ZIWEI_14_FULL.get(star)
            if not full:
                continue
            out.append({"source": "《紫微斗数全书》", "topic": "主星星性",
                        "title": f"{star}·星性总论", "text": full["星性总论"]})
            out.append({"source": "《紫微斗数全书》", "topic": "性情为人",
                        "title": f"{star}·性情", "text": full["性情为人"]})
            out.append({"source": "《紫微斗数全书》", "topic": "庙旺喜忌",
                        "title": f"{star}·庙旺喜忌", "text": full["庙旺喜忌"]})
            out.append({"source": "《紫微斗数全书》", "topic": "事业财禄",
                        "title": f"{star}·事业财禄", "text": full["事业财禄"]})
            if full.get("经典断语"):
                out.append({"source": "《紫微斗数全书》", "topic": "经典断语",
                            "title": f"{star}·经典断语", "text": full["经典断语"]})
    except Exception as _e1:
        from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e1)

    # 格局典籍（成格之经典含义）
    try:
        good = (chart.get("insights", {}) or {}).get("patterns", {}).get("good", []) or []
        for g in good[:2]:
            if g.get("meaning"):
                out.append({"source": "紫微格局", "topic": "格局",
                            "title": g.get("name", ""), "text": g["meaning"]})
    except Exception as _e2:
        from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e2)

    return {"available": bool(out), "statements": out, "count": len(out)}
