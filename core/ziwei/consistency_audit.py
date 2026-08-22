"""
core/ziwei/consistency_audit.py
===============================
紫微斗数·命盘一致性审核引擎（确定性层）。

紫微诸子模块各自成断，彼此可能潜藏矛盾：命格评等高而推理链评弱、吉格凶格并见
未明孰主、命宫主星陷而仍评上格、煞忌交冲而命格仍高……本引擎据已知矛盾型态
确定性核查，产出结构化「审核发现」，每条标明涉及模块、轻重、缘由、建议。
可测试、可复现；其上另有 AI 审定层。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SEV_RANK = {"矛盾": 3, "注意": 2, "提示": 1}

# 评等 / 推理链评定 → 三级（高/中/低），以便比对
_RATING_TIER = {"上格": 2, "中上格": 2, "中格": 1, "平格": 1, "中下格": 0, "下格": 0}
_COMP_TIER = {"命格上乘": 2, "命格中上": 2, "命格中平": 1, "命格偏弱": 0, "命格受损": 0}
_SHA = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}
_FALLEN = {"陷", "不"}


def audit_consistency(chart: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []

    palaces = chart.get("palaces", []) or []
    ins = chart.get("insights", {}) or {}
    rating = ins.get("rating", {}) or {}
    patterns = ins.get("patterns", {}) or {}
    fs = ins.get("feihua_summary", {}) or {}
    mg = chart.get("mingge_synthesis", {}) or {}
    ming = next((p for p in palaces if p.get("is_soul")), None)

    overall = rating.get("overall", "")
    comp = mg.get("composite_label", "")
    r_tier = _RATING_TIER.get(overall)
    c_tier = _COMP_TIER.get(comp)

    # ① 命格评等 vs 推理链综合评定 张力
    if r_tier is not None and c_tier is not None:
        gap = r_tier - c_tier
        if gap >= 2:
            findings.append({
                "id": "rating_vs_synthesis_hard",
                "severity": "矛盾",
                "title": "命格评等高 · 推理链却评弱",
                "modules": ["命格评等", "命格力量推理链"],
                "detail": f"评等判「{overall}」，然命格推理链评「{comp}」，相去甚远。",
                "suggestion": "评等主据命宫三方主星之庙旺，推理链则折入煞星、凶格、四化之损；"
                              "二者分歧多因煞忌或凶格拖累。宜以推理链为准看实际成色，评等看先天底子。",
            })
        elif gap == 1:
            findings.append({
                "id": "rating_vs_synthesis_soft",
                "severity": "注意",
                "title": "命格评等略高于推理链",
                "modules": ["命格评等", "命格力量推理链"],
                "detail": f"评等「{overall}」、推理链「{comp}」，略有落差。",
                "suggestion": "先天主星明而后天有煞忌之损；底子虽好，须留意减分之处，趋避方显其格。",
            })
        elif gap <= -1:
            findings.append({
                "id": "synthesis_above_rating",
                "severity": "提示",
                "title": "推理链评高于命格评等",
                "modules": ["命格评等", "命格力量推理链"],
                "detail": f"评等「{overall}」、推理链却「{comp}」。",
                "suggestion": "或因吉格、吉化补益超出主星庙旺之评；命格实际成色或胜先天底子。",
            })

    # ② 吉格 + 凶格并存
    good = patterns.get("good", []) or []
    bad = patterns.get("bad", []) or []
    if good and bad:
        findings.append({
            "id": "good_bad_coexist",
            "severity": "提示",
            "title": "吉格凶格并见 · 宜辨主从",
            "modules": ["格局成破"],
            "detail": f"命中既成吉格（{('、'.join(g.get('name','') for g in good[:2]))}），"
                      f"又带凶格（{('、'.join(b.get('name','') for b in bad[:2]))}）。",
            "suggestion": "吉凶交杂之命，须辨何者居命宫三方为主、何者在闲宫为次；"
                          "吉格在命而凶格在外则吉为主，反之则须防凶格破局。",
        })

    # ③ 命宫主星落陷 vs 命格评等高
    if ming and r_tier == 2:
        majors = ming.get("major_stars", []) or []
        fallen_majors = [s.get("name", "") for s in majors if s.get("brightness", "") in _FALLEN]
        if fallen_majors:
            findings.append({
                "id": "ming_fallen_but_high",
                "severity": "注意",
                "title": "命宫主星落陷 · 评等却高",
                "modules": ["命宫主星", "命格评等"],
                "detail": f"命宫主星{('、'.join(fallen_majors))}落陷，然命格评「{overall}」。",
                "suggestion": "评等高或赖三方四正庙旺补之；然命宫主星陷者，本宫之事（性情、际遇）"
                              "终有亏，宜看三方能否实补，否则评等虚高。",
            })

    # ④ 煞忌交冲 vs 命格评等高
    soul_chong = fs.get("soul_chong", []) or []
    double_ji = fs.get("double_ji", []) or []
    sj_idx = set(((chart.get("sanjiao_analysis", {}) or {}).get("sanjiao", {}) or {}).get("palaces", []) or [])
    if ming:
        sj_idx |= {ming.get("index")}
    sha_n = sum(1 for p in palaces if p.get("index") in sj_idx
                for s in (p.get("minor_stars", []) or []) + (p.get("adj_stars", []) or [])
                if s.get("name") in _SHA)
    if r_tier == 2 and (soul_chong or sha_n >= 3):
        bits = []
        if soul_chong:
            bits.append(f"{len(soul_chong)}化忌冲命")
        if sha_n >= 3:
            bits.append(f"{sha_n}煞入命三方")
        findings.append({
            "id": "shaji_vs_high",
            "severity": "注意",
            "title": "煞忌交冲 · 命格评等却高",
            "modules": ["煞星四化", "命格评等"],
            "detail": f"命三方{('、'.join(bits))}，然命格评「{overall}」。",
            "suggestion": "煞忌重者纵主星庙旺，亦主成中带败、富贵中有波折；评等宜下调一档看实际，"
                          "或赖吉化、吉格化解方能保其格。",
        })

    # ⑤ 空宫坐命
    if ming and not (ming.get("major_stars") or []):
        findings.append({
            "id": "empty_ming",
            "severity": "提示",
            "title": "命宫无正曜 · 借星论命",
            "modules": ["命宫主星"],
            "detail": "命宫无主星（空宫），须借对宫（迁移宫）主星论命。",
            "suggestion": "空宫坐命者性情多浮动、易受环境影响；论命当重对宫主星及三方四正之力。",
        })

    # ⑥ 双忌叠宫
    if double_ji:
        gongs = list(dict.fromkeys(d.get("to", "") for d in double_ji if d.get("to")))
        findings.append({
            "id": "double_ji_warn",
            "severity": "提示",
            "title": "双忌叠宫 · 该宫之事纠缠",
            "modules": ["四化飞星"],
            "detail": f"两化忌同叠于{('、'.join(gongs[:2]))}宫，主该宫之事多反复、损耗重。",
            "suggestion": "双忌之宫为命中症结所在，须于该宫所主之事（如父母、疾厄）格外谨慎、早作筹谋。",
        })

    n_conflict = sum(1 for f in findings if f["severity"] == "矛盾")
    n_attn = sum(1 for f in findings if f["severity"] == "注意")
    n_tip = sum(1 for f in findings if f["severity"] == "提示")
    findings.sort(key=lambda f: -_SEV_RANK.get(f["severity"], 0))

    if n_conflict:
        verdict = f"发现 {n_conflict} 处跨模块矛盾，宜审定后再据以论命。"
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
