"""
core/qimen/synthesis.py
=======================
奇门遁甲·用神力量综合推理链（子模块互助集成层）。

仿八字/紫微 synthesis：奇门诸子模块（用神落宫吉凶、星门神三盘、干仪关系、
门宫生克旺衰、值符值使关系、格局）原各自成断，本引擎汇于一条可见推理链——
以用神落宫立基，叠加星门神之吉凶、干仪之利主利客、门宫生克之旺衰、值符值使
之生克、格局之成破，每因子标【来源模块·利/害/中·权重】，合成「用神力量评定」。
"""
from __future__ import annotations
from typing import Dict, Any, List

# 八门五行
_DOOR_WX = {
    "休门": "水", "生门": "土", "伤门": "木", "杜门": "木",
    "景门": "火", "死门": "土", "惊门": "金", "开门": "金",
}
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}


def _men_wangshuai(door_wx, gong_wx):
    """门五行于宫五行之旺衰。返回 (label, polarity, weight)。"""
    if not door_wx or not gong_wx:
        return "平", "中", 0
    if door_wx == gong_wx:
        return "比和得地·旺", "利", 1
    if _SHENG.get(gong_wx) == door_wx:        # 宫生门
        return "宫生门·相", "利", 1
    if _SHENG.get(door_wx) == gong_wx:        # 门生宫（泄）
        return "门泄于宫·休", "害", -1
    if _KE.get(gong_wx) == door_wx:           # 宫克门
        return "宫克门·囚", "害", -1
    if _KE.get(door_wx) == gong_wx:           # 门克宫
        return "门克宫·有力", "中", 0
    return "平", "中", 0


def _nature_pol(nature):
    if not nature:
        return "中", 0
    if "大吉" in nature:
        return "利", 2
    if "吉" in nature:
        return "利", 1
    if "大凶" in nature:
        return "害", -2
    if "凶" in nature:
        return "害", -1
    return "中", 0


def synthesize_yongshen_force(chart: Dict[str, Any]) -> Dict[str, Any]:
    palaces = chart.get("palaces", []) or []
    ys = chart.get("yong_shen", {}) or {}
    if not palaces or not ys:
        return {"available": False}

    yp = next((p for p in palaces if p.get("palace_name") == ys.get("palace")), None)
    if not yp:
        return {"available": False}

    factors: List[Dict[str, Any]] = []
    score = 0

    door = yp.get("door", "")
    star = yp.get("star", "")
    deity = yp.get("deity", "")
    gong_wx = yp.get("gong_wx", "")

    # ① 用神门落宫（立基）
    factors.append({
        "module": "用神落宫", "factor": f"{ys.get('topic','')}用{door}落{ys.get('palace','')}",
        "polarity": "中", "weight": 0,
        "note": f"宫位本评「{yp.get('quality','平')}」（score {yp.get('score','?')}），用神之根基在此",
    })

    # ② 用神门旺衰（门宫生克）
    label, pol, w = _men_wangshuai(_DOOR_WX.get(door, ""), gong_wx)
    score += w
    factors.append({
        "module": "门宫旺衰", "factor": f"{door}（{_DOOR_WX.get(door,'')}）于{gong_wx}宫·{label}",
        "polarity": pol, "weight": w,
        "note": "门得宫生比和则用神有力，受宫克或泄则用神乏力",
    })

    # ③ 星之吉凶
    pol, w = _nature_pol(yp.get("star_nature", ""))
    score += w
    factors.append({"module": "九星", "factor": f"{star}（{yp.get('star_nature','')}）",
                    "polarity": pol, "weight": w, "note": "用神宫所临之九星，主事之吉凶底色"})

    # ④ 神之吉凶
    deity_nat = yp.get("deity_nature", "")
    pol, w = _nature_pol(deity_nat)
    score += w
    factors.append({"module": "八神", "factor": f"{deity}（{deity_nat or '中性'}）",
                    "polarity": pol, "weight": w, "note": "用神宫所临之八神，主辅佐之力与隐显"})

    # ⑤ 干仪关系（利主利客 / 迫墓击）
    sd_tag = yp.get("sd_tag", "")
    sd_rel = yp.get("sd_rel", "")
    if sd_tag or sd_rel:
        if "迫" in sd_rel or "墓" in sd_rel or "击" in sd_rel:
            pol, w = "害", -1
        elif "利主" in sd_tag:
            pol, w = "利", 1
        elif "利客" in sd_tag:
            pol, w = "中", 0
        else:
            pol, w = "中", 0
        score += w
        factors.append({"module": "干仪关系", "factor": f"{sd_tag or '干仪'}",
                        "polarity": pol, "weight": w, "note": (sd_rel or "")[:48]})

    # ⑥ 值符值使关系
    zf = chart.get("zhifu_analysis", {}) or {}
    rel = zf.get("relationship", {}) or {}
    if rel.get("name"):
        lvl = rel.get("level", "")
        if "吉" in lvl:
            pol, w = "利", 1
        elif "凶" in lvl:
            pol, w = "害", -1
        else:
            pol, w = "中", 0
        score += w
        factors.append({"module": "值符值使", "factor": f"{rel['name']}（{lvl}）",
                        "polarity": pol, "weight": w, "note": (rel.get("detail", "") or "")[:48]})

    # ⑦ 格局（落于用神宫者）
    for pat in chart.get("patterns", []) or []:
        if pat.get("direction") and pat["direction"] == ys.get("palace"):
            if pat.get("severity") == "auspicious":
                score += 1
                factors.append({"module": "格局", "factor": f"吉格·{pat.get('name','')}",
                                "polarity": "利", "weight": 1, "note": (pat.get("desc", "") or "")[:40]})
            elif pat.get("severity") == "inauspicious":
                score -= 1
                factors.append({"module": "格局", "factor": f"凶格·{pat.get('name','')}",
                                "polarity": "害", "weight": -1, "note": (pat.get("desc", "") or "")[:40]})

    # ⑧ 用神力量评定
    if score >= 4:
        label2, desc = "用神大有力", "用神门旺、星神俱吉、关系顺生，所问气数极顺，事多速成。"
    elif score >= 2:
        label2, desc = "用神有力", "用神得地、吉多于凶，所问可成，宜把握吉方吉时。"
    elif score >= -1:
        label2, desc = "用神中平", "用神力量参半、吉凶互见，须趋避格局、择吉而动方成。"
    elif score >= -3:
        label2, desc = "用神乏力", "用神休囚或逢凶神凶门，所问阻力较重，宜缓图改方。"
    else:
        label2, desc = "用神受制", "用神受克入墓、凶格交加，所问难成，宜另谋他途。"

    seg = []
    for f in factors:
        pol = {"利": "＋", "害": "－", "中": "·"}.get(f["polarity"], "·")
        seg.append(f"〔{f['module']}〕{pol}{f['factor']}")
    chain_text = "　→　".join(seg) + f"　⟹　{label2}（综合力{score:+d}）"

    return {
        "available": True,
        "topic": ys.get("topic", ""),
        "yongshen_palace": ys.get("palace", ""),
        "factors": factors,
        "composite_score": score,
        "composite_label": label2,
        "composite_desc": desc,
        "chain_text": chain_text,
    }
