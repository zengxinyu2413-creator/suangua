"""
api/fengshui.py
===============
FastAPI router for FengShui (风水) endpoints.
"""
from fastapi import APIRouter, HTTPException
from models.common import ApiResponse
from models.fengshui import FengShuiRequest
from core.fengshui.calculator import (
    calculate_ming_gua, get_ming_gua_group,
    get_house_gua, get_house_group,
    check_compatibility, get_sector_analysis,
)
from core.fengshui.flying_stars import (
    calculate_annual_flying_stars, get_personal_directions, comprehensive_fengshui_analysis,
)
from core.fengshui.xuankong import (
    calculate_xuankong_chart as calculate_xuankong_pro,
    get_yun, get_chengmen_jue, TWENTY_FOUR_MOUNTAINS,
)

router = APIRouter(prefix="/fengshui", tags=["风水"])


@router.post("/analysis", summary="风水分析 — 命卦与宅卦")
async def feng_shui_analysis(req: FengShuiRequest):
    """
    Calculate Ming Gua, House Gua, compatibility, and Eight-Mansion
    sector analysis.
    """
    try:
        ming_gua    = calculate_ming_gua(req.birth_year, req.gender)
        ming_group  = get_ming_gua_group(ming_gua)
        house_gua   = get_house_gua(req.house_facing)
        house_group = get_house_group(house_gua)
        compat      = check_compatibility(ming_gua, house_gua)
        sectors     = get_sector_analysis(house_gua)

        auspicious   = [s for s in sectors if s["quality"] == "吉"]
        inauspicious = [s for s in sectors if s["quality"] in ("凶", "大凶")]

        from datetime import datetime
        year = datetime.now().year
        flying = comprehensive_fengshui_analysis(ming_gua, house_gua, year, req.house_facing)

        # 解析 compatibility 字符串首部判断相配/不相配
        is_compatible = compat.startswith("相配")

        return ApiResponse(success=True, data={
            "ming_gua":           ming_gua,
            "ming_gua_group":     ming_group,
            "ming_gua_name":      {1:"坎",2:"坤",3:"震",4:"巽",6:"乾",7:"兑",8:"艮",9:"离"}.get(ming_gua, ""),
            "house_gua":          house_gua,
            "house_group":        house_group,
            "house_gua_name":     {1:"坎",2:"坤",3:"震",4:"巽",6:"乾",7:"兑",8:"艮",9:"离"}.get(house_gua, ""),
            "compatibility":      compat,        # 完整中文描述
            "is_compatible":      is_compatible, # 布尔，给前端用
            "house_facing":       req.house_facing,    # 用户输入的朝向
            "house_sitting": {                          # 计算出的坐山
                "南":"北","北":"南","东":"西","西":"东",
                "东南":"西北","西北":"东南","东北":"西南","西南":"东北",
            }.get(req.house_facing, ""),
            "auspicious_sectors": auspicious,
            "inauspicious_sectors": inauspicious,
            "overall_advice": (
                f"命卦{ming_gua}({ming_group})，宅卦{house_gua}({house_group})，"
                f"{'命宅相配，居住有利' if is_compatible else '命宅不相配，建议以吉方弥补'}。"
            ),
            "annual_flying_stars": flying["annual_chart"],
            "personal_directions": flying["personal_directions"],
            "combined_advice":     flying["combined_advice"],
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/xuankong", summary="玄空飞星专业排盘 — 运盘+山盘+向盘三盘合参")
async def xuankong_chart(req: dict):
    """
    完整玄空飞星排盘（《沈氏玄空学》专业版）
    
    请求: { "sitting_mountain": "子", "year": 2026 } 
       或: { "sitting_degree": 5.2, "year": 2026 }   # 精确度数 → 自动判定下卦/起星
    year 为建宅/入伙年（定运·本盘静态）；analysis_year 为分析流年（流年叠加·动态，缺省当前年）。
    """
    try:
        from datetime import datetime as _dtn
        sitting = req.get("sitting_mountain") or req.get("xiang")
        degree = req.get("sitting_degree")
        year = int(req.get("year", 2026))
        analysis_year = int(req.get("analysis_year", _dtn.now().year))
        analysis_month = int(req.get("analysis_month", _dtn.now().month))
        
        if degree is not None:
            result = calculate_xuankong_pro(year, sitting_mountain=sitting,
                                            sitting_degree=float(degree), analysis_year=analysis_year)
        else:
            result = calculate_xuankong_pro(year, sitting_mountain=sitting or "子",
                                            analysis_year=analysis_year)
        
        result["chengmen"] = get_chengmen_jue(result["sitting_mountain"])
        result["analysis_month"] = analysis_month   # 流月方位辅参用
        # 多层级峦头形理（每宫砂水宜忌 + 流年催动）
        try:
            from core.fengshui.xuankong_luantou import enrich_xuankong_luantou
            enrich_xuankong_luantou(result)
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        # 命卦人盘（玄空纳命卦 — 理气×命卦，主人宜居用之方）
        try:
            from core.fengshui.xuankong_mingua import analyze_xuankong_mingua
            mm = analyze_xuankong_mingua(result, req.get("birth_year"), req.get("gender"))
            if mm.get("available"):
                result["mingua_renpan"] = mm
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        # 宅运总论合成（综合总论层：坐向×山向格局×特殊格局×正零城门×峦头）
        try:
            from core.fengshui.xuankong_overview import synthesize_overview
            ov = synthesize_overview(result)
            if ov.get("available"):
                result["overview"] = ov
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        # 宅运力量推理链（子模块互助：山向格局×特殊格局×城门×峦头×反伏吟）
        try:
            from core.fengshui.xuankong_synthesis import synthesize_zhaiyun
            mg = synthesize_zhaiyun(result)
            if mg.get("available"):
                result["zhaiyun_synthesis"] = mg
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        # 多视角整合
        try:
            from core.fengshui.xuankong_perspectives import build_perspectives
            pv = build_perspectives(result)
            if pv.get("available"):
                result["perspectives"] = pv
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        # 宅运一致性审核
        try:
            from core.fengshui.xuankong_audit import audit_consistency
            ca = audit_consistency(result)
            if ca.get("available"):
                result["consistency_audit"] = ca
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        # 综合宅论（总汇合参 — 山向格局×特殊格局×旺衰方×命卦宜居×化解）
        try:
            from core.fengshui.xuankong_master import build_xuankong_master_synthesis
            ms = build_xuankong_master_synthesis(result)
            if ms.get("available"):
                result["master_synthesis"] = ms
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/twenty_four_mountains", summary="24 山方位列表")
async def twenty_four_mountains():
    """返回 24 山方位列表，供前端下拉选择。"""
    return ApiResponse(success=True, data={
        "mountains": [
            {"name": m["name"], "gua": m["gua"], "yin_yang": m["yin_yang"], "start": m["start"], "end": m["end"]}
            for m in TWENTY_FOUR_MOUNTAINS
        ],
    })


@router.get("/monthly_flying", summary="流月紫白飞星")
async def monthly_flying(year: int = 2026, month: int = 1):
    """
    返回某年某月的流月紫白飞星 + 警示。
    """
    from core.fengshui.xuankong_advanced import (
        overlay_monthly_on_annual, detect_monthly_warnings,
    )
    overlaid = overlay_monthly_on_annual(year, month)
    warnings = detect_monthly_warnings(year, month)
    return ApiResponse(success=True, data={
        "year": year, "month": month,
        "overlaid": overlaid,
        "warnings": warnings,
    })


@router.post("/house_report", summary="统一宅报告 — 理气(玄空飞星)×形法(阳宅三要)合断")
async def house_report(req: dict):
    """
    一栋房理气形法合断。

    Body: {
      "sitting_mountain": "子",   坐山（玄空理气）
      "year": 2026,
      "men": "坎", "zhu": "巽", "zao": "震",   门主灶（阳宅形法）
      "zao_facing": "南",         (可选)
      "birth_year": 1990, "gender": "male"   (可选，主人命卦)
    }
    """
    try:
        from core.fengshui.house_report import build_unified_house_report
        result = build_unified_house_report(
            sitting_mountain=str(req.get("sitting_mountain", "子")),
            year=int(req.get("year", 2026)),
            men=str(req.get("men", "")), zhu=str(req.get("zhu", "")), zao=str(req.get("zao", "")),
            zao_facing=req.get("zao_facing"),
            birth_year=req.get("birth_year"), gender=req.get("gender"),
        )
        if not result.get("available"):
            raise HTTPException(status_code=400, detail=result.get("error", "参数有误"))
        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/yangzhai_sanyao", summary="阳宅三要 — 门主灶大游年断")
async def yangzhai_sanyao(req: dict):
    """
    《阳宅三要》门、主、灶三要断法。

    Body:
      {
        "men":  "坎" | "北" | 1 …  (大门卦位/方位)
        "zhu":  "巽" | "东南" …      (主房卦位/方位)
        "zao":  "震" | "东" …        (灶位卦位/方位)
        "zao_facing": "南"           (可选，灶口所向)
      }
    """
    try:
        from core.fengshui.yangzhai_sanyao import synthesize_full_judgment
        result = synthesize_full_judgment(
            men=str(req.get("men", "")),
            zhu=str(req.get("zhu", "")),
            zao=str(req.get("zao", "")),
            zao_facing=req.get("zao_facing"),
            floor=req.get("floor"),
            jin=req.get("jin"),
            liushi=req.get("liushi"),
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "参数有误"))

        # 命卦匹配（人宅相配 — 八宅明镜之命根）：据生年性别断主人命卦配宅
        try:
            from core.fengshui.yangzhai_mingua import analyze_mingua_match
            mm = analyze_mingua_match(result.get("men", {}), result.get("zhu", {}),
                                      result.get("zao", {}),
                                      req.get("birth_year"), req.get("gender"))
            if mm.get("available"):
                result["mingua_match"] = mm
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)

        # 六件套：① 宅相总论 ② 推理链 ③ 多视角 ④ 一致性审核
        try:
            from core.fengshui.yangzhai_overview import synthesize_overview
            ov = synthesize_overview(result)
            if ov.get("available"):
                result["overview"] = ov
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        try:
            from core.fengshui.yangzhai_synthesis import synthesize_zhaixiang
            mg = synthesize_zhaixiang(result)
            if mg.get("available"):
                result["zhaixiang_synthesis"] = mg
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        try:
            from core.fengshui.yangzhai_perspectives import build_perspectives
            pv = build_perspectives(result)
            if pv.get("available"):
                result["perspectives"] = pv
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)
        try:
            from core.fengshui.yangzhai_audit import audit_consistency
            ca = audit_consistency(result)
            if ca.get("available"):
                result["consistency_audit"] = ca
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)

        # 综合宅论（总汇合参 — 宅型纯净×门主局×灶局×命卦相配×六事）
        try:
            from datetime import datetime as _dtn
            result["analysis_year"] = int(req.get("analysis_year", _dtn.now().year))  # 流年方位辅参用
            result["analysis_month"] = int(req.get("analysis_month", _dtn.now().month))  # 流月方位辅参用
            from core.fengshui.yangzhai_master import build_yangzhai_master_synthesis
            ms = build_yangzhai_master_synthesis(result)
            if ms.get("available"):
                result["master_synthesis"] = ms
        except Exception as _e:
            from core.log import log_failure; log_failure("fengshui", "装配六件套/总汇", _e)

        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/yangzhai_layout", summary="阳宅三要 — 门卦八方游年布局表")
