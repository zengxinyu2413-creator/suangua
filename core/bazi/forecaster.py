"""
core/bazi/forecaster.py
=======================
Time-based fortune forecasting:
  • DaYun  (大运) — 10-year luck cycles
  • LiuNian (流年) — yearly fortune
  • LiuYue  (流月) — monthly fortune

Bugs fixed:
  B-07 — season quality now uses 旺/相/休/囚/死 vocabulary
  B-08 — DaYun start age uses exact solar-day-distance ÷ 3 method
  B-11 — DaYun GanZhi sequence starts correctly from the next Jié
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import math

from core.constants import (
    TIANGAN, DIZHI, TIANGAN_INDEX, DIZHI_INDEX,
    TIANGAN_WUXING, DIZHI_WUXING, WUXING,
    get_month_gan, get_wuxing_strength,
)
from core.calendar.ganzhi import ganzhi_from_index, ganzhi_index
from core.calendar.solar_terms import nearest_jie, get_jie_dates

# ─────────────────────────────────────────────────────────────
# Interaction analysis helpers
# ─────────────────────────────────────────────────────────────

# 地支三合局 (each group shares the same element)
_SANHE_GROUPS: List[Tuple[str, str, str]] = [
    ("寅","午","戌"), ("申","子","辰"),
    ("巳","酉","丑"), ("亥","卯","未"),
]
# 地支六冲
_LIUCHONG: Dict[str, str] = {
    "子":"午","午":"子","丑":"未","未":"丑",
    "寅":"申","申":"寅","卯":"酉","酉":"卯",
    "辰":"戌","戌":"辰","巳":"亥","亥":"巳",
}
# 地支六合
_LIUHE: Dict[str, str] = {
    "子":"丑","丑":"子","寅":"亥","亥":"寅",
    "卯":"戌","戌":"卯","辰":"酉","酉":"辰",
    "巳":"申","申":"巳","午":"未","未":"午",
}
# 三刑（《滴天髓》完整四类）：
#   无礼之刑：子刑卯、卯刑子
#   恃势之刑：寅刑巳、巳刑申、申刑寅
#   无恩之刑：丑刑戌、戌刑未、未刑丑
#   自刑：辰、午、酉、亥
_SANXING: Dict[str, str] = {
    "寅":"巳","巳":"申","申":"寅",
    "子":"卯","卯":"子",
    "丑":"戌","戌":"未","未":"丑",
    "辰":"辰","午":"午","酉":"酉","亥":"亥",  # 自刑
}


def _analyze_dayun_interactions(
    chart: Dict[str, Any],
    dy_gan: str,
    dy_zhi: str,
) -> Dict[str, Any]:
    """
    Analyze interactions between a DaYun ganzhi and the natal chart.

    Checks:
      • 大运天干 vs 命局四柱天干: 冲/克/合/生
      • 大运地支 vs 命局四柱地支: 六冲/六合/三合/三刑
      • 太岁(年支) vs 命局日支: 是否冲日支（重要警示）
    Returns structured warnings and auspicious signals.
    """
    pillars = ["year_pillar","month_pillar","day_pillar","hour_pillar"]
    natal_gan  = [chart[p]["tiangan"] for p in pillars]
    natal_zhi  = [chart[p]["dizhi"]   for p in pillars]
    day_zhi    = chart["day_pillar"]["dizhi"]
    month_zhi  = chart["month_pillar"]["dizhi"]
    dm = chart["day_master"]
    dm_wx = TIANGAN_WUXING[dm]

    from core.constants import WUXING_KE, WUXING_SHENG, TIANGAN_WUXING as TGW

    warnings: List[str]   = []
    auspicious: List[str] = []

    dy_wx  = TGW.get(dy_gan, "")
    dy_zwx = DIZHI_WUXING.get(dy_zhi, "")

    # ── 天干互动 ────────────────────────────────────────────────
    for natal_g in natal_gan:
        ng_wx = TGW.get(natal_g, "")
        # 大运干克命局干
        if WUXING_KE.get(dy_wx) == ng_wx and natal_g in (dm,):
            warnings.append(f"大运{dy_gan}（{dy_wx}）克日主{natal_g}，运中压力较大")
        # 大运干生日主
        if WUXING_SHENG.get(dy_wx) == dm_wx:
            auspicious.append(f"大运{dy_gan}生扶日主，运势有助")
        # 天干相合（甲己合, 乙庚合, 丙辛合, 丁壬合, 戊癸合）
    _TIANGAN_HE = {"甲":"己","己":"甲","乙":"庚","庚":"乙",
                    "丙":"辛","辛":"丙","丁":"壬","壬":"丁","戊":"癸","癸":"戊"}
    if _TIANGAN_HE.get(dy_gan) == dm:
        auspicious.append(f"大运{dy_gan}与日主{dm}天干相合，运中有贵人缘")

    # ── 地支互动 ────────────────────────────────────────────────
    for p_label, natal_z in zip(["年支","月支","日支","时支"], natal_zhi):
        # 六冲
        if _LIUCHONG.get(dy_zhi) == natal_z:
            severity = "⚠ 重要" if natal_z == day_zhi else "注意"
            warnings.append(
                f"{severity}：大运支{dy_zhi}冲{p_label}{natal_z}"
                + ("（冲日支，配偶宫/身体宫受冲，需谨慎）" if natal_z == day_zhi else "")
            )
        # 六合
        if _LIUHE.get(dy_zhi) == natal_z:
            auspicious.append(f"大运支{dy_zhi}与{p_label}{natal_z}六合，{p_label}所主之事有益")
        # 三刑
        if _SANXING.get(dy_zhi) == natal_z and dy_zhi != natal_z:
            warnings.append(f"大运支{dy_zhi}刑{p_label}{natal_z}，有是非争讼或身体隐患")

    # ── 太岁(年支)冲日支警示 ─────────────────────────────────────
    if _LIUCHONG.get(dy_zhi) == day_zhi:
        warnings.append(
            f"⚠ 大运地支{dy_zhi}冲日支{day_zhi}（日支为配偶宫和本人安危宫），"
            "此运感情婚姻多波折，身体需加注意"
        )

    return {
        "warnings":   warnings,
        "auspicious": auspicious,
        "clash_day_zhi": _LIUCHONG.get(dy_zhi) == day_zhi,
    }


def _analyze_liunian_taisu(
    chart: Dict[str, Any],
    ly_gan: str,
    ly_zhi: str,
    year: int,
) -> Dict[str, Any]:
    """
    Analyze the annual influence (流年太岁) vs natal chart.

    Key checks:
      • 太岁冲日支 (本命年逢冲): 非常凶险
      • 太岁冲月支: 影响事业/健康
      • 太岁冲年支: 影响祖宅/父母
      • 伏吟: 流年干支与命局某柱完全相同
      • 反吟: 流年干支与命局某柱完全相冲
      • 天干合化: 流年干与日主合
    """
    pillars = ["year_pillar","month_pillar","day_pillar","hour_pillar"]
    natal_zhi = [chart[p]["dizhi"] for p in pillars]
    natal_gan = [chart[p]["tiangan"] for p in pillars]
    day_zhi   = chart["day_pillar"]["dizhi"]
    dm        = chart["day_master"]

    from core.constants import TIANGAN_WUXING as TGW, WUXING_KE, WUXING_SHENG

    warnings: List[str]   = []
    auspicious: List[str] = []
    tags: List[str]       = []

    # ── 太岁冲各柱地支 ──────────────────────────────────────────
    labels = ["年支","月支","日支","时支"]
    for lbl, nz in zip(labels, natal_zhi):
        if _LIUCHONG.get(ly_zhi) == nz:
            if lbl == "日支":
                warnings.append(f"⚠ 太岁冲日支（{ly_zhi}冲{nz}）：本命年遭冲，感情健康最须谨慎")
                tags.append("太岁冲日支")
            elif lbl == "年支":
                warnings.append(f"太岁冲年支（{ly_zhi}冲{nz}）：祖宅祖业有变动")
                tags.append("冲年支")
            elif lbl == "月支":
                warnings.append(f"太岁冲月支（{ly_zhi}冲{nz}）：事业健康有波折")
                tags.append("冲月支")

    # ── 伏吟 / 反吟（《滴天髓·六亲论》）─────────────────────────────
    # 天干七冲：甲庚冲、乙辛冲、丙壬冲、丁癸冲（戊己土居中不冲）
    _TG_CHONG = {"甲":"庚","庚":"甲","乙":"辛","辛":"乙",
                 "丙":"壬","壬":"丙","丁":"癸","癸":"丁"}
    for lbl, ng, nz in zip(labels, natal_gan, natal_zhi):
        if ly_gan == ng and ly_zhi == nz:
            tags.append(f"伏吟（{lbl}）")
            warnings.append(f"伏吟年（流年与{lbl}完全相同）：诸事停滞，宜守不宜动")
        # 反吟 = 天干冲 + 地支冲
        if _TG_CHONG.get(ly_gan) == ng and _LIUCHONG.get(ly_zhi) == nz:
            tags.append(f"反吟（{lbl}）")
            warnings.append(f"反吟年（流年天干地支双冲{lbl}）：反复颠覆，最忌动作")
        # 单天干冲
        elif _TG_CHONG.get(ly_gan) == ng:
            tags.append(f"天干冲{lbl}")
            warnings.append(f"流年天干{ly_gan}冲{lbl}{ng}：易有意外冲突，须防口舌官非")

    # ── 天干相合 ─────────────────────────────────────────────────
    _TG_HE = {"甲":"己","己":"甲","乙":"庚","庚":"乙",
               "丙":"辛","辛":"丙","丁":"壬","壬":"丁","戊":"癸","癸":"戊"}
    if _TG_HE.get(ly_gan) == dm:
        auspicious.append(f"流年{ly_gan}与日主{dm}天干相合，此年有贵人际遇")

    # ── 流年三合会命局 ────────────────────────────────────────────
    natal_zhi_set = set(natal_zhi)
    for sanhe in _SANHE_GROUPS:
        if ly_zhi in sanhe:
            others = [z for z in sanhe if z != ly_zhi]
            hits = natal_zhi_set & set(others)
            if len(hits) >= 1:
                auspicious.append(
                    f"流年{ly_zhi}与命局{'/'.join(hits)}三合，运势有助推")

    return {
        "warnings":   warnings,
        "auspicious": auspicious,
        "tags":       tags,
        "is_benming_chong": "太岁冲日支" in tags,
    }


# ─────────────────────────────────────────────────────────────
# DaYun start age (B-08 fixed)
# ─────────────────────────────────────────────────────────────

def _dayun_start_age(birth_dt: datetime, gender: str,
                     year_gan: str) -> float:
    """
    Calculate the exact DaYun start age using the traditional
    solar-day-distance ÷ 3 method.

    Rule:
      阳男 / 阴女 → forward direction (顺), count to next Jié
      阴男 / 阳女 → reverse direction (逆), count to previous Jié
    """
    from core.constants import TIANGAN_INDEX
    # Yin/Yang of year TianGan: even index = 阳 (甲丙戊庚壬), odd = 阴
    year_yang = (TIANGAN_INDEX[year_gan] % 2 == 0)
    male = gender in ("male", "男")

    forward = (year_yang and male) or (not year_yang and not male)

    prev_jie, next_jie = nearest_jie(birth_dt)

    if forward:
        target = next_jie
    else:
        target = prev_jie

    if target is None:
        # 真正回退：基于月份估算（每月 30 天，3 天 = 1 年）
        # 阳男阴女顺：到下个月初；阴男阳女逆：到本月初
        from datetime import timedelta
        if forward:
            # 到下个月 1 日
            next_month = birth_dt.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            delta_days = (next_month - birth_dt).total_seconds() / 86400
        else:
            # 到本月 1 日
            this_month_1 = birth_dt.replace(day=1)
            delta_days = (birth_dt - this_month_1).total_seconds() / 86400
        return round(delta_days / 3.0, 2)

    delta_days = abs((target - birth_dt).total_seconds() / 86400)
    # Traditional: 3 days = 1 year, 1 day = 4 months
    age = delta_days / 3.0
    return round(age, 2)


# ─────────────────────────────────────────────────────────────
# DaYun sequence (B-11 fixed)
# ─────────────────────────────────────────────────────────────

def _dayun_direction(gender: str, year_gan: str) -> int:
    """Return +1 (forward/顺) or -1 (reverse/逆)."""
    from core.constants import TIANGAN_INDEX
    year_yang = (TIANGAN_INDEX[year_gan] % 2 == 0)
    male = gender in ("male", "男")
    forward = (year_yang and male) or (not year_yang and not male)
    return 1 if forward else -1


def calculate_dayun(chart: Dict[str, Any], gender: str,
                    birth_year: int, num_periods: int = 10) -> List[Dict[str, Any]]:
    """
    Calculate *num_periods* DaYun 10-year luck cycles.

    Starting point: the GanZhi immediately after (or before, if 逆)
    the month pillar's GanZhi in the 60-cycle.  (B-11 fix)
    """
    year_gan   = chart["year_pillar"]["tiangan"]
    month_gan  = chart["month_pillar"]["tiangan"]
    month_zhi  = chart["month_pillar"]["dizhi"]

    direction  = _dayun_direction(gender, year_gan)
    start_age  = _dayun_start_age(
        datetime.fromisoformat(chart["birth_dt"]), gender, year_gan
    )

    # Current 60-cycle index of the month pillar
    month_idx  = ganzhi_index(month_gan, month_zhi)

    dayun_list = []
    for i in range(num_periods):
        # Each period advances/retreats by (i+1) steps from month pillar
        idx = (month_idx + direction * (i + 1)) % 60
        dy_gan, dy_zhi = ganzhi_from_index(idx)

        period_start_age  = start_age + i * 10
        period_end_age    = start_age + (i + 1) * 10
        period_start_year = birth_year + math.floor(period_start_age)
        period_end_year   = birth_year + math.floor(period_end_age)

        # Quality — does the DaYun wuxing help or hinder the day master?
        dm_wx   = TIANGAN_WUXING[chart["day_master"]]
        dy_wx   = TIANGAN_WUXING[dy_gan]
        # 兼容 chart 是否已含 strength 字段（来自 analyzer）
        strength_label = chart.get("strength", "")
        if isinstance(strength_label, dict):
            strength_label = strength_label.get("strength", "中和")
        if not strength_label:
            # 即时计算
            try:
                from core.bazi.analyzer import calculate_strength
                strength_info = calculate_strength(chart)
                strength_label = strength_info.get("strength", "中和")
            except Exception:
                strength_label = "中和"
        quality = _assess_quality(dm_wx, dy_wx, strength_label)

        # Interaction analysis with natal chart
        interactions = _analyze_dayun_interactions(chart, dy_gan, dy_zhi)

        dayun_list.append({
            "index":       i + 1,
            "tiangan":     dy_gan,
            "dizhi":       dy_zhi,
            "start_age":   round(period_start_age, 1),
            "end_age":     round(period_end_age, 1),
            "start_year":  period_start_year,
            "end_year":    period_end_year,
            "quality":     quality,
            "dm_shishen":  _shishen_label(chart["day_master"], dy_gan),
            "warnings":    interactions["warnings"],
            "auspicious":  interactions["auspicious"],
            "clash_day_zhi": interactions["clash_day_zhi"],
        })

    return dayun_list


def _shishen_label(dm: str, stem: str) -> str:
    from core.constants import SHISHEN
    return SHISHEN.get((dm, stem), "")


def _assess_quality(dm_wx: str, target_wx: str, strength: str) -> str:
    """
    Simple quality heuristic:
      身强 benefits from 克泄耗 (food/wealth/officer wuxing)
      身弱 benefits from 生扶 (印/比 wuxing)
    """
    from core.constants import WUXING_SHENG, WUXING_KE
    helps  = target_wx == WUXING_SHENG.get(WUXING_KE.get(dm_wx, ""), "") or target_wx == dm_wx
    drains = target_wx == WUXING_KE.get(dm_wx, "") or target_wx == WUXING_SHENG.get(dm_wx, "")

    if strength == "身强":
        if drains: return "吉"
        if helps:  return "凶"
    else:
        if helps:  return "吉"
        if drains: return "凶"
    return "平"


# ─────────────────────────────────────────────────────────────
# LiuNian (流年)
# ─────────────────────────────────────────────────────────────

def calculate_liunian(chart: Dict[str, Any], gender: str,
                      birth_year: int,
                      from_year: Optional[int] = None,
                      to_year: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Return yearly fortune for years [from_year, to_year].
    Defaults to birth_year through birth_year+80.
    """
    if from_year is None:
        from_year = birth_year
    if to_year is None:
        to_year = birth_year + 80

    dm = chart["day_master"]
    dm_wx = TIANGAN_WUXING[dm]
    strength = chart.get("strength", "中和")

    result = []
    for yr in range(from_year, to_year + 1):
        # 1984 = 甲子 year (index 0)
        idx = (yr - 1984) % 60
        ly_gan, ly_zhi = ganzhi_from_index(idx)
        ly_wx = TIANGAN_WUXING[ly_gan]
        quality = _assess_quality(dm_wx, ly_wx, strength)

        # Taisui (太岁) analysis
        taisu = _analyze_liunian_taisu(chart, ly_gan, ly_zhi, yr)

        result.append({
            "year":        yr,
            "tiangan":     ly_gan,
            "dizhi":       ly_zhi,
            "age":         yr - birth_year,
            "shishen_gan": _shishen_label(dm, ly_gan),
            "shishen_zhi": _shishen_label(dm, DIZHI_WUXING.get(ly_zhi, "")),
            "quality":     quality,
            "summary":     _liunian_summary(dm, ly_gan, ly_zhi, quality),
            "warnings":    taisu["warnings"],
            "auspicious":  taisu["auspicious"],
            "tags":        taisu["tags"],
            "is_benming_chong": taisu["is_benming_chong"],
        })
    return result


