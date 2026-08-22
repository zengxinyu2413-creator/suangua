"""
core/fengshui/xuankong_master.py
================================
玄空·综合宅论（总汇合参 — 全功能激活后的最终汇总层）。

玄空既排运山向三盘、定山向格局、检特殊格局、判旺衰方、纳命卦人盘、出化解，须汇为
一处：此宅理气吉凶、当运旺衰之方、合主人之宜居方、必化之凶方，成一明确「综合宅论」。
单点（山向格局/特殊格局/旺衰方/命卦宜居/化解）→ 组合 → 汇总（总评+宜居+化解）。
"""
from __future__ import annotations
from typing import Dict, Any, List

_LEVEL_Q = {
    "auspicious_great": ("吉", "上吉之局"), "auspicious": ("吉", "吉局"),
    "neutral": ("中", "平局"), "inauspicious": ("凶", "凶局"),
    "inauspicious_great": ("凶", "大凶之局"),
}


def build_xuankong_master_synthesis(chart: Dict[str, Any]) -> Dict[str, Any]:
    verdict = chart.get("verdict", "")
    vlevel = chart.get("verdict_level", "")
    vdesc = chart.get("verdict_desc", "")
    patterns = chart.get("special_patterns", []) or []
    lt = chart.get("luantou_summary", {}) or {}
    mr = chart.get("mingua_renpan", {}) or {}
    remedies = chart.get("remedies", []) or []
    sitting = chart.get("sitting_mountain", "")
    facing = chart.get("facing_mountain", "")
    yun = chart.get("yun", {}) or {}

    if not verdict:
        return {"available": False}

    dims: List[Dict[str, str]] = []

    # ① 山向格局
    gq, glabel = _LEVEL_Q.get(vlevel, ("中", "平局"))
    dims.append({"dim": "山向格局", "quality": gq,
                 "verdict": f"{sitting}山{facing}向（{yun.get('yun_name', '')}），{verdict}·{glabel}。{str(vdesc)[:40]}"})

    # ② 特殊格局
    aus = [p for p in patterns if isinstance(p, dict) and p.get("level") == "auspicious"]
    inaus = [p for p in patterns if isinstance(p, dict) and p.get("level") in ("inauspicious", "inauspicious_great")]
    if aus or inaus:
        bits = []
        if aus:
            bits.append("吉格：" + "、".join(p.get("name", "") for p in aus[:3]))
        if inaus:
            bits.append("凶格：" + "、".join(p.get("name", "") for p in inaus[:3]))
        pq = "吉" if len(aus) > len(inaus) else ("凶" if len(inaus) > len(aus) else "中")
        dims.append({"dim": "特殊格局", "quality": pq, "verdict": "；".join(bits) + "。"})

    # ③ 旺衰方
    wang = lt.get("wang_directions", []) or []
    shuai = lt.get("shuai_directions", []) or []
    if wang or shuai:
        dims.append({"dim": "旺衰方位", "quality": "中",
                     "verdict": f"当运旺方：{('、'.join(wang)) or '无'}；衰死方：{('、'.join(shuai)) or '无'}。旺方宜门、卧、灶，衰方宜静、藏。"})

    # ④ 命卦宜居（人盘，若有主人）
    if mr.get("available"):
        best = mr.get("best_dirs", [])
        avoid = mr.get("avoid_dirs", [])
        mq = "吉" if best else ("凶" if avoid and not best else "中")
        dims.append({"dim": "命卦宜居", "quality": mq,
                     "verdict": f"主人{mr.get('ming_gua', '')}命，宜居用之方（旺方又命吉）：{('、'.join(best)) or '取命卦吉方为辅'}"
                                + (f"；切忌：{('、'.join(avoid))}" if avoid else "") + "。"})

    # ⑤ 化解
    if remedies:
        r0 = remedies[0]
        dims.append({"dim": "化解要点", "quality": "中",
                     "verdict": f"凶方须化（共 {len(remedies)} 处），如{r0.get('direction', '')}：{r0.get('issue', '')}，{r0.get('remedy', '')}。"})

    # ── 综合总评 ──
    overall_q = gq
    if gq == "吉" and inaus:
        headline = f"此宅理气{verdict}、{glabel}，然检出{len(inaus)}凶格须化；得运而有微疵，化解后大吉。"
        overall_q = "吉"
    elif gq == "吉":
        headline = f"此宅理气{verdict}、{glabel}，丁财得位，宜居宜久。"
    elif gq == "凶":
        headline = f"此宅理气{verdict}、{glabel}，山向失位，宜大改坐向或重化解、或俟交运。"
    else:
        headline = f"此宅理气{verdict}，吉凶相参，趋旺避衰、化其凶方则可居。"

    # ── 汇总段落 ──
    paras: List[str] = []
    paras.append(headline)
    body = "；".join(d["verdict"].rstrip("。") for d in dims if d["dim"] in ("特殊格局", "旺衰方位", "命卦宜居"))
    if body:
        paras.append("分而论之：" + body + "。")
    paras.append("玄空之要，先以运定山向之旺衰（理气之体），次以峦头砂水应之（形法之用），"
                 + ("终以主人命卦择其宜居之方（人盘之宜）" if mr.get("available") else "补主人生辰可再定合命之宜居方")
                 + "，三盘合参方为全吉。")

    # 流年辅参（宅静时动：建宅年定运为体·不易，分析流年紫白叠加为用·一年一应）
    try:
        _by = chart.get("year")
        _ay = chart.get("analysis_year")
        _yun = chart.get("yun", {})
        _yun_n = _yun.get("yun") if isinstance(_yun, dict) else _yun
        _ZIBAI = {1: "一白", 2: "二黑", 3: "三碧", 4: "四绿", 5: "五黄",
                  6: "六白", 7: "七赤", 8: "八白", 9: "九紫"}
        _ovl = chart.get("overlaid_with_annual", {}) or {}
        _ann_center = _ovl.get(5, _ovl.get("5", {})) or {}
        _ann_star = _ann_center.get("annual")
        _aw = len(chart.get("annual_warnings", []) or [])
        if _by and _ay:
            _zb = _ZIBAI.get(_ann_star, "")
            _txt = (f"流年辅参：本盘以建宅（入伙）{_by}年定运（{_yun_n}运为「体」，一运约二十年、终身不易）；"
                    f"分析流年{_ay}年{_zb}入中飞布，年飞星加临各宫，是为「用」——"
                    f"宅静时动，流年一年一换，吉凶之应多验于流年飞星与本盘山向相合冲之年月"
                    + (f"（本年另有 {_aw} 处流年紫白凶位警示）。" if _aw else "。"))
            dims.append({"dim": "流年", "domain": "流年辅参", "quality": "中", "verdict": _txt})
            paras.append(_txt)
            # 流月方位（再细化：流月紫白叠流年，精确到月之吉凶方）
            try:
                from core.fengshui.xuankong_advanced import get_monthly_directions
                from datetime import datetime as _dtm2
                _am = chart.get("analysis_month") or _dtm2.now().month
                _md = get_monthly_directions(_ay, _am)
                _mtxt = (f"流月方位（{_ay}年{_am}月）：本月文昌在{_md['wenchang']['dir']}、"
                         f"财位在{_md['caiwei']['dir']}、五黄在{_md['wuhuang']['dir']}、病符在{_md['bingfu']['dir']}"
                         + (f"；尤忌 {('；'.join(_md['overlaps']))}——流月凶星叠流年凶星，此月此方大凶。"
                            if _md.get("overlaps") else "；本月无流月叠流年之大凶方。"))
                dims.append({"dim": "流月", "domain": "流月辅参", "quality": "中", "verdict": _mtxt})
                paras.append(_mtxt)
                # 流日方位（三元日白）
                try:
                    from core.fengshui.xuankong_advanced import get_daily_directions
                    _dd = get_daily_directions(_dtm2.now())
                    _dtxt = (f"流日方位（当日·三元日白）：本日文昌在{_dd['wenchang']['dir']}、"
                             f"财位在{_dd['caiwei']['dir']}、五黄在{_dd['wuhuang']['dir']}、病符在{_dd['bingfu']['dir']}。")
                    dims.append({"dim": "流日", "domain": "流日辅参", "quality": "中", "verdict": _dtxt})
                    paras.append(_dtxt)
                except Exception as _e1:
                    from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e1)
                # 流时方位（最细：时白诀，精确择时择方到当下时辰）
                try:
                    from core.fengshui.xuankong_advanced import get_hourly_directions
                    _hd = get_hourly_directions(_dtm2.now())
                    _htxt = (f"流时方位（当下{_hd['hour_zhi']}时·时白）：此时辰文昌在{_hd['wenchang']['dir']}、"
                             f"财位在{_hd['caiwei']['dir']}、五黄在{_hd['wuhuang']['dir']}、病符在{_hd['bingfu']['dir']}"
                             f"；欲精确择时动作可趋文昌财位、避五黄病符之方。")
                    dims.append({"dim": "流时", "domain": "流时辅参", "quality": "中", "verdict": _htxt})
                    paras.append(_htxt)
                except Exception as _e2:
                    from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e2)
            except Exception as _e3:
                from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e3)
    except Exception as _e4:
        from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e4)

    # 当下时辰（宅静时动，流时辅参）
    try:
        from core.calendar.current_moment import moment_dimension
        md = moment_dimension("static")
        dims.append(md["dimension"])
        paras.append(md["paragraph"])
    except Exception as _e5:
        from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e5)

    advice = "趋当运旺方安门主灶、避衰死之方久居"
    if mr.get("available") and mr.get("best_dirs"):
        advice += f"；主人尤宜居用{('、'.join(mr['best_dirs']))}之方"
    if remedies:
        advice += f"；凶方 {len(remedies)} 处依化解法布置。"

    return {
        "available": True,
        "headline": headline,
        "overall_quality": overall_q,
        "sitting": sitting, "facing": facing,
        "dimension_verdicts": dims,
        "integrated_paragraphs": paras,
        "master_advice": advice,
    }
