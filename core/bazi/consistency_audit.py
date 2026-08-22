"""
core/bazi/consistency_audit.py
==============================
八字·命局一致性审核引擎（确定性层）。

八字诸子模块各自成断，彼此可能潜藏矛盾：身弱却取克泄为用、调候用神与扶抑用神
相克、格局评凶而命局推理链评上佳、用神忌神五行重叠……规则引擎不会自我报警。
本引擎据已知矛盾型态确定性核查，产出结构化「审核发现」，每条标明涉及模块、
轻重（矛盾/注意/提示）、缘由、建议。可测试、可复现；其上另有 AI 审定层。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SEV_RANK = {"矛盾": 3, "注意": 2, "提示": 1}

# 天干→五行
_GAN_WX = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
# 五行相生（我生者）、相克（我克者）
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}   # X 生 _SHENG[X]
_KE = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}        # X 克 _KE[X]


def _sheng_wo(wx):  # 生我者（印）
    for k, v in _SHENG.items():
        if v == wx:
            return k
    return ""


def _ke_wo(wx):  # 克我者（官杀）
    for k, v in _KE.items():
        if v == wx:
            return k
    return ""


def _fu_yi_sets(dm_wx):
    """返回 (扶身五行集, 克泄五行集)。扶=印+比；泄=食伤+财+官杀。"""
    fu = {dm_wx, _sheng_wo(dm_wx)}                       # 同我 + 生我
    xie = {_SHENG.get(dm_wx, ""), _KE.get(dm_wx, ""), _ke_wo(dm_wx)}  # 我生 + 我克 + 克我
    return {x for x in fu if x}, {x for x in xie if x}


def audit_consistency(chart: Dict[str, Any]) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []

    dm = chart.get("day_master", "")
    dm_wx = chart.get("day_master_wuxing", "") or _GAN_WX.get(dm, "")
    strength = chart.get("strength", "")
    ys = chart.get("yong_shen", {}) or {}
    th = chart.get("tiaohou", {}) or {}
    ge = (chart.get("combos", {}) or {}).get("geju_evaluation", {}) or {}
    mj = chart.get("mingju_synthesis", {}) or {}
    sp = chart.get("special_patterns", {}) or {}

    yw = ys.get("yong_shen_wx", "")
    jw = ys.get("ji_shen_wx", "")
    fu_set, xie_set = _fu_yi_sets(dm_wx) if dm_wx else (set(), set())

    # ① 身强弱 vs 用神方向矛盾
    if yw and dm_wx and strength:
        if "弱" in strength and yw in xie_set:
            findings.append({
                "id": "weak_but_drain_yong",
                "severity": "矛盾",
                "title": "身弱却取克泄为用",
                "modules": ["日主旺衰", "用神喜忌"],
                "detail": f"日主{dm}{dm_wx}评为{strength}，然用神取{yw}——{yw}于{dm_wx}属克泄耗之神。"
                          f"身弱当扶（取印比），反取克泄则身愈不堪。",
                "suggestion": "复核：若确系身弱，用神当取印（生我）、比劫（同我）扶身；"
                              "若取克泄，或为从弱格、或身弱有从势之象，须明示其取用之据。",
            })
        elif "强" in strength and yw in fu_set:
            findings.append({
                "id": "strong_but_help_yong",
                "severity": "矛盾",
                "title": "身强却取生扶为用",
                "modules": ["日主旺衰", "用神喜忌"],
                "detail": f"日主{dm}{dm_wx}评为{strength}，然用神取{yw}——{yw}于{dm_wx}属生扶之神。"
                          f"身强当抑（取克泄），反取生扶则旺上加旺。",
                "suggestion": "复核：身强用神当取官杀、食伤、财以泄耗；"
                              "若取生扶，或为专旺/从强格，须明示其取用之据。",
            })

    # ② 调候用神 vs 扶抑用神冲突
    th_primary = th.get("primary", "")
    th_wx = _GAN_WX.get(th_primary, "")
    if th_wx and yw and th_wx != yw:
        # 调候用神与扶抑用神分属扶/泄两端 → 打架
        if (th_wx in fu_set and yw in xie_set) or (th_wx in xie_set and yw in fu_set):
            findings.append({
                "id": "tiaohou_vs_fuyi",
                "severity": "注意",
                "title": "调候用神与扶抑用神两端",
                "modules": ["调候", "用神喜忌"],
                "detail": f"调候须{th_primary}（{th_wx}），扶抑用神取{yw}——一属扶身、一属克泄，方向相左。",
                "suggestion": "调候与扶抑相争，乃八字常见之两难。须权其缓急："
                              "气候过偏（寒暖燥湿太过）则调候为急、否则以扶抑财官为重；宜明示取舍。",
            })

    # ③ 格局质量 vs 命局推理链综合评定 张力
    quality = ge.get("quality", "")
    comp = mj.get("composite_label", "")
    if quality and comp:
        if quality == "凶" and comp in ("命局上佳", "命局中平偏上"):
            findings.append({
                "id": "quality_vs_composite",
                "severity": "矛盾",
                "title": "格局评凶 · 命局推理链却评上佳",
                "modules": ["格局成破", "命局力量推理链"],
                "detail": f"格局品评「凶」，然命局综合推理链评为「{comp}」。二者吉凶相左。",
                "suggestion": "复核推理链权重：格局破而无救者，纵调候得宜亦难称上佳；"
                              "或格局之凶已有救应、特殊吉格补之，则推理链评高有据——须明其所以。",
            })
        elif quality == "吉" and comp in ("命局偏弱", "命局受损"):
            findings.append({
                "id": "quality_vs_composite2",
                "severity": "注意",
                "title": "格局评吉 · 命局推理链却偏弱",
                "modules": ["格局成破", "命局力量推理链"],
                "detail": f"格局品评「吉」，然命局综合推理链评为「{comp}」。",
                "suggestion": "或因刑冲损益、调候失位拖累；格局虽吉而根基受损，宜复核。",
            })

    # ④ 用神 / 忌神 五行重叠
    if yw and jw and yw == jw:
        findings.append({
            "id": "yong_ji_overlap",
            "severity": "矛盾",
            "title": "用神与忌神五行重叠",
            "modules": ["用神喜忌"],
            "detail": f"用神与忌神同取{yw}，自相矛盾。",
            "suggestion": "用神忌神不可同一五行；须重新厘定喜忌，多因身强弱判定有误所致。",
        })

    # ⑤ 格局成破 status vs 命中
    status = ge.get("status", "")
    cheng = ge.get("cheng_hit", []) or []
    po = ge.get("po_hit", []) or []
    if status == "成格" and po:
        findings.append({
            "id": "status_has_po",
            "severity": "提示",
            "title": "判为成格 · 然有破格之象",
            "modules": ["格局成破"],
            "detail": f"格局判「成格」，然检出破格之象：{po[0]}。",
            "suggestion": "成格而有微破者，须看破之轻重、有无救应；若破重，当降为「破而有救」或「破格」论。",
        })
    elif status in ("破格", "破而有救") and not po:
        findings.append({
            "id": "status_no_po",
            "severity": "提示",
            "title": f"判为{status} · 却未列破象",
            "modules": ["格局成破"],
            "detail": f"格局判「{status}」，然未检出具体破格之象。",
            "suggestion": "破格之论须有所据；宜复核破在何处，免致空言其破。",
        })

    # ⑥ 特殊凶格 vs 命局上佳
    matched = sp.get("matched", []) or []
    inaus = [m["name"] for m in matched if not m.get("auspicious")]
    if inaus and comp == "命局上佳":
        findings.append({
            "id": "xiong_pattern_vs_upper",
            "severity": "提示",
            "title": "带凶格 · 命局却评上佳",
            "modules": ["特殊格局", "命局力量推理链"],
            "detail": f"命带凶格（{('、'.join(inaus[:2]))}），然命局综合评「上佳」。",
            "suggestion": "凶格未必全减命局，然评上佳须确认凶格已被化解或无关大局；宜留意其潜在之患。",
        })

    # ⑦ 命局先天 vs 当前运程（命运背驰 — 后天之时）
    cf = chart.get("current_fortune", {}) or {}
    if cf.get("available"):
        cdy = cf.get("current_dayun", {}) or {}
        helpv = cdy.get("help", "")
        if comp in ("命局上佳", "命局中平偏上") and helpv == "助忌":
            findings.append({
                "id": "good_ming_bad_yun",
                "severity": "提示",
                "title": "命局上佳 · 然现行大运助忌",
                "modules": ["命局力量推理链", "大运"],
                "detail": f"先天命局评「{comp}」，然现行{cdy.get('ganzhi','')}大运助起忌神。",
                "suggestion": "命好运背者，纵根基佳亦逢此运受抑、宜守不宜进；待忌运过、用神之运至方大展。先天定高低、后天定起伏，二者须并看。",
            })
        elif comp in ("命局偏弱", "命局受损") and helpv == "扶用":
            findings.append({
                "id": "weak_ming_good_yun",
                "severity": "提示",
                "title": "命局偏弱 · 然现行大运扶用",
                "modules": ["命局力量推理链", "大运"],
                "detail": f"先天命局评「{comp}」，然现行{cdy.get('ganzhi','')}大运扶起用神。",
                "suggestion": "命弱逢扶用之运，乃枯木逢春、此运可借势而起；然根基终弱，运过须防回落，宜趁运积累。先天定高低、后天定起伏，二者须并看。",
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
