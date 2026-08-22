"""
core/bazi/special_patterns.py
=============================
B-2: 八字特殊格局深度识别。

在 analyzer.detect_pattern 的基础上识别 10 个核心特殊/复合格局：
  1. 日禄归时格    — 日干禄在时支
  2. 官印相生     — 财→官→印→身的良性流通
  3. 食神制杀     — 食神制服七杀
  4. 伤官见官     — 凶格
  5. 财官印齐全    — 三全为贵
  6. 羊刃驾杀     — 七杀有羊刃制为吉
  7. 杂气月令     — 辰戌丑未月，财官印藏库
  8. 拱禄拱贵     — 邻支夹禄/夹贵人
  9. 天乙独贵     — 命带天乙贵人无破
 10. 魁罡格      — 庚辰、庚戌、壬辰、戊戌
"""
from __future__ import annotations
from typing import Any, Dict, List

from core.constants import TIANGAN, DIZHI

# ─────────────────────────────────────────────────────────────
# 数据表
# ─────────────────────────────────────────────────────────────

# 天干五行
TG_WX = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 十干禄位（日干 → 禄地支）
LUWEI = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}

# 阳干羊刃（阳干 → 羊刃地支：禄前一位）
YANGREN = {
    "甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子",
    # 阴干的羊刃就是禄位（不被使用，命理界多只论阳干羊刃）
}

# 天乙贵人（日干 → 两个贵人地支）
# 直接从 core/constants.SHENSHA 引用，避免数据漂移
from core.constants import SHENSHA as _SHENSHA
TIANYI_GUI = _SHENSHA.get("天乙贵人", {})

# 杂气库（四墓库 → 藏的五行）
ZAQI = {
    "辰": ("水", "土", "木"),   # 水库，藏戊乙癸
    "戌": ("火", "土", "金"),   # 火库，藏戊辛丁
    "丑": ("金", "土", "水"),   # 金库，藏己癸辛
    "未": ("木", "土", "火"),   # 木库，藏己丁乙
}

# 魁罡（4 个）
KUI_GANG = {("庚", "辰"), ("庚", "戌"), ("壬", "辰"), ("戊", "戌")}


# ─────────────────────────────────────────────────────────────
# 通用辅助
# ─────────────────────────────────────────────────────────────

def _get_pillar_tg(chart: Dict, key: str) -> str:
    return (chart.get(key) or {}).get("tiangan", "")

def _get_pillar_dz(chart: Dict, key: str) -> str:
    return (chart.get(key) or {}).get("dizhi", "")

def _all_dz(chart: Dict) -> List[str]:
    return [_get_pillar_dz(chart, k) for k in
            ("year_pillar", "month_pillar", "day_pillar", "hour_pillar")]

def _all_tg(chart: Dict) -> List[str]:
    return [_get_pillar_tg(chart, k) for k in
            ("year_pillar", "month_pillar", "day_pillar", "hour_pillar")]

def _all_canggan(chart: Dict) -> List[str]:
    """合并四柱所有藏干（含本气）"""
    out: List[str] = []
    for k in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"):
        out.extend((chart.get(k) or {}).get("canggan", []))
    return out


def _ten_god_from_dm(dm: str, target: str) -> str:
    """根据日干和目标天干，返回十神类型。"""
    if not dm or not target:
        return ""
    from core.bazi.analyzer import get_shishen
    return get_shishen(dm, target)


def _shishen_present(chart: Dict, *target_shishens: str) -> Dict[str, List[str]]:
    """
    返回 {十神名: [出现的天干位置, ...]}
    扫描四柱天干 + 月柱本气藏干。
    """
    dm = chart.get("day_master", "")
    result: Dict[str, List[str]] = {sname: [] for sname in target_shishens}
    
    # 四柱透干
    for key in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"):
        tg = _get_pillar_tg(chart, key)
        if not tg or tg == dm:
            continue
        ss = _ten_god_from_dm(dm, tg)
        if ss in result:
            result[ss].append(f"{key}天干{tg}")
    
    # 月支藏干（命理学上月支藏干力量最大）
    month_cg = (chart.get("month_pillar") or {}).get("canggan", [])
    for tg in month_cg:
        if tg == dm:
            continue
        ss = _ten_god_from_dm(dm, tg)
        if ss in result:
            result[ss].append(f"月支藏{tg}")
    
    return result


