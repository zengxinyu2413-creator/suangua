"""
core/qimen/yongshen.py
======================
奇门遁甲·用神宫自动定位。

奇门取用，先定「用神之宫」，方能就宫论层级吉凶：
  · 值符宫 —— 旬首符头（九星之值符）所临，为一局之主帅、贵人、事之主导。
  · 值使宫 —— 值使门所临，为用事之门、行动之枢。
  · 日干宫 —— 日干所落，为求测人（己/主）。
  · 时干宫 —— 时干所落，为所占之事（或对方/客）。
  · 年命宫 —— 求测人本命年支所纳之宫，为其人身命之根（需生年）。
  · 用事神 —— 随所占之事另取（求财生门、词讼日时干比较…），接 purpose_analysis。

日时干以 lunar_python 取真太阳前之干支；甲为旬首隐遁，落宫从值符。
就各用神宫取 palace_layers 已补之层级，合参定吉凶，并论日干（己）⇄时干（事/彼）
之生克——我克彼则事由我成、彼克我则事难、相生相合则谐。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.qimen.palace_layers import GAN_WX, GONG_DIZHI, _wx_relation

_GAN_ORDER = "甲乙丙丁戊己庚辛壬癸"


def _day_hour_gan(dt: datetime) -> Dict[str, str]:
    """取日干、时干（及年支供年命用）。"""
    try:
        from lunar_python import Solar
        ec = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, 0, 0)\
            .getLunar().getEightChar()
        return {"day_gan": ec.getDayGan(), "hour_gan": ec.getTimeGan()}
    except Exception:
        return {"day_gan": "", "hour_gan": ""}


def _nianming_zhi(birth_year: int) -> str:
    """生年 → 年支（本命年支）。"""
    try:
        from lunar_python import Solar
        ec = Solar.fromYmdHms(birth_year, 6, 1, 12, 0, 0).getLunar().getEightChar()
        return ec.getYearZhi()
    except Exception:
        return ""


def _locate_stem(layout: Dict[str, Any], stem: str) -> Dict[str, Optional[str]]:
    """定位天干在天盘/地盘所落之宫。甲则归值符宫。"""
    palaces = layout.get("palaces", [])
    if stem == "甲":   # 甲遁旬首，从值符
        zf = next((p for p in palaces if p.get("is_zhifu")), None)
        n = zf.get("palace_name") if zf else None
        return {"tian": n, "di": n, "via": "甲遁旬首·从值符"}
    tian = next((p["palace_name"] for p in palaces if p.get("tian_pan") == stem), None)
    di = next((p["palace_name"] for p in palaces
               if (p.get("di_pan") or p.get("stem")) == stem), None)
    return {"tian": tian, "di": di, "via": ""}


def _palace_by_name(layout: Dict[str, Any], name: Optional[str]) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    return next((p for p in layout.get("palaces", []) if p.get("palace_name") == name), None)


def _palace_layer_brief(layout: Dict[str, Any], name: Optional[str]) -> str:
    """某宫之层级吉凶一句话。"""
    p = _palace_by_name(layout, name)
    if not p:
        return "不入九宫"
    layers = p.get("layers", {}) or {}
    flags = [f["type"] for f in layers.get("flags", [])]
    q = p.get("quality", "")
    return f"{name}（{q}{'·' + '·'.join(flags) if flags else ''}）"


def analyze_yongshen_palaces(layout: Dict[str, Any],
                             birth_year: Optional[int] = None) -> Dict[str, Any]:
    """自动定位并合参各用神宫。"""
    dt_str = layout.get("datetime", "")
    try:
        dt = datetime.fromisoformat(dt_str) if dt_str else datetime.now()
    except Exception:
        dt = datetime.now()
    gans = _day_hour_gan(dt)
    day_gan, hour_gan = gans["day_gan"], gans["hour_gan"]

    palaces = layout.get("palaces", [])
    zhifu = next((p for p in palaces if p.get("is_zhifu")), None)
    zhishi = next((p for p in palaces if p.get("is_zhishi")), None)

    items: List[Dict[str, Any]] = []

    # 值符宫 / 值使宫
    if zhifu:
        items.append({
            "role": "值符宫", "symbol": zhifu.get("star", ""),
            "palace": zhifu.get("palace_name", ""),
            "meaning": "一局主帅·贵人·事之主导",
            "layer": _palace_layer_brief(layout, zhifu.get("palace_name")),
        })
    if zhishi:
        items.append({
            "role": "值使宫", "symbol": zhishi.get("door", ""),
            "palace": zhishi.get("palace_name", ""),
            "meaning": "用事之门·行动之枢",
            "layer": _palace_layer_brief(layout, zhishi.get("palace_name")),
        })

    # 日干宫（己/主）
    rg_loc = _locate_stem(layout, day_gan) if day_gan else {}
    rg_palace = rg_loc.get("di") or rg_loc.get("tian")
    if rg_palace:
        items.append({
            "role": "日干宫", "symbol": day_gan,
            "palace": rg_palace, "meaning": "求测人（己/主）" + (f"·{rg_loc.get('via')}" if rg_loc.get("via") else ""),
            "tian_palace": rg_loc.get("tian"), "di_palace": rg_loc.get("di"),
            "layer": _palace_layer_brief(layout, rg_palace),
        })

    # 时干宫（事/彼/客）
    sg_loc = _locate_stem(layout, hour_gan) if hour_gan else {}
    sg_palace = sg_loc.get("di") or sg_loc.get("tian")
    if sg_palace:
        items.append({
            "role": "时干宫", "symbol": hour_gan,
            "palace": sg_palace, "meaning": "所占之事（事/彼/客）" + (f"·{sg_loc.get('via')}" if sg_loc.get("via") else ""),
            "tian_palace": sg_loc.get("tian"), "di_palace": sg_loc.get("di"),
            "layer": _palace_layer_brief(layout, sg_palace),
        })

    # 年命宫（需生年）
    nm_zhi = ""
    if birth_year:
        nm_zhi = _nianming_zhi(birth_year)
        if nm_zhi:
            nm_palace = next((p["palace_name"] for p in palaces
                              if nm_zhi in GONG_DIZHI.get(p.get("palace_name", ""), [])), None)
            items.append({
                "role": "年命宫", "symbol": nm_zhi,
                "palace": nm_palace or "不入九宫",
                "meaning": f"求测人本命（{nm_zhi}年）身命之根",
                "layer": _palace_layer_brief(layout, nm_palace) if nm_palace else "不入九宫",
            })

    # ── 日干 ⇄ 时干（我 vs 事/彼）生克 ──
    rg_wx = GAN_WX.get(day_gan, "")
    sg_wx = GAN_WX.get(hour_gan, "")
    rel = _wx_relation(rg_wx, sg_wx)
    REL_NOTE = {
        "我克": f"日干{day_gan}({rg_wx})克时干{hour_gan}({sg_wx})——我克彼，事由我主、可得可成，宜主动进取。",
        "克我": f"时干{hour_gan}({sg_wx})克日干{day_gan}({rg_wx})——彼克我，事受制于人、求之费力，宜待时或借力。",
        "我生": f"日干{day_gan}生时干{hour_gan}——我生彼，我为之付出耗力，利人多于利己。",
        "生我": f"时干{hour_gan}生日干{day_gan}——彼生我，事来助我、有人扶持，得益顺遂。",
        "比和": f"日干时干同气({rg_wx})——我彼比和，事与我相合、和顺易谐。",
    }
    rg_sg_rel = REL_NOTE.get(rel, "")

    return {
        "success": True,
        "day_gan": day_gan, "hour_gan": hour_gan, "nianming_zhi": nm_zhi,
        "items": items,
        "rg_sg_relation": {"relation": rel, "desc": rg_sg_rel},
        "note": "用神既定，须就其宫之层级（旺衰·门迫·入墓·击刑·空亡·马星）论吉凶；"
                "用神宫旺而无破则所主有力，逢空入墓击刑则其事虚滞难成。",
    }
