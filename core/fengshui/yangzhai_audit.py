"""
core/fengshui/yangzhai_audit.py
===============================
阳宅三要·宅相一致性审核引擎（确定性层）。

核查跨模块矛盾：内格上吉而人宅不配（《八宅明镜》大忌）、门主局吉而灶局凶、
纯杂与等第相左、门主灶落主人凶方而内格仍判吉等。可测试、可复现。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SEV_RANK = {"矛盾": 3, "注意": 2, "提示": 1}
_GRADE_Q = {"上吉之宅": "吉", "中吉之宅": "吉", "中吉": "吉", "上吉": "吉",
            "平宅": "中", "平": "中", "凶宅": "凶", "次凶之宅": "凶", "大凶之宅": "凶"}


def audit_consistency(result: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    if not result or not result.get("grade"):
        return {"available": False}

    grade = result.get("grade", "")
    gq = _GRADE_Q.get(grade, "中")
    mm = result.get("mingua_match", {}) or {}
    mzj = result.get("menzhu_ju", {}) or {}
    zaoju = result.get("zao_ju", {}) or {}
    pur = result.get("purity", {}) or {}

    # ① 内格吉 vs 人宅不配（八宅明镜大忌）
    if mm.get("available"):
        mq = mm.get("match_quality", "")
        if gq == "吉" and mq == "凶":
            findings.append({
                "id": "grade_vs_person", "severity": "矛盾",
                "title": "门主灶内格吉 · 然人宅不配",
                "modules": ["门主灶内格", "人宅相配"],
                "detail": f"门主灶内格判「{grade}」，然主人{mm.get('ming_gua','')}命与此宅「{mm.get('match_level','')}」。",
                "suggestion": "《八宅明镜》最重人宅相得：内格再吉，若东西四命宅相违、门主灶落主人凶方，"
                              "此宅于此人仍凶。当以人宅相配为准、内格为辅；宜另择合命之宅，或重调门主灶就主人吉方。",
            })
        elif gq == "凶" and mq == "吉":
            findings.append({
                "id": "grade_vs_person2", "severity": "注意",
                "title": "门主灶内格凶 · 然人宅尚配",
                "modules": ["门主灶内格", "人宅相配"],
                "detail": f"内格「{grade}」，然主人命卦与宅「{mm.get('match_level','')}」。",
                "suggestion": "命宅虽同类，然门主灶内部游年犯凶；宜调门主灶之凶位，人宅相得之利方能尽显。",
            })
        # 门主灶落主人凶方而内格判吉
        xiong_n = mm.get("xiong_count", 0)
        if gq == "吉" and xiong_n >= 2 and mm.get("match_quality") != "凶":
            findings.append({
                "id": "ji_pos_xiong", "severity": "注意",
                "title": "内格吉 · 然门主灶多落主人凶方",
                "modules": ["人宅相配"],
                "detail": f"门主灶有 {xiong_n} 处落主人（{mm.get('ming_gua','')}命）之凶游年。",
                "suggestion": "纵命宅同类、内格亦吉，门主灶若落主人绝命五鬼等凶方，主人仍受其害；宜就主人吉方安主卧、灶位。",
            })

    # ② 门主局吉 vs 灶局凶
    mlvl = mzj.get("level", "")
    zq = zaoju.get("quality", "")
    if mlvl in ("上吉", "中吉") and ("凶" in zq):
        findings.append({
            "id": "men_vs_zao", "severity": "注意",
            "title": "门主局吉 · 然灶局凶",
            "modules": ["门主局", "灶局"],
            "detail": f"门主局「{mlvl}」，然灶局「{zq}」。",
            "suggestion": "灶为养命之源，灶凶则门主之吉打折，主病灾口角；宜迁灶或调灶口向就吉方。",
        })
    elif ("凶" in mlvl) and zq in ("大吉", "上吉", "中吉"):
        findings.append({
            "id": "zao_vs_men", "severity": "提示",
            "title": "灶局吉 · 然门主局凶",
            "modules": ["门主局", "灶局"],
            "detail": f"灶局「{zq}」，然门主局「{mlvl}」。",
            "suggestion": "门主为宅之大局，门主凶则灶吉难救全局；宜以改门移主为先。",
        })

    # ③ 纯杂 vs 等第
    if pur and not pur.get("pure") and gq == "吉":
        findings.append({
            "id": "purity_vs_grade", "severity": "提示",
            "title": "判为吉宅 · 然东西四驳杂",
            "modules": ["东西四纯度", "门主灶内格"],
            "detail": "门主灶东西四混杂，然内格仍判吉。",
            "suggestion": "驳杂之宅吉力不纯、易生反复；纵游年得吉亦宜留意，长居须防杂气之扰。",
        })

    # ④ 门主局犯绝命五鬼而等第未判大凶
    yn = mzj.get("younian", "")
    if yn in ("绝命", "五鬼") and gq != "凶":
        findings.append({
            "id": "juemin_not_xiong", "severity": "注意",
            "title": f"门主犯{yn} · 然等第未判凶",
            "modules": ["门主局"],
            "detail": f"门主游年为{yn}（大凶），然综合等第为「{grade}」。",
            "suggestion": f"{yn}为八宅大凶之星，门主犯之主损丁重病；纵灶吉纯一，亦宜以改门移主为亟，等第宜从严。",
        })

    n_conflict = sum(1 for f in findings if f["severity"] == "矛盾")
    n_attn = sum(1 for f in findings if f["severity"] == "注意")
    n_tip = sum(1 for f in findings if f["severity"] == "提示")
    findings.sort(key=lambda f: -_SEV_RANK.get(f["severity"], 0))

    if n_conflict:
        verdict = f"发现 {n_conflict} 处跨模块矛盾，宜审定后再据以断宅。"
    elif n_attn:
        verdict = f"未见硬性矛盾，有 {n_attn} 处需权衡之张力。"
    elif n_tip:
        verdict = f"各模块结论协调，余 {n_tip} 处常规提示。"
    else:
        verdict = "门主灶与人宅各模块结论协调，无矛盾。"

    return {
        "available": True,
        "summary": {"矛盾": n_conflict, "注意": n_attn, "提示": n_tip},
        "verdict": verdict,
        "findings": findings,
        "clean": n_conflict == 0 and n_attn == 0,
    }
