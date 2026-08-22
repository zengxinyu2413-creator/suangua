"""
core/ziwei/master_synthesis.py
==============================
紫微斗数·综合论断（总汇合参 — 全功能激活后的最终汇总层）。

紫微以十二宫分论人生各域；一次完整读盘，须把命宫之命格、连同财帛/官禄/夫妻/
疾厄/福德各要宫之吉凶，及当前大限流年，合参于一处，成「一人·分宫吉凶·此运休咎」
之总论：单点（各要宫吉凶速览）→ 组合（命格×各宫×行运）→ 汇总（总评+总建议）。
"""
from __future__ import annotations
from typing import Dict, Any, List

# 要宫 → 人生域
_KEY_PALACES = {
    "官禄宫": "事业", "财帛宫": "财运", "夫妻宫": "婚姻",
    "疾厄宫": "健康", "福德宫": "福分", "田宅宫": "家宅",
}
_JI_STARS = {"紫微", "天府", "天相", "天梁", "太阳", "太阴", "天机",
             "天同", "武曲", "禄存", "天魁", "天钺", "左辅", "右弼", "文昌", "文曲"}
_SHA_STARS = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}
_BRIGHT_GOOD = {"庙", "旺", "得"}
_BRIGHT_BAD = {"不", "陷"}


def _palace_verdict(palace: Dict[str, Any]) -> Dict[str, str]:
    majors = palace.get("major_stars", []) or []
    minors = palace.get("minor_stars", []) or []
    score = 0
    notes = []

    star_names = []
    for s in majors:
        nm = s.get("name", "") if isinstance(s, dict) else str(s)
        star_names.append(nm)
        if isinstance(s, dict):
            b = s.get("brightness", "")
            mut = s.get("mutagen", "")
            if nm in _JI_STARS:
                score += 1
            if b in _BRIGHT_GOOD:
                score += 1
            elif b in _BRIGHT_BAD:
                score -= 1
            if mut in ("禄", "权", "科"):
                score += 1
                notes.append(f"{nm}化{mut}")
            elif mut == "忌":
                score -= 2
                notes.append(f"{nm}化忌")
    # 煞星
    n_sha = sum(1 for s in (majors + minors)
                if isinstance(s, dict) and (s.get("type") == "tough" or s.get("name") in _SHA_STARS))
    score -= n_sha

    if not star_names:
        q, desc = "中", "宫无正曜，借对宫论"
    elif score >= 2:
        q, desc = "吉", "星曜得地、四化呈祥"
    elif score <= -2:
        q, desc = "凶", "煞忌交侵、星曜失辉"
    else:
        q, desc = "中", "吉煞相参、得失互见"

    stars_s = "、".join(star_names[:3]) if star_names else "无正曜"
    note_s = ("（" + "，".join(notes) + "）") if notes else ""
    return {"quality": q, "stars": stars_s, "verdict": f"坐{stars_s}{note_s}，{desc}"}


