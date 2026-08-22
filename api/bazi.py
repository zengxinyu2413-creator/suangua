"""
api/bazi.py
===========
FastAPI router for all BaZi (八字) endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from models.common import ApiResponse
from models.bazi import (
    BaziRequest, FortuneRequest, CompatibilityRequest,
    BaziChartResponse, FortuneResponse, CompatibilityResponse, ApplicationResponse,
)
from core.bazi.chart import build_chart
from core.bazi.analyzer import analyze_chart
from core.bazi.forecaster import calculate_dayun, calculate_liunian, calculate_liuyue
from core.bazi.applications import (
    career_analysis, marriage_analysis, health_analysis, wealth_analysis,
)
from core.bazi.day_master_profiles import get_day_master_profile, analyze_yong_shen
from lunar_python import Lunar

router = APIRouter(prefix="/bazi", tags=["八字"])


def _lunar_to_solar(req: "BaziRequest") -> tuple[int, int, int]:
    """Convert lunar date to solar date using lunar_python.
    Returns (solar_year, solar_month, solar_day).
    If is_lunar=False, returns the original values unchanged.
    """
    if not req.is_lunar:
        return req.year, req.month, req.day
    # lunar_python: negative month = leap month
    lm = -req.month if req.is_leap_month else req.month
    try:
        lunar = Lunar.fromYmdHms(req.year, lm, req.day, req.hour, req.minute, 0)
        solar = lunar.getSolar()
        return solar.getYear(), solar.getMonth(), solar.getDay()
    except Exception as e:
        raise ValueError(f"农历转换失败 {req.year}年{req.month}月{req.day}日: {e}")


def _location_context(req: "BaziRequest") -> str:
    """Build a location string for AI context injection."""
    parts = []
    if req.province:
        parts.append(req.province)
    if req.city:
        parts.append(req.city)
    if parts:
        return "出生地：" + "·".join(parts)
    return ""


def _build_and_analyze(req: BaziRequest) -> dict:
    """Build chart + run full static analysis. Shared by multiple endpoints."""
    sy, sm, sd = _lunar_to_solar(req)

    # ── True solar time: pass city/longitude to build_chart ──
    city_str = None
    longitude = None
    if req.use_true_solar_time:
        city_str = (req.city or "") + (req.province or "")
        from core.bazi.chart import longitude_from_city
        longitude = longitude_from_city(city_str) if city_str else None

    chart = build_chart(sy, sm, sd, req.hour, req.minute,
                        longitude=longitude, city=city_str)
    analyze_chart(chart)
    chart["_gender"]   = req.gender
    chart["_is_lunar"] = req.is_lunar
    chart["_lunar_input"] = {
        "year": req.year, "month": req.month, "day": req.day,
        "is_leap": req.is_leap_month,
    } if req.is_lunar else None
    chart["_solar_birth"] = {"year": sy, "month": sm, "day": sd}
    loc = _location_context(req)
    if loc:
        chart["_location"] = loc
    return chart


@router.post("/chart", summary="排盘 — 生成四柱八字命盘")
async def get_chart(req: BaziRequest):
    """
    Build the Four Pillars chart with Ten Gods, pattern, strength,
    Shensha analysis, and B-1 relations (刑冲合害).
    """
    try:
        chart = _build_and_analyze(req)
        chart["day_master_profile"] = get_day_master_profile(chart["day_master"])
        chart["yong_shen"] = analyze_yong_shen(chart)

        # B-1: 地支刑冲合害自动检测
        try:
            from core.bazi.relations import analyze_all_relations
            chart["relations"] = analyze_all_relations(chart)
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # B-2: 特殊格局深度识别
        try:
            from core.bazi.special_patterns import detect_all_special_patterns
            chart["special_patterns"] = detect_all_special_patterns(chart)
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # D: 组合断（神煞组合 + 格局成破评断）
        try:
            from core.bazi.combos import bazi_combos
            chart["combos"] = bazi_combos(chart)
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 当前运程（大运流年并入主读盘 — 时间维度，供六件套织入）
        try:
            from core.bazi.current_fortune import build_current_fortune
            sb = chart.get("_solar_birth", {}) or {}
            cf = build_current_fortune(chart, req.gender, sb.get("year") or req.year)
            if cf.get("available"):
                chart["current_fortune"] = cf
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 全功能激活：事业/婚姻/财运/健康 各专域单点专断，一并随主读盘激活
        # （每问皆启动全部功能；专域结论供「综合论断」总汇合参）
        try:
            from core.bazi.applications import (
                career_analysis, marriage_analysis, wealth_analysis, health_analysis,
            )
            life_aspects = {}
            for name, fn in (("career", career_analysis), ("wealth", wealth_analysis),
                             ("health", health_analysis)):
                try:
                    life_aspects[name] = fn(chart)
                except Exception as _e1:
                    from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e1)
            try:
                life_aspects["marriage"] = marriage_analysis(chart, req.gender)
            except Exception as _e2:
                from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e2)
            if life_aspects:
                chart["life_aspects"] = life_aspects
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 命局总论（把各结构化结果编织成连贯叙述，置顶呈现）
        try:
            from core.bazi.overview import synthesize_overview
            ov = synthesize_overview(chart)
            if ov.get("available"):
                chart["overview"] = ov
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 命局力量综合推理链（子模块互助：日主旺衰×格局成破×用神调候×刑冲）
        try:
            from core.bazi.synthesis import synthesize_mingju
            mj = synthesize_mingju(chart)
            if mj.get("available"):
                chart["mingju_synthesis"] = mj
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 多视角整合：八字子模块编为六视角，确保尽其用、无孤儿
        try:
            from core.bazi.perspectives import build_perspectives
            pv = build_perspectives(chart)
            if pv.get("available"):
                chart["perspectives"] = pv
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 命局一致性审核（确定性层）：核查跨模块矛盾，AI 审定层前端按需调用
        try:
            from core.bazi.consistency_audit import audit_consistency
            ca = audit_consistency(chart)
            if ca.get("available"):
                chart["consistency_audit"] = ca
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 传统断语（古籍原文层：调候/滴天髓/子平真诠，原仅入 AI，现示于用户）
        try:
            from core.bazi.classical import collect_classical_statements
            cs = collect_classical_statements(chart)
            if cs.get("available"):
                chart["classical_statements"] = cs
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        # 综合论断（总汇合参 — 全功能激活后的最终汇总：命局×各专域×运程）
        try:
            from core.bazi.master_synthesis import build_master_synthesis
            ms = build_master_synthesis(chart)
            if ms.get("available"):
                chart["master_synthesis"] = ms
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        return ApiResponse(success=True, data=chart)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fortune", summary="运势 — 大运流年流月流日流时预测")
async def get_fortune(req: FortuneRequest):
    """
    Calculate DaYun (10-year cycles), LiuNian (yearly), LiuYue (monthly),
    LiuRi (daily), and LiuShi (hourly) fortune.
    """
    try:
        birth = req.birth
        chart = _build_and_analyze(birth)

        dayun = calculate_dayun(chart, birth.gender, birth.year)

        from_yr = req.query_year or birth.year
        to_yr   = (req.query_year or birth.year) + 20
        liunian = calculate_liunian(chart, birth.gender, birth.year,
                                    from_yr, to_yr)

        # D: 岁运组合断 —— 为每个流年匹配其所属大运，析岁运并临/相战/引动
        try:
            from core.bazi.combos import analyze_suiyun
            def _dayun_of(year: int):
                for d in dayun:
                    if d.get("start_year", 0) <= year < d.get("end_year", 0):
                        return d
                return dayun[-1] if dayun else None
            for ly in liunian:
                d = _dayun_of(ly["year"])
                if d:
                    ly["suiyun"] = analyze_suiyun(
                        chart, d["tiangan"], d["dizhi"], ly["tiangan"], ly["dizhi"])
                    # 逐年组合断（完整十神+喜忌+应事+大运组合）
                    try:
                        from core.bazi.combos import analyze_liunian_combo
                        ly["liunian_combo"] = analyze_liunian_combo(
                            chart, d["tiangan"], d["dizhi"], ly["tiangan"], ly["dizhi"])
                        # 回填空的 shishen_zhi
                        if not ly.get("shishen_zhi") and ly["liunian_combo"].get("shishen_zhi"):
                            ly["shishen_zhi"] = ly["liunian_combo"]["shishen_zhi"]
                    except Exception as _e3:
                        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e3)
        except Exception as _e:
            from core.log import log_failure; log_failure("bazi", "装配六件套/总汇", _e)

        liuyue = None
        liuri = None
        liushi = None

        if req.query_year:
            from core.calendar.ganzhi import ganzhi_from_index
            ly_idx = (req.query_year - 1984) % 60
            ly_gan, ly_zhi = ganzhi_from_index(ly_idx)
            liuyue = calculate_liuyue(chart, req.query_year, ly_gan)

            # 流月逐期组合断（parent = 流年）
            try:
                from core.bazi.combos import analyze_period_combo
                for lm in (liuyue or []):
                    lm["combo"] = analyze_period_combo(
                        chart, ly_gan, ly_zhi, lm["tiangan"], lm["dizhi"],
                        label="流月", parent_label="流年")
                    if not lm.get("shishen_zhi") and lm["combo"].get("shishen_zhi"):
                        lm["shishen_zhi"] = lm["combo"]["shishen_zhi"]
            except Exception as _e4:
                from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e4)

            if req.query_month:
                from core.bazi.forecaster import calculate_liuri, calculate_liushi
                liuri = calculate_liuri(chart, req.query_year, req.query_month, ly_gan)

                # 流日逐期组合断（parent = 该月流月）
                try:
                    from core.bazi.combos import analyze_period_combo
                    pm = next((m for m in (liuyue or [])
                               if m.get("month_num") == req.query_month), None)
                    pm_gan = pm["tiangan"] if pm else ly_gan
                    pm_zhi = pm["dizhi"] if pm else ly_zhi
                    for ld in (liuri or []):
                        ld["combo"] = analyze_period_combo(
                            chart, pm_gan, pm_zhi, ld["tiangan"], ld["dizhi"],
                            label="流日", parent_label="流月")
                        if not ld.get("shishen_zhi") and ld["combo"].get("shishen_zhi"):
                            ld["shishen_zhi"] = ld["combo"]["shishen_zhi"]
                except Exception as _e5:
                    from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e5)

                if req.query_day:
                    liushi = calculate_liushi(chart, req.query_year, req.query_month, req.query_day)
                    # 流时逐期组合断（parent = 该日流日）
                    try:
                        from core.bazi.combos import analyze_period_combo
                        pd = next((x for x in (liuri or [])
                                   if x.get("day") == req.query_day), None)
                        pd_gan = pd["tiangan"] if pd else None
                        pd_zhi = pd["dizhi"] if pd else None
                        for lh in (liushi or []):
                            lh["combo"] = analyze_period_combo(
                                chart, pd_gan, pd_zhi, lh["tiangan"], lh["dizhi"],
                                label="流时", parent_label="流日")
                            if not lh.get("shishen_zhi") and lh["combo"].get("shishen_zhi"):
                                lh["shishen_zhi"] = lh["combo"]["shishen_zhi"]
                    except Exception as _e6:
                        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e6)

        data = {
            "dayun":   dayun,
            "liunian": liunian,
            "liuyue":  liuyue,
            "liuri":   liuri,
            "liushi":  liushi,
        }
        return ApiResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/career", summary="事业 — 职业方向分析")
async def get_career(req: BaziRequest):
    try:
        chart = _build_and_analyze(req)
        result = career_analysis(chart)
        profile = get_day_master_profile(chart["day_master"])
        result["profile_career"] = profile.get("career", {})
        result["personality_traits"] = profile.get("strengths", [])
        result["weaknesses"] = profile.get("weaknesses", [])
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/marriage", summary="婚姻 — 感情婚姻分析")
async def get_marriage(req: BaziRequest):
    try:
        chart = _build_and_analyze(req)
        result = marriage_analysis(chart, req.gender)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/health", summary="健康 — 身体健康分析")
async def get_health(req: BaziRequest):
    try:
        chart = _build_and_analyze(req)
        result = health_analysis(chart)
        profile = get_day_master_profile(chart["day_master"])
        result["profile_health"] = profile.get("health", {})
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/wealth", summary="财运 — 财富潜力分析")
async def get_wealth(req: BaziRequest):
    try:
        chart = _build_and_analyze(req)
        result = wealth_analysis(chart)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compatibility", summary="合婚 — 八字合婚分析")
async def get_compatibility(req: CompatibilityRequest):
    """Compare two BaZi charts for relationship compatibility."""
    try:
        chart_a = _build_and_analyze(req.person_a)
        chart_b = _build_and_analyze(req.person_b)

        # Simple compatibility: compare wuxing balance
        from core.constants import WUXING_SHENG, WUXING_KE, TIANGAN_WUXING
        wx_a = TIANGAN_WUXING[chart_a["day_master"]]
        wx_b = TIANGAN_WUXING[chart_b["day_master"]]

        if WUXING_SHENG.get(wx_a) == wx_b or WUXING_SHENG.get(wx_b) == wx_a:
            score, summary = 85, f"五行相生（{wx_a}生{wx_b}），婚配和谐，相互扶持"
        elif wx_a == wx_b:
            score, summary = 70, "五行同类，志同道合，需注意各自独立空间"
        elif WUXING_KE.get(wx_a) == wx_b or WUXING_KE.get(wx_b) == wx_a:
            score, summary = 55, "五行相克，性格差异较大，需多磨合包容"
        else:
            score, summary = 75, "五行平衡，婚配较好，相互补充"

        return ApiResponse(success=True, data={
            "score": score,
            "summary": summary,
            "person_a": {"day_master": chart_a["day_master"],
                         "pattern":    chart_a.get("pattern", "")},
            "person_b": {"day_master": chart_b["day_master"],
                         "pattern":    chart_b.get("pattern", "")},
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chenggu", summary="称骨 — 袁天罡称骨算命")
async def get_chenggu(req: BaziRequest):
    """Calculate bone weight fortune using Yuan Tiangang method."""
    try:
        sy, sm, sd = _lunar_to_solar(req)
        chart = build_chart(sy, sm, sd, req.hour, req.minute)
        from core.bazi.chenggu import calculate_chenggu
        from core.constants import hour_to_dizhi
        year_gz = chart["year_pillar"]["tiangan"] + chart["year_pillar"]["dizhi"]
        h_zhi = hour_to_dizhi(req.hour)
        lunar_month = req.month if req.is_lunar else sm  # approximate
        lunar_day = req.day if req.is_lunar else sd
        result = calculate_chenggu(year_gz, lunar_month, lunar_day, h_zhi)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reverse", summary="反查 — 八字反查出生日期")
async def reverse_bazi(req: dict):
    """Find birth dates matching given GanZhi pillars."""
    try:
        from core.bazi.reverse_lookup import quick_reverse, reverse_lookup
        year_gz = req.get("year_gz", "")
        day_gz = req.get("day_gz", "")
        month_gz = req.get("month_gz")
        hour_gz = req.get("hour_gz")
        yr = (int(req.get("from_year", 1960)), int(req.get("to_year", 2030)))
        
        if day_gz and not month_gz and not hour_gz:
            results = quick_reverse(year_gz, day_gz, yr)
        else:
            results = reverse_lookup(year_gz, month_gz, day_gz, hour_gz, yr)
        return ApiResponse(success=True, data={"matches": results, "count": len(results)})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
