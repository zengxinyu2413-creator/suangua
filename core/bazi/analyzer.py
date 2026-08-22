"""
core/bazi/analyzer.py
=====================
Static analysis of a BaZi chart:
  • Ten Gods (十神) for every stem/branch
  • Day-master strength (身强/身弱)
  • Pattern detection (格局)
  • Shensha (神煞) identification

Bugs fixed:
  B-01 — WUXING_MAP renamed to WUXING (single definition in constants)
  B-12 — Shensha now uses complete table including 禄神 and 羊刃
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional

from core.constants import (
    SHISHEN, CANGGAN, WUXING, TIANGAN_WUXING, DIZHI_WUXING,
    WUXING_SHENG, WUXING_KE, SHENSHA,
    get_wuxing_strength, TIANGAN_INDEX,
    MAJOR_PATTERNS, SPECIAL_PATTERNS,
    SHENSHA_EXTENDED, ZHUAN_WANG_GE, HUA_QI_GE, get_sanhe_group,
)


# ─────────────────────────────────────────────────────────────
# Ten Gods
# ─────────────────────────────────────────────────────────────

def get_shishen(day_master: str, stem: str) -> str:
    """Return the Ten God name for *stem* relative to *day_master*."""
    return SHISHEN.get((day_master, stem), "")


def annotate_pillars(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add shishen_gan / shishen_zhi to every pillar in the chart dict.
    Returns the mutated chart.
    """
    dm = chart["day_master"]
    for pk in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"):
        p = chart[pk]
        p["shishen_gan"] = get_shishen(dm, p["tiangan"])
        # Ten God of branch = Ten God of its main (first) hidden stem
        main_hidden = CANGGAN.get(p["dizhi"], [])
        p["shishen_zhi"] = get_shishen(dm, main_hidden[0]) if main_hidden else ""
    return chart


