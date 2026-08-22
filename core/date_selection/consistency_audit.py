"""
core/date_selection/consistency_audit.py
========================================
择日·一致性审核引擎（确定性层）。

核查跨模块矛盾：首选日分数高而力量推理链评弱、建除宜事而老黄历忌（或反之）、
黄道吉日却凶煞重、首选日竟犯岁破月破等。可测试、可复现。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SEV_RANK = {"矛盾": 3, "注意": 2, "提示": 1}


def audit_consistency(result: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    best = result.get("best_days", []) or []
    ausp = result.get("auspicious_days", []) or []
    top = best[0] if best else (ausp[0] if ausp else None)
    if not top:
        return {"available": True, "summary": {"矛盾": 0, "注意": 0, "提示": 0},
                "verdict": "本月无吉日可选，无可审核。", "findings": [], "clean": True}

    purpose = result.get("purpose", "")
    syn = result.get("zeri_synthesis", {}) or {}
    comp = syn.get("composite_label", "")
    comp_q = "吉" if comp in ("上吉之日", "吉日可用") else ("凶" if comp in ("次日宜慎", "凶日勿用") else "中")
    score = top.get("score", 0)

    # ① 首选日分数 vs 力量推理链
    sc_q = "吉" if score >= 6 else ("凶" if score <= 2 else "中")
    if sc_q != "中" and comp_q != "中" and sc_q != comp_q:
        findings.append({
            "id": "score_vs_force", "severity": "注意",
            "title": "首选日评分 · 与力量推理链相左",
            "modules": ["首选吉日", "吉日力量推理链"],
            "detail": f"该日老黄历评分 {score}（{sc_q}向），然力量推理链评「{comp}」（{comp_q}向）。",
            "suggestion": "评分综合宜事多寡，推理链折入建除、黄道、凶煞、岁破之轻重；"
                          "二者分歧时，岁破月破、重凶煞当以推理链为准从严，宁可另择。",
        })

    # ② 建除宜事 vs 老黄历宜忌（建除忌而黄历宜，或反之）
    od = str(top.get("officer_detail", ""))
    yi = top.get("yi", []) or []
    ji = top.get("ji", []) or []
    _SYN = {
        "结婚": ["嫁娶", "婚", "纳采", "订盟"], "婚嫁": ["嫁娶", "婚", "纳采"],
        "搬家": ["移徙", "入宅", "搬"], "入宅": ["入宅", "移徙"],
        "动土": ["动土", "破土"], "开业": ["开市", "开业"], "开市": ["开市", "开业"],
        "安葬": ["安葬", "破土", "启钻"], "出行": ["出行", "远行"],
    }
    keys = [purpose] + _SYN.get(purpose, [])
    yi_hit = purpose and any(any(k in str(y) for k in keys) for y in yi)
    ji_hit = purpose and any(any(k in str(j) for k in keys) for j in ji)
    officer_avoids = purpose and ("忌" in od) and any(k in od for k in keys)
    if yi_hit and officer_avoids:
        findings.append({
            "id": "officer_vs_huangli", "severity": "注意",
            "title": "建除忌此事 · 老黄历却宜",
            "modules": ["建除十二神", "老黄历宜忌"],
            "detail": f"{top.get('officer','')}日之性忌「{purpose}」，然老黄历列此日宜「{purpose}」。",
            "suggestion": "建除与老黄历各有所本而偶相左；婚嫁尤重，建除「建破平收」等本忌嫁娶者，"
                          "纵黄历列宜亦宜慎，可优先取「成、开、定」等日，或细配吉神化解。",
        })
    if ji_hit:
        findings.append({
            "id": "huangli_ji", "severity": "矛盾",
            "title": "老黄历此日正忌所择之事",
            "modules": ["老黄历宜忌"],
            "detail": f"老黄历明列此日忌「{purpose}」，却被选为首选。",
            "suggestion": "老黄历忌某事者，纵分数较高亦不宜强用此事；当于吉日中另取不忌之日。",
        })

    # ③ 黄道吉日却凶煞重
    xs = top.get("xiong_sha", []) or []
    if (top.get("huangdao") or "黄道" in str(top.get("day_god_type", ""))) and len(xs) >= 4:
        findings.append({
            "id": "huangdao_but_sha", "severity": "提示",
            "title": "黄道吉日 · 然凶煞较重",
            "modules": ["黄道吉日", "凶煞"],
            "detail": f"该日虽属黄道吉日，然值{len(xs)}凶煞（{('、'.join(str(x) for x in xs[:3]))}等）。",
            "suggestion": "黄道能解部分凶煞，然凶煞过重者仍须避其所忌、以吉神制之，或择凶煞较少之吉日。",
        })

    # ④ 首选日犯岁破月破
    if top.get("is_year_breaker") or top.get("is_month_breaker"):
        findings.append({
            "id": "top_is_breaker", "severity": "矛盾",
            "title": "首选日竟犯" + ("岁破" if top.get("is_year_breaker") else "月破"),
            "modules": ["首选吉日", "岁破月破"],
            "detail": "首选之日犯" + ("岁破（冲太岁）" if top.get("is_year_breaker") else "月破（冲月建）") + "，本应百事不宜。",
            "suggestion": "岁破月破为择日第一大忌，任何吉神不能解；此日断不可用，须从吉日中重新遴选。",
        })

    n_conflict = sum(1 for f in findings if f["severity"] == "矛盾")
    n_attn = sum(1 for f in findings if f["severity"] == "注意")
    n_tip = sum(1 for f in findings if f["severity"] == "提示")
    findings.sort(key=lambda f: -_SEV_RANK.get(f["severity"], 0))

    if n_conflict:
        verdict = f"发现 {n_conflict} 处跨模块矛盾，首选日宜复核或另择。"
    elif n_attn:
        verdict = f"未见硬性矛盾，有 {n_attn} 处需权衡之张力。"
    elif n_tip:
        verdict = f"各模块结论协调，余 {n_tip} 处常规提示。"
    else:
        verdict = "首选日各模块结论协调，无矛盾。"

    return {
        "available": True,
        "summary": {"矛盾": n_conflict, "注意": n_attn, "提示": n_tip},
        "verdict": verdict,
        "findings": findings,
        "clean": n_conflict == 0 and n_attn == 0,
    }