# ─────────────────────────────────────────────────────────────
# 1. 日禄归时格
# ─────────────────────────────────────────────────────────────

def detect_rilu_guishi(chart: Dict) -> Dict[str, Any]:
    """日干之禄在时支 → 日禄归时格（青云得路格）"""
    dm = chart.get("day_master", "")
    hour_dz = _get_pillar_dz(chart, "hour_pillar")
    if dm and LUWEI.get(dm) == hour_dz:
        # 日禄归时忌见官星
        guan_killer = {"金": "火", "木": "金", "水": "土", "火": "水", "土": "木"}
        dm_wx = TG_WX[dm]
        ke_wx = guan_killer.get(dm_wx, "")
        all_tg = _all_tg(chart)
        has_guan = any(TG_WX.get(t, "") == ke_wx for t in all_tg)
        return {
            "name": "日禄归时格",
            "matched": True,
            "auspicious": not has_guan,
            "condition": f"日干{dm}之禄{hour_dz}恰落时支",
            "interpretation": (
                f"日禄归时（{dm}禄归{hour_dz}）— 主晚景丰隆、子孙得力、自立成名。"
                + ("忌见官星，本盘有官星制禄，格局减分。" if has_guan else "无官星破，格局成立。")
            ),
        }
    return {"name": "日禄归时格", "matched": False}


# ─────────────────────────────────────────────────────────────
# 2. 官印相生
# ─────────────────────────────────────────────────────────────

def detect_guanyin_xiangsheng(chart: Dict) -> Dict[str, Any]:
    """官星生印星，印星生日主 → 官印相生"""
    present = _shishen_present(chart, "正官", "七杀", "正印", "偏印")
    has_guan = bool(present["正官"] or present["七杀"])
    has_yin  = bool(present["正印"] or present["偏印"])
    
    if has_guan and has_yin:
        guan_pos = present["正官"] + present["七杀"]
        yin_pos  = present["正印"] + present["偏印"]
        return {
            "name": "官印相生",
            "matched": True,
            "auspicious": True,
            "condition": f"官星 ({len(guan_pos)} 处) + 印星 ({len(yin_pos)} 处) 同透",
            "evidence": guan_pos + yin_pos,
            "interpretation": (
                "官印相生 — 官星生印（化煞为权），印星扶身，主权贵、学问、文职、清贵之命。"
                "尤其官印同透不杂财，可由学入仕、由文得贵。"
            ),
        }
    return {"name": "官印相生", "matched": False}


# ─────────────────────────────────────────────────────────────
# 3. 食神制杀
# ─────────────────────────────────────────────────────────────

def detect_shishen_zhisha(chart: Dict) -> Dict[str, Any]:
    """食神制七杀 — 七杀凶神被食神制服"""
    present = _shishen_present(chart, "食神", "七杀", "正印", "偏印")
    has_shi = bool(present["食神"])
    has_sha = bool(present["七杀"])
    has_yin = bool(present["正印"] or present["偏印"])
    
    if has_shi and has_sha:
        # 警示：食神制杀时若印星过重会破格（夺食）
        return {
            "name": "食神制杀",
            "matched": True,
            "auspicious": not (has_yin and len(present["正印"] + present["偏印"]) >= 2),
            "condition": "食神与七杀同透",
            "evidence": present["食神"] + present["七杀"],
            "interpretation": (
                "食神制杀 — 七杀本凶神，得食神制约则化为权威，"
                "主有谋略、能担大任、武贵之命。"
                + ("但本命印星过重，恐'枭神夺食'破格。" if has_yin and len(present["正印"] + present["偏印"]) >= 2 else "")
            ),
        }
    return {"name": "食神制杀", "matched": False}


# ─────────────────────────────────────────────────────────────
# 4. 伤官见官（凶格）
# ─────────────────────────────────────────────────────────────