def summarize_shishen(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Count Ten God occurrences across all stems (天干) and hidden stems (藏干).
    Returns list of {shishen, count, stems} sorted by count descending.
    """
    dm = chart["day_master"]
    counter: Dict[str, Dict] = {}

    pillars = [chart["year_pillar"], chart["month_pillar"],
               chart["day_pillar"], chart["hour_pillar"]]

    for p in pillars:
        # Visible stems
        ss = get_shishen(dm, p["tiangan"])
        if ss:
            counter.setdefault(ss, {"count": 0, "stems": []})
            counter[ss]["count"] += 1
            counter[ss]["stems"].append(p["tiangan"])
        # Hidden stems
        for h in p.get("canggan", []):
            ss_h = get_shishen(dm, h)
            if ss_h:
                counter.setdefault(ss_h, {"count": 0, "stems": []})
                counter[ss_h]["count"] += 1
                counter[ss_h]["stems"].append(h)

    result = []
    month_dz = chart["month_pillar"]["dizhi"]
    for ss, info in counter.items():
        wx = TIANGAN_WUXING.get(info["stems"][0], "") if info["stems"] else ""
        result.append({
            "shishen": ss,
            "count":   info["count"],
            "stems":   info["stems"],
            "strength": get_wuxing_strength(wx, month_dz) if wx else "",
        })
    result.sort(key=lambda x: x["count"], reverse=True)
    return result


# ─────────────────────────────────────────────────────────────
# Day-master strength
# ─────────────────────────────────────────────────────────────

_HELP_SHISHEN  = {"比肩", "劫财", "正印", "偏印"}
_DRAIN_SHISHEN = {"食神", "伤官", "正财", "偏财", "正官", "七杀"}


def calculate_strength(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate whether the day master is 身强 (strong) or 身弱 (weak).

    Algorithm:
      1. Check month-branch rooting (得令)
      2. Sum helper vs draining Ten Gods
      3. Classify as 强/弱/中和
    """
    dm = chart["day_master"]
    dm_wx = TIANGAN_WUXING[dm]
    month_dz = chart["month_pillar"]["dizhi"]

    # 1. 得令 — 严格意义上只有"旺"才得令；"相"是"得气"但非得令
    #   旺 = 同我（如木日寅月）= 得令
    #   相 = 我得生（如木日子月，水生木）= 得气，但传统上不算严格得令
    #   命理学严格定义：得令仅指日主五行与月令同气
    monthly_strength = get_wuxing_strength(dm_wx, month_dz)
    deling = monthly_strength == "旺"     # 严格得令
    deqi   = monthly_strength in ("旺", "相")  # 广义得气（旺或得生）

    # 2. Count helping vs draining stems (visible + hidden)
    help_score  = 0
    drain_score = 0
    pillars = [chart["year_pillar"], chart["month_pillar"],
               chart["day_pillar"], chart["hour_pillar"]]

    for p in pillars:
        stems = [p["tiangan"]] + p.get("canggan", [])
        for s in stems:
            ss = get_shishen(dm, s)
            if ss in _HELP_SHISHEN:
                help_score  += 1
            elif ss in _DRAIN_SHISHEN:
                drain_score += 1

    # 2b. Branch combination bonus: 三合/三会 greatly amplify element power
    # 三合局 (three-harmony): 寅午戌=火局, 申子辰=水局, 巳酉丑=金局, 亥卯未=木局
    # 三会方 (directional): 寅卯辰=木, 巳午未=火, 申酉戌=金, 亥子丑=水
    all_dz = [p["dizhi"] for p in pillars]
    _SANHE = [
        ({"寅","午","戌"}, "火"), ({"申","子","辰"}, "水"),
        ({"巳","酉","丑"}, "金"), ({"亥","卯","未"}, "木"),
    ]
    _SANHUI = [
        ({"寅","卯","辰"}, "木"), ({"巳","午","未"}, "火"),
        ({"申","酉","戌"}, "金"), ({"亥","子","丑"}, "水"),
    ]
    dz_set = set(all_dz)
    for group, wx in _SANHE + _SANHUI:
        if len(dz_set & group) == 3:  # complete combination
            if WUXING_SHENG.get(wx) == dm_wx:
                help_score  += 3  # 三合生日主: major help
            elif wx == dm_wx:
                help_score  += 3  # 三合同类: major help
            elif WUXING_KE.get(wx) == dm_wx:
                drain_score += 3  # 三合克日主: major drain
            elif WUXING_KE.get(dm_wx) == wx:
                drain_score += 2  # 日主克三合: some drain
        elif len(dz_set & group) == 2:  # partial combination (半合)
            if WUXING_SHENG.get(wx) == dm_wx or wx == dm_wx:
                help_score  += 1
            elif WUXING_KE.get(wx) == dm_wx:
                drain_score += 1

    # 3. Classify — 综合判定
    if deling and help_score >= drain_score:
        label = "身强"
    elif deqi and help_score > drain_score:
        label = "身强"   # 月令"相"+ 帮扶占优 也算身强
    elif not deqi and drain_score > help_score + 1:
        label = "身弱"
    else:
        label = "中和"

    return {
        "strength":       label,
        "monthly_status": monthly_strength,
        "deling":         deling,     # 严格得令（仅"旺"）
        "deqi":           deqi,       # 得气（"旺"或"相"）
        "help_score":     help_score,
        "drain_score":    drain_score,
    }


# ─────────────────────────────────────────────────────────────
# Pattern detection (格局)
# ─────────────────────────────────────────────────────────────

def detect_pattern(chart: Dict[str, Any]) -> Dict[str, str]:
    """
    Detect the dominant BaZi pattern (格局).
    Priority: 专旺格 > 化气格 > special (从格) > month-branch major pattern.
    """
    dm     = chart["day_master"]
    dm_wx  = TIANGAN_WUXING[dm]
    m_p    = chart["month_pillar"]
    month_canggan = m_p.get("canggan", [])
    strength_info = calculate_strength(chart)

    # ── 专旺格五局 ────────────────────────────────────────────────────────────
    all_dz = {chart[p]["dizhi"] for p in ["year_pillar","month_pillar","day_pillar","hour_pillar"]}
    for gname, gdata in ZHUAN_WANG_GE.items():
        if dm not in gdata["stems"]:
            continue
        # Check: required branches present, no destructive element in stems
        req_zhi  = gdata["required_zhi"]
        has_reqs = len(all_dz & req_zhi) >= 3  # at least 3 of 4 required branches
        ke_elem  = WUXING_KE.get(gdata["element"], "")  # element that destroys this
        all_tg   = [chart[p]["tiangan"] for p in ["year_pillar","month_pillar","day_pillar","hour_pillar"]]
        has_ke   = any(TIANGAN_WUXING.get(t,"") == ke_elem for t in all_tg)
        if has_reqs and not has_ke and strength_info["strength"] in ("身强","中和"):
            return {"pattern": gname, "desc": gdata["desc"]}

    # ── 化气格五局 ────────────────────────────────────────────────────────────
    hour_gan = chart["hour_pillar"]["tiangan"]
    for gname, gdata in HUA_QI_GE.items():
        a, b = gdata["stems_pair"]
        if (dm == a and hour_gan == b) or (dm == b and hour_gan == a):
            if m_p["dizhi"] in gdata["month_zhi"]:
                ke_elem = WUXING_KE.get(gdata["element"], "")
                all_tg2 = [chart[p]["tiangan"] for p in ["year_pillar","month_pillar","day_pillar","hour_pillar"]]
                has_ke2 = any(TIANGAN_WUXING.get(t,"") == ke_elem for t in all_tg2)
                if not has_ke2:
                    return {"pattern": gname, "desc": gdata["desc"]}

    # Special patterns: strict criteria (真从格)
    # Must be: 极弱 (very weak), overwhelmingly dominated by one type,
    # and no saving grace (no 印/比 to rescue the day master)
    if strength_info["strength"] == "身弱":
        ss_list   = summarize_shishen(chart)
        top_ss    = ss_list[0]["shishen"] if ss_list else ""
        top_count = ss_list[0]["count"]   if ss_list else 0
        help_sc   = strength_info["help_score"]
        drain_sc  = strength_info["drain_score"]

        # Strict 从格 conditions:
        # 1. Top shishen must dominate: count >= 3 AND no equally strong rival
        # 2. Help score must be very low (≤2: at most 1-2 helper stems)
        # 3. Drain score must be overwhelming (≥8)
        rival_count = ss_list[1]["count"] if len(ss_list) > 1 else 0
        dominant = top_count >= 3 and top_count > rival_count
        extreme  = help_sc <= 2 and drain_sc >= 8

        if dominant and extreme:
            if top_ss in ("正财", "偏财"):
                return {"pattern": "从财格", "desc": SPECIAL_PATTERNS[2]["desc"]}
            if top_ss in ("正官", "七杀"):
                return {"pattern": "从杀格", "desc": SPECIAL_PATTERNS[3]["desc"]}
            if top_ss in ("食神", "伤官"):
                # Also verify: no 官杀 lurking (官杀克食伤阻碍从儿)
                guan_sha = next((s for s in ss_list if s["shishen"] in ("正官","七杀")), None)
                if not guan_sha or guan_sha["count"] <= 1:
                    return {"pattern": "从儿格", "desc": SPECIAL_PATTERNS[4]["desc"]}

    # Major patterns — 透干优先 + 格局高低原则 (《子平真诠》)
    #
    # Rules:
    # 1. 建禄/月刃: identified by 比肩/劫财 — always take priority if applicable
    # 2. 透干优先: if any hidden stem appears as visible TianGan, prefer it over main qi
    # 3. 多干俱透 (multiple transparent): take the highest-ranking pattern
    #    Hierarchy: 建禄=月刃 > 正官 > 正印 > 食神 > 正财=偏财 > 七杀 > 偏印 > 伤官
    # 4. No transparent: fall back to main qi (第一藏干)

    _PATTERN_RANK: Dict[str, int] = {
        "建禄格": 0, "月刃格": 0,
        "正官格": 1, "正印格": 2, "食神格": 3,
        "正财格": 4, "偏财格": 4,
        "七杀格": 5, "偏印格": 6, "伤官格": 7,
    }

    def _rich_desc(pattern_name: str, fallback: str = "") -> str:
        """格局富描述：优先《子平真诠》章旨（ZIPING_GE_FULL），退而用 MAJOR_PATTERNS。"""
        try:
            from knowledge.bazi_classical_deep import ZIPING_GE_FULL
            full = ZIPING_GE_FULL.get(pattern_name, {})
            if full.get("章旨"):
                return full["章旨"]
        except Exception as _e1:
            from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e1)
        # MAJOR_PATTERNS 以全名键存
        mp = MAJOR_PATTERNS.get(pattern_name, {})
        if mp.get("desc"):
            return mp["desc"]
        return fallback

    def _cg_to_pattern(cg: str) -> Dict[str, str]:
        """Return {pattern, desc} for a hidden stem relative to day master."""
        ss = get_shishen(dm, cg)
        if ss == "比肩":
            return {"pattern": "建禄格", "desc": _rich_desc("建禄格", SPECIAL_PATTERNS[0]["desc"])}
        if ss == "劫财":
            return {"pattern": "月刃格", "desc": _rich_desc("月刃格", SPECIAL_PATTERNS[1]["desc"])}
        # 十神名 → 格名（补「格」后缀，兼容键差异）
        pat_name = ss + "格"
        if ss in MAJOR_PATTERNS or pat_name in MAJOR_PATTERNS:
            mp = MAJOR_PATTERNS.get(ss) or MAJOR_PATTERNS.get(pat_name, {})
            name = mp.get("name", pat_name)
            return {"pattern": name, "desc": _rich_desc(name, mp.get("desc", ""))}
        return {"pattern": pat_name, "desc": _rich_desc(pat_name)}

    if month_canggan:
        visible_tg = {chart[p]["tiangan"] for p in
                      ("year_pillar","month_pillar","day_pillar","hour_pillar")}

        # Collect all transparent hidden stems
        transparent_cg = [cg for cg in month_canggan if cg in visible_tg]

        if transparent_cg:
            # Pick the highest-ranking pattern among all transparent stems
            best_cg = min(
                transparent_cg,
                key=lambda cg: _PATTERN_RANK.get(_cg_to_pattern(cg)["pattern"], 99)
            )
            return _cg_to_pattern(best_cg)

        # No transparent stem: use main qi (first hidden stem)
        return _cg_to_pattern(month_canggan[0])

    return {"pattern": "杂气格", "desc": "月支藏干杂，需综合论断"}


