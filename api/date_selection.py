"""
api/date_selection.py
=====================
FastAPI router for DateSelection (择日) endpoints.
"""
from fastapi import APIRouter, HTTPException
from models.common import ApiResponse
from models.fengshui import DateSelectionRequest
from core.date_selection.selector import select_dates

router = APIRouter(prefix="/date-selection", tags=["择日"])


@router.post("/select", summary="择日 — 选取吉日")
async def select_auspicious_dates(req: DateSelectionRequest):
    """
    Return auspicious days for the given purpose in a month.
    """
    try:
        result = select_dates(
            purpose=req.purpose,
            year=req.year,
            month=req.month,
            birth_year=req.birth_year,
            birth_month=req.birth_month,
            birth_day=req.birth_day,
        )
        # 神煞释义 + 择事专属断：为每日吉神/凶煞补含义，并判该日神煞利忌此事
        try:
            from core.date_selection.shensha_meanings import synthesize_shensha_for_purpose
            for _day in result.get("all_days", []):
                _syn = synthesize_shensha_for_purpose(
                    _day.get("ji_shen", []), _day.get("xiong_sha", []), req.purpose)
                _day["shensha_purpose"] = _syn
                _day["shensha_annotated"] = _syn.get("shensha_annotated")
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "神煞释义", _e)

        # 按「事项专属神煞净分」精排 best_days/auspicious_days ——
        # 通用 score 不分事项，可能被与本事项无关的凶煞（如"忌出行"对结婚无碍）拉低，
        # 导致真正最利本事项的日子未进入推荐前列。原 score>=3（含岁破月破硬排除）
        # 仍作为基础质量门槛不变，此处仅在该及格候选池内改用更精准的 shensha_purpose.net 排序，
        # 必须置于此处（shensha_purpose 刚算好、后续 overview/synthesis/perspectives/
        # consistency_audit/master_synthesis 尚未读取 best_days 之前），否则这些模块生成的
        # 文案会与精排后的实际推荐结果不一致。
        try:
            _asp = result.get("auspicious_days", [])
            if _asp and all(isinstance(_d.get("shensha_purpose"), dict) for _d in _asp):
                # 先排除「专忌此事」之日——净分排序不能替代吉凶门槛：一日纵使通用 score
                # 达标，若其神煞组合明确「忌」本事项（如忌搬家日撞入宅正忌之凶煞），
                # 就不该被推荐，无论净分数值高低。仅当全月候选皆忌（无一日不冲本事）时，
                # 才退回原候选池精排，避免 best_days 因过滤而整月落空。
                _asp_ok = [x for x in _asp if x["shensha_purpose"].get("level") != "忌"] or _asp
                _asp_sorted = sorted(_asp_ok, key=lambda x: x["shensha_purpose"].get("net", 0), reverse=True)
                result["auspicious_days"] = _asp_sorted
                result["best_days"] = _asp_sorted[:3]
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "按事项净分精排", _e)
        # 八字个性化（吉日按本人用神/冲克过滤 — 真个性化）
        try:
            if req.birth_year and req.birth_month and req.birth_day:
                from core.date_selection.personalize import personalize_days
                pz = personalize_days(result.get("all_days", []),
                                      req.birth_year, req.birth_month, req.birth_day,
                                      getattr(req, "birth_hour", None) or 12)
                if pz.get("available"):
                    result["personalization"] = pz
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "装配六件套/总汇", _e)

        # 选期总论合成（综合总论层：月令×首选吉日×次吉×忌避×三煞）
        try:
            from core.date_selection.overview import synthesize_overview
            ov = synthesize_overview(result)
            if ov.get("available"):
                result["overview"] = ov
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "装配六件套/总汇", _e)
        # 吉日力量推理链
        try:
            from core.date_selection.synthesis import synthesize_zeri
            mg = synthesize_zeri(result)
            if mg.get("available"):
                result["zeri_synthesis"] = mg
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "装配六件套/总汇", _e)
        # 多视角整合
        try:
            from core.date_selection.perspectives import build_perspectives
            pv = build_perspectives(result)
            if pv.get("available"):
                result["perspectives"] = pv
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "装配六件套/总汇", _e)
        # 一致性审核
        try:
            from core.date_selection.consistency_audit import audit_consistency
            ca = audit_consistency(result)
            if ca.get("available"):
                result["consistency_audit"] = ca
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "装配六件套/总汇", _e)
        # 综合总论（总汇合参 — 月令×通用首选×个人首选×忌避）
        try:
            from core.date_selection.master_synthesis import build_date_master_synthesis
            ms = build_date_master_synthesis(result)
            if ms.get("available"):
                result["master_synthesis"] = ms
        except Exception as _e:
            from core.log import log_failure; log_failure("date_selection", "装配六件套/总汇", _e)
        return ApiResponse(success=True, data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