def _liunian_summary(dm: str, ly_gan: str, ly_zhi: str, quality: str) -> str:
    ss_gan = _shishen_label(dm, ly_gan)
    wx_gan = TIANGAN_WUXING.get(ly_gan, "")
    if quality == "吉":
        return f"{ly_gan}{ly_zhi}年，{ss_gan}临运，五行{wx_gan}旺，诸事顺遂"
    elif quality == "凶":
        return f"{ly_gan}{ly_zhi}年，{ss_gan}临运，五行{wx_gan}克身，需谨慎行事"
    return f"{ly_gan}{ly_zhi}年，{ss_gan}临运，运势平稳，宜守成待时"


# ─────────────────────────────────────────────────────────────
# LiuYue (流月) — B-07 fixed: uses 旺/相/休/囚/死
# ─────────────────────────────────────────────────────────────

def calculate_liuyue(chart: Dict[str, Any], year: int,
                     liunian_gan: str) -> List[Dict[str, Any]]:
    """
    Calculate 12 monthly fortunes for a given LiuNian year.

    Month DiZhi sequence: 寅(1)卯(2)…丑(12)
    Month TianGan: calculated by 五虎遁年起月法 using the LiuNian year's TianGan.
    (B-06/B-07 fixed)
    """
    dm = chart["day_master"]
    dm_wx = TIANGAN_WUXING[dm]
    strength = chart.get("strength", "中和")

    month_dizhi_seq = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
    result = []

    for i, m_zhi in enumerate(month_dizhi_seq):
        m_gan = get_month_gan(liunian_gan, m_zhi)
        m_wx  = TIANGAN_WUXING[m_gan]
        # B-07 fix: use 旺/相/休/囚/死 for month season effect
        season_status = get_wuxing_strength(dm_wx, m_zhi)

        quality = _assess_quality(dm_wx, m_wx, strength)
        # Boost or reduce quality based on season
        if season_status == "旺":
            final_quality = "吉" if quality != "凶" else "平"
        elif season_status in ("囚", "死"):
            final_quality = "凶" if quality != "吉" else "平"
        else:
            final_quality = quality

        result.append({
            "month_num":    i + 1,
            "tiangan":      m_gan,
            "dizhi":        m_zhi,
            "shishen_gan":  _shishen_label(dm, m_gan),
            "season_status": season_status,
            "quality":      final_quality,
            "summary":      _liuyue_summary(m_gan, m_zhi, final_quality, season_status),
        })
    return result


