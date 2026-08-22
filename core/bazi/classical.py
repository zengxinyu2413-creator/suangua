"""
core/bazi/classical.py
======================
八字·传统断语汇集（古籍原文层）。

各古籍断语（《穷通宝鉴》调候、《滴天髓》十干体性与取用、《子平真诠》格局成破）
原本只注入 AI prompt、不示于用户。本模块据命盘汇集这些传统语句，连同出处，
供前端「传统断语」层完整呈现——让用户既见综合总论，亦见古籍原文，再由 AI 解读。
"""
from __future__ import annotations
from typing import Dict, Any, List


def collect_classical_statements(chart: Dict[str, Any]) -> Dict[str, Any]:
    """据命盘汇集古籍传统断语。"""
    dm = chart.get("day_master", "")
    month_dz = (chart.get("month_pillar", {}) or {}).get("dizhi", "")
    pattern = chart.get("pattern", "")
    out: List[Dict[str, str]] = []

    # 《穷通宝鉴》调候
    try:
        from knowledge.bazi_classical import TIAO_HOU_TABLE
        th = TIAO_HOU_TABLE.get(dm, {}).get(month_dz, "")
        if th:
            out.append({
                "source": "《穷通宝鉴》", "topic": "调候",
                "title": f"{dm}金日生{month_dz}月" if dm in "庚辛" else f"{dm}日生{month_dz}月",
                "text": th if isinstance(th, str) else str(th),
            })
    except Exception as _e1:
        from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e1)

    # 《滴天髓》十干体性 + 取用
    try:
        from knowledge.bazi_classical_deep import DITIAN_SHIGAN_FULL
        df = DITIAN_SHIGAN_FULL.get(dm, {})
        if df:
            # 深化层：原文 + 体性详注 + 四时取用 + 喜忌成器（实质详解）
            out.append({"source": "《滴天髓》", "topic": "十干原文",
                        "title": f"{dm}干·本文", "text": df.get("原文", "")})
            if df.get("体性详注"):
                out.append({"source": "《滴天髓·任注》", "topic": "体性详注",
                            "title": f"{dm}干体性", "text": df["体性详注"]})
            if df.get("四时取用"):
                out.append({"source": "《滴天髓·任注》", "topic": "四时取用",
                            "title": f"{dm}干四时", "text": df["四时取用"]})
            if df.get("喜忌成器"):
                out.append({"source": "《滴天髓·任注》", "topic": "喜忌成器",
                            "title": f"{dm}干成器", "text": df["喜忌成器"]})
            _deep_dm = True
        else:
            _deep_dm = False
    except Exception:
        _deep_dm = False
    if not _deep_dm:
        try:
            from knowledge.bazi_classical import SHIGAN_JIJUE
            sj = SHIGAN_JIJUE.get(dm, {})
            if sj.get("口诀"):
                txt = sj["口诀"]
                if sj.get("解析"):
                    txt += "　——" + sj["解析"]
                out.append({"source": "《滴天髓》", "topic": "十干体性",
                            "title": f"{dm}干体性诀", "text": txt})
        except Exception as _e2:
            from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e2)
        try:
            from knowledge.knowledge_deep import DITIAN_SUI_SHIGAN
            dt = DITIAN_SUI_SHIGAN.get(dm, {})
            if dt.get("取用要领"):
                out.append({"source": "《滴天髓》", "topic": "四时取用",
                            "title": f"{dm}干四时取用", "text": dt["取用要领"]})
        except Exception as _e3:
            from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e3)

    # 《子平真诠》格局
    _deep_ge = False
    try:
        from knowledge.bazi_classical_deep import ZIPING_GE_FULL
        gf = ZIPING_GE_FULL.get(pattern, {})
        if gf:
            if gf.get("章旨"):
                out.append({"source": "《子平真诠》", "topic": "章旨",
                            "title": f"论{pattern.replace('格','')}·章旨", "text": gf["章旨"]})
            if gf.get("成格详"):
                out.append({"source": "《子平真诠》", "topic": "成格",
                            "title": f"{pattern}成格", "text": gf["成格详"]})
            if gf.get("破格详"):
                out.append({"source": "《子平真诠》", "topic": "破格",
                            "title": f"{pattern}破格", "text": gf["破格详"]})
            if gf.get("救应详"):
                out.append({"source": "《子平真诠》", "topic": "救应",
                            "title": f"{pattern}救应", "text": gf["救应详"]})
            if gf.get("行运详"):
                out.append({"source": "《子平真诠》", "topic": "行运",
                            "title": f"{pattern}行运", "text": gf["行运详"]})
            _deep_ge = True
    except Exception:
        _deep_ge = False
    if not _deep_ge:
        try:
            from knowledge.bazi_classical import BAZIGE_SYSTEM
            ge = BAZIGE_SYSTEM.get(pattern, {})
            if ge:
                parts = []
                if ge.get("取格"):
                    parts.append("取格：" + ge["取格"])
                if ge.get("喜"):
                    parts.append("喜：" + "、".join(ge["喜"]))
                if ge.get("忌"):
                    parts.append("忌：" + "、".join(ge["忌"]))
                if parts:
                    out.append({"source": "《子平真诠》", "topic": "格局",
                                "title": f"{pattern}取用", "text": "　".join(parts)})
        except Exception as _e4:
            from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e4)
        try:
            from knowledge.knowledge_deep import ZIPING_GEJV_DEEP
            gd = ZIPING_GEJV_DEEP.get(pattern, {})
            if gd:
                parts = []
                if gd.get("定义"):
                    parts.append("定义：" + gd["定义"])
                if gd.get("成格"):
                    parts.append("成格：" + "；".join(gd["成格"][:3]))
                if gd.get("破格"):
                    parts.append("破格：" + "；".join(gd["破格"][:3]))
                if gd.get("行运"):
                    parts.append("行运：" + gd["行运"])
                if parts:
                    out.append({"source": "《子平真诠》", "topic": "格局成破",
                                "title": f"{pattern}成破行运", "text": "　".join(parts)})
        except Exception as _e5:
            from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e5)

    return {"available": bool(out), "count": len(out), "statements": out}
