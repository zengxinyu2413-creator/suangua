"""
core/date_selection/personalize.py
==================================
择日·八字个性化（吉日按本人八字用神/冲克过滤 — 真个性化）。

原择日只论通用宜忌（建除、黄道、神煞），至多按本命年支冲合微调，未据本人八字
之用神喜忌。然真择吉，须「日扶其用、不犯其冲」：日干支五行属本人用神喜神者吉、
属忌神者减，日支冲本命日支/年支者大忌、六合三合者加。本引擎据此为每一吉日加
「个人契合分」，并重排出「合本命之首选吉日」。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

_GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
           "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
_ZHI_WX = {"寅": "木", "卯": "木", "巳": "火", "午": "火", "辰": "土", "丑": "土",
           "戌": "土", "未": "土", "申": "金", "酉": "金", "子": "水", "亥": "水"}
# 地支六冲
_CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
          "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
# 地支六合
_LIUHE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
          "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
# 三合局
_SANHE = [{"申", "子", "辰"}, {"亥", "卯", "未"}, {"寅", "午", "戌"}, {"巳", "酉", "丑"}]


def _person_profile(birth_year, birth_month, birth_day, birth_hour) -> Optional[Dict[str, Any]]:
    try:
        from core.bazi.chart import build_chart
        from core.bazi.day_master_profiles import analyze_yong_shen
        ch = build_chart(int(birth_year), int(birth_month), int(birth_day),
                         int(birth_hour or 12), 0)
        ys = analyze_yong_shen(ch)
        yong = {ys.get("yong_shen_wx", ""), ys.get("xi_shen_wx", "")}
        ji = {ys.get("ji_shen_wx", ""), ys.get("chou_shen_wx", "")}
        yong.discard("")
        ji.discard("")
        day_zhi = ch.get("day_pillar", {}).get("dizhi", "")
        year_zhi = ch.get("year_pillar", {}).get("dizhi", "")
        return {"yong": yong, "ji": ji, "day_zhi": day_zhi, "year_zhi": year_zhi,
                "yong_str": "、".join(yong), "ji_str": "、".join(ji)}
    except Exception:
        return None


def _sanhe_with(z1, z2) -> bool:
    return any(z1 in s and z2 in s and z1 != z2 for s in _SANHE)


def personalize_days(days: List[Dict[str, Any]],
                     birth_year, birth_month, birth_day, birth_hour=12) -> Dict[str, Any]:
    prof = _person_profile(birth_year, birth_month, birth_day, birth_hour)
    if not prof:
        return {"available": False}

    for d in days:
        gz = d.get("ganzhi", "")
        if len(gz) < 2:
            d["personal_score"] = 0
            continue
        gan, zhi = gz[0], gz[1]
        gwx, zwx = _GAN_WX.get(gan, ""), _ZHI_WX.get(zhi, "")
        ps = 0
        reasons = []

        # 用神/忌神 五行匹配
        if gwx in prof["yong"]:
            ps += 2
            reasons.append(f"日干{gan}({gwx})扶本命用神")
        elif gwx in prof["ji"]:
            ps -= 2
            reasons.append(f"日干{gan}({gwx})助本命忌神")
        if zwx in prof["yong"]:
            ps += 1
            reasons.append(f"日支{zhi}({zwx})益用神")
        elif zwx in prof["ji"]:
            ps -= 1
            reasons.append(f"日支{zhi}({zwx})助忌神")

        # 冲本命（日支为重、年支次之）
        if prof["day_zhi"] and _CHONG.get(zhi) == prof["day_zhi"]:
            ps -= 3
            reasons.append(f"日支{zhi}冲本命日支{prof['day_zhi']}（个人大忌）")
        elif prof["year_zhi"] and _CHONG.get(zhi) == prof["year_zhi"]:
            ps -= 2
            reasons.append(f"日支{zhi}冲本命年支{prof['year_zhi']}")

        # 六合/三合本命
        if prof["day_zhi"] and (_LIUHE.get(zhi) == prof["day_zhi"] or _sanhe_with(zhi, prof["day_zhi"])):
            ps += 2
            reasons.append(f"日支{zhi}合本命日支{prof['day_zhi']}（个人加持）")
        elif prof["year_zhi"] and (_LIUHE.get(zhi) == prof["year_zhi"] or _sanhe_with(zhi, prof["year_zhi"])):
            ps += 1
            reasons.append(f"日支{zhi}合本命年支{prof['year_zhi']}")

        d["personal_score"] = ps
        d["personal_reasons"] = reasons
        d["combined_score"] = d.get("score", 0) + ps

    # 重排：通用吉日中，按 combined_score 选合本命之首选
    ranked = sorted([d for d in days if d.get("score", 0) >= 4],
                    key=lambda x: (-x.get("combined_score", 0), -x.get("score", 0)))
    personal_best = ranked[:3]

    # 个人不宜（通用吉但个人冲克）
    personal_avoid = [d for d in days if d.get("score", 0) >= 4 and d.get("personal_score", 0) <= -3]

    return {
        "available": True,
        "profile": {"yong": prof["yong_str"], "ji": prof["ji_str"],
                    "day_zhi": prof["day_zhi"], "year_zhi": prof["year_zhi"]},
        "personal_best": [{"date": d.get("date"), "ganzhi": d.get("ganzhi"),
                           "base_score": d.get("score"), "personal_score": d.get("personal_score"),
                           "combined_score": d.get("combined_score"),
                           "personal_reasons": d.get("personal_reasons", [])} for d in personal_best],
        "personal_avoid": [{"date": d.get("date"), "ganzhi": d.get("ganzhi"),
                            "personal_reasons": d.get("personal_reasons", [])} for d in personal_avoid],
    }
