"""
core/ziwei/synthesis.py
=======================
紫微斗数·命格力量综合推理链（子模块互助集成层）。

仿八字 synthesis：紫微诸子模块（命宫主星庙旺、三方四正明暗、格局成破、
煞星交冲、四化引动）原各自成断，本引擎将其汇于一条可见推理链——以命宫主星
立基，叠加三方会照之明暗、格局之成破、煞星之多寡、四化之引动，每因子标明
【来源模块·利/害/中·权重】，合成「命格综合评定」。使分析路径显式。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SHA = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}
_BRIGHT_OK = {"庙", "旺", "得"}
_FALLEN = {"陷", "不"}


def synthesize_mingge(chart: Dict[str, Any]) -> Dict[str, Any]:
    palaces = chart.get("palaces", []) or []
    if not palaces:
        return {"available": False}

    ins = chart.get("insights", {}) or {}
    rating = ins.get("rating", {}) or {}
    patterns = ins.get("patterns", {}) or {}
    sj = (chart.get("sanjiao_analysis", {}) or {}).get("sanjiao", {}) or {}
    bsp = chart.get("birth_sihua", {}) or {}

    ming = next((p for p in palaces if p.get("is_soul")), None)
    if not ming:
        return {"available": False}
    sfsz_idx = set(sj.get("palaces", []) or []) | {ming.get("index")}

    factors: List[Dict[str, Any]] = []
    score = 0

    # ① 命宫主星 + 庙旺（立基）
    ming_majors = ming.get("major_stars", []) or []
    if ming_majors:
        names = []
        bright_n = 0
        for s in ming_majors:
            br = s.get("brightness", "")
            names.append(f"{s.get('name','')}（{br}）" if br else s.get("name", ""))
            if br in _BRIGHT_OK:
                bright_n += 1
            elif br in _FALLEN:
                bright_n -= 1
        if bright_n > 0:
            score += 2
            pol, w = "利", 2
            note = "命宫主星庙旺得地，禀赋厚、根基正"
        elif bright_n < 0:
            score -= 2
            pol, w = "害", -2
            note = "命宫主星落陷失辉，禀赋有亏、须三方补救"
        else:
            pol, w = "中", 0
            note = "命宫主星平和"
        factors.append({"module": "命宫主星", "factor": "、".join(names), "polarity": pol,
                        "weight": w, "note": note})
    else:
        factors.append({"module": "命宫主星", "factor": "命宫无主星", "polarity": "中",
                        "weight": 0, "note": "命无正曜，借对宫主星论之，性情多浮动"})

    # ② 三方四正明暗
    bright = rating.get("bright_in_sfsz", []) or []
    fallen = rating.get("fallen_in_sfsz", []) or []
    if bright:
        score += min(len(bright), 3)
        factors.append({"module": "三方四正", "factor": f"{len(bright)}星庙旺会照", "polarity": "利",
                        "weight": min(len(bright), 3),
                        "note": "庙旺者：" + "、".join(bright[:6]) + "，吉星拱照、助力广"})
    if fallen:
        score -= min(len(fallen), 3)
        factors.append({"module": "三方四正", "factor": f"{len(fallen)}星落陷", "polarity": "害",
                        "weight": -min(len(fallen), 3),
                        "note": "落陷者：" + "、".join(fallen[:5]) + "，其位之事多波折"})

    # ③ 格局成破
    good = patterns.get("good", []) or []
    bad = patterns.get("bad", []) or []
    for g in good[:3]:
        score += 2
        factors.append({"module": "格局成破", "factor": f"成吉格·{g.get('name','')}", "polarity": "利",
                        "weight": 2, "note": (g.get("meaning", "") or "")[:42]})
    for b in bad[:3]:
        score -= 2
        factors.append({"module": "格局成破", "factor": f"带凶格·{b.get('name','')}", "polarity": "害",
                        "weight": -2, "note": (b.get("meaning", "") or "")[:42]})

    # ④ 煞星交冲（命宫三方四正）
    sha_found = []
    for p in palaces:
        if p.get("index") in sfsz_idx:
            for s in (p.get("minor_stars", []) or []) + (p.get("adj_stars", []) or []):
                if s.get("name") in _SHA:
                    sha_found.append(f"{s.get('name')}（{p.get('name','')}）")
    if sha_found:
        pen = min(len(sha_found), 3)
        score -= pen
        factors.append({"module": "煞星", "factor": f"{len(sha_found)}煞入命三方", "polarity": "害",
                        "weight": -pen, "note": "、".join(sha_found[:4]) + "——煞星交冲，主波折、刑伤、阻力"})

    # ⑤ 四化引动（生年四化落命宫三方四正）
    sihua = (bsp.get("sihua", {}) or {}) if bsp.get("available") else {}
    for hua in ("化禄", "化权", "化科"):
        h = sihua.get(hua, {}) or {}
        if h.get("palace_idx") in sfsz_idx:
            score += 1
            factors.append({"module": "四化引动", "factor": f"{hua}·{h.get('star','')}入{h.get('palace','')}",
                            "polarity": "利", "weight": 1,
                            "note": f"生年{hua}照命三方，{('增福禄' if hua=='化禄' else '掌权柄' if hua=='化权' else '增名声')}"})
    hj = sihua.get("化忌", {}) or {}
    if hj.get("palace_idx") in sfsz_idx:
        score -= 1
        factors.append({"module": "四化引动", "factor": f"化忌·{hj.get('star','')}入{hj.get('palace','')}",
                        "polarity": "害", "weight": -1,
                        "note": "生年化忌冲扰命三方，主该宫之事纠缠、损耗"})

    # ⑥ 命格综合评定
    if score >= 5:
        label, desc = "命格上乘", "主星明、格局正、吉化拱照，根基稳固，一生大局向上。"
    elif score >= 2:
        label, desc = "命格中上", "格局可成、吉多于凶，然不无瑕疵，趋吉避忌则显。"
    elif score >= -1:
        label, desc = "命格中平", "明暗成破相参，全凭大限流年扶抑，重在扬长避短。"
    elif score >= -4:
        label, desc = "命格偏弱", "主星陷或煞忌重，一生多费周折，尤须借运补救。"
    else:
        label, desc = "命格受损", "主星陷、凶格成、煞忌交加，根基不固，须大运得力方转。"

    seg = []
    for f in factors:
        pol = {"利": "＋", "害": "－", "中": "·"}.get(f["polarity"], "·")
        seg.append(f"〔{f['module']}〕{pol}{f['factor']}")
    chain_text = "　→　".join(seg) + f"　⟹　{label}（先天综合力{score:+d}）"

    # 后天行运（大限流年并入，单列不改先天命格评定）
    cf = chart.get("current_fortune", {}) or {}
    fortune_note = ""
    if cf.get("available"):
        dx = cf.get("daxian", {}) or {}
        ln = cf.get("liunian", {}) or {}
        chain_text += f"　‖后天‖　〔现行大限〕{dx.get('palace','')}（{('、'.join(dx.get('major_stars', [])[:2]) or '无主星')}）"
        if ln and ln.get("palace"):
            chain_text += f" · {cf.get('current_year','')}年流年{ln.get('palace','')}"
        fortune_note = cf.get("daxian_tone", "")

    return {
        "available": True,
        "ming_branch": ming.get("earthly_branch", ""),
        "rating": rating.get("overall", ""),
        "factors": factors,
        "composite_score": score,
        "composite_label": label,
        "composite_desc": desc,
        "current_fortune_note": fortune_note,
        "chain_text": chain_text,
    }