# ─────────────────────────────────────────────────────────────
# Shensha (神煞) — B-12 fixed: full table including 禄神/羊刃
# ─────────────────────────────────────────────────────────────

def find_shensha(chart: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Find all active Shensha (神煞) in the chart.
    Checks each pillar's DiZhi against the Shensha lookup table
    using the day-master TianGan as the reference key.

    Returns list of {name, dizhi, pillar}.
    """
    dm = chart["day_master"]
    year_dz  = chart["year_pillar"]["dizhi"]
    result: List[Dict[str, str]] = []

    pillar_map = {
        "年支": chart["year_pillar"]["dizhi"],
        "月支": chart["month_pillar"]["dizhi"],
        "日支": chart["day_pillar"]["dizhi"],
        "时支": chart["hour_pillar"]["dizhi"],
    }

    for sha_name, sha_data in SHENSHA.items():
        # 天乙贵人 / 文昌贵人 / 禄神 / 羊刃 — keyed by TianGan
        if dm in sha_data:
            active_branches = sha_data[dm]
            for pillar_label, dz in pillar_map.items():
                if dz in active_branches:
                    result.append({
                        "name":   sha_name,
                        "dizhi":  dz,
                        "pillar": pillar_label,
                    })

        # 驿马 / 华盖 — keyed by DiZhi (usually year or day branch)
        elif year_dz in sha_data:
            active_branches = sha_data[year_dz]
            for pillar_label, dz in pillar_map.items():
                if dz in active_branches:
                    result.append({
                        "name":   sha_name,
                        "dizhi":  dz,
                        "pillar": pillar_label,
                    })

    # ── Extended shensha (将星/桃花/孤辰/寡宿/劫煞/亡神/咸池/魁罡/金舆/红艳) ──
    year_zhi = chart["year_pillar"]["dizhi"]
    day_zhi  = chart["day_pillar"]["dizhi"]

    # Group-based (寅午戌 etc.) — checked against year zhi
    from core.constants import SANHE_GROUPS
    year_group = get_sanhe_group(year_zhi)

    GROUP_SHENSHA = ["将星", "桃花", "孤辰", "寡宿", "劫煞", "亡神", "咸池", "灾煞"]
    for sha_name in GROUP_SHENSHA:
        sha_data = SHENSHA_EXTENDED.get(sha_name, {})
        for group_key, target_zhi in sha_data.items():
            if year_zhi in group_key:
                for pl, dz in pillar_map.items():
                    if dz == target_zhi:
                        result.append({"name": sha_name, "dizhi": dz, "pillar": pl})
                break

    # 魁罡 (specific ganzhi combos)
    kuigang = SHENSHA_EXTENDED.get("魁罡", {})
    day_gan  = chart["day_pillar"]["tiangan"]
    if day_gan in kuigang and day_zhi in kuigang[day_gan]:
        result.append({"name": "魁罡", "dizhi": day_zhi, "pillar": "日支（魁罡贵格）"})

    # 金舆 / 红艳煞 / 天厨贵人 / 学堂 / 词馆 — keyed by day stem
    for sha_name in ["金舆", "红艳煞", "天厨贵人", "学堂", "词馆"]:
        sha_data = SHENSHA_EXTENDED.get(sha_name, {})
        if dm in sha_data:
            for pl, dz in pillar_map.items():
                if dz in sha_data[dm]:
                    result.append({"name": sha_name, "dizhi": dz, "pillar": pl})

    # 天罗 / 地网 — 仅丙丁/壬癸日主见特定地支
    for sha_name in ["天罗", "地网"]:
        sha_data = SHENSHA_EXTENDED.get(sha_name, {})
        if dm in sha_data:
            for pl, dz in pillar_map.items():
                if dz in sha_data[dm]:
                    result.append({"name": sha_name, "dizhi": dz, "pillar": pl})

    # 天德贵人 / 月德贵人 — 以月支查，看其他柱天干是否匹配
    month_zhi = chart["month_pillar"]["dizhi"]
    pillar_gan_map = {
        "年干": chart["year_pillar"]["tiangan"],
        "月干": chart["month_pillar"]["tiangan"],
        "日干": chart["day_pillar"]["tiangan"],
        "时干": chart["hour_pillar"]["tiangan"],
    }
    for sha_name in ["天德贵人", "月德贵人"]:
        sha_data = SHENSHA_EXTENDED.get(sha_name, {})
        targets = sha_data.get(month_zhi, [])
        for pl, gan in pillar_gan_map.items():
            if gan in targets:
                result.append({"name": sha_name, "dizhi": gan, "pillar": pl})

    # 国印 — 以年干查地支
    year_gan = chart["year_pillar"]["tiangan"]
    guoyin = SHENSHA_EXTENDED.get("国印", {})
    if year_gan in guoyin:
        for pl, dz in pillar_map.items():
            if dz in guoyin[year_gan]:
                result.append({"name": "国印", "dizhi": dz, "pillar": pl})

    return result


# ─────────────────────────────────────────────────────────────
# Master analyze function
# ─────────────────────────────────────────────────────────────

def analyze_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run full static analysis on a chart dict (from build_chart).
    Mutates and returns the chart with analysis results attached.
    """
    annotate_pillars(chart)
    chart["shishen_summary"] = summarize_shishen(chart)
    chart["strength_info"]   = calculate_strength(chart)
    chart["strength"]        = chart["strength_info"]["strength"]
    chart["pattern_info"]    = detect_pattern(chart)
    chart["pattern"]         = chart["pattern_info"]["pattern"]
    chart["pattern_desc"]    = chart["pattern_info"]["desc"]
    chart["shensha"]         = find_shensha(chart)
    
    # ── 调候用神（《穷通宝鉴》）+ 子平真诠格局成败救应 ──
    try:
        from core.bazi.tiaohou_yongshen import (
            analyze_tiaohou_in_chart, analyze_geju_cheng_bai,
        )
        chart["tiaohou"] = analyze_tiaohou_in_chart(chart)
        # 如果格局是 8 大正格之一，加入成败救应分析
        pattern_name = chart["pattern_info"].get("pattern", "")
        geju = analyze_geju_cheng_bai(chart, pattern_name)
        if geju.get("available"):
            chart["geju_cheng_bai"] = geju
    except Exception as _e2:
        from core.log import log_failure; log_failure("bazi", "装配(自动补充日志)", _e2)
    
    return chart