def detect_shangguan_jianguan(chart: Dict) -> Dict[str, Any]:
    """伤官见官 — 凶格"""
    present = _shishen_present(chart, "伤官", "正官")
    has_shang = bool(present["伤官"])
    has_guan  = bool(present["正官"])
    
    if has_shang and has_guan:
        return {
            "name": "伤官见官",
            "matched": True,
            "auspicious": False,
            "condition": "伤官与正官同透",
            "evidence": present["伤官"] + present["正官"],
            "interpretation": (
                "伤官见官 — 经典凶格，伤官克正官（克夫/克权威），"
                "主官非、口舌、上司不睦、女命婚姻不顺。"
                "化解需有财通关（伤官生财，财生官）或印星制伤。"
            ),
        }
    return {"name": "伤官见官", "matched": False}


# ─────────────────────────────────────────────────────────────
# 5. 财官印齐全
# ─────────────────────────────────────────────────────────────

def detect_cai_guan_yin_quanju(chart: Dict) -> Dict[str, Any]:
    """财官印三全 — 大贵之命"""
    present = _shishen_present(chart, "正官", "七杀", "正印", "偏印", "正财", "偏财")
    has_guan = bool(present["正官"] or present["七杀"])
    has_yin  = bool(present["正印"] or present["偏印"])
    has_cai  = bool(present["正财"] or present["偏财"])
    
    if has_guan and has_yin and has_cai:
        evidence = (present["正官"] + present["七杀"] + present["正印"] +
                    present["偏印"] + present["正财"] + present["偏财"])
        return {
            "name": "财官印三全",
            "matched": True,
            "auspicious": True,
            "condition": "财、官（杀）、印 三神同透",
            "evidence": evidence,
            "interpretation": (
                "财官印齐全（财→官→印→身的完整流通）— 大富大贵之格，"
                "主一生事业财禄印俱足，主名利双收，常见于实业、政商人物。"
            ),
        }
    return {"name": "财官印三全", "matched": False}


# ─────────────────────────────────────────────────────────────
# 6. 羊刃驾杀
# ─────────────────────────────────────────────────────────────

def detect_yangren_jiasha(chart: Dict) -> Dict[str, Any]:
    """七杀有羊刃制 → 武贵之格"""
    dm = chart.get("day_master", "")
    if dm not in YANGREN:
        return {"name": "羊刃驾杀", "matched": False}
    
    yangren_zhi = YANGREN[dm]
    has_yangren = yangren_zhi in _all_dz(chart)
    
    present = _shishen_present(chart, "七杀")
    has_sha = bool(present["七杀"])
    
    if has_yangren and has_sha:
        return {
            "name": "羊刃驾杀",
            "matched": True,
            "auspicious": True,
            "condition": f"羊刃{yangren_zhi}地支 + 七杀同透",
            "evidence": [f"羊刃{yangren_zhi}", *present["七杀"]],
            "interpretation": (
                f"羊刃驾杀（羊刃{yangren_zhi}+七杀同制）— 武贵之格，"
                "主英雄豪杰、军政高位、敢担当能成大事，"
                "尤适合军警、运动、外科医生等高强度行业。"
            ),
        }
    return {"name": "羊刃驾杀", "matched": False}


# ─────────────────────────────────────────────────────────────
# 7. 杂气月令格
# ─────────────────────────────────────────────────────────────

def detect_zaqi_yueling(chart: Dict) -> Dict[str, Any]:
    """月支为辰戌丑未（库），藏财官印 → 杂气格"""
    month_dz = _get_pillar_dz(chart, "month_pillar")
    if month_dz not in ZAQI:
        return {"name": "杂气月令格", "matched": False}
    
    dm = chart.get("day_master", "")
    month_canggan = (chart.get("month_pillar") or {}).get("canggan", [])
    
    important_ss = []
    for tg in month_canggan:
        if tg == dm:
            continue
        ss = _ten_god_from_dm(dm, tg)
        if ss in ("正官", "七杀", "正印", "偏印", "正财", "偏财"):
            important_ss.append((ss, tg))
    
    if important_ss:
        ss_names = list(set([x[0] for x in important_ss]))
        return {
            "name": "杂气月令格",
            "matched": True,
            "auspicious": True,
            "condition": f"月支{month_dz}（四库土）藏 {'/'.join(ss_names)}",
            "evidence": [f"{tg}({ss})" for ss, tg in important_ss],
            "interpretation": (
                f"杂气月令格 — 月支{month_dz}为四库土，藏 {'/'.join(ss_names)} 等用神。"
                "杂气格需冲开库门（大运/流年遇相冲）才能富贵显现，"
                "故应期常在 30-40 岁后或库被冲之运。"
            ),
        }
    return {"name": "杂气月令格", "matched": False}


