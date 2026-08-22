"""行文层 API —— 将引擎 master_synthesis 事实转写为流畅古文（下游、护栏强制）。

契约：facts in（master_synthesis）→ prose out。
  · 若服务端配置 ANTHROPIC_API_KEY 且装有 anthropic SDK，则启用 AI 行文（经忠实度护栏）；
  · 否则返回确定性拼接（纯引擎事实，无 AI）。
  · AI 输出若越界（新增星曜/神煞/格局/翻转吉凶），护栏 fail-closed，退回确定性文本。
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from core.narration import (narrate, verify_fidelity, llm_anthropic, build_lexicon,
                            STYLES, DEFAULT_STYLE, collect_facts, collect_facts_multi,
                            guard_metrics, build_export_document)

router = APIRouter(prefix="/narration", tags=["行文层"])

# 术语表构建一次，复用（避免每请求重扫常量）
_LEXICON = build_lexicon()


@router.get("/styles", summary="可用文风分级")
async def styles():
    return {"success": True, "data": {
        "styles": [{"key": k, "label": v["label"]} for k, v in STYLES.items()],
        "default": DEFAULT_STYLE,
    }}


class NarrationRequest(BaseModel):
    master_synthesis: Dict[str, Any]
    use_ai: bool = True            # False 则强制确定性拼接
    model: Optional[str] = None    # 覆盖默认行文模型
    style: str = DEFAULT_STYLE     # 白话 / 半文 / 文言


@router.post("/synthesize", summary="转写 master_synthesis 为行文（护栏强制下游）")
async def synthesize(req: NarrationRequest):
    llm = None
    if req.use_ai:
        llm = llm_anthropic(model=req.model) if req.model else llm_anthropic()
    result = narrate(req.master_synthesis, llm_call=llm, lexicon=_LEXICON, style=req.style)
    # 不回传内部 prompt / 被拒文本给前端，仅留必要字段
    return {
        "success": True,
        "data": {
            "prose": result.get("prose", ""),
            "source": result.get("source"),       # ai | fallback_no_llm | fallback_fidelity
            "style": result.get("style"),
            "fidelity": result.get("fidelity", {"clean": True, "violations": []}),
            "ai_enabled": llm is not None,
        },
    }


class FullNarrationRequest(BaseModel):
    chart_data: Dict[str, Any]     # 整盘响应 data
    module: str                    # bazi/ziwei/liuyao/qimen/xuankong/yangzhai/date
    use_ai: bool = True
    model: Optional[str] = None
    style: str = DEFAULT_STYLE


@router.post("/synthesize_full", summary="整盘综合行文（汇聚多面板事实，护栏强制下游）")
async def synthesize_full(req: FullNarrationRequest):
    ms = collect_facts(req.chart_data, req.module)
    llm = None
    if req.use_ai:
        llm = llm_anthropic(model=req.model) if req.model else llm_anthropic()
    result = narrate(ms, llm_call=llm, lexicon=_LEXICON, style=req.style)
    return {
        "success": True,
        "data": {
            "prose": result.get("prose", ""),
            "source": result.get("source"),
            "style": result.get("style"),
            "fidelity": result.get("fidelity", {"clean": True, "violations": []}),
            "ai_enabled": llm is not None,
            "aggregated_paragraphs": len(ms.get("integrated_paragraphs", [])),
        },
    }


class MultiChartItem(BaseModel):
    chart_data: Dict[str, Any]
    module: str
    label: Optional[str] = None


class MultiNarrationRequest(BaseModel):
    charts: List[MultiChartItem]   # 同人多盘（如八字+紫微）
    use_ai: bool = True
    model: Optional[str] = None
    style: str = DEFAULT_STYLE


@router.post("/synthesize_multi", summary="多盘合参行文（并陈多盘事实，护栏强制下游）")
async def synthesize_multi(req: MultiNarrationRequest):
    charts = [(it.chart_data, it.module) for it in req.charts]
    labels = [it.label for it in req.charts] if any(it.label for it in req.charts) else None
    ms = collect_facts_multi(charts, labels=labels)
    llm = None
    if req.use_ai:
        llm = llm_anthropic(model=req.model) if req.model else llm_anthropic()
    result = narrate(ms, llm_call=llm, lexicon=_LEXICON, style=req.style)
    return {
        "success": True,
        "data": {
            "prose": result.get("prose", ""),
            "source": result.get("source"),
            "style": result.get("style"),
            "fidelity": result.get("fidelity", {"clean": True, "violations": []}),
            "ai_enabled": llm is not None,
            "charts": [it.module for it in req.charts],
        },
    }


class FidelityRequest(BaseModel):
    master_synthesis: Dict[str, Any]
    prose: str


@router.post("/verify", summary="独立校验一段行文是否忠实于引擎事实（不调 LLM）")
async def verify(req: FidelityRequest):
    fid = verify_fidelity(req.master_synthesis, req.prose, lexicon=_LEXICON)
    return {"success": True, "data": fid}


class ExportRequest(BaseModel):
    master_synthesis: Optional[Dict[str, Any]] = None   # 直接给事实
    chart_data: Optional[Dict[str, Any]] = None         # 或给整盘 data
    module: Optional[str] = None                        # 与 chart_data 同传则整盘汇聚
    styles: Optional[List[str]] = None                  # 要导出的风格，默认全部三档
    use_ai: bool = True
    scope_label: str = "本论"


@router.post("/export", summary="行文存档导出（多风格 markdown，自带凭据）")
async def export(req: ExportRequest):
    # 解析事实：整盘优先，否则用 master_synthesis
    if req.chart_data is not None and req.module:
        ms = collect_facts(req.chart_data, req.module)
        scope = req.scope_label if req.scope_label != "本论" else "整盘综合"
    elif req.master_synthesis is not None:
        ms = req.master_synthesis
        scope = req.scope_label
    else:
        return {"success": False, "error": "需提供 master_synthesis 或 chart_data+module"}

    styles = [s for s in (req.styles or list(STYLES.keys())) if s in STYLES] or [DEFAULT_STYLE]
    llm = llm_anthropic() if req.use_ai else None

    narrations: Dict[str, str] = {}
    parts: Dict[str, Any] = {}
    all_clean = True
    for st in styles:
        r = narrate(ms, llm_call=llm, lexicon=_LEXICON, style=st)
        narrations[st] = r.get("prose", "")
        parts[st] = {"source": r.get("source"), "fidelity_clean": r.get("fidelity", {}).get("clean", True)}
        all_clean = all_clean and parts[st]["fidelity_clean"]

    note = "全部风格均通过忠实度护栏。" if all_clean else "注意：部分风格因 AI 越界已退回确定性文本（见各风格 source）。"
    doc = build_export_document(ms, narrations, scope_label=scope, fidelity_note=note)
    return {"success": True, "data": {
        "document": doc, "parts": parts, "ai_enabled": llm is not None,
        "filename": f"行文存档_{scope}.md",
    }}


class MetricsRequest(BaseModel):
    ms_list: List[Dict[str, Any]]   # 一组 master_synthesis（事实），用于量化护栏


@router.post("/metrics", summary="护栏量化指标（忠实通过率/拦截率/分类型，回归监控）")
async def metrics(req: MetricsRequest):
    m = guard_metrics(req.ms_list, lexicon=_LEXICON)
    return {"success": True, "data": m}
