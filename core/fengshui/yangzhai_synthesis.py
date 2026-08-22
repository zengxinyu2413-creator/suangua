"""
core/fengshui/yangzhai_synthesis.py
===================================
阳宅三要·宅相力量综合推理链（子模块互助集成层）。

仿八字/玄空 synthesis：阳宅诸子模块（门主局、灶局、东西四纯度、命卦人宅相配、
楼层）原各自成断，本引擎汇于一条可见推理链——以门主局立基，叠加灶局、纯度、
人宅相配（命根·重权）、楼层，每因子标【来源模块·利/害/中·权重】，
合成「宅相综合评定」。命卦匹配为《八宅明镜》之命根，权重最重。
"""
from __future__ import annotations
from typing import Dict, Any, List

_LEVEL_W = {"上吉": 3, "中吉": 2, "小吉": 1, "平": 0, "次凶": -2, "凶": -2, "大凶": -3}
_QUALITY_W = {"大吉": 2, "上吉": 2, "中吉": 1, "中": 0, "平": 0, "次凶": -1, "凶": -2, "大凶": -2}


def synthesize_zhaixiang(result: Dict[str, Any]) -> Dict[str, Any]:
    if not result or not result.get("grade"):
        return {"available": False}

    factors: List[Dict[str, Any]] = []
    score = 0

    # ① 门主局（立基）
    mzj = result.get("menzhu_ju", {}) or {}
    lvl = mzj.get("level", "")
    w = _LEVEL_W.get(lvl, 0)
    score += w
    factors.append({"module": "门主局", "factor": f"{mzj.get('younian','')}·{lvl}",
                    "polarity": "利" if w > 0 else ("害" if w < 0 else "中"), "weight": w,
                    "note": (mzj.get("ming", "") or "")[:30]})

    # ② 灶局
    zaoju = result.get("zao_ju", {}) or {}
    zq = zaoju.get("quality", "")
    w = _QUALITY_W.get(zq, 0)
    score += w
    factors.append({"module": "灶局", "factor": f"灶{zq}（主灶{zaoju.get('zhu_zao_star','')}）",
                    "polarity": "利" if w > 0 else ("害" if w < 0 else "中"), "weight": w,
                    "note": f"门灶{zaoju.get('men_zao_star','')}、灶口{zaoju.get('mouth_star','')}，养命之源"})

    # ③ 东西四纯度
    pur = result.get("purity", {}) or {}
    if pur:
        if pur.get("pure"):
            score += 1
            factors.append({"module": "纯度", "factor": "东西四纯一", "polarity": "利", "weight": 1,
                            "note": "门主灶同属一卦组，气纯不杂，吉力专一"})
        else:
            score -= 1
            factors.append({"module": "纯度", "factor": "东西四驳杂", "polarity": "害", "weight": -1,
                            "note": (pur.get("desc", "") or "")[:30] or "门主灶东西四混杂，气驳力散"})

    # ④ 命卦人宅相配（命根·重权）
    mm = result.get("mingua_match", {}) or {}
    if mm.get("available"):
        mq = mm.get("match_quality", "中")
        if mq == "吉":
            w = 3
        elif mq == "凶":
            w = -4
        else:
            w = -1
        score += w
        factors.append({"module": "人宅相配", "factor": f"{mm.get('match_level','')}（{mm.get('ming_gua','')}命）",
                        "polarity": "利" if w > 0 else ("害" if w < 0 else "中"), "weight": w,
                        "note": f"门{mm.get('men_younian',{}).get('younian','')}·主{mm.get('zhu_younian',{}).get('younian','')}·灶{mm.get('zao_younian',{}).get('younian','')}——《八宅明镜》命根"})

    # ⑤ 楼层
    fl = result.get("floor_guide", {}) or {}
    if fl:
        fq = str(fl.get("quality", fl.get("level", "")))
        if "吉" in fq or "相生" in str(fl.get("desc", "")):
            score += 1
            factors.append({"module": "楼层", "factor": "楼层五行得生", "polarity": "利", "weight": 1,
                            "note": (fl.get("desc", "") or "")[:30]})
        elif "凶" in fq or "相克" in str(fl.get("desc", "")):
            score -= 1
            factors.append({"module": "楼层", "factor": "楼层五行受克", "polarity": "害", "weight": -1,
                            "note": (fl.get("desc", "") or "")[:30]})

    # ⑥ 宅相综合评定
    if score >= 6:
        label, desc = "宅相上吉", "三要俱合、人宅相得，丁财两旺、家道昌隆之上吉宅。"
    elif score >= 3:
        label, desc = "宅相向吉", "格局可成、吉多于凶，居之安泰，趋吉位起居则更显。"
    elif score >= 0:
        label, desc = "宅相平和", "吉凶相参，须调门主灶之失、配主人吉方，方为稳妥。"
    elif score >= -4:
        label, desc = "宅相偏凶", "犯凶游年或人宅不配，主丁财有损，宜亟改门主灶或另择。"
    else:
        label, desc = "宅相大凶", "三要犯凶又人宅相违，损丁破财，《八宅明镜》忌之，宜重立或迁居。"

    seg = []
    for f in factors:
        pol = {"利": "＋", "害": "－", "中": "·"}.get(f["polarity"], "·")
        seg.append(f"〔{f['module']}〕{pol}{f['factor']}")
    chain_text = "　→　".join(seg) + f"　⟹　{label}（综合力{score:+d}）"

    return {
        "available": True,
        "grade": result.get("grade", ""),
        "factors": factors,
        "composite_score": score,
        "composite_label": label,
        "composite_desc": desc,
        "chain_text": chain_text,
    }
