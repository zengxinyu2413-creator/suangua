"""
core/fengshui/xuankong_audit.py
===============================
玄空飞星·宅运一致性审核引擎（确定性层）。

核查跨模块矛盾：山向格局吉凶 vs 力量推理链、上山下水却评吉（须有救应）、
旺山旺向却评弱（须有破局）、犯反伏吟、五黄入向山等。可测试、可复现。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SEV_RANK = {"矛盾": 3, "注意": 2, "提示": 1}
_LEVEL_Q = {"auspicious_great": "吉", "auspicious": "吉",
            "inauspicious": "凶", "inauspicious_great": "凶"}


def audit_consistency(chart: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    if not chart or not chart.get("verdict"):
        return {"available": False}

    verdict = chart.get("verdict", "")
    level = chart.get("verdict_level", "")
    vq = _LEVEL_Q.get(level, "中")
    zsyn = chart.get("zhaiyun_synthesis", {}) or {}
    comp = zsyn.get("composite_label", "")
    comp_q = "吉" if comp in ("宅运极旺", "宅运向上") else ("凶" if comp in ("宅运偏弱", "宅运受损") else "中")
    sps = chart.get("special_patterns", []) or []
    ss = chart.get("shangshan")
    xs = chart.get("xiashui")

    # ① 山向格局吉凶 vs 力量推理链
    if vq != "中" and comp_q != "中" and vq != comp_q:
        sev = "注意"
        findings.append({
            "id": "verdict_vs_force", "severity": sev,
            "title": "山向格局吉凶 · 与力量推理链相左",
            "modules": ["山向格局", "宅运力量推理链"],
            "detail": f"山向定盘「{verdict}」（{vq}向），力量推理链评「{comp}」（{comp_q}向）。",
            "suggestion": "定盘只论山向到位之吉凶，推理链折入特殊格局救应、城门、峦头之补；"
                          "上山下水逢三般卦反吉、旺山旺向遇五黄反伏吟则减分——以推理链看实际成色。",
        })

    # ② 上山下水却推理链评吉（须有救应）—— 解释性提示
    if ss and xs and comp_q == "吉":
        has_save = any(s.get("level", "").startswith("auspicious") and
                       any(k in s.get("name", "") for k in ("三般卦", "连珠", "父母", "合十"))
                       for s in sps)
        findings.append({
            "id": "shangshan_saved", "severity": "提示",
            "title": "上山下水 · 然得救应转吉",
            "modules": ["山向格局", "特殊格局"],
            "detail": "本为上山下水之凶局，然推理链评吉——" + ("已检出三般卦/合十等救应格" if has_save else "其救应之据须复核"),
            "suggestion": "上山下水唯逢三般卦、合十、连珠一气贯通方可反吉，且须峦头配合（山向颠倒之水法）；"
                          "若无此等救应，则不宜评吉，当以凶局论。",
        })

    # ③ 旺山旺向却推理链评弱（须有破局）
    if chart.get("wangshan") and chart.get("wangxiang") and comp_q == "凶":
        findings.append({
            "id": "wangshan_broken", "severity": "注意",
            "title": "旺山旺向 · 然推理链评弱",
            "modules": ["山向格局", "特殊格局"],
            "detail": "本为旺山旺向之吉局，然推理链评弱——多因反伏吟、五黄、衰方过多破局。",
            "suggestion": "旺山旺向虽吉，若犯反伏吟、五黄入中或峦头不配，则吉局受损；须化解破局之煞方保其格。",
        })

    # ④ 犯反伏吟
    ff = chart.get("fan_fu_yin", {}) or {}
    if ff.get("has_fan_fu_yin"):
        findings.append({
            "id": "fan_fu_yin", "severity": "注意",
            "title": "盘犯反吟伏吟",
            "modules": ["反伏吟"],
            "detail": "飞星盘见反吟或伏吟，主反复、哭泣、动荡不宁。",
            "suggestion": "反伏吟之患，纵山向得令亦减其吉；须以五行通关、化解物制之，或避其方不作动用。",
        })

    # ⑤ 五黄入向/山
    wuhuang = [s.get("name", "") for s in sps
               if "五黄" in s.get("name", "") and s.get("level", "").startswith("inauspicious")]
    if wuhuang:
        findings.append({
            "id": "wuhuang", "severity": "提示",
            "title": "五黄入向／入山",
            "modules": ["特殊格局"],
            "detail": f"检出{('、'.join(wuhuang))}——五黄廉贞为第一凶星，所临之方忌动忌水。",
            "suggestion": "五黄所在之方，忌开门、动土、见水路；宜静、宜以金（铜铃等）泄之，流年五黄叠加尤须谨慎。",
        })

    n_conflict = sum(1 for f in findings if f["severity"] == "矛盾")
    n_attn = sum(1 for f in findings if f["severity"] == "注意")
    n_tip = sum(1 for f in findings if f["severity"] == "提示")
    findings.sort(key=lambda f: -_SEV_RANK.get(f["severity"], 0))

    if n_conflict:
        verdict_t = f"发现 {n_conflict} 处跨模块矛盾，宜审定后再据以布局。"
    elif n_attn:
        verdict_t = f"未见硬性矛盾，有 {n_attn} 处需权衡之张力。"
    elif n_tip:
        verdict_t = f"各模块结论协调，余 {n_tip} 处常规提示。"
    else:
        verdict_t = "各模块结论彼此协调，无矛盾。"

    return {
        "available": True,
        "summary": {"矛盾": n_conflict, "注意": n_attn, "提示": n_tip},
        "verdict": verdict_t,
        "findings": findings,
        "clean": n_conflict == 0 and n_attn == 0,
    }
