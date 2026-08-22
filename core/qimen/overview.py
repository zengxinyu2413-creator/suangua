"""
core/qimen/overview.py
======================
奇门遁甲·局势总论合成（综合总论层）。

奇门诸果（阴阳遁局数元、值符值使、用神落宫吉凶、格局、吉方应期）原散见各处。
本引擎以「所问之用神落宫」为纲，织之成篇、扣题作答，并提炼吉凶定盘
（用神落宫吉凶 + 最吉方位）置顶 hero。仿八字/紫微 overview 之法。
"""
from __future__ import annotations
from typing import Dict, Any, List

# 用神落宫品质 → 吉凶质量（供 hero 着色）
_Q = {
    "大吉": "吉", "吉": "吉", "小吉": "吉",
    "大凶": "凶", "凶": "凶", "次凶": "凶",
    "平": "中", "中平": "中", "平平": "中",
}


def _quality_dir(q: str) -> str:
    if not q:
        return "中"
    if any(k in q for k in ("吉",)):
        return "吉"
    if any(k in q for k in ("凶",)):
        return "凶"
    return "中"


def synthesize_overview(chart: Dict[str, Any]) -> Dict[str, Any]:
    palaces = chart.get("palaces", []) or []
    if not palaces:
        return {"available": False}

    ys = chart.get("yong_shen", {}) or {}
    ysp = chart.get("yongshen_palaces", {}) or {}
    zf = chart.get("zhifu_analysis", {}) or {}
    patterns = chart.get("patterns", []) or []
    best = chart.get("best_palaces", []) or []
    worst = chart.get("worst_palaces", []) or []
    timing = chart.get("yingqi", {}) or chart.get("timing", {}) or {}

    topic = ys.get("topic", "") or chart.get("question", "所问")
    quality = ys.get("quality", "")
    q = _quality_dir(quality)

    paras: List[Dict[str, str]] = []

    # ① 局势
    ju = f"{chart.get('ju_type','')}{chart.get('ju_number','')}局（{chart.get('yuan','')}）"
    p1 = f"此局为{ju}。"
    zfs = zf.get("zhifu", {}) or {}
    zss = zf.get("zhishi", {}) or {}
    if zfs:
        p1 += f"值符{zfs.get('star','')}临{zfs.get('palace','')}（{zfs.get('wangshuai','')}），统全局之主帅、主长远前景。"
    if zss:
        p1 += f"值使{zss.get('door','')}临{zss.get('palace','')}，主事之经过动向。"
    paras.append({"title": "局势纲领", "text": p1})

    # ② 用神落宫（所问之答案）
    p2 = f"所问「{topic}」，以{ys.get('name','用神')}为用——用神落{ys.get('palace','')}，"
    p2 += f"品论「{quality or '平'}」。{ys.get('rules','')}"
    if ys.get("best"):
        p2 += f"　最吉之象：{ys['best']}。"
    paras.append({"title": "用神落宫", "text": p2})

    # ③ 格局成败
    good_p = [p for p in patterns if p.get("severity") == "auspicious" or "吉" in p.get("level", "")]
    bad_p = [p for p in patterns if p.get("severity") == "inauspicious" or "凶" in p.get("level", "")]
    if good_p or bad_p:
        p3 = ""
        if good_p:
            p3 += "得吉格：" + "、".join(f"{g.get('name','')}（{g.get('desc','')[:18]}）" for g in good_p[:2]) + "。"
        if bad_p:
            p3 += "犯凶格：" + "、".join(f"{b.get('name','')}（{b.get('desc','')[:18]}）" for b in bad_p[:2]) + "，须避之化之。"
        paras.append({"title": "格局成败", "text": p3})

    # ④ 吉方时机
    p4 = ""
    if best:
        p4 += f"吉方：{('、'.join(best[:4]))}，宜向此方位行事、求谋、出行。"
    if worst:
        p4 += f"凶方：{('、'.join(worst[:3]))}，避之。"
    tv = timing.get("verdict") or timing.get("text") or ""
    if tv:
        p4 += f"　应期：{tv[:40]}"
    if p4:
        paras.append({"title": "吉方应期", "text": p4})

    # ⑤ 总评
    tone = {
        "吉": f"用神落宫得吉，所问「{topic}」气数顺遂，宜把握吉方吉时、顺势而为，事多可成。",
        "中": f"用神落宫平平，所问「{topic}」成败相参，须借吉方吉时、趋避格局之凶，谋定而后动。",
        "凶": f"用神落宫不利，所问「{topic}」阻力较重，宜缓图、改方易时、化解凶格，强求多不顺。",
    }.get(q)
    paras.append({"title": "综断总评", "text": tone})

    headline = f"{ju}·用神落{ys.get('palace','')}·{quality or '平'}"
    if best:
        headline += f"·吉方{best[0]}"

    return {
        "available": True,
        "headline": headline,
        "quality": q,
        "topic": topic,
        "yongshen_name": ys.get("name", ""),
        "yongshen_palace": ys.get("palace", ""),
        "yongshen_quality": quality,
        "best_direction": best[0] if best else "",
        "ju": ju,
        "verdict_line": tone,
        "paragraphs": paras,
    }
