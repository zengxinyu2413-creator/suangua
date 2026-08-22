"""
core/qimen/geju_layers.py
=========================
奇门遁甲·格局 × 九宫层级联动断。

格局不可孤论：同一吉格，落旺宫得地则吉力充沛，落门迫/入墓/击刑之宫则吉而受制，
落空亡之宫则吉虚不实；同一凶格，落旺宫则凶力强，落空亡则凶可减，带马星则凶来速。
本模块把 patterns（格局）按方位/值符值使定位到具体宫，取该宫之层级（门迫·入墓·
击刑·空亡·马星·旺衰），二者合参，给「格落某宫」之联动成文断与校正吉凶。

复用 palace_layers 已补之每宫 layers，与排盘同源。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

# 方位 → 宫位序
DIR_TO_POS: Dict[str, int] = {
    "北": 1, "西南": 2, "东": 3, "东南": 4, "中": 5,
    "西北": 6, "西": 7, "东北": 8, "南": 9,
}

# severity → 吉凶基分
_SEV_SCORE: Dict[str, int] = {
    "auspicious_great": 3, "auspicious": 2, "mixed": 0,
    "inauspicious": -2, "inauspicious_great": -3, "大凶": -3,
}
_SEV_JI = {"auspicious_great", "auspicious"}
_SEV_XIONG = {"inauspicious", "inauspicious_great", "大凶"}


def _find_palace(layout: Dict[str, Any], pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """据格局之 direction / 值符值使 定位其所落之宫。"""
    palaces = layout.get("palaces", [])
    # 1) 有方位
    d = pattern.get("direction", "")
    if d in DIR_TO_POS:
        pos = DIR_TO_POS[d]
        return next((p for p in palaces if p.get("position") == pos), None)
    # 2) 值符/值使类全局格（飞鸟跌穴=值符值使同宫等）
    name = pattern.get("name", "")
    if any(k in name for k in ("飞鸟跌穴", "值符", "值使", "伏吟", "返首")):
        zf = next((p for p in palaces if p.get("is_zhifu")), None)
        if zf:
            return zf
    return None


def link_patterns_to_layers(layout: Dict[str, Any]) -> Dict[str, Any]:
    """把每个可定位之格局与其所落宫之层级合参，产出联动断。"""
    palaces = layout.get("palaces", [])
    linked: List[Dict[str, Any]] = []

    for pat in layout.get("patterns", []):
        sev = pat.get("severity", "")
        base = _SEV_SCORE.get(sev, 0)
        is_ji = sev in _SEV_JI
        is_xiong = sev in _SEV_XIONG

        palace = _find_palace(layout, pat)
        if not palace:
            linked.append({
                "name": pat.get("name", ""), "severity": sev,
                "palace": "", "located": False,
                "joint": pat.get("desc", ""),
                "adjusted": "吉格" if is_ji else ("凶格" if is_xiong else "中性格"),
            })
            continue

        layers = palace.get("layers", {}) or {}
        flags = layers.get("flags", [])
        flag_types = {f["type"] for f in flags}
        pname = palace.get("palace_name", "")

        has_kong = "空亡" in flag_types
        has_ma = "马星" in flag_types
        block = flag_types & {"门迫", "入墓", "击刑"}

        # ── 层级校正 ──
        adj = base + layers.get("layer_score_adj", 0)

        # ── 联动断 ──
        if is_ji:
            if block:
                verdict = f"吉格受制——{pat['name']}落{pname}，然此宫{'、'.join(block)}，吉格被制，吉而打折、成中带阻、迟滞难以尽显。"
                tag = "吉格受制"
            elif has_kong:
                verdict = f"吉格逢空——{pat['name']}落{pname}旬空，吉应虚而不实，待填实/冲空之时方验，眼下不可全恃。"
                tag = "吉格逢空"
            elif has_ma:
                verdict = f"吉格得马——{pat['name']}落{pname}带驿马，吉力充沛且应速，宜乘势速动、远图大利。"
                tag = "吉格得马"
            else:
                verdict = f"吉格得地——{pat['name']}落{pname}，宫吉无破，吉力充分发挥，所主之利应验有力。"
                tag = "吉格得地"
        elif is_xiong:
            if has_kong:
                verdict = f"凶格逢空——{pat['name']}落{pname}旬空，凶气泄于空，凶可减缓，灾轻而易解。"
                tag = "凶格逢空"
            elif has_ma:
                verdict = f"凶格带马——{pat['name']}落{pname}带驿马，凶来迅速、动则生灾，宜静避其锋。"
                tag = "凶格带马"
            elif block:
                verdict = f"凶格叠制——{pat['name']}落{pname}，又逢{'、'.join(block)}，凶上加凶，此宫此事最忌触犯。"
                tag = "凶格叠制"
            else:
                verdict = f"凶格力强——{pat['name']}落{pname}，宫无解救，凶应明显，于此方此事宜避。"
                tag = "凶格力强"
        else:
            verdict = f"{pat['name']}落{pname}（中性格）：{pat.get('desc','')}　宜参此宫层级（{'、'.join(flag_types) or '无特态'}）权衡。"
            tag = "中性格"

        linked.append({
            "name": pat.get("name", ""), "severity": sev, "palace": pname,
            "located": True, "flags": sorted(flag_types),
            "adjusted_score": adj, "tag": tag, "joint": verdict,
        })

    ji = [l for l in linked if l.get("tag", "").startswith("吉")]
    xiong = [l for l in linked if l.get("tag", "").startswith("凶")]
    summary = (
        f"全局共析格局 {len(linked)} 例，其中吉格 {len(ji)}、凶格 {len(xiong)}。"
        + ("　吉格之中，" + "、".join(f"{l['name']}({l['tag'][2:]})" for l in ji[:4]) + "。" if ji else "")
        + ("　凶格之中，" + "、".join(f"{l['name']}({l['tag'][2:]})" for l in xiong[:4]) + "。" if xiong else "")
        + "格落吉宫则力全、落破宫则受制、逢空则虚、带马则速——此奇门「格不离宫」之要。"
    )

    layout["geju_layers"] = {"linked": linked, "summary": summary}
    return layout