# ─────────────────────────────────────────────────────────────
# 8. 拱禄拱贵
# ─────────────────────────────────────────────────────────────

def detect_gonglu_gonggui(chart: Dict) -> Dict[str, Any]:
    """邻柱地支相隔一位，中间夹禄或贵人 → 拱"""
    dm = chart.get("day_master", "")
    if not dm:
        return {"name": "拱禄拱贵", "matched": False}
    
    lu = LUWEI.get(dm, "")
    guis = set(TIANYI_GUI.get(dm, []))
    
    # 邻柱顺序：年-月、月-日、日-时
    pillar_pairs = [
        ("year_pillar", "month_pillar"),
        ("month_pillar", "day_pillar"),
        ("day_pillar", "hour_pillar"),
    ]
    DZ_ORDER = "子丑寅卯辰巳午未申酉戌亥"
    
    findings = []
    for p1, p2 in pillar_pairs:
        d1 = _get_pillar_dz(chart, p1)
        d2 = _get_pillar_dz(chart, p2)
        if not d1 or not d2:
            continue
        try:
            i1, i2 = DZ_ORDER.index(d1), DZ_ORDER.index(d2)
            # 相距 2（中间夹 1 支）
            if abs(i1 - i2) == 2 or abs(i1 - i2) == 10:  # 循环考虑
                # 中间支
                mid_idx = (i1 + i2) // 2 if abs(i1 - i2) == 2 else (i1 + i2 + 12) // 2 % 12
                mid_dz = DZ_ORDER[mid_idx]
                if mid_dz == lu:
                    findings.append(f"{d1}{d2}拱禄{mid_dz}")
                elif mid_dz in guis:
                    findings.append(f"{d1}{d2}拱贵{mid_dz}")
        except ValueError:
            pass
    
    # 注意命盘中实际有该夹支时，不算拱
    actual_dz = set(_all_dz(chart))
    findings = [f for f in findings 
                if f.split("拱")[1].replace("禄", "").replace("贵", "") not in actual_dz]
    
    if findings:
        return {
            "name": "拱禄拱贵",
            "matched": True,
            "auspicious": True,
            "condition": "邻柱地支夹禄/夹贵人",
            "evidence": findings,
            "interpretation": (
                f"拱禄拱贵 — {'/'.join(findings)}，"
                "命无禄贵却暗藏，主有贵人暗助、机缘暗生，"
                "看似无形实则得力，是命书中的'隐贵'之格。"
            ),
        }
    return {"name": "拱禄拱贵", "matched": False}


# ─────────────────────────────────────────────────────────────
# 9. 天乙独贵
# ─────────────────────────────────────────────────────────────

def detect_tianyi_dugui(chart: Dict) -> Dict[str, Any]:
    """命带天乙贵人，且无刑冲破害"""
    dm = chart.get("day_master", "")
    if dm not in TIANYI_GUI:
        return {"name": "天乙独贵", "matched": False}
    
    guis = TIANYI_GUI[dm]
    all_dz = _all_dz(chart)
    gui_in_chart = [g for g in guis if g in all_dz]
    
    if not gui_in_chart:
        return {"name": "天乙独贵", "matched": False}
    
    # 查刑冲（用 relations 模块）
    try:
        from core.bazi.relations import analyze_all_relations
        rel = analyze_all_relations(chart)
        # 若有冲或刑且涉及贵人，则破格
        for c in rel.get("chong", []) + rel.get("xing", []):
            if any(g in c.get("branches", []) for g in gui_in_chart):
                return {
                    "name": "天乙独贵",
                    "matched": True,
                    "auspicious": False,
                    "condition": f"天乙贵人 {gui_in_chart} 受刑冲",
                    "interpretation": (
                        f"天乙贵人 {gui_in_chart} 被刑冲，贵气被破，"
                        "贵人助力大打折扣，需有合化通关方可解。"
                    ),
                }
    except Exception as _e1:
        from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e1)
    
    return {
        "name": "天乙独贵",
        "matched": True,
        "auspicious": True,
        "condition": f"命带天乙贵人 {gui_in_chart} 且无刑冲破害",
        "evidence": gui_in_chart,
        "interpretation": (
            f"天乙独贵 — 命带天乙贵人 {gui_in_chart}，"
            "天乙乃天上之极尊神，主一生多遇贵人提携，"
            "逢凶化吉，事业上常得长辈/上司/师长之助。"
        ),
    }


