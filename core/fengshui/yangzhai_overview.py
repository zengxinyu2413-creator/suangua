"""
core/fengshui/yangzhai_overview.py
==================================
阳宅三要·宅相总论合成（综合总论层）。

阳宅诸果（门主灶三要、灶座灶口、东西四纯度、命卦人宅相配、楼层、六事）原散见各处。
本引擎以「门主灶之格 + 人宅相配」为纲，织之成篇，并提炼宅相定盘（内格等第 +
人宅契合）置顶 hero。命卦匹配为《八宅明镜》之命根，若主人在则尤重之。
"""
from __future__ import annotations
from typing import Dict, Any, List

_GRADE_Q = {"上吉之宅": "吉", "上吉": "吉", "中吉之宅": "吉", "中吉": "吉",
            "平宅": "中", "平": "中", "小吉之宅": "中",
            "凶宅": "凶", "次凶之宅": "凶", "大凶之宅": "凶"}


def synthesize_overview(result: Dict[str, Any]) -> Dict[str, Any]:
    if not result or not result.get("grade"):
        return {"available": False}

    grade = result.get("grade", "")
    inner_q = _GRADE_Q.get(grade, "中")
    mm = result.get("mingua_match", {}) or {}
    has_person = mm.get("available")

    # 综合质量：内格 + 人宅相配（若有主人）
    if has_person:
        mq = mm.get("match_quality", "中")
        if inner_q == "吉" and mq == "吉":
            q = "吉"
        elif inner_q == "凶" or mq == "凶":
            q = "凶"
        else:
            q = "中"
    else:
        q = inner_q

    house_type = result.get("house_type", "")
    paras: List[Dict[str, str]] = []

    # ① 立宅定卦
    ho = result.get("house_overview", {}) or {}
    p1 = f"此宅为{house_type}（{ho.get('facing','')}，{ho.get('group','')}宅，宅主{ho.get('lord','')}）。"
    dd = result.get("door_detail", {}) or {}
    if dd.get("shan"):
        p1 += f"门立{dd.get('shan')}山（{dd.get('yuan','')}元龙）。"
    p1 += "阳宅以门为纳气之口、主为居人之位、灶为养命之源，三要相得方为吉宅。"
    paras.append({"title": "立宅定卦", "text": p1})

    # ② 门主灶三要（内格答案）
    mzj = result.get("menzhu_ju", {}) or {}
    zaoju = result.get("zao_ju", {}) or {}
    p2 = f"门主一节：{mzj.get('ming','')}（{mzj.get('younian','')}·{mzj.get('level','')}）。"
    if zaoju.get("quality"):
        p2 += f"灶局：主灶{zaoju.get('zhu_zao_star','')}、门灶{zaoju.get('men_zao_star','')}，灶口{zaoju.get('mouth_star','')}，品「{zaoju.get('quality','')}」。"
    paras.append({"title": "门主灶三要", "text": p2})

    # ③ 人宅相配（命卦匹配 — 命根）
    if has_person:
        my = mm.get("men_younian", {}) or {}
        zy = mm.get("zhu_younian", {}) or {}
        zaoy = mm.get("zao_younian", {}) or {}
        p3 = (f"主人{mm.get('ming_gua','')}命（{mm.get('ming_group','')}）配此{mm.get('house_group','').replace('卦','宅')}，"
              f"断「{mm.get('match_level','')}」。门落主人{my.get('younian','')}（{my.get('ji_xiong','')}）、"
              f"主落{zy.get('younian','')}（{zy.get('ji_xiong','')}）、灶落{zaoy.get('younian','')}（{zaoy.get('ji_xiong','')}）。")
        paras.append({"title": "人宅相配", "text": p3})

    # ④ 东西四纯度
    pur = result.get("purity", {}) or {}
    if pur:
        p4 = f"东西四纯度：{pur.get('desc','')}"
        paras.append({"title": "纯度", "text": p4})

    # ⑤ 楼层 / 六事（若有）
    extras = []
    fl = result.get("floor_guide", {}) or {}
    if fl:
        extras.append(f"楼层：{(fl.get('desc') or fl.get('summary') or '')[:30]}")
    if result.get("liushi"):
        extras.append("已纳六事安置之断")
    if extras:
        paras.append({"title": "楼层六事", "text": "；".join(extras) + "。"})

    # ⑥ 宅相总评
    if has_person:
        tone = {
            "吉": f"内格{grade}、人宅相配，{mm.get('summary','')[:40]}此乃宅得其格、人得其宅之上吉。",
            "中": f"内格{grade}，然人宅相配尚有未谐——{mm.get('summary','')[:36]}宜调门主灶以就主人吉方。",
            "凶": f"虽内格或可，然人宅不配为大忌——{mm.get('summary','')[:40]}《八宅明镜》最重命宅相得，宜亟改或另择。",
        }.get(q)
    else:
        tone = {
            "吉": f"门主灶三要俱合、{grade}，丁财可旺；若再以主人命卦相配则尽善。",
            "中": f"三要{grade}、吉凶相参，宜调门主灶之失，并配主人命卦以求全吉。",
            "凶": f"三要{grade}、犯凶游年，主损丁破财，宜亟改门、移主或迁灶。",
        }.get(q)
    paras.append({"title": "宅相总评", "text": tone})

    headline = f"{house_type}·{grade}"
    if has_person:
        headline += f"·{mm.get('match_level','')}"

    return {
        "available": True,
        "headline": headline,
        "quality": q,
        "grade": grade,
        "house_type": house_type,
        "has_person": bool(has_person),
        "match_level": mm.get("match_level", "") if has_person else "",
        "verdict_line": tone,
        "paragraphs": paras,
    }
