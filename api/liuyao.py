"""
api/liuyao.py
=============
FastAPI router for LiuYao (六爻) divination endpoints.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional, List

from models.common import ApiResponse
from models.liuyao import DivinationRequest
from core.liuyao.divination import (
    coin_divination, yarrow_divination, time_divination, manual_divination,
)
from core.liuyao.interpreter import interpret
from core.liuyao.najia import annotate_with_najia, HEXAGRAM_PALACE

router = APIRouter(prefix="/liuyao", tags=["六爻"])


@router.post("/divine", summary="占卜 — 起卦")
async def divine(req: DivinationRequest):
    """
    Perform a LiuYao divination using the specified method.
    Methods: coin | yarrow | time | manual
    """
    try:
        method = req.method.lower()

        if method == "coin":
            result = coin_divination(req.yao_values)
        elif method == "yarrow":
            result = yarrow_divination()
        elif method == "time":
            dt = datetime.fromisoformat(req.query_time) if req.query_time else None
            result = time_divination(dt)
        elif method == "manual":
            if not req.yao_values or len(req.yao_values) != 6:
                raise ValueError("manual方法需要提供6个爻值 (6/7/8/9)")
            result = manual_divination(req.yao_values)
        else:
            raise ValueError(f"不支持的占卜方法: {method}")

        # Step 1: annotate with Najia (sets is_world, is_application, liu_qin, liu_shen, etc.)
        from core.calendar.ganzhi import ganzhi_from_index, _REF_DATE, _REF_DAY_IDX
        from core.calendar.solar_terms import day_ganzhi_at, month_dizhi_at
        # 占卦时刻：任何起卦皆有时间影响（月令定用神旺衰、日辰定应期），
        # 故所有方法（含手动/铜钱）均尊重 query_time；未给则取当前。
        # najia 日辰月令与应期推算基准共用此时刻，保证一致。
        if req.query_time:
            now = datetime.fromisoformat(req.query_time)
        else:
            now = datetime.now()
        # 日干支与月令一律走历法底座（节气月支、节气日干支），杜绝自造转换。
        _dgz = day_ganzhi_at(now)
        day_gan, day_zhi = _dgz[0], _dgz[1]
        month_zhi = month_dizhi_at(now)            # 节气月支（月建）
        # day_idx 仍据连续六十甲子推（najia 起伏神等需序号）
        day_delta = (now.date() - _REF_DATE).days
        day_idx = (_REF_DAY_IDX + day_delta) % 60
        hex_num    = result["original"]["number"]
        lower_name = result["original"]["lower"]["name"]
        upper_name = result["original"]["upper"]["name"]
        try:
            annotate_with_najia(
                result, hex_num, lower_name, upper_name,
                day_gan, day_idx, month_zhi,   # 第7参为 month_zhi（月令）：六爻旺衰严格按月令，非日支
            )
        except Exception as _e1:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e1)  # Najia is enhancement; don't fail the whole request

        # 注入月日地支让 interpret 用（L-1 关系深度分析需要）
        result["month_zhi"] = month_zhi
        result["day_zhi"] = day_zhi
        result["day_gan"] = day_gan
        # 记录占卦时刻 —— 应期精算需以此为基准向后推日
        result["divine_date"] = now.isoformat()

        # Step 2: apply classical interpretation (now has is_world, liu_qin, etc.)
        interpreted = interpret(
            result, req.question,
            gender=getattr(req, "gender", "male"),
            is_proxy=getattr(req, "is_proxy", False),
            explicit_topic=getattr(req, "topic", None),
        )
        # 把占者性别/是否代占这两个用户输入原样带回结果里 —— 之前 interpret()
        # 内部用它们选对了用神（男看妻财/女看官鬼），但从未回写进返回数据，
        # 导致后续 AI 解读环节完全看不到这两个用户实际选择的输入。
        interpreted["gender"] = getattr(req, "gender", "male")
        interpreted["is_proxy"] = getattr(req, "is_proxy", False)

        # 用神力量综合评估：汇旺衰×动变×合局×空破墓于用神，显式呈现子模块互助
        try:
            from core.liuyao.yongshen_synthesis import synthesize_yongshen_strength
            ys_syn = synthesize_yongshen_strength(interpreted)
            if ys_syn.get("available"):
                interpreted["yongshen_strength"] = ys_syn
        except Exception as _e:
            from core.log import log_failure; log_failure("liuyao", "装配六件套/总汇", _e)

        # 用神落爻多维断语：现伏×旺衰×动静化象×空破墓×元神×忌神×世应 → 综合成败
        try:
            from core.liuyao.yongshen_judgment import synthesize_yongshen_judgment
            yj = synthesize_yongshen_judgment(interpreted)
            if yj.get("available"):
                interpreted["yongshen_judgment"] = yj
        except Exception as _e:
            from core.log import log_failure; log_failure("liuyao", "装配六件套/总汇", _e)

        # 完整断卦合成：以所问为纲，织全卦信号成篇（置顶呈现 / 入 AI）
        try:
            from core.liuyao.full_reading import build_full_reading
            fr = build_full_reading(interpreted)
            if fr.get("available"):
                interpreted["full_reading"] = fr
        except Exception as _e:
            from core.log import log_failure; log_failure("liuyao", "装配六件套/总汇", _e)

        # 断卦一致性审核（确定性层）：核查跨模块矛盾，AI 审定层在前端按需调用
        try:
            from core.liuyao.consistency_audit import audit_consistency
            ca = audit_consistency(interpreted)
            if ca.get("available"):
                interpreted["consistency_audit"] = ca
        except Exception as _e:
            from core.log import log_failure; log_failure("liuyao", "装配六件套/总汇", _e)

        # 多视角整合解读：把全部子模块编为六视角，确保尽其用、无孤儿
        try:
            from core.liuyao.perspectives import build_perspectives
            pv = build_perspectives(interpreted)
            if pv.get("available"):
                interpreted["perspectives"] = pv
        except Exception as _e:
            from core.log import log_failure; log_failure("liuyao", "装配六件套/总汇", _e)

        # 综合总断（总汇合参 — 用神×世应×动爻×卦型×应期 → 成败+应期+提示）
        try:
            from core.liuyao.master_synthesis import build_liuyao_master_synthesis
            ms = build_liuyao_master_synthesis(interpreted)
            if ms.get("available"):
                interpreted["master_synthesis"] = ms
        except Exception as _e:
            from core.log import log_failure; log_failure("liuyao", "装配六件套/总汇", _e)

        return ApiResponse(success=True, data=interpreted)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hexagram/{number}", summary="查卦 — 查询指定卦象")
async def get_hexagram(number: int):
    """Get full data for a specific hexagram by King-Wen number (1-64)."""
    try:
        from core.liuyao.hexagram_data import HEXAGRAM_DATA, HEXAGRAM_TRIGRAM_MAPPING
        from core.constants import TRIGRAMS
        if number < 1 or number > 64:
            raise ValueError("卦序必须在1-64之间")
        data    = HEXAGRAM_DATA[number]
        lower_n, upper_n = HEXAGRAM_TRIGRAM_MAPPING[number]
        return ApiResponse(success=True, data={
            "number":   number,
            "name":     data["name"],
            "upper":    {**TRIGRAMS[upper_n], "name": upper_n},
            "lower":    {**TRIGRAMS[lower_n], "name": lower_n},
            "judgment": data["judgment"],
            "image":    data.get("image", ""),
            "lines":    data.get("lines", {}),
            "interpretation": data.get("interpretation", ""),
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hexagrams", summary="列卦 — 获取所有64卦列表")
async def list_hexagrams():
    """Return a compact list of all 64 hexagrams."""
    from core.liuyao.hexagram_data import HEXAGRAM_DATA
    items = [
        {"number": n, "name": d["name"], "element": d.get("element", "")}
        for n, d in sorted(HEXAGRAM_DATA.items())
    ]
    return ApiResponse(success=True, data=items)


@router.get("/gua_static/{number}", summary="卦定式 — 装卦/持世/六爻应事静态断")
async def gua_static(number: int, gender: str = "male"):
    """
    某卦的静态断语三件套（不依赖摇卦日辰）：
      · 装卦定式（六爻纳甲地支/五行/六亲/世应）
      · 世爻六亲持世断
      · 384 爻六亲分类应事断（本卦六爻部分）
    gender: male/female，影响婚姻类用神取法。
    """
    try:
        if number < 1 or number > 64:
            raise ValueError("卦序必须在1-64之间")
        from core.liuyao.zhuang_gua import analyze_gua_static
        result = analyze_gua_static(number, gender=gender)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "参数有误"))
        return ApiResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/gua_catalog", summary="卦目录 — 64卦世爻持世断速览")
async def gua_catalog():
    """返回 64 卦的世位/世爻六亲/持世口诀速览（供目录检索）。"""
    try:
        from core.liuyao.zhuang_gua import chi_shi_judgment, build_zhuang_gua
        items = []
        for n in range(1, 65):
            zg = build_zhuang_gua(n)
            cs = chi_shi_judgment(n)
            items.append({
                "number": n,
                "name": zg["gua_name"],
                "palace": zg["palace"],
                "gua_type": zg["gua_type"],
                "world_line": zg["world_line"],
                "world_liu_qin": cs["world_liu_qin"],
                "kou_jue": cs["kou_jue"],
            })
        return ApiResponse(success=True, data=items)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