# ─────────────────────────────────────────────────────────────
# 10. 魁罡格
# ─────────────────────────────────────────────────────────────

def detect_kuigang_ge(chart: Dict) -> Dict[str, Any]:
    """日柱为 庚辰/庚戌/壬辰/戊戌"""
    day_tg = _get_pillar_tg(chart, "day_pillar")
    day_dz = _get_pillar_dz(chart, "day_pillar")
    if (day_tg, day_dz) not in KUI_GANG:
        return {"name": "魁罡格", "matched": False}
    
    # 魁罡忌冲、忌财官
    all_dz = _all_dz(chart)
    chong_dz = {"辰": "戌", "戌": "辰"}.get(day_dz, "")
    has_chong = chong_dz in all_dz and any(dz == chong_dz for dz in all_dz if dz != day_dz)
    
    return {
        "name": "魁罡格",
        "matched": True,
        "auspicious": not has_chong,
        "condition": f"日柱{day_tg}{day_dz}（魁罡四柱之一）",
        "interpretation": (
            f"魁罡格 — 日柱{day_tg}{day_dz}为'天罡之首'，主聪明果断、性烈、有权威，"
            "宜任领导/法律/军警。"
            + ("但有冲魁罡（辰戌冲），减半甚至破格，主一生劳碌。" if has_chong
               else "无冲，格局成立。女命魁罡多个性独立、晚婚或事业心重。")
        ),
    }


# ─────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────

def detect_all_special_patterns(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    跑全部 10 个特殊格局检测，返回汇总。
    """
    detectors = [
        detect_rilu_guishi,
        detect_guanyin_xiangsheng,
        detect_shishen_zhisha,
        detect_shangguan_jianguan,
        detect_cai_guan_yin_quanju,
        detect_yangren_jiasha,
        detect_zaqi_yueling,
        detect_gonglu_gonggui,
        detect_tianyi_dugui,
        detect_kuigang_ge,
    ]
    
    matched: List[Dict[str, Any]] = []
    auspicious: List[Dict[str, Any]] = []
    inauspicious: List[Dict[str, Any]] = []
    
    for fn in detectors:
        try:
            r = fn(chart)
            if r.get("matched"):
                matched.append(r)
                if r.get("auspicious"):
                    auspicious.append(r)
                else:
                    inauspicious.append(r)
        except Exception as _e2:
            from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e2)
    
    return {
        "matched":      matched,
        "auspicious":   auspicious,
        "inauspicious": inauspicious,
        "total":        len(matched),
        "total_aus":    len(auspicious),
        "total_inaus":  len(inauspicious),
    }


def format_special_patterns_for_prompt(result: Dict[str, Any]) -> str:
    """给 LLM 用的中文段"""
    if not result or result.get("total", 0) == 0:
        return ""
    lines = [f"【特殊格局深度识别】（共检测出 {result['total']} 个特殊格局）"]
    if result.get("auspicious"):
        lines.append(f"  ◆ 吉格 ({len(result['auspicious'])} 个)：")
        for p in result["auspicious"]:
            lines.append(f"    ✦ 【{p['name']}】")
            lines.append(f"       成格条件：{p.get('condition', '')}")
            lines.append(f"       含义：{p['interpretation']}")
    if result.get("inauspicious"):
        lines.append(f"  ◆ 凶格/破格 ({len(result['inauspicious'])} 个)：")
        for p in result["inauspicious"]:
            lines.append(f"    ⚠ 【{p['name']}】")
            lines.append(f"       条件：{p.get('condition', '')}")
            lines.append(f"       含义：{p['interpretation']}")
    return "\n".join(lines)
