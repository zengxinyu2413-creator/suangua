"""
core/qimen/consistency_audit.py
===============================
奇门遁甲·局势一致性审核引擎（确定性层）。

奇门诸子模块各自成断，彼此可能潜藏矛盾：用神落宫评吉而力量推理链评乏、
用神落宫却在凶方、用事类别与所问不符、值符值使关系与总断相左……本引擎据
已知矛盾型态确定性核查，产出结构化审核发现。可测试、可复现；其上有 AI 审定层。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SEV_RANK = {"矛盾": 3, "注意": 2, "提示": 1}


def _q_dir(q: str) -> str:
    if not q:
        return "中"
    if "吉" in q:
        return "吉"
    if "凶" in q:
        return "凶"
    return "中"


def audit_consistency(chart: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []

    ys = chart.get("yong_shen", {}) or {}
    ysf = chart.get("yongshen_synthesis", {}) or {}
    best = chart.get("best_palaces", []) or []
    worst = chart.get("worst_palaces", []) or []
    ls = chart.get("layer_summary", {}) or {}
    palaces = chart.get("palaces", []) or []

    yp = ys.get("palace", "")
    yq_dir = _q_dir(ys.get("quality", ""))
    comp = ysf.get("composite_label", "")
    comp_dir = "吉" if comp in ("用神大有力", "用神有力") else ("凶" if comp in ("用神乏力", "用神受制") else "中")

    # ① 用神落宫吉凶 vs 力量推理链
    if yq_dir and comp_dir and yq_dir != "中" and comp_dir != "中" and yq_dir != comp_dir:
        findings.append({
            "id": "yonggong_vs_force",
            "severity": "矛盾",
            "title": "用神落宫吉凶 · 与力量推理链相左",
            "modules": ["用神落宫", "用神力量推理链"],
            "detail": f"用神落宫评「{ys.get('quality','')}」（{yq_dir}向），然力量推理链评「{comp}」（{comp_dir}向）。",
            "suggestion": "落宫品质主看星门神本身，推理链折入门宫旺衰、干仪、值符关系；"
                          "二者分歧时以推理链为准看实际成色，落宫吉凶看底色。",
        })

    # ② 用神落宫在凶方
    if yp and yp in worst:
        findings.append({
            "id": "yong_in_worst",
            "severity": "注意",
            "title": "用神落宫正在凶方",
            "modules": ["用神落宫", "吉凶方位"],
            "detail": f"用神落{yp}，而{yp}列为凶方。",
            "suggestion": "用神所落即凶方者，所问之事其方位不利、须避正冲；宜以用神宫之吉凶为主、方位为辅权衡。",
        })
    elif yp and best and yp not in best:
        findings.append({
            "id": "yong_not_in_best",
            "severity": "提示",
            "title": "用神落宫非最吉方",
            "modules": ["用神落宫", "吉凶方位"],
            "detail": f"用神落{yp}，不在吉方（{('、'.join(best[:3]))}）之列。",
            "suggestion": "用神不临吉方，行事可借吉方之力辅之，然成败终以用神宫本身为准。",
        })

    # ③ 用神宫击刑入墓空亡
    sp = ls.get("special", {}) or {}
    afflict = []
    if yp in (sp.get("击刑宫", []) or []):
        afflict.append("击刑")
    if yp in (sp.get("入墓宫", []) or []):
        afflict.append("入墓")
    if yp in (sp.get("空亡宫", []) or []):
        afflict.append("空亡")
    if afflict:
        findings.append({
            "id": "yong_afflicted",
            "severity": "注意",
            "title": f"用神宫逢{('、'.join(afflict))}",
            "modules": ["用神落宫", "击刑入墓空亡"],
            "detail": f"用神落{yp}，该宫逢{('、'.join(afflict))}之累。",
            "suggestion": "用神逢击刑则事受冲击、入墓则气闭难发、空亡则事多落空；"
                          "纵落宫星门吉，亦须待出空、冲墓、解刑之时方应，宜降信心或改时改方。",
        })

    # ④ 用神门是否上盘
    if "未上盘" in yp:
        findings.append({
            "id": "yong_not_on_plate",
            "severity": "注意",
            "title": "用神门不上盘",
            "modules": ["用神落宫"],
            "detail": "所取用神之门未现于盘中，已取次门论之。",
            "suggestion": "用神门不上盘者，所问之事缺乏直接凭借，须借次用神或对宫论之，成事较费力。",
        })

    n_conflict = sum(1 for f in findings if f["severity"] == "矛盾")
    n_attn = sum(1 for f in findings if f["severity"] == "注意")
    n_tip = sum(1 for f in findings if f["severity"] == "提示")
    findings.sort(key=lambda f: -_SEV_RANK.get(f["severity"], 0))

    if n_conflict:
        verdict = f"发现 {n_conflict} 处跨模块矛盾，宜审定后再据以决断。"
    elif n_attn:
        verdict = f"未见硬性矛盾，有 {n_attn} 处需权衡之张力。"
    elif n_tip:
        verdict = f"各模块结论协调，余 {n_tip} 处常规提示。"
    else:
        verdict = "各模块结论彼此协调，无矛盾。"

    return {
        "available": True,
        "summary": {"矛盾": n_conflict, "注意": n_attn, "提示": n_tip},
        "verdict": verdict,
        "findings": findings,
        "clean": n_conflict == 0 and n_attn == 0,
    }
