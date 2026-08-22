"""
core/ziwei/overview.py
======================
紫微斗数·命盘总论合成（综合总论层）。

紫微诸结果（命宫主星庙旺、命格评定、格局成破、三方四正会照、身宫命主、四化引动）
原散见各处。本引擎以「命主立命」为纲，织之成篇，扣命主作答，并提炼命格定盘
（评等+主星）置顶 hero。仿八字 overview 之法。
"""
from __future__ import annotations
from typing import Dict, Any, List

# 命格评等 → 吉凶质量（供 hero 着色）
_RATING_Q = {
    "上格": "吉", "中上格": "吉", "中格": "中",
    "中下格": "凶", "下格": "凶", "平格": "中",
}


def _stars_with_bright(palace: Dict[str, Any]) -> str:
    out = []
    for s in palace.get("major_stars", []) or []:
        nm = s.get("name", "")
        br = s.get("brightness", "")
        out.append(f"{nm}（{br}）" if br else nm)
    return "、".join(out) if out else "无主星（借对宫）"


def synthesize_overview(chart: Dict[str, Any]) -> Dict[str, Any]:
    palaces = chart.get("palaces", []) or []
    if not palaces:
        return {"available": False}

    md = chart.get("metadata", {}) or {}
    ins = chart.get("insights", {}) or {}
    rating = ins.get("rating", {}) or {}
    patterns = ins.get("patterns", {}) or {}
    sj = chart.get("sanjiao_analysis", {}) or {}

    ming = next((p for p in palaces if p.get("is_soul")), None)
    body = next((p for p in palaces if p.get("is_body")), None)
    if not ming:
        return {"available": False}

    paras: List[Dict[str, str]] = []

    # ① 立命主星
    ming_stars = _stars_with_bright(ming)
    minor = "、".join(s.get("name", "") for s in (ming.get("minor_stars", []) or [])[:4])
    p1 = f"命宫坐{ming.get('earthly_branch','')}，主星{ming_stars}"
    if minor:
        p1 += f"，辅以{minor}"
    p1 += "。命宫为一身之主，定其禀赋、格局与终身气象。"
    paras.append({"title": "立命主星", "text": p1})

    # ② 命格评定
    overall = rating.get("overall", "")
    bright = rating.get("bright_in_sfsz", []) or []
    fallen = rating.get("fallen_in_sfsz", []) or []
    p2 = f"综命宫及三方四正主星之庙旺，命格评为「{overall}」。"
    if bright:
        p2 += f"庙旺得地者：{('、'.join(bright[:6]))}，主星有力则格局可成。"
    if fallen:
        p2 += f"落陷失辉者：{('、'.join(fallen[:4]))}，须防其位之事多波折。"
    paras.append({"title": "命格评定", "text": p2})

    # ③ 格局成破
    good = patterns.get("good", []) or []
    bad = patterns.get("bad", []) or []
    if good or bad:
        p3 = ""
        if good:
            gnames = "、".join(g.get("name", "") for g in good[:3])
            p3 += f"命中成吉格：{gnames}——{good[0].get('meaning','')[:40]}。"
        if bad:
            bnames = "、".join(b.get("name", "") for b in bad[:3])
            p3 += f"然亦带凶格：{bnames}，{bad[0].get('meaning','')[:36]}，须以吉制凶、趋避得宜。"
        paras.append({"title": "格局成破", "text": p3})

    # ④ 三方四正会照
    conv = sj.get("converging_stars", []) or []
    if conv:
        cs = "、".join(f"{c.get('star','')}（{c.get('palace','')}"
                      + (f"·化{c.get('mutagen','')}" if c.get('mutagen') else "") + "）"
                      for c in conv[:5])
        p4 = f"三方四正会照：{cs}。诸宫之星汇于命宫，吉星拱照则助力广，煞忌交冲则牵掣多。"
        paras.append({"title": "三方四正", "text": p4})

    # ⑤ 身宫命主
    soul_star = md.get("soul_star", "")
    body_star = md.get("body_star", "")
    wuxing_ju = md.get("five_elements", "")
    p5 = f"命主{soul_star}、身主{body_star}，{wuxing_ju}。"
    if body:
        bstars = _stars_with_bright(body)
        p5 += f"身宫坐{body.get('earthly_branch','')}（{body.get('name','')}），主星{bstars}——身宫主后天趋向、中年后渐显。"
    paras.append({"title": "身宫命主", "text": p5})

    # 5.5 当前运限（大限流年并入 — 后天之行运）
    cf = chart.get("current_fortune", {}) or {}
    if cf.get("available"):
        dx = cf.get("daxian", {}) or {}
        ln = cf.get("liunian", {}) or {}
        rng = dx.get("range", [])
        rng_s = f"{rng[0]}-{rng[1]}岁" if isinstance(rng, (list, tuple)) and len(rng) == 2 else ""
        stars = "、".join(dx.get("major_stars", [])[:3]) or "无主星（借对宫论）"
        pcf = f"现行大限行{dx.get('palace','')}（{dx.get('branch','')}，{rng_s}），坐{stars}。{cf.get('daxian_tone','')}。"
        if ln and ln.get("palace"):
            lstars = "、".join(ln.get("major_stars", [])[:2]) or "无主星"
            pcf += f"{cf.get('current_year','')}年流年入{ln.get('palace','')}（{lstars}）。"
        paras.append({"title": "当前运限", "text": pcf})

    # ⑥ 命格总评
    q = _RATING_Q.get(overall, "中")
    tone = {
        "吉": "命格上乘，主星明而格局正，一生根基稳固、宜顺势进取、守正以致远。",
        "中": "命格中平，成破相参、明暗互见，全凭大限流年扶抑，重在扬长避短、趋吉避凶。",
        "凶": "命格偏弱，主星陷或煞忌重，一生多费周折，尤须借运补救、避其所忌、积善转之。",
    }.get(q)
    paras.append({"title": "命格总评", "text": tone})

    # 摘要
    headline = f"{ming.get('earthly_branch','')}命·{ming_stars}·{overall}"
    if good:
        headline += f"·{good[0].get('name','')}"

    return {
        "available": True,
        "headline": headline,
        "quality": q,
        "rating": overall,
        "ming_branch": ming.get("earthly_branch", ""),
        "ming_stars": ming_stars,
        "soul_star": soul_star,
        "body_star": body_star,
        "five_elements": wuxing_ju,
        "top_pattern": good[0].get("name", "") if good else "",
        "verdict_line": tone,
        "paragraphs": paras,
    }