def _liuyue_summary(m_gan: str, m_zhi: str, quality: str, status: str) -> str:
    if quality == "吉":
        return f"{m_gan}{m_zhi}月，日主{status}，月运顺畅"
    elif quality == "凶":
        return f"{m_gan}{m_zhi}月，日主{status}，月运有阻，宜低调"
    return f"{m_gan}{m_zhi}月，日主{status}，月运平稳"


# ─────────────────────────────────────────────────────────────
# 流日 (LiuRi) — Daily fortune
# ─────────────────────────────────────────────────────────────

def calculate_liuri(chart: Dict[str, Any], year: int, month: int,
                    liunian_gan: str) -> List[Dict[str, Any]]:
    """
    Calculate daily fortune for a given year-month.
    Day GanZhi uses the standard 60-cycle counting from a known anchor.
    """
    dm = chart["day_master"]
    dm_wx = TIANGAN_WUXING[dm]
    strength = chart.get("strength", "中和")

    import calendar
    days_in_month = calendar.monthrange(year, month)[1]

    # Anchor: 2000-01-07 = 甲子日 (cycle index 0)
    anchor = datetime(2000, 1, 7)
    result = []

    for d in range(1, days_in_month + 1):
        dt = datetime(year, month, d)
        delta = (dt - anchor).days
        idx = delta % 60
        d_gan, d_zhi = ganzhi_from_index(idx)
        d_wx = TIANGAN_WUXING[d_gan]
        quality = _assess_quality(dm_wx, d_wx, strength)

        result.append({
            "day":         d,
            "date":        f"{year}-{month:02d}-{d:02d}",
            "tiangan":     d_gan,
            "dizhi":       d_zhi,
            "shishen_gan": _shishen_label(dm, d_gan),
            "quality":     quality,
        })
    return result


