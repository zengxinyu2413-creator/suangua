"""
core/fengshui/house_report.py
=============================
风水·统一宅报告（理气 × 形法 合断同一栋房）。

原玄空（理气·飞星旺衰）与阳宅三要（形法·门主灶）各自成断、互不相干。然真实
堪舆一栋房，须二者合参：玄空定各方旺衰，阳宅定门主灶所在——门主灶若落玄空当运
旺方则理气形法兼得，落衰方则虽形法吉而理气衰、须权衡。本引擎交叉门主灶 × 玄空
旺衰飞星，产出「理气形法兼断」之统一宅报告。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.fengshui.xuankong import calculate_xuankong_chart as _xuankong
from core.fengshui.yangzhai_sanyao import synthesize_full_judgment

# 方位 → 后天八卦宫数
_DIR_GONG = {"北": 1, "西南": 2, "东": 3, "东南": 4, "中": 5,
             "西北": 6, "西": 7, "东北": 8, "南": 9}
_GUA_DIR = {"坎": "北", "坤": "西南", "震": "东", "巽": "东南",
            "乾": "西北", "兑": "西", "艮": "东北", "离": "南"}


def _liqi_at(xk: Dict[str, Any], direction: str) -> Dict[str, Any]:
    """玄空理气在某方位之旺衰飞星。"""
    lt = xk.get("luantou_summary", {}) or {}
    wang = lt.get("wang_directions", []) or []
    shuai = lt.get("shuai_directions", []) or []
    pj = xk.get("palace_judgments", {}) or {}
    gong = _DIR_GONG.get(direction)
    pjd = pj.get(str(gong), {}) if gong else {}
    if direction in wang:
        liqi = "旺"
    elif direction in shuai:
        liqi = "衰"
    else:
        liqi = "平"
    return {
        "direction": direction,
        "liqi": liqi,
        "star_nature": pjd.get("nature", ""),
        "short": pjd.get("short", ""),
    }


def _combine(liqi: str, xing_jx: str) -> Dict[str, str]:
    """理气旺衰 × 形法吉凶 → 兼断。"""
    lq_good = liqi == "旺"
    lq_bad = liqi == "衰"
    xf_good = xing_jx == "吉"
    xf_bad = xing_jx == "凶"
    if lq_good and xf_good:
        return {"level": "理气形法兼吉", "q": "吉", "note": "当运旺方又得吉游年，理气形法两全，此位最宜重用"}
    if lq_bad and xf_bad:
        return {"level": "理气形法皆凶", "q": "凶", "note": "衰死之方又落凶游年，二者皆背，此位大忌、宜避宜化"}
    if lq_good and xf_bad:
        return {"level": "理气旺·形法凶", "q": "中", "note": "虽居当运旺方，然游年不利；旺气可助、然门主灶之凶须调，宜趋旺而避其游年凶"}
    if lq_bad and xf_good:
        return {"level": "形法吉·理气衰", "q": "中", "note": "游年虽吉，然居衰死之方；形法之吉打折，宜俟交运或以峦头催之"}
    if xf_good:
        return {"level": "形法吉·理气平", "q": "吉", "note": "游年得吉、理气平和，可用"}
    if xf_bad:
        return {"level": "形法凶·理气平", "q": "凶", "note": "游年不利，宜调此位门主灶"}
    return {"level": "理气形法俱平", "q": "中", "note": "旺衰游年俱平，无功无过"}


def build_unified_house_report(sitting_mountain: str, year: int,
                               men: str, zhu: str, zao: str,
                               zao_facing: Optional[str] = None,
                               birth_year: Optional[int] = None,
                               gender: Optional[str] = None) -> Dict[str, Any]:
    # 1) 理气：玄空飞星
    try:
        xk = _xuankong(year, sitting_mountain=sitting_mountain or "子")
        # 富集峦头旺衰方（与 /xuankong 端点一致）
        try:
            from core.fengshui.xuankong_luantou import enrich_xuankong_luantou
            enrich_xuankong_luantou(xk)
        except Exception as _e1:
            from core.log import log_failure; log_failure("fengshui", "装配(自动补充日志)", _e1)
    except Exception as e:
        return {"available": False, "error": f"玄空排盘失败：{e}"}

    # 2) 形法：阳宅三要（含命卦）
    yz = synthesize_full_judgment(men=men, zhu=zhu, zao=zao, zao_facing=zao_facing)
    if not yz.get("success"):
        return {"available": False, "error": yz.get("error", "阳宅三要参数有误")}
    mm = None
    if birth_year:
        try:
            from core.fengshui.yangzhai_mingua import analyze_mingua_match
            mm = analyze_mingua_match(yz.get("men", {}), yz.get("zhu", {}), yz.get("zao", {}),
                                      birth_year, gender)
        except Exception:
            mm = None

    # 3) 交叉：门主灶 × 玄空旺衰飞星
    relations = yz.get("relations", {}) or {}
    items = []
    role_map = [("门", yz.get("men", {}), relations.get("men_zhu", {})),
                ("主", yz.get("zhu", {}), relations.get("men_zhu", {})),
                ("灶", yz.get("zao", {}), relations.get("zhu_zao", {}))]
    # 形法游年：门以门主局、主灶以各自关系；此处统一取该位之命卦游年（若有主人）或门主灶局吉凶
    mm_map = {}
    if mm and mm.get("available"):
        mm_map = {"门": mm.get("men_younian", {}), "主": mm.get("zhu_younian", {}), "灶": mm.get("zao_younian", {})}

    cross_q = []
    for role, node, _rel in role_map:
        direction = node.get("direction") or _GUA_DIR.get(node.get("gua", ""), "")
        liqi = _liqi_at(xk, direction)
        # 形法吉凶：优先用命卦游年，否则用门主灶内格
        if role in mm_map and mm_map[role]:
            xf = mm_map[role].get("ji_xiong", "平")
            xf_label = mm_map[role].get("younian", "")
        else:
            # 退而用门主灶局等第
            lvl = (yz.get("menzhu_ju", {}) or {}).get("level", "") if role in ("门", "主") else (yz.get("zao_ju", {}) or {}).get("quality", "")
            xf = "吉" if any(k in lvl for k in ("上吉", "中吉", "大吉")) else ("凶" if "凶" in lvl else "平")
            xf_label = lvl
        comb = _combine(liqi["liqi"], xf)
        cross_q.append(comb["q"])
        items.append({
            "role": role, "gua": node.get("gua", ""), "direction": direction,
            "liqi": liqi["liqi"], "star_nature": liqi["star_nature"], "liqi_short": liqi["short"],
            "xingfa": xf, "xingfa_label": xf_label,
            "combine": comb["level"], "combine_q": comb["q"], "note": comb["note"],
        })

    # 4) 统一总评
    nj = cross_q.count("吉")
    nx = cross_q.count("凶")
    if nj >= 2 and nx == 0:
        uni_q, uni = "吉", "理气形法多兼吉，此宅理气得运、门主灶又合，宜居宜久。"
    elif nx >= 2:
        uni_q, uni = "凶", "理气形法多相背，旺衰与游年俱不利，宜大调门主灶或择运另立。"
    elif nx >= 1 and nj >= 1:
        uni_q, uni = "中", "理气形法吉凶互见，得失参半，须趋兼吉之位、调相背之处。"
    else:
        uni_q, uni = "中", "理气形法俱平，无大利亦无大害，宜以峦头化解微调求进。"

    return {
        "available": True,
        "house_type": yz.get("house_type", ""),
        "sitting_mountain": xk.get("sitting_mountain", sitting_mountain),
        "facing_mountain": xk.get("facing_mountain", ""),
        "yun": xk.get("yun", {}),
        # 理气摘要
        "liqi_verdict": xk.get("verdict", ""),
        "liqi_level": xk.get("verdict_level", ""),
        "wang_directions": (xk.get("luantou_summary", {}) or {}).get("wang_directions", []),
        "shuai_directions": (xk.get("luantou_summary", {}) or {}).get("shuai_directions", []),
        # 形法摘要
        "xingfa_grade": yz.get("grade", ""),
        "menzhu_ju": (yz.get("menzhu_ju", {}) or {}).get("ming", ""),
        "mingua_match": mm if (mm and mm.get("available")) else None,
        # 交叉兼断
        "cross_items": items,
        "unified_quality": uni_q,
        "unified_verdict": uni,
        "headline": f"{yz.get('house_type','')}·理气[{xk.get('verdict','')}]×形法[{yz.get('grade','')}]",
    }
