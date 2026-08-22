"""
core/date_selection/overview.py
===============================
择日·选期总论合成（综合总论层）。

择日诸果（月令节气、建除十二神、黄道吉日、吉神凶煞、宜忌、岁破月破、三煞）
原散见各日。本引擎以「本月首选吉日」为纲，织之成篇、扣事作答，并提炼选期定盘
（吉日数 + 首选之日）置顶 hero。仿八字 overview 之法。
"""
from __future__ import annotations
from typing import Dict, Any, List


def synthesize_overview(result: Dict[str, Any]) -> Dict[str, Any]:
    best = result.get("best_days", []) or []
    ausp = result.get("auspicious_days", []) or []
    inausp = result.get("inauspicious_days", []) or []
    purpose = result.get("purpose", "所择之事")
    jieqi = result.get("month_jieqi", []) or []
    three_kill = result.get("three_killings", "")

    n_good = len(ausp)
    top = best[0] if best else (ausp[0] if ausp else None)

    # 质量：有高分吉日→吉；仅中平→中；全无→凶
    if top and top.get("score", 0) >= 6:
        q = "吉"
    elif top and top.get("score", 0) >= 4:
        q = "中"
    elif not top:
        q = "凶"
    else:
        q = "中"

    paras: List[Dict[str, str]] = []

    # ① 月令节气
    p1 = f"择「{purpose}」之吉期，"
    if jieqi:
        p1 += f"本月含节气{('、'.join(jieqi))}，"
    p1 += f"月建{result.get('month_zhi','')}、太岁{result.get('year_zhi','')}。择日之法，以年月日时四柱配建除、黄道、神煞，趋吉避凶以定良辰。"
    paras.append({"title": "月令节气", "text": p1})

    # ② 首选吉日（答案核心）
    if top:
        yi = top.get("yi", []) or []
        yi_str = "、".join(yi[:5]) if isinstance(yi, list) else str(yi)
        reasons = top.get("reasons", []) or []
        p2 = (f"首选吉日：{top.get('date','')}（{top.get('weekday','')}）{top.get('ganzhi','')}日，"
              f"{top.get('officer','')}日（{top.get('officer_nature','')}）、{top.get('star','')}宿，评分{top.get('score','')}。")
        if yi_str:
            p2 += f"老黄历宜：{yi_str}。"
        if reasons:
            p2 += "得吉之由：" + "；".join(str(r) for r in reasons[:2])[:80] + "。"
        paras.append({"title": "首选吉日", "text": p2})
    else:
        paras.append({"title": "首选吉日", "text": f"本月未见适宜「{purpose}」之上吉日，宜另择他月，或退求中平之日谨慎行事。"})

    # ③ 次吉可选
    others = [d for d in ausp if not top or d.get("date") != top.get("date")]
    if others:
        ds = "、".join(f"{d.get('date','')[5:]}（{d.get('ganzhi','')}·{d.get('score','')}分）" for d in others[:5])
        paras.append({"title": "次吉可选", "text": f"本月另有吉日 {n_good} 天可选：{ds} 等，可视具体时辰、个人八字进一步遴选。"})

    # ④ 忌避之日
    breakers = [d for d in (result.get("all_days", []) or []) if d.get("is_year_breaker") or d.get("is_month_breaker")]
    p4 = ""
    if inausp:
        ds = "、".join(d.get("date", "")[5:] for d in inausp[:6])
        p4 += f"忌避之日：{ds} 等，犯凶煞或建除不利，不宜举事。"
    if breakers:
        bd = "、".join(f"{d.get('date','')[5:]}（{'岁破' if d.get('is_year_breaker') else '月破'}）" for d in breakers[:3])
        p4 += f"　大凶岁破月破：{bd}，百事不宜、务必避之。"
    if p4:
        paras.append({"title": "忌避之日", "text": p4})

    # ⑤ 三煞方位
    if three_kill:
        paras.append({"title": "三煞方位", "text": f"本{'年' if '年' in str(three_kill) else '月'}三煞在{three_kill}，此方忌动土、修造、安葬，举事时座向亦宜避之。"})

    # ⑤.5 个人配合（八字个性化）
    pz = result.get("personalization", {}) or {}
    if pz.get("available") and pz.get("personal_best"):
        prof = pz.get("profile", {})
        pb = pz["personal_best"]
        pp = (f"以本命八字论（用神{prof.get('yong','')}、忌神{prof.get('ji','')}、日支{prof.get('day_zhi','')}），"
              f"于通用吉日中再择合本命者，个人首选：")
        pp += "、".join(f"{b['date'][5:]}（{b['ganzhi']}·合{b['combined_score']}）" for b in pb[:3])
        pp += "。此「日扶其用、不犯其冲」，方为合本命之真吉。"
        paras.append({"title": "个人配合", "text": pp})

    # ⑥ 总评
    tone = {
        "吉": f"本月吉日颇丰、首选之日上佳，宜把握良辰择吉「{purpose}」，配本人八字择时则更稳。",
        "中": f"本月吉日中平，首选之日尚可用，然须细配时辰、避开冲煞，方为稳妥。",
        "凶": f"本月乏善可陈、无上吉之日，「{purpose}」宜缓、另择吉月，强择则须重重化解。",
    }.get(q)
    paras.append({"title": "选期总评", "text": tone})

    headline = f"{purpose}·本月吉日{n_good}天"
    if top:
        headline += f"·首选{top.get('date','')[5:]}（{top.get('ganzhi','')}）"

    return {
        "available": True,
        "headline": headline,
        "quality": q,
        "purpose": purpose,
        "good_count": n_good,
        "top_date": top.get("date", "") if top else "",
        "top_ganzhi": top.get("ganzhi", "") if top else "",
        "top_score": top.get("score", "") if top else "",
        "verdict_line": tone,
        "paragraphs": paras,
    }