async def yangzhai_layout(men: str = "坎"):
    """给定门卦，返回该门八方游年，供布主、布灶择吉。"""
    try:
        from core.fengshui.yangzhai_sanyao import get_best_layout
        result = get_best_layout(men)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "参数有误"))
        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/yangzhai_liushi", summary="阳宅六事 — 路井灶厕碓磨畜栏安置断")
async def yangzhai_liushi(req: dict):
    """
    《阳宅十书·论六事》安置吉凶断（净者居吉方·秽者镇凶方）。

    Body:
      {
        "men": "坎" | "北" | 1 …,           (大门卦位/方位)
        "placements": { "井":"巽", "厕":"艮", "碓磨":"坤", "路":"震" }
                                            (各事安置方位；方位可为卦/八方/二十四山/洛书数，或"中宫")
      }
    """
    try:
        from core.fengshui.yangzhai_liushi import analyze_liushi
        result = analyze_liushi(
            men_gua=str(req.get("men", "")),
            placements=req.get("placements") or {},
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "参数有误"))
        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/yangzhai_liushi_guide", summary="阳宅六事 — 门卦六事宜方/忌方表")
async def yangzhai_liushi_guide(men: str = "坎"):
    """给定门卦，返回六事各自的宜方（净物吉方/秽物凶方）与忌方。"""
    try:
        from core.fengshui.yangzhai_liushi import liushi_best_positions
        result = liushi_best_positions(men)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "参数有误"))
        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
