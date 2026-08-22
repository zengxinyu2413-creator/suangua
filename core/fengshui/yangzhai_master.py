"""
core/fengshui/yangzhai_master.py
================================
阳宅三要·综合宅论（总汇合参 — 全功能激活后的最终汇总层）。

阳宅三要既定门主灶之游年局、判灶局、配主人命卦、核东西四卦纯净、列六事，须汇为
一处：此宅形法吉凶、门主灶配置之优劣、人宅相配与否、六事宜忌，成一明确「综合宅论」。
单点（宅型纯净/门主局/灶局/命卦相配/六事）→ 组合 → 汇总（总评+人宅+建议）。
"""
from __future__ import annotations
from typing import Dict, Any, List


def _q_of(text: str) -> str:
    t = str(text or "")
    if any(k in t for k in ("上吉", "大吉", "中吉", "次吉", "吉")):
        return "吉"
    if any(k in t for k in ("大凶", "凶", "煞", "破")):
        return "凶"
    return "中"


def build_yangzhai_master_synthesis(result: Dict[str, Any]) -> Dict[str, Any]:
    house_type = result.get("house_type", "")
    grade = result.get("grade", "")
    mz = result.get("menzhu_ju", {}) or {}
    zj = result.get("zao_ju", {}) or {}
    mm = result.get("mingua_match", {}) or {}
    purity = result.get("purity", {}) or {}
    liushi = result.get("liushi_guide", {}) or result.get("liushi", {}) or {}

    if not house_type and not grade:
        return {"available": False}

    dims: List[Dict[str, str]] = []

    # ① 宅型纯净（东西四卦是否一气）
    pure = purity.get("pure")
    pq = "吉" if pure else "中"
    dims.append({"dim": "宅型纯净", "quality": pq,
                 "verdict": f"{house_type}，门主灶三者"
                            + ("同属一卦、东西不杂，纯净为上" if pure else "东西四卦相杂、不纯，吉凶相参")
                            + f"（门{purity.get('men_group', '')}·主{purity.get('zhu_group', '')}·灶{purity.get('zao_group', '')}）。"})

    # ② 门主局（核心）
    if mz.get("ming"):
        mzq = _q_of(mz.get("level", "") or mz.get("younian", ""))
        dims.append({"dim": "门主局", "quality": mzq,
                     "verdict": f"{mz.get('ming', '')}（{mz.get('level', '')}）：{str(mz.get('zong', ''))[:40]}"})

    # ③ 灶局
    if zj.get("quality"):
        zq = _q_of(zj.get("quality", ""))
        dims.append({"dim": "灶局", "quality": zq,
                     "verdict": f"灶{zj.get('quality', '')}（主灶{zj.get('zhu_zao_star', '')}、门灶{zj.get('men_zao_star', '')}），司一家饮食祸福。"})

    # ④ 命卦相配（人宅）
    if mm.get("match_level"):
        _ml = mm.get("match_level", "")
        if any(k in _ml for k in ("不配", "不宜", "相背", "凶", "受克")):
            mmq = "凶"
        elif any(k in _ml for k in ("大吉", "吉", "相得")):
            mmq = "吉"
        else:
            mmq = "中"
        dims.append({"dim": "命卦相配", "quality": mmq,
                     "verdict": f"主人{mm.get('ming_gua', '')}命配此{house_type}：{_ml}。人宅相得则吉、相背则凶。"})

    # ⑤ 六事
    if liushi:
        n = len(liushi.get("items", []) or liushi.get("guide", []) or []) if isinstance(liushi, dict) else 0
        if n or liushi:
            dims.append({"dim": "六事布置", "quality": "中",
                         "verdict": "路井灶厕碓磨畜栏等六事，须各安吉方、避凶方，详见六事指南。"})

    # ── 综合总评 ──
    overall_q = _q_of(grade)
    match_level = mm.get("match_level", "")
    mm_bad = bool(match_level) and (("凶" in match_level) or any(k in match_level for k in ("不配", "不宜", "相背", "受克")))
    if overall_q == "吉" and mm_bad:
        headline = f"此宅形法{grade}，门主灶配置佳；然主人命卦与宅相背（{match_level}），宅吉而人不宜，宜易居或调主卧灶位。"
        overall_q = "中"
    elif overall_q == "吉":
        headline = f"此宅形法{grade}，门主灶相生得位" + (f"，{match_level}" if match_level else "") + "，宜居宜久。"
    elif overall_q == "凶":
        headline = f"此宅形法{grade}，门主灶相克失位，宜大调门主灶之位或另择宅。"
    else:
        headline = f"此宅形法{grade}，吉凶相参，须调其失位之处、避其凶方。"

    # ── 汇总段落 ──
    paras: List[str] = []
    paras.append(headline)
    body = "；".join(d["verdict"].rstrip("。") for d in dims if d["dim"] in ("门主局", "灶局", "命卦相配"))
    if body:
        paras.append("分而论之：" + body + "。")
    paras.append("阳宅三要，门为气口、主为坐山、灶为养命，三者游年相生比和则吉、相克则凶；"
                 "更须门主灶同属东四或西四（纯净），并合主人命卦（人宅相配），方为全吉之宅。")

    # 流年方位辅参（宅静时动：门主灶为静·终身不易，流年九星加临各方·一年一换）
    try:
        from datetime import datetime as _dty
        from core.fengshui.xuankong_advanced import get_annual_directions, get_monthly_directions
        _ay = result.get("analysis_year") or _dty.now().year
        _ad = get_annual_directions(_ay)
        _txt = (f"流年方位（{_ay}年·动态辅参）：门主灶为静、终身不易；流年九星加临各方，一年一换。"
                f"本年文昌位在{_ad['wenchang']['dir']}（宜书房助学）、"
                f"财位在{_ad['caiwei']['dir']}（宜开门动催财）；"
                f"五黄大煞在{_ad['wuhuang']['dir']}、病符在{_ad['bingfu']['dir']}、"
                f"太岁在{_ad['taisui']['dir']}、三煞在{_ad['sansha']['dir']}"
                f"——此数方忌动土修造、宜静，犯之主灾病。择吉用事须避凶就吉，是为静宅之流年辅参。")
        dims.append({"dim": "流年方位", "domain": "流年辅参", "quality": "中", "verdict": _txt})
        paras.append(_txt)
        # 流月方位（再细化：流月紫白叠流年，精确到月之吉凶方）
        _am = result.get("analysis_month") or _dty.now().month
        _md = get_monthly_directions(_ay, _am)
        _mtxt = (f"流月方位（{_ay}年{_am}月）：本月文昌在{_md['wenchang']['dir']}、"
                 f"财位在{_md['caiwei']['dir']}、五黄在{_md['wuhuang']['dir']}、病符在{_md['bingfu']['dir']}。"
                 + (f"尤忌：{('；'.join(_md['overlaps']))}——流月凶星叠流年凶星，此月此方大凶，万勿动土。"
                    if _md.get("overlaps") else "本月无流月叠流年之大凶方。"))
        dims.append({"dim": "流月方位", "domain": "流月辅参", "quality": "中", "verdict": _mtxt})
        paras.append(_mtxt)
        # 流日方位（三元日白，精确择日到某日吉凶方）
        try:
            from core.fengshui.xuankong_advanced import get_daily_directions
            _dd = get_daily_directions(_dty.now())
            _dtxt = (f"流日方位（当日·三元日白）：本日文昌在{_dd['wenchang']['dir']}、"
                     f"财位在{_dd['caiwei']['dir']}、五黄在{_dd['wuhuang']['dir']}、病符在{_dd['bingfu']['dir']}。"
                     f"择日动作可趋本日文昌财位、避五黄病符之方。")
            dims.append({"dim": "流日方位", "domain": "流日辅参", "quality": "中", "verdict": _dtxt})
            paras.append(_dtxt)
        except Exception as _e1:
            from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e1)
        # 流时方位（最细：流时紫白·时白诀，精确择时择方到当下时辰）
        try:
            from core.fengshui.xuankong_advanced import get_hourly_directions
            _hd = get_hourly_directions(_dty.now())
            _htxt = (f"流时方位（当下{_hd['hour_zhi']}时·时白）：此时辰文昌在{_hd['wenchang']['dir']}、"
                     f"财位在{_hd['caiwei']['dir']}、五黄在{_hd['wuhuang']['dir']}、病符在{_hd['bingfu']['dir']}。"
                     f"欲精确择时动作（如此刻出行、签约、求谋），可趋此时文昌财位、避五黄病符之方。")
            dims.append({"dim": "流时方位", "domain": "流时辅参", "quality": "中", "verdict": _htxt})
            paras.append(_htxt)
        except Exception as _e2:
            from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e2)
    except Exception as _e3:
        from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e3)

    # 当下时辰（宅静时动，流时辅参）
    try:
        from core.calendar.current_moment import moment_dimension
        md = moment_dimension("static")
        dims.append(md["dimension"])
        paras.append(md["paragraph"])
    except Exception as _e4:
        from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e4)

    advice = "门主灶以相生比和、同卦纯净为上"
    if mm.get("match_level"):
        advice += f"；主人{mm.get('ming_gua', '')}命，" + ("人宅相得，宜久居" if not mm_bad else "人宅相背，宜调主卧灶位或易居")
    advice += "。"

    return {
        "available": True,
        "headline": headline,
        "overall_quality": overall_q,
        "house_type": house_type, "grade": grade,
        "dimension_verdicts": dims,
        "integrated_paragraphs": paras,
        "master_advice": advice,
    }