def build_ziwei_master_synthesis(chart: Dict[str, Any]) -> Dict[str, Any]:
    overview = chart.get("overview", {}) or {}
    synth = chart.get("mingge_synthesis", {}) or {}
    cf = chart.get("current_fortune", {}) or {}
    palaces = chart.get("palaces", []) or []

    if not overview.get("available") and not synth.get("available"):
        return {"available": False}

    ming_q = synth.get("composite_label", "") or overview.get("quality", "")
    ming_quality = overview.get("quality", "中")
    headline_ming = overview.get("headline", "")

    # ── 单点：各要宫吉凶速览 ──
    dims: List[Dict[str, str]] = []
    for p in palaces:
        nm = p.get("name", "")
        if nm in _KEY_PALACES:
            v = _palace_verdict(p)
            dims.append({"domain": _KEY_PALACES[nm], "palace": nm,
                         "quality": v["quality"], "verdict": v["verdict"]})
    # 要宫排序：事业/财运/婚姻/健康/福分/家宅
    order = ["事业", "财运", "婚姻", "健康", "福分", "家宅"]
    dims.sort(key=lambda d: order.index(d["domain"]) if d["domain"] in order else 99)

    # 行运
    yun_line = ""
    if cf.get("available"):
        dx = cf.get("daxian", {}) or {}
        ln = cf.get("liunian", {}) or {}
        rng = dx.get("range", [])
        rng_s = f"{rng[0]}-{rng[1]}岁" if isinstance(rng, (list, tuple)) and len(rng) == 2 else ""
        yun_line = (f"现行大限{dx.get('palace', '')}（{rng_s}，坐{('、'.join(dx.get('major_stars', [])[:2]) or '无正曜')}），"
                    f"{cf.get('daxian_tone', '')}。"
                    + (f"{cf.get('current_year', '')}年流年入{ln.get('palace', '')}。" if ln and ln.get('palace') else ""))
        dims.append({"domain": "行运", "palace": dx.get("palace", ""),
                     "quality": "吉" if "向上" in cf.get("daxian_tone", "") else ("凶" if "波折" in cf.get("daxian_tone", "") else "中"),
                     "verdict": yun_line})

    # 当下时辰（此刻 × 命宫地支冲合 — 纳当下合参）
    moment_line = ""
    try:
        from core.calendar.current_moment import current_sizhu
        mo = current_sizhu()
        hour_zhi = mo.get("hour_zhi", "")
        soul = chart.get("soul_palace", {}) or {}
        soul_zhi = soul.get("earthly_branch", "") or soul.get("branch", "")
        from core.constants import LIUCHONG as _CHONG, LIUHE as _HE
        rel, mq = "平", "中"
        if soul_zhi and hour_zhi:
            if _CHONG.get(soul_zhi) == hour_zhi:
                rel, mq = f"冲命宫（{soul_zhi}）", "凶"
            elif _HE.get(soul_zhi) == hour_zhi:
                rel, mq = f"合命宫（{soul_zhi}）", "吉"
            else:
                rel, mq = "与命宫无冲合", "中"
        moment_line = (f"此刻{mo.get('hour_name', '')}（{mo.get('hour_gz', '')}时），时支{rel}，"
                       + {"吉": "此时谋事得助、较顺。", "凶": "此时易动荡，宜静守。", "中": "此时平平，依事而行。"}.get(mq, ""))
        dims.append({"domain": "当下", "palace": "", "quality": mq, "verdict": moment_line})
    except Exception as _e1:
        from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e1)

    # ── 综合总评 ──
    _R = {"吉": 2, "中": 1, "凶": 0}
    dq = [_R.get(d["quality"], 1) for d in dims if d["domain"] not in ("行运", "当下")]
    avg = sum(dq) / len(dq) if dq else 1
    if ming_quality == "吉" and avg >= 1.3:
        overall_q, headline = "吉", "命格上乘，财官夫疾各得其位，一生大局向上、宜顺势进取。"
    elif ming_quality == "凶" or avg < 0.7:
        overall_q, headline = "凶", "命格或要宫煞忌较重，须借运补救、避其所忌、积善以转。"
    else:
        overall_q, headline = "中", "命格成破相参，诸宫吉煞互见，扬长避短、顺运而为则吉。"

    # ── 汇总段落 ──
    paras: List[str] = []
    paras.append(f"综观全盘，{headline_ming or ming_q}。" + (synth.get("composite_desc", "") or ""))
    if dims:
        dom_bits = [f"{d['domain']}{ {'吉':'佳','中':'平','凶':'需慎'}.get(d['quality'],'平') }"
                    for d in dims if d["domain"] not in ("行运", "当下")]
        if dom_bits:
            paras.append("分宫而论，" + "、".join(dom_bits) + "。此命盘十二宫之分野，定一生各域之高下。")
    if yun_line:
        paras.append("叠以行运：" + yun_line + "本命定格局高下，大限定十年休咎、流年定一岁吉凶，三盘合参方知此时此事。")
    if moment_line:
        paras.append("再合当下之时：" + moment_line + "本命为体、行运为势、当下为机，三者合参方知此时此事之宜。")

    advice = "总以扶本命吉曜、化解煞忌为纲：行大限流年至吉宫吉化则顺，逢煞忌冲会则宜守。"
    if any(d["domain"] == "婚姻" and d["quality"] == "凶" for d in dims):
        advice += "夫妻一宫煞重者，姻缘宜缓择、善经营。"

    return {
        "available": True,
        "headline": headline,
        "overall_quality": overall_q,
        "ming_label": ming_q or ming_quality,
        "dimension_verdicts": dims,
        "integrated_paragraphs": paras,
        "master_advice": advice,
    }
