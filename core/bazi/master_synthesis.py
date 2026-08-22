"""
core/bazi/master_synthesis.py
=============================
八字·综合论断（总汇合参 — 全功能激活后的最终汇总层）。

六件套之 ① 总论合成的是「命局本体」（格局/用神/强弱）；然一次完整读盘，须把
事业、婚姻、财运、健康各专域之单点结论，连同当前大运流年，一并汇于一处，合参
为「一人一生·分域吉凶·此时休咎」之总论。本层即此「汇总到一起」之件：
  单点（各域专断）→ 组合（命局×各域×运程）→ 汇总（综合论断 + 分域速览 + 总建议）。
"""
from __future__ import annotations
from typing import Dict, Any, List

_Q_RANK = {"吉": 2, "中": 1, "平": 1, "凶": 0}


def _grade_to_q(text: str) -> str:
    """从专域结论文字粗提吉/中/凶。"""
    if not text:
        return "中"
    t = str(text)
    if any(k in t for k in ("上佳", "上等", "极佳", "旺", "上吉", "富", "美满", "和合", "健旺", "优")):
        return "吉"
    if any(k in t for k in ("受损", "凶", "破", "弱", "差", "刑冲", "病", "衰", "薄")):
        return "凶"
    return "中"


def build_master_synthesis(chart: Dict[str, Any]) -> Dict[str, Any]:
    overview = chart.get("overview", {}) or {}
    synth = chart.get("mingju_synthesis", {}) or {}
    cf = chart.get("current_fortune", {}) or {}
    aspects = chart.get("life_aspects", {}) or {}

    if not overview.get("available") and not synth.get("available"):
        return {"available": False}

    dm = overview.get("day_master", "") or synth.get("day_master", "")
    ming_q = synth.get("composite_label", "") or overview.get("quality", "")
    ming_quality = overview.get("quality", "中")

    # ── 分域速览（单点专断 → 一句吉凶）──
    dims: List[Dict[str, str]] = []

    career = aspects.get("career", {}) or {}
    if career:
        cf_list = career.get("career_fields", [])
        cf_fields = "、".join(cf_list[:3]) if isinstance(cf_list, list) else str(cf_list)[:24]
        sa = career.get("shishen_advice", "")
        sa_text = ("；".join(sa) if isinstance(sa, list) else str(sa))[:24]
        q = _grade_to_q(str(career.get("analysis", "")))
        dims.append({"domain": "事业", "quality": q,
                     "verdict": (f"宜{cf_fields}等" + (f"；{sa_text}" if sa_text else "")).strip("；"),
                     "key": cf_fields})

    def _txt(v, n=28):
        if isinstance(v, list):
            return "；".join(str(x) for x in v)[:n]
        return str(v or "")[:n]

    wealth = aspects.get("wealth", {}) or {}
    if wealth:
        lvl = str(wealth.get("level", ""))
        q = _grade_to_q(lvl)
        dims.append({"domain": "财运", "quality": q,
                     "verdict": (f"财格{lvl}" + (f"；{_txt(wealth.get('advice'))}" if wealth.get('advice') else "")).strip("；"),
                     "key": lvl})

    marriage = aspects.get("marriage", {}) or {}
    if marriage:
        ql = str(marriage.get("quality", ""))
        q = _grade_to_q(ql)
        extra = "有刑冲" if marriage.get("clash_present") else ("得合" if marriage.get("harmony_present") else "")
        dims.append({"domain": "婚姻", "quality": q,
                     "verdict": (f"姻缘{ql}" + (f"·{extra}" if extra else "") + (f"；{_txt(marriage.get('advice'), 24)}" if marriage.get('advice') else "")).strip("；"),
                     "key": ql})

    health = aspects.get("health", {}) or {}
    if health:
        cond = str(health.get("dm_condition", ""))
        q = _grade_to_q(cond + _txt(health.get("analysis"), 20))
        weak = str(health.get("weak_organ", ""))
        dims.append({"domain": "健康", "quality": q,
                     "verdict": (f"日主{health.get('dm_organ', '')}{cond}" + (f"，注意{weak}" if weak else "") + (f"；{_txt(health.get('advice'), 20)}" if health.get('advice') else "")).strip("；"),
                     "key": weak})

    # 运程（后天之时）
    yun_line = ""
    if cf.get("available"):
        cdy = cf.get("current_dayun", {}) or {}
        cln = cf.get("current_liunian", {}) or {}
        help_map = {"扶用": "顺境之运、宜进取", "助忌": "受抑之运、宜守成", "中性": "平运守常"}
        yun_line = (f"现行{cdy.get('ganzhi', '')}大运（{cdy.get('shishen', '')}），"
                    f"{help_map.get(cdy.get('help', ''), '')}"
                    f"，{cf.get('current_year', '')}年{cln.get('ganzhi', '')}（{cln.get('quality', '')}）。")
        dims.append({"domain": "运程", "quality": cln.get("quality", "中"),
                     "verdict": yun_line, "key": cdy.get("ganzhi", "")})

    # 当下时辰（此刻时空 × 本命用神 — 任何解读皆纳入当下合参）
    yong_wx = synth.get("yong_shen_wx", "") or overview.get("yong_shen_wx", "")
    ji_wx = synth.get("ji_shen_wx", "") or overview.get("ji_shen_wx", "")
    moment_line = ""
    try:
        from core.calendar.current_moment import current_sizhu, moment_vs_yongshen
        mo = current_sizhu()
        yong_list = [w for w in (yong_wx if isinstance(yong_wx, list) else [yong_wx]) if w]
        ji_list = [w for w in (ji_wx if isinstance(ji_wx, list) else [ji_wx]) if w]
        mv = moment_vs_yongshen(mo, yong_list, ji_list)
        moment_line = mv["note"] + {"扶用": "此时谋事、决断较顺。", "助忌": "此时宜缓、不宜强求。",
                                     "中性": "此时平平，依事而行。"}.get(mv["tone"], "")
        dims.append({"domain": "当下", "quality": mv["quality"],
                     "verdict": moment_line, "key": mo.get("hour_gz", "")})
    except Exception as _e1:
        from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e1)

    # ── 综合总评（命局体 × 各域均值 × 运程）──
    domain_qs = [_Q_RANK.get(d["quality"], 1) for d in dims if d["domain"] not in ("运程", "当下")]
    avg = sum(domain_qs) / len(domain_qs) if domain_qs else 1
    if ming_quality == "吉" and avg >= 1.3:
        overall_q, headline = "吉", "命局格正用真，事业财帛婚姻各得其位，allgood一生大局向上。"
    elif ming_quality == "凶" or avg < 0.7:
        overall_q, headline = "凶", "命局或专域有损，须重趋用避忌、借岁运补救，事在人为。"
    else:
        overall_q, headline = "中", "命局成破相参，各域得失互见，扬长补短、顺运而为则吉。"
    headline = headline.replace("allgood", "")

    # ── 汇总段落（命局 → 各域 → 运程 → 当下 串成连贯总论）──
    paras: List[str] = []
    p_ming = f"综观全局，{dm}日主，{ming_q or ming_quality}。"
    if synth.get("composite_desc"):
        p_ming += synth["composite_desc"]
    paras.append(p_ming)

    if dims:
        dom_bits = []
        for d in dims:
            if d["domain"] in ("运程", "当下"):
                continue
            mark = {"吉": "佳", "中": "平", "凶": "需慎"}.get(d["quality"], "平")
            dom_bits.append(f"{d['domain']}{mark}")
        if dom_bits:
            paras.append("分域而论，" + "、".join(dom_bits) + "；详见各专断。此先天之分野，定一生各域之高下。")

    if yun_line:
        paras.append("叠以后天之运：" + yun_line + "先天定格局高下，后天定何时起伏、何域应验，二者合参方知此时此事。")

    if moment_line:
        paras.append("再合当下之时：" + moment_line + "先天为体、行运为势、当下为机，三者合参，方知此人此时此事之宜忌。")

    # 总建议
    yong = synth.get("yong_shen_wx", "") or overview.get("yong_shen_wx", "")
    ji = synth.get("ji_shen_wx", "") or overview.get("ji_shen_wx", "")
    advice = f"总以扶{yong}抑{ji}为纲：趋用神之乡（事业方位、行业五行、流年）则顺，犯忌神之地则滞。"
    if any(d["domain"] == "婚姻" and d["quality"] == "凶" for d in dims):
        advice += "婚姻一域尤须留意刑冲，宜缓择良配、善加经营。"

    return {
        "available": True,
        "headline": headline,
        "overall_quality": overall_q,
        "day_master": dm,
        "ming_label": ming_q or ming_quality,
        "dimension_verdicts": dims,         # 单点：各域一句吉凶速览
        "integrated_paragraphs": paras,     # 汇总：命局→各域→运程连贯总论
        "master_advice": advice,            # 总建议
    }