# ─────────────────────────────────────────────────────────────
# 流时 (LiuShi) — Hourly fortune for a given day
# ─────────────────────────────────────────────────────────────

def calculate_liushi(chart: Dict[str, Any], year: int, month: int,
                     day: int) -> List[Dict[str, Any]]:
    """
    Calculate 12 two-hour period fortunes for a specific day.
    Hour TianGan calculated by 五鼠遁日起时法 using day's TianGan.
    """
    dm = chart["day_master"]
    dm_wx = TIANGAN_WUXING[dm]
    strength = chart.get("strength", "中和")

    # Get this day's GanZhi
    from core.constants import get_hour_gan
    anchor = datetime(2000, 1, 7)
    dt = datetime(year, month, day)
    delta = (dt - anchor).days
    idx = delta % 60
    d_gan, _ = ganzhi_from_index(idx)

    hour_dizhi = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    hour_ranges = [
        "23:00-01:00","01:00-03:00","03:00-05:00","05:00-07:00",
        "07:00-09:00","09:00-11:00","11:00-13:00","13:00-15:00",
        "15:00-17:00","17:00-19:00","19:00-21:00","21:00-23:00",
    ]

    result = []
    for i, h_zhi in enumerate(hour_dizhi):
        h_gan = get_hour_gan(d_gan, h_zhi)
        h_wx = TIANGAN_WUXING[h_gan]
        quality = _assess_quality(dm_wx, h_wx, strength)

        result.append({
            "hour_idx":    i,
            "tiangan":     h_gan,
            "dizhi":       h_zhi,
            "time_range":  hour_ranges[i],
            "shishen_gan": _shishen_label(dm, h_gan),
            "quality":     quality,
        })
    return result
