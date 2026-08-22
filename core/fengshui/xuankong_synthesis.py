"""
core/fengshui/xuankong_synthesis.py
===================================
玄空飞星·宅运力量综合推理链（子模块互助集成层）。

仿八字/紫微 synthesis：玄空诸子模块（山向格局、特殊吉凶格、城门、峦头旺衰、
反伏吟）原各自成断，本引擎汇于一条可见推理链——以山向格局立基，叠加特殊格局
之救应、城门之催财、峦头之配合，每因子标【来源模块·利/害/中·权重】，
合成「宅运综合评定」。尤重「上山下水逢三般卦反吉」之类救应关系。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SAVE_PATTERNS = ("三般卦", "连珠", "父母")   # 能救上山下水之格


def synthesize_zhaiyun(chart: Dict[str, Any]) -> Dict[str, Any]:
    if not chart or not chart.get("verdict"):
        return {"available": False}

    factors: List[Dict[str, Any]] = []
    score = 0

    verdict = chart.get("verdict", "")
    ws = chart.get("wangshan")
    wx = chart.get("wangxiang")
    ss = chart.get("shangshan")
    xs = chart.get("xiashui")

    # ① 山向格局（立基）
    if ws and wx:
        score += 3
        factors.append({"module": "山向格局", "factor": "旺山旺向", "polarity": "利", "weight": 3,
                        "note": "山星到坐、向星到向，丁财两旺之上吉局"})
    elif ss and xs:
        score -= 3
        factors.append({"module": "山向格局", "factor": "上山下水", "polarity": "害", "weight": -3,
                        "note": "山星到向、向星到坐，错位之局，主损丁破财（然逢三般卦/合十可救）"})
    elif wx:
        score += 1
        factors.append({"module": "山向格局", "factor": "双星到向", "polarity": "利", "weight": 1,
                        "note": "向星得令到向，旺财而丁稍逊，宜向方见水"})
    elif ws:
        score += 1
        factors.append({"module": "山向格局", "factor": "双星到坐", "polarity": "利", "weight": 1,
                        "note": "山星得令到坐，旺丁而财稍逊，宜坐方见山"})
    else:
        factors.append({"module": "山向格局", "factor": verdict, "polarity": "中", "weight": 0,
                        "note": "山向格局平常，须以峦头理气补之"})

    # ② 特殊吉格（含救应）
    sps = chart.get("special_patterns", []) or []
    saved = False
    for s in sps:
        lvl = s.get("level", "")
        if lvl.startswith("auspicious"):
            nm = s.get("name", "")
            w = 2 if "great" in lvl else 1
            score += w
            is_save = any(k in nm for k in _SAVE_PATTERNS)
            if is_save and (ss and xs):
                saved = True
            factors.append({"module": "特殊格局", "factor": f"吉格·{nm}", "polarity": "利", "weight": w,
                            "note": (s.get("desc", "") or "")[:40] + ("（救上山下水）" if is_save and ss and xs else "")})
    if saved:
        score += 2
        factors.append({"module": "格局救应", "factor": "三般卦救上山下水", "polarity": "利", "weight": 2,
                        "note": "上山下水本凶，得三般卦/连珠一气贯通，反主旺丁财，凶中藏吉"})

    # ③ 特殊凶象
    for s in sps:
        lvl = s.get("level", "")
        if lvl.startswith("inauspicious"):
            nm = s.get("name", "")
            w = -2 if "great" in lvl else -1
            score += w
            factors.append({"module": "特殊格局", "factor": f"凶象·{nm}", "polarity": "害", "weight": w,
                            "note": (s.get("desc", "") or "")[:40]})

    # ④ 反伏吟
    ff = chart.get("fan_fu_yin", {}) or {}
    if ff.get("has_fan_fu_yin"):
        score -= 2
        pats = ff.get("patterns", []) or []
        factors.append({"module": "反伏吟", "factor": "犯反吟伏吟", "polarity": "害", "weight": -2,
                        "note": "盘见反吟伏吟，主反复哭泣、动荡不安" + (f"（{len(pats)}处）" if pats else "")})

    # ⑤ 城门诀
    cm = chart.get("chengmen", {}) or {}
    if cm.get("desc"):
        score += 1
        factors.append({"module": "城门", "factor": "城门可用", "polarity": "利", "weight": 1,
                        "note": (cm.get("desc", "") or "")[:40]})

    # ⑥ 峦头旺衰配合
    lt = chart.get("luantou_summary", {}) or {}
    nw = len(lt.get("wang_directions", []) or [])
    nsh = len(lt.get("shuai_directions", []) or [])
    if nw or nsh:
        if nw > nsh:
            score += 1
            factors.append({"module": "峦头旺衰", "factor": f"旺方{nw}>衰方{nsh}", "polarity": "利", "weight": 1,
                            "note": "当运旺方居多，得地利之助，宜顺势布局催吉"})
        elif nsh > nw:
            score -= 1
            factors.append({"module": "峦头旺衰", "factor": f"衰方{nsh}>旺方{nw}", "polarity": "害", "weight": -1,
                            "note": "衰死方居多，地气偏弱，须谨守化解"})

    # ⑦ 宅运综合评定
    if score >= 5:
        label, desc = "宅运极旺", "山向得令、吉格拱照，丁财两旺、根基稳固，乃难得之上吉宅。"
    elif score >= 2:
        label, desc = "宅运向上", "格局可成、吉多于凶，顺旺方布局、催吉避煞则家道兴隆。"
    elif score >= -1:
        label, desc = "宅运平平", "吉凶相参、明暗互见，全凭峦头配合与化解，重在趋旺避衰。"
    elif score >= -4:
        label, desc = "宅运偏弱", "山向失令或凶象较重，丁财易损，须以城门、化解、峦头力补。"
    else:
        label, desc = "宅运受损", "上山下水又无救、凶象交加，根基不固，宜大改格局或择吉另立。"

    seg = []
    for f in factors:
        pol = {"利": "＋", "害": "－", "中": "·"}.get(f["polarity"], "·")
        seg.append(f"〔{f['module']}〕{pol}{f['factor']}")
    chain_text = "　→　".join(seg) + f"　⟹　{label}（综合力{score:+d}）"

    return {
        "available": True,
        "verdict": verdict,
        "factors": factors,
        "composite_score": score,
        "composite_label": label,
        "composite_desc": desc,
        "chain_text": chain_text,
    }
