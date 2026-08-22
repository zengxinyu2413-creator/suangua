"""
api/ziwei.py
============
FastAPI router for Zi Wei Dou Shu (紫微斗数) endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from models.common import ApiResponse
from core.ziwei.chart import build_ziwei_chart, calculate_feihua, get_palace_three_directions

router = APIRouter(prefix="/ziwei", tags=["紫微斗数"])

# Hour index reference (0=子时 … 11=亥时, each covers 2 hours)
HOUR_MAP = {
    "子时(23-1)": 0, "丑时(1-3)": 1, "寅时(3-5)": 2,  "卯时(5-7)": 3,
    "辰时(7-9)": 4,  "巳时(9-11)": 5, "午时(11-13)": 6, "未时(13-15)": 7,
    "申时(15-17)": 8,"酉时(17-19)": 9,"戌时(19-21)": 10,"亥时(21-23)": 11,
}


class ZiWeiRequest(BaseModel):
    year:   int  = Field(..., ge=1800, le=2100, description="出生年")
    month:  int  = Field(..., ge=1, le=12)
    day:    int  = Field(..., ge=1, le=31)
    hour:   int  = Field(..., ge=0, le=23, description="出生小时（0-23，24小时制）")
    minute: int  = Field(0, ge=0, le=59, description="出生分钟（可选，用于真太阳时校正）")
    gender: str  = Field("男", description="男 | 女")
    name:   Optional[str] = None
    is_lunar:      bool = Field(True,  description="输入日期为农历（默认）")
    is_leap_month: bool = Field(False, description="农历闰月")
    longitude: Optional[float] = Field(None, description="出生地经度（用于真太阳时校正）")
    sect:   int  = Field(1, ge=1, le=2, description="八字派别: 1=节气派(默认) 2=非节气派")

    def to_solar_date(self) -> str:
        """Convert input date to solar date string for iztro."""
        if not self.is_lunar:
            return f"{self.year}-{self.month}-{self.day}"
        try:
            from lunar_python import Lunar
            lm = -self.month if self.is_leap_month else self.month
            sol = Lunar.fromYmdHms(self.year, lm, self.day, self.hour, 0, 0).getSolar()
            return f"{sol.getYear()}-{sol.getMonth()}-{sol.getDay()}"
        except Exception:
            return f"{self.year}-{self.month}-{self.day}"  # fallback

    def to_hour_index(self, apply_solar_time: bool = True) -> int:
        """
        Convert 24h hour to ziwei time index (0=子 … 11=亥).
        Each time slot is [start, start+2) — 含起始整点，不含结束整点。
        例如 hour=5 应为卯时（5:00-7:00），不是寅时。
        
        当 apply_solar_time=True 且 longitude 不为 None 时，先做真太阳时校正：
          - 北京时区中心 120°E，每经度差 4 分钟
          - 西部经度（如成都 104°E）真太阳时比钟表晚约 64 分钟
          - 这可能让时辰从「卯时 5:30」变为「寅时 04:26」
        
        紫微古法以"真太阳时"为准，钟表时间是民国后的人造时间，
        必须校正到出生地实际太阳位置对应的时辰。
        """
        h = self.hour
        m = self.minute or 0
        
        # 真太阳时校正
        if apply_solar_time and self.longitude is not None:
            offset_min = (self.longitude - 120.0) * 4
            total = h * 60 + m + offset_min
            # 处理跨日（极少出现，但要正确）
            total = total % (24 * 60)
            h = int(total // 60)
            m = int(total % 60)
        
        if h == 23 or h == 0: return 0  # 子时 23:00-01:00
        if h in (1, 2):       return 1  # 丑时 01:00-03:00
        if h in (3, 4):       return 2  # 寅时 03:00-05:00
        if h in (5, 6):       return 3  # 卯时 05:00-07:00
        if h in (7, 8):       return 4  # 辰时 07:00-09:00
        if h in (9, 10):      return 5  # 巳时 09:00-11:00
        if h in (11, 12):     return 6  # 午时 11:00-13:00
        if h in (13, 14):     return 7  # 未时 13:00-15:00
        if h in (15, 16):     return 8  # 申时 15:00-17:00
        if h in (17, 18):     return 9  # 酉时 17:00-19:00
        if h in (19, 20):     return 10 # 戌时 19:00-21:00
        if h in (21, 22):     return 11 # 亥时 21:00-23:00
        return 0  # 兜底


def _norm_gender(g) -> str:
    """归一化性别：男/女 与 male/female/man/woman/m/f 皆可，未知方默认男。
    修复：旧逻辑 `g if g in ('男','女') else '男'` 会把合法的 'female' 误判为男。"""
    s = str(g or "").strip().lower()
    if s in ("女", "female", "woman", "f", "girl", "lady"):
        return "女"
    if s in ("男", "male", "man", "m", "boy"):
        return "男"
    # 兼容原始中文（未小写化匹配到时）
    if str(g).strip() == "女":
        return "女"
    return "男"


@router.post("/chart", summary="紫微斗数排盘")
async def ziwei_chart(req: ZiWeiRequest):
    """Generate a complete Zi Wei Dou Shu astrolabe."""
    try:
        gender = _norm_gender(req.gender)
        result = build_ziwei_chart(
            solar_date=req.to_solar_date(),
            birth_hour_index=req.to_hour_index(),
            gender=gender,
        )
        # ── 飞化+三方四正 ────────────────────────────────────────────────
        try:
            result["feihua"] = calculate_feihua(result["palaces"])
            soul_idx = next((p["index"] for p in result["palaces"] if p.get("is_soul")), 0)
            body_idx = next((p["index"] for p in result["palaces"] if p.get("is_body")), 0)
            result["sanjiao_analysis"] = get_palace_three_directions(
                soul_idx, result["palaces"], result["feihua"]
            )
            # 关键：暴露命宫/身宫索引到 metadata，前端 InsightsBar 等组件依赖
            if "metadata" in result:
                result["metadata"]["soul_palace_index"] = soul_idx
                result["metadata"]["body_palace_index"] = body_idx
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # ── 八字大运/十神/真太阳时 ─────────────────────────────────────
        try:
            from core.ziwei.chart import build_bazi_overlay, build_time_panel
            from datetime import datetime
            # 用钟表时间（取时辰中点，hour=req.hour 不可靠时用 to_hour_index 推算）
            clock_hour = req.hour if 0 <= req.hour <= 23 else 0
            longitude = getattr(req, "longitude", None)
            result["bazi_overlay"] = build_bazi_overlay(
                solar_date=req.to_solar_date(),
                hour=clock_hour,
                minute=getattr(req, "minute", 0) or 0,
                gender=gender,
                longitude=longitude,
            )
            # 流月/流日/流时表
            current_year = datetime.now().year
            result["time_panel"] = build_time_panel(req.to_solar_date(), current_year)
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # ── insights：Z-2 飞化语象 + Z-3 评级 + Z-4 格局（前端 polish 用） ──
        # 注意：失败不影响主返回；前端检测到 insights 字段才渲染
        try:
            from core.ziwei.context_builder import find_soul_palace, get_san_fang_si_zheng
            insights = {}
            palaces = result.get("palaces") or []
            soul_p = find_soul_palace(palaces)

            # Z-3 命格评级
            try:
                from core.ziwei.brightness import compute_mingge_overall_rating
                if soul_p is not None:
                    sfsz = get_san_fang_si_zheng(palaces, soul_p.get("index", -1))
                    rating = compute_mingge_overall_rating(soul_p, sfsz)
                    # 仅取前端要用的字段，避免响应臃肿
                    insights["rating"] = {
                        "overall":        rating.get("overall_rating"),
                        "score":          rating.get("average_score"),
                        "summary":        rating.get("summary"),
                        "soul_rating":    rating.get("soul_palace_score", {}).get("rating"),
                        "soul_average":   rating.get("soul_palace_score", {}).get("average"),
                        "soul_stars":     rating.get("soul_palace_score", {}).get("major_stars"),
                        # 庙旺/失陷主星完整统计（基于亮度阈值）
                        "bright_in_sfsz": rating.get("bright_in_sfsz", []),
                        "fallen_in_sfsz": rating.get("fallen_in_sfsz", []),
                        "sfsz_brief": [
                            {
                                "palace":     s.get("palace_name"),
                                "branch":     s.get("branch"),
                                "stars":      s.get("major_stars"),
                                "rating":     s.get("rating"),
                                "score":      s.get("average"),
                            }
                            for s in rating.get("sfsz_scores", [])
                        ],
                        "star_notes":     rating.get("star_notes", [])[:10],
                    }
            except Exception as _e1:
                from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e1)

            # Z-4 格局检测
            try:
                from core.ziwei.pattern_detector import detect_all_patterns
                patterns = detect_all_patterns(palaces, birth_hour_index=req.to_hour_index())
                insights["patterns"] = {
                    "good":  [
                        {
                            "name":              p.get("name"),
                            "category":          p.get("category"),
                            "evidence":          p.get("evidence", []),
                            "meaning":           p.get("meaning"),
                            "break_conditions":  p.get("break_conditions", []),
                            "is_partial":        p.get("is_partial", False),
                        }
                        for p in patterns.get("good_patterns", [])
                    ],
                    "bad":   [
                        {
                            "name":              p.get("name"),
                            "category":          p.get("category"),
                            "evidence":          p.get("evidence", []),
                            "meaning":           p.get("meaning"),
                            "break_conditions":  p.get("break_conditions", []),
                        }
                        for p in patterns.get("bad_patterns", [])
                    ],
                    "total": patterns.get("total_count", 0),
                }
            except Exception as e:
                import traceback
                print(f"[ziwei API] patterns 异常: {e}")
                traceback.print_exc()

            # Z-2 飞化关键警示（汇总，不包含全 12 宫详情）
            try:
                from core.ziwei.feihua_advanced import (
                    analyze_palace_feihua, summarize_feihua_landscape,
                )
                feihua_records = analyze_palace_feihua(palaces, school="zhongzhou")
                summary = summarize_feihua_landscape(feihua_records, palaces)
                insights["feihua_summary"] = {
                    "quality_changes":     summary.get("key_quality_changes", []),
                    "double_ji":           summary.get("double_ji", []),
                    "lu_jie_ji":           summary.get("lu_jie_ji", []),
                    "lu_ji_war":           summary.get("lu_ji_war", []),
                    "soul_incoming":       summary.get("soul_palace_incoming", []),
                    "soul_chong":          summary.get("soul_palace_chong", []),
                    "self_out_palaces":    summary.get("self_out_palaces", []),
                    "self_in_palaces":     summary.get("self_in_palaces", []),
                    "concentration":       summary.get("concentration", {}),
                }

                # 每宫的详细飞化数据（按 palace_idx 索引）— 用于"宫位详情面板"
                # 不包含原始 records 全部冗余字段，只取前端要用的
                insights["feihua_by_palace"] = {
                    str(r["palace_idx"]): {
                        "palace_idx":       r["palace_idx"],
                        "palace_name":      r["palace_name"],
                        "stem":             r["stem"],
                        "branch":           r["branch"],
                        "opp_palace_name":  r["opp_palace_name"],
                        # 4 化象的轻量版本（去掉 natal_overlap、tags 的冗余）
                        "transformations": [
                            {
                                "hua_type":             tr["hua_type"],
                                "target_star":          tr["target_star"],
                                "target_palace_name":   tr["target_palace_name"],
                                "target_palace_idx":    tr["target_palace_idx"],
                                "fh_type":              tr["fh_type"],
                                "is_inner":             tr["is_inner"],
                                "chong_palace":         tr["chong_palace"],
                                "is_he_won_ji":         tr["is_he_won_ji"],
                                "is_double_ji":         tr["is_double_ji"],
                                "is_lu_ji_war":         tr["is_lu_ji_war"],
                                "is_quality_change":    tr["is_quality_change"],
                                "interpretation":       tr["interpretation"],
                            }
                            for tr in r["transformations"]
                        ],
                        "self_out_count":   r["self_out_count"],
                        "self_in_count":    r["self_in_count"],
                        "fly_out_count":    r["fly_out_count"],
                        "incoming_count":   r["incoming_count"],
                        "incoming_list":    r["incoming_list"],
                    }
                    for r in feihua_records
                }

                # Z-8 冲宫连锁分析（仅本命层，因为 /chart 没大限/流年数据）
                try:
                    from core.ziwei.chong_analysis import analyze_chong_chains
                    chains = analyze_chong_chains(palaces, feihua_records)
                    insights["chong_chains"] = {
                        "total":           chains["total"],
                        "events":          chains["events"][:30],  # 限 30 条防臃肿
                        "top_warnings":    chains["top_warnings"][:8],
                        "key_palaces_hit": chains["key_palaces_hit"],
                    }
                except Exception as _e2:
                    from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e2)
            except Exception as _e3:
                from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e3)

            if insights:
                result["insights"] = insights
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 飞星派论命起手：生年四化盘 + 来因宫
        try:
            from core.ziwei.birth_sihua import build_birth_sihua_panel
            bsp = build_birth_sihua_panel(result)
            if bsp.get("available"):
                result["birth_sihua"] = bsp
                # 飞化链路多步串联（互化/化忌连环/化禄流通/焦点/生年串联）
                try:
                    from core.ziwei.feihua_chain import analyze_feihua_chains
                    fc = analyze_feihua_chains(result, bsp)
                    if fc.get("available"):
                        result["feihua_chains"] = fc
                except Exception as _e4:
                    from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e4)
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 当前运限（大限流年并入主读盘 — 时间维度，供六件套织入）
        try:
            from core.ziwei.current_fortune import build_ziwei_current_fortune
            cf = build_ziwei_current_fortune(result, req.year)
            if cf.get("available"):
                result["current_fortune"] = cf
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 命盘总论合成（综合总论层：立命主星×命格评定×格局×三方四正×身宫命主）
        try:
            from core.ziwei.overview import synthesize_overview
            ov = synthesize_overview(result)
            if ov.get("available"):
                result["overview"] = ov
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 命格力量综合推理链（子模块互助：主星庙旺×三方明暗×格局×煞星×四化）
        try:
            from core.ziwei.synthesis import synthesize_mingge
            mg = synthesize_mingge(result)
            if mg.get("available"):
                result["mingge_synthesis"] = mg
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 多视角整合：紫微子模块编为六视角，确保尽其用、无孤儿
        try:
            from core.ziwei.perspectives import build_perspectives
            pv = build_perspectives(result)
            if pv.get("available"):
                result["perspectives"] = pv
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 命盘一致性审核（确定性层）：核查跨模块矛盾，AI 审定层前端按需调用
        try:
            from core.ziwei.consistency_audit import audit_consistency
            ca = audit_consistency(result)
            if ca.get("available"):
                result["consistency_audit"] = ca
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 传统断语（古籍层：命宫主星《紫微斗数全书》深度释义 + 格局典籍）
        try:
            from core.ziwei.classical import collect_classical_statements
            cs = collect_classical_statements(result)
            if cs.get("available"):
                result["classical_statements"] = cs
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        # 综合论断（总汇合参 — 全功能激活后的最终汇总：命格×各要宫×行运）
        try:
            from core.ziwei.master_synthesis import build_ziwei_master_synthesis
            ms = build_ziwei_master_synthesis(result)
            if ms.get("available"):
                result["master_synthesis"] = ms
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hours", summary="时辰对照表")
async def hour_table():
    """Return the 12 Chinese hours with clock-time ranges."""
    hours = [
        {"index": 0,  "name": "子时", "range": "23:00–01:00", "clock": [23, 0]},
        {"index": 1,  "name": "丑时", "range": "01:00–03:00", "clock": [1, 2]},
        {"index": 2,  "name": "寅时", "range": "03:00–05:00", "clock": [3, 4]},
        {"index": 3,  "name": "卯时", "range": "05:00–07:00", "clock": [5, 6]},
        {"index": 4,  "name": "辰时", "range": "07:00–09:00", "clock": [7, 8]},
        {"index": 5,  "name": "巳时", "range": "09:00–11:00", "clock": [9, 10]},
        {"index": 6,  "name": "午时", "range": "11:00–13:00", "clock": [11, 12]},
        {"index": 7,  "name": "未时", "range": "13:00–15:00", "clock": [13, 14]},
        {"index": 8,  "name": "申时", "range": "15:00–17:00", "clock": [15, 16]},
        {"index": 9,  "name": "酉时", "range": "17:00–19:00", "clock": [17, 18]},
        {"index": 10, "name": "戌时", "range": "19:00–21:00", "clock": [19, 20]},
        {"index": 11, "name": "亥时", "range": "21:00–23:00", "clock": [21, 22]},
    ]
    return ApiResponse(success=True, data=hours)


@router.post("/triple", summary="三盘叠合 — 本命+大限+流年")
async def triple_chart(req: dict):
    """Calculate the full triple-plate (三盘叠合) analysis."""
    try:
        from core.ziwei.chart import calculate_triple_chart
        # Accept both formats
        if "solar_date" in req:
            solar_date = req["solar_date"]
            hour_index = int(req.get("hour_index", 4))
        else:
            tmp = ZiWeiRequest(
                year=int(req.get("year",1990)), month=int(req.get("month",1)),
                day=int(req.get("day",1)), hour=int(req.get("hour",12)),
                gender=_norm_gender(req.get("gender")),
                is_lunar=req.get("is_lunar", True),
                is_leap_month=req.get("is_leap_month", False),
            )
            solar_date = tmp.to_solar_date()
            hour_index = tmp.to_hour_index()
        gender = _norm_gender(req.get("gender"))
        age = int(req.get("age", 30))
        # current_year 默认值用当前年份，确保 annual 总是有数据
        from datetime import datetime
        current_year = int(req.get("current_year", 0)) or datetime.now().year
        result = calculate_triple_chart(solar_date, hour_index, gender, age, current_year)
        natal = result.get("natal_chart") or {}
        result.pop("natal_chart", None)

        # ── overlay_insights（Z-6 增强）：把大限/流年飞化按落点 palace 索引化 ──
        # 让前端 PalaceDetailPanel 在大限/三盘视图下能为每宫显示对应层的飞化
        try:
            from core.ziwei.feihua_advanced import analyze_overlay_feihua
            palaces = natal.get("palaces") or []
            decade_info = result.get("decade_info") or {}
            decade_palace_idx = decade_info.get("palace_idx")
            decade_stem = decade_info.get("stem")
            current_year_value = result.get("current_year")

            decade_overlay_record = None
            annual_overlay_record = None

            if palaces and decade_stem and decade_palace_idx is not None:
                decade_overlay_record = analyze_overlay_feihua(
                    palaces=palaces,
                    overlay_stem=decade_stem,
                    overlay_palace_idx=int(decade_palace_idx),
                    overlay_label="大限",
                    school="zhongzhou",
                )

            if palaces and current_year_value:
                try:
                    from core.constants import TIANGAN
                    year_stem = TIANGAN[(int(current_year_value) - 1984) % 10]
                except Exception:
                    year_stem = ""
                soul_idx = next((p["index"] for p in palaces if p.get("is_soul")), 0)
                if year_stem:
                    annual_overlay_record = analyze_overlay_feihua(
                        palaces=palaces,
                        overlay_stem=year_stem,
                        overlay_palace_idx=int(soul_idx),
                        overlay_label=f"流年{current_year_value}",
                        school="zhongzhou",
                    )

            # 按落点 palace_idx 索引飞化象
            def index_by_target(record):
                if not record:
                    return {}
                indexed = {}
                for tr in record.get("transformations", []):
                    target_idx = tr.get("target_palace_idx", -1)
                    if target_idx < 0:
                        continue
                    indexed.setdefault(str(target_idx), []).append({
                        "hua_type":           tr["hua_type"],
                        "target_star":        tr["target_star"],
                        "target_palace_name": tr["target_palace_name"],
                        "fh_type":            tr["fh_type"],
                        "is_inner":           tr["is_inner"],
                        "chong_palace":       tr["chong_palace"],
                        "is_he_won_ji":       tr["is_he_won_ji"],
                        "is_double_ji":       tr["is_double_ji"],
                        "is_lu_ji_war":       tr["is_lu_ji_war"],
                        "interpretation":     tr["interpretation"],
                    })
                return indexed

            # 流年命宫的本命 idx：按流年地支查找
            # 流年地支 = current_year 的地支（如 2026 = 丙午 → 午）
            annual_palace_idx_in_natal = None
            if palaces and current_year_value:
                try:
                    from core.constants import DIZHI
                    year_branch = DIZHI[(int(current_year_value) - 1984) % 12]
                    for p in palaces:
                        if p.get("earthly_branch") == year_branch:
                            annual_palace_idx_in_natal = p["index"]
                            break
                except Exception as _e5:
                    from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e5)

            # 大限十二宫和流年十二宫 layout（重排）
            from core.ziwei.chart import (
                compute_decade_palaces_layout, compute_annual_palaces_layout
            )
            decade_layout = None
            annual_layout = None
            if decade_palace_idx is not None:
                decade_layout = compute_decade_palaces_layout(int(decade_palace_idx))
            if annual_palace_idx_in_natal is not None:
                annual_layout = compute_annual_palaces_layout(annual_palace_idx_in_natal)

            result["overlay_insights"] = {
                "decade": {
                    "stem":           decade_overlay_record.get("overlay_stem") if decade_overlay_record else None,
                    "palace_name":    decade_overlay_record.get("overlay_palace_name") if decade_overlay_record else None,
                    "palace_idx":     decade_overlay_record.get("overlay_palace_idx") if decade_overlay_record else None,
                    "key_warnings":   decade_overlay_record.get("key_warnings", []) if decade_overlay_record else [],
                    "by_target_idx":  index_by_target(decade_overlay_record),
                    "transformations": decade_overlay_record.get("transformations", []) if decade_overlay_record else [],
                    "palaces_layout": decade_layout,
                } if decade_overlay_record else None,
                "annual": {
                    "stem":           annual_overlay_record.get("overlay_stem") if annual_overlay_record else None,
                    "year":           current_year_value,
                    "palace_idx":     annual_palace_idx_in_natal,
                    "palace_name":    annual_overlay_record.get("overlay_palace_name") if annual_overlay_record else None,
                    "key_warnings":   annual_overlay_record.get("key_warnings", []) if annual_overlay_record else [],
                    "by_target_idx":  index_by_target(annual_overlay_record),
                    "transformations": annual_overlay_record.get("transformations", []) if annual_overlay_record else [],
                    "palaces_layout": annual_layout,
                } if annual_overlay_record else None,
            }

            # Z-8 三层冲宫连锁分析（natal + decade + annual）
            try:
                from core.ziwei.chong_analysis import analyze_chong_chains
                from core.ziwei.feihua_advanced import analyze_palace_feihua as _ana
                natal_records = _ana(palaces, school="zhongzhou")
                chains = analyze_chong_chains(
                    palaces, natal_records,
                    decade_overlay_record=decade_overlay_record,
                    annual_overlay_record=annual_overlay_record,
                    decade_layout=decade_layout,
                    annual_layout=annual_layout,
                )
                result["chong_chains"] = {
                    "total":           chains["total"],
                    "events":          chains["events"][:40],
                    "top_warnings":    chains["top_warnings"][:10],
                    "key_palaces_hit": chains["key_palaces_hit"],
                }
            except Exception as _e6:
                from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e6)

            # 大限 / 流年 飞化链路多步串联
            try:
                from core.ziwei.feihua_chain import analyze_layer_feihua_chains
                from core.ziwei.birth_sihua import build_birth_sihua_panel
                chart_for_chain = {"palaces": palaces, "metadata": result.get("metadata", {})}
                bsp = build_birth_sihua_panel(chart_for_chain)
                bsp = bsp if bsp.get("available") else None
                dfc = analyze_layer_feihua_chains(chart_for_chain, "大限", birth_sihua=bsp)
                if dfc.get("available"):
                    result["decade_feihua_chains"] = dfc
                _GAN = "甲乙丙丁戊己庚辛壬癸"
                if current_year_value:
                    ys = _GAN[(int(current_year_value) - 4) % 10]
                    afc = analyze_layer_feihua_chains(
                        chart_for_chain, "流年", year_stem=ys, birth_sihua=bsp)
                    if afc.get("available"):
                        result["annual_feihua_chains"] = afc
            except Exception as _e7:
                from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e7)
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/decade", summary="大限四化 — 大限命宫飞化")  
async def decade_feihua(req: dict):
    """Calculate decadal flying transformations."""
    try:
        from core.ziwei.chart import (
            build_ziwei_chart, get_decade_palace, calculate_decade_feihua
        )
        # Accept both formats: {solar_date, hour_index} or {year, month, day, hour}
        if "solar_date" in req:
            solar_date = req["solar_date"]
            hour_index = int(req.get("hour_index", 4))
        else:
            # Convert from form fields
            tmp = ZiWeiRequest(
                year=int(req.get("year",1990)), month=int(req.get("month",1)),
                day=int(req.get("day",1)), hour=int(req.get("hour",12)),
                gender=_norm_gender(req.get("gender")),
                is_lunar=req.get("is_lunar", True),
                is_leap_month=req.get("is_leap_month", False),
            )
            solar_date = tmp.to_solar_date()
            hour_index = tmp.to_hour_index()
        gender = _norm_gender(req.get("gender"))
        age = int(req.get("age", 30))
        decade = get_decade_palace(solar_date, hour_index, gender, age)
        if not decade:
            raise HTTPException(status_code=400, detail="无法找到对应大限宫位")
        chart = build_ziwei_chart(solar_date, hour_index, gender)
        decade_fh = calculate_decade_feihua(chart["palaces"], decade["stem"], decade["palace_idx"])

        # ── Z-6: 大限层 by_target_idx 索引化（让 PalaceDetailPanel 在 layer='decade' 时显示） ──
        overlay_insights = None
        try:
            from core.ziwei.feihua_advanced import analyze_overlay_feihua
            rec = analyze_overlay_feihua(
                palaces=chart["palaces"],
                overlay_stem=decade["stem"],
                overlay_palace_idx=int(decade["palace_idx"]),
                overlay_label="大限",
                school="zhongzhou",
            )
            by_target = {}
            for tr in rec.get("transformations", []):
                tidx = tr.get("target_palace_idx", -1)
                if tidx < 0:
                    continue
                by_target.setdefault(str(tidx), []).append({
                    "hua_type":           tr["hua_type"],
                    "target_star":        tr["target_star"],
                    "target_palace_name": tr["target_palace_name"],
                    "fh_type":            tr["fh_type"],
                    "is_inner":           tr["is_inner"],
                    "chong_palace":       tr["chong_palace"],
                    "is_he_won_ji":       tr["is_he_won_ji"],
                    "is_double_ji":       tr["is_double_ji"],
                    "is_lu_ji_war":       tr["is_lu_ji_war"],
                    "interpretation":     tr["interpretation"],
                })
            overlay_insights = {
                "decade": {
                    "stem":            rec.get("overlay_stem"),
                    "palace_name":     rec.get("overlay_palace_name"),
                    "palace_idx":      rec.get("overlay_palace_idx"),
                    "key_warnings":    rec.get("key_warnings", []),
                    "by_target_idx":   by_target,
                    "transformations": rec.get("transformations", []),
                    "palaces_layout":  decade.get("palaces_layout"),
                },
                "annual": None,
            }
        except Exception as _e:
            from core.log import log_failure; log_failure("ziwei", "装配六件套/总汇", _e)

        return ApiResponse(success=True, data={
            "decade": decade, "feihua": decade_fh,
            "overlay_insights": overlay_insights,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
