"""
api/qimen.py
============
FastAPI router for QiMen DunJia (奇门遁甲) endpoints.
"""
from fastapi import APIRouter, HTTPException
from models.common import ApiResponse
from models.qimen import QimenRequest
from core.qimen.algorithm import calculate_qimen
from core.qimen.analyzer import analyze_qimen
from core.qimen.purpose_analysis import enrich_qimen_analysis

router = APIRouter(prefix="/qimen", tags=["奇门遁甲"])


@router.post("/layout", summary="排盘 — 奇门遁甲布局")
async def get_layout(req: QimenRequest):
    """Calculate a full QiMen DunJia layout with interpretation."""
    try:
        layout = calculate_qimen(
            req.year, req.month, req.day, req.hour, req.minute,
            yang_dun_override=req.use_yang_dun,
        )
        if req.birth_year:
            layout["_birth_year"] = req.birth_year
        layout["question"] = req.question or ""
        layout["purpose"] = req.purpose or ""
        result = analyze_qimen(layout)
        result = enrich_qimen_analysis(result)
        # 局势总论合成（综合总论层：局势×用神落宫×格局×吉方应期）
        try:
            from core.qimen.overview import synthesize_overview
            ov = synthesize_overview(result)
            if ov.get("available"):
                result["overview"] = ov
        except Exception as _e:
            from core.log import log_failure; log_failure("qimen", "装配六件套/总汇", _e)
        # 用神力量综合推理链（子模块互助：门宫旺衰×星门神×干仪×值符值使×格局）
        try:
            from core.qimen.synthesis import synthesize_yongshen_force
            mg = synthesize_yongshen_force(result)
            if mg.get("available"):
                result["yongshen_synthesis"] = mg
        except Exception as _e:
            from core.log import log_failure; log_failure("qimen", "装配六件套/总汇", _e)
        # 多视角整合：奇门子模块编为视角，确保尽其用、无孤儿
        try:
            from core.qimen.perspectives import build_perspectives
            pv = build_perspectives(result)
            if pv.get("available"):
                result["perspectives"] = pv
        except Exception as _e:
            from core.log import log_failure; log_failure("qimen", "装配六件套/总汇", _e)
        # 局势一致性审核（确定性层）
        try:
            from core.qimen.consistency_audit import audit_consistency
            ca = audit_consistency(result)
            if ca.get("available"):
                result["consistency_audit"] = ca
        except Exception as _e:
            from core.log import log_failure; log_failure("qimen", "装配六件套/总汇", _e)
        # 综合断（总汇合参 — 用神落宫×格局×值符×吉凶方×应期）
        try:
            from core.qimen.master_synthesis import build_qimen_master_synthesis
            ms = build_qimen_master_synthesis(result)
            if ms.get("available"):
                result["master_synthesis"] = ms
        except Exception as _e:
            from core.log import log_failure; log_failure("qimen", "装配六件套/总汇", _e)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/now", summary="即时排盘 — 以当前时间起局")
async def get_now_layout():
    """Calculate QiMen layout for the current moment."""
    from datetime import datetime
    now = datetime.now()
    try:
        layout = calculate_qimen(now.year, now.month, now.day, now.hour, now.minute)
        result = analyze_qimen(layout)
        result = enrich_qimen_analysis(result)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/hour-layout", summary="时家奇门排盘 — 日盘+时盘双盘")
async def get_hour_layout(req: QimenRequest):
    try:
        from core.qimen.algorithm import calculate_qimen_hour
        result = calculate_qimen_hour(
            req.year, req.month, req.day, req.hour, req.minute,
            yang_dun_override=req.use_yang_dun,
        )
        # Run analysis on combined palaces for zhifu_analysis etc.
        try:
            combined = result.get("combined", result.get("hour_plate", []))
            layout_for_analysis = {
                "palaces": combined,
                "ju_type": result.get("ju_type"),
                "ju_number": result.get("hour_ju", result.get("day_ju")),
                "yuan": result.get("yuan"),
                "datetime": result.get("datetime"),
            }
            analysis = analyze_qimen(layout_for_analysis)
            result["zhifu_analysis"] = analysis.get("zhifu_analysis")
            result["summary"] = analysis.get("summary", "")
            result["advice"] = analysis.get("advice", "")
            result["purpose_analyses"] = analysis.get("purpose_analyses", {})
            result["palaces"] = combined
        except Exception:
            result["palaces"] = result.get("combined", result.get("hour_plate", []))
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hour-now", summary="即时时家奇门排盘")
async def get_hour_now():
    from datetime import datetime
    from core.qimen.algorithm import calculate_qimen_hour
    now = datetime.now()
    try:
        result = calculate_qimen_hour(now.year, now.month, now.day, now.hour, now.minute)
        # Run analysis on combined palaces
        try:
            combined = result.get("combined", result.get("hour_plate", []))
            layout_for_analysis = {
                "palaces": combined,
                "ju_type": result.get("ju_type"),
                "ju_number": result.get("hour_ju", result.get("day_ju")),
                "yuan": result.get("yuan"),
                "datetime": result.get("datetime"),
            }
            analysis = analyze_qimen(layout_for_analysis)
            result["zhifu_analysis"] = analysis.get("zhifu_analysis")
            result["summary"] = analysis.get("summary", "")
            result["advice"] = analysis.get("advice", "")
            result["purpose_analyses"] = analysis.get("purpose_analyses", {})
            result["palaces"] = combined
        except Exception:
            result["palaces"] = result.get("combined", result.get("hour_plate", []))
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/zeji", summary="奇门择吉 — 为某事择日×时辰×方位（与择日打通）")
async def qimen_zeji(req: dict):
    """
    Body:
      {
        "purpose": "求财" | "出行" | "婚姻" | ...,   (用事，见 PURPOSE_LOGIC)
        "year": 2024, "month": 6,
        "birth_year": 1988,                          (可选，避本命冲克)
        "top_n": 8                                   (可选，返回前 N 个时空)
      }
    返回最佳「日×时辰×方位」之吉（择日吉分 + 奇门时盘用事分）。
    """
    try:
        from core.qimen.zeji import select_qimen_times
        result = select_qimen_times(
            purpose=str(req.get("purpose", "谋事")),
            year=int(req.get("year")),
            month=int(req.get("month")),
            birth_year=req.get("birth_year"),
            top_n=int(req.get("top_n", 8)),
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "参数有误"))
        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
