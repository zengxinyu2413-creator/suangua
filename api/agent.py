"""
api/agent.py
============
AI Agent endpoints — streaming LLM-powered consultations.

Supports multiple providers via request headers:
  X-LLM-Key:       API key
  X-LLM-Provider:  anthropic | deepseek | openai | moonshot  (default: anthropic)
  X-LLM-Base-Url:  optional override base URL
  X-LLM-Model:     optional override model name

All endpoints stream Server-Sent Events (SSE).
"""
from __future__ import annotations
import json
try:
    from lunar_python import Lunar as _LunarLib
except ImportError:
    _LunarLib = None
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.common import ApiResponse

router = APIRouter(prefix="/agent", tags=["AI命理顾问"])

# ─────────────────────────────────────────────────────────────
# Provider configuration
# ─────────────────────────────────────────────────────────────

PROVIDER_DEFAULTS = {
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1/messages",
        "model":    "claude-sonnet-4-6",
        "style":    "anthropic",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1/chat/completions",
        "model":    "deepseek-chat",
        "style":    "openai",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "model":    "gpt-4o",
        "style":    "openai",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1/chat/completions",
        "model":    "moonshot-v1-8k",
        "style":    "openai",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
        "model":    "gemini-2.0-flash",
        "style":    "gemini",
    },
}


def _get_llm_config(request: Request) -> dict:
    """
    Read LLM config from request headers.

    Headers:
      X-LLM-Provider  — known id (anthropic/openai/deepseek/moonshot/gemini)
                        OR any string label for a custom provider
      X-LLM-Key       — API key
      X-LLM-Base-Url  — full base URL (required for custom providers)
      X-LLM-Model     — model name
      X-LLM-Style     — api style: anthropic | openai | gemini
                        (auto-detected from provider if omitted)
    """
    provider = (request.headers.get("X-LLM-Provider") or "anthropic").lower().strip()
    key      = (request.headers.get("X-LLM-Key") or "").strip()
    base_url = (request.headers.get("X-LLM-Base-Url") or "").strip()
    model    = (request.headers.get("X-LLM-Model") or "").strip()
    style_hdr = (request.headers.get("X-LLM-Style") or "").strip().lower()

    if provider in PROVIDER_DEFAULTS:
        # Known preset provider
        defaults = PROVIDER_DEFAULTS[provider]
        resolved_style    = style_hdr or defaults["style"]
        resolved_base_url = base_url  or defaults["base_url"]
        resolved_model    = model     or defaults["model"]
    else:
        # Custom / unknown provider — trust whatever the frontend sends
        # Style: use header if set, else default to openai-compatible
        resolved_style = style_hdr or "openai"
        resolved_model = model or ""

        # For OpenAI-compatible providers, base_url is a prefix like
        # https://open.bigmodel.cn/api/paas/v4
        # The actual chat endpoint must be …/chat/completions.
        # Append it automatically if missing, so users only need to set the base.
        if base_url:
            stripped = base_url.rstrip("/")
            if resolved_style == "openai" and not stripped.endswith("/chat/completions"):
                resolved_base_url = stripped + "/chat/completions"
            else:
                resolved_base_url = stripped
        else:
            resolved_base_url = ""

    # Gemini: keep base_url as the domain prefix, model is spliced in _stream_gemini
    # (nothing special needed here, _stream_gemini handles the URL template itself)

    return {
        "provider": provider,
        "key":      key,
        "base_url": resolved_base_url,
        "model":    resolved_model,
        "style":    resolved_style,
    }


# ─────────────────────────────────────────────────────────────
# Streaming helpers — one per API style
# ─────────────────────────────────────────────────────────────

async def _stream_anthropic(cfg: dict, system: str, messages: list, max_tokens: int = 2000):
    """Stream from Anthropic-style API."""
    headers = {
        "Content-Type":    "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key":       cfg["key"],
    }
    payload = {
        "model":      cfg["model"],
        "max_tokens": max_tokens,
        "stream":     True,
        "system":     system,
        "messages":   messages,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream("POST", cfg["base_url"], headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    err  = body.decode(errors="replace")
                    msg  = f"⚠️ API错误({resp.status_code}) — 请求地址: {cfg['base_url']}\n详情: {err[:300]}"
                    yield "data: " + json.dumps({"text": msg}, ensure_ascii=False) + "\n\n"
                    yield "data: [DONE]\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        ev = json.loads(data)
                        if ev.get("type") == "content_block_delta":
                            text = ev.get("delta", {}).get("text", "")
                            if text:
                                yield "data: " + json.dumps({"text": text}, ensure_ascii=False) + "\n\n"
                    except Exception as _e1:
                        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e1)
    except Exception as e:
        msg = f"⚠️ 网络错误: {type(e).__name__}: {str(e)[:200]}"
        yield "data: " + json.dumps({"text": msg}, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"


async def _stream_openai(cfg: dict, system: str, messages: list, max_tokens: int = 2000):
    """Stream from OpenAI-compatible API (DeepSeek, Moonshot, OpenAI)."""
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {cfg['key']}",
    }
    full_messages = [{"role": "system", "content": system}] + messages
    payload = {
        "model":      cfg["model"],
        "max_tokens": max_tokens,
        "stream":     True,
        "messages":   full_messages,
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream("POST", cfg["base_url"], headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    err  = body.decode(errors="replace")
                    msg  = f"⚠️ API错误({resp.status_code}) — 请求地址: {cfg['base_url']}\n详情: {err[:300]}"
                    yield "data: " + json.dumps({"text": msg}, ensure_ascii=False) + "\n\n"
                    yield "data: [DONE]\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        ev = json.loads(data)
                        text = ev.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if text:
                            yield "data: " + json.dumps({"text": text}, ensure_ascii=False) + "\n\n"
                    except Exception as _e2:
                        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e2)
    except Exception as e:
        msg = f"⚠️ 网络错误: {type(e).__name__}: {str(e)[:200]}"
        yield "data: " + json.dumps({"text": msg}, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"



async def _stream_gemini(cfg: dict, system: str, messages: list, max_tokens: int = 2000):
    """
    Stream from Google Gemini API (streamGenerateContent with SSE).

    Endpoint: POST {base}/{model}:streamGenerateContent?alt=sse&key={api_key}
    SSE chunks: {"candidates":[{"content":{"parts":[{"text":"..."}]}}]}
    """
    base    = cfg.get("base_url", "https://generativelanguage.googleapis.com/v1beta/models").rstrip("/")
    model   = cfg["model"]
    api_key = cfg["key"]
    url     = f"{base}/{model}:streamGenerateContent?alt=sse&key={api_key}"

    # Convert messages to Gemini contents format
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7,
        },
    }
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    err  = body.decode(errors="replace")
                    try:
                        err_msg = json.loads(err).get("error", {}).get("message", err[:300])
                    except Exception:
                        err_msg = err[:300]
                    msg = f"\u26a0\ufe0f Gemini API\u9519\u8bef({resp.status_code}): {err_msg}"
                    yield "data: " + json.dumps({"text": msg}, ensure_ascii=False) + "\n\n"
                    yield "data: [DONE]\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        break
                    try:
                        ev   = json.loads(data)
                        text = (ev.get("candidates", [{}])[0]
                                  .get("content", {})
                                  .get("parts", [{}])[0]
                                  .get("text", ""))
                        if text:
                            yield "data: " + json.dumps({"text": text}, ensure_ascii=False) + "\n\n"
                    except Exception as _e3:
                        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e3)
    except Exception as e:
        msg = f"\u26a0\ufe0f \u7f51\u7edc\u9519\u8bef: {type(e).__name__}: {str(e)[:200]}"
        yield "data: " + json.dumps({"text": msg}, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"


async def _stream_llm(cfg: dict, system: str, messages: list, max_tokens: int = 2000):
    """Dispatch to the right streaming function based on provider style."""
    if not cfg["key"]:
        yield f'data: {json.dumps({"text": "⚠️ 未配置 API Key，请在设置页面填写。"})}\n\n'
        yield "data: [DONE]\n\n"
        return

    if cfg["style"] == "anthropic":
        async for chunk in _stream_anthropic(cfg, system, messages, max_tokens):
            yield chunk
    elif cfg["style"] == "gemini":
        async for chunk in _stream_gemini(cfg, system, messages, max_tokens):
            yield chunk
    else:
        async for chunk in _stream_openai(cfg, system, messages, max_tokens):
            yield chunk


# ─────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────

class ConsultRequest(BaseModel):
    question: str
    context:  Optional[Dict[str, Any]] = None
    session_history: Optional[List[Dict]] = None


class BaziAgentRequest(BaseModel):
    year: int; month: int; day: int; hour: int; minute: int = 0
    gender: str = "male"
    is_lunar:      bool = True
    is_leap_month: bool = False
    province:      Optional[str] = None
    city:          Optional[str] = None
    question: Optional[str] = None
    focus:    Optional[str] = None
    precomputed: Optional[Dict[str, Any]] = None  # frontend pre-computed chart data


class LiuyaoAgentRequest(BaseModel):
    method:     str = "time"
    yao_values: Optional[List[int]] = None
    question:   str = ""
    query_time: Optional[str] = None
    precomputed: Optional[Dict[str, Any]] = None  # frontend pre-computed divination data


class QimenAgentRequest(BaseModel):
    year: Optional[int] = None; month: Optional[int] = None
    day:  Optional[int] = None; hour:  Optional[int] = None
    minute: int = 0
    question: str = ""
    precomputed: Optional[Dict[str, Any]] = None  # frontend pre-computed qimen layout


class FengShuiAgentRequest(BaseModel):
    birth_year:    int
    gender:        str = "male"
    house_facing:  str
    question:      Optional[str] = None
    precomputed: Optional[Dict[str, Any]] = None  # frontend pre-computed fengshui data


# ─────────────────────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────────────────────

MASTER_SYSTEM = """你是一位精通中国传统命理的AI命理顾问，深研：
《穷通宝鉴》《滴天髓》《三命通会》《子平真诠》《神峰通考》《奇门遁甲》《六爻纳甲》《八宅风水》。

职责：用专业而通俗的语言解答命理问题，引用经典典籍支撑论断，给出实用建议。
格式：先给核心论断 → 引用典籍 → 给出建议，使用小标题分隔。
语言：中文，专业而不失亲切。"""

BAZI_SYSTEM = """你是专精八字命理的AI命理师，精通《穷通宝鉴》《滴天髓》《子平真诠》《三命通会》。
分析步骤：①日主强弱（月令旺衰）→ ②用神喜忌（调候+格局）→ ③格局判断 → ④十神六亲 → ⑤运程论断
引经据典，如"《穷通宝鉴》云：…"，语言专业含人情味，用中文回答。"""

LIUYAO_SYSTEM = """你是精通六爻纳甲的AI占卜师，深研《增删卜易》《卜筮正宗》。
分析框架：①本卦卦义 → ②世应关系 → ③用神取定 → ④旺衰动静 → ⑤六亲六神 → ⑥吉凶应期
结合问题具体分析，给出时间应期判断，用中文回答。

【术语规范】必须严格使用以下标准术语，禁止使用同音错字：
- "卦"（不是"挂"）— 本卦、变卦、互卦、错卦、综卦、八卦
- "变卦"（不是"之卦"，与界面术语统一；古籍引文除外可用"之卦"）
- "爻"（不是"交"或"尧"）— 世爻、应爻、动爻、变爻、用神爻
- "六亲"：父母、兄弟、子孙、妻财、官鬼（不是"妻才"）
- "六神"：青龙、朱雀、勾陈、腾蛇、白虎、玄武
- "纳甲"（不是"那甲"）/ "卜筮"（不是"卜噬"）"""

QIMEN_SYSTEM = """你是精通奇门遁甲的AI战略顾问，深研《奇门遁甲统宗》《烟波钓叟赋》。
分析框架：①局势判断 → ②宫位解读 → ③星门神综合 → ④格局识别 → ⑤行动建议
从全局到细节，给出具体可操作的方向建议，用中文回答。"""

FENGSHUI_SYSTEM = """你是精通八宅风水的AI风水顾问，深研《阳宅三要》《八宅明镜》。
分析框架：①命卦 → ②宅卦 → ③命宅配合 → ④四吉四凶 → ⑤布局建议（化煞方法）
给出具体家居布局建议，化解方案切实可行，用中文回答。"""


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

def _sse_response(generator, cfg: dict):
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                 "X-LLM-Provider": cfg["provider"], "X-LLM-Model": cfg["model"]},
    )


@router.post("/consult")
async def consult(req: ConsultRequest, request: Request):
    """
    智能路由顾问 — 根据问题自动判断模块并计算
    如果提供了生辰信息，自动排八字注入上下文
    """
    cfg = _get_llm_config(request)
    messages = list(req.session_history or [])
    content  = req.question
    computed_ctx = ""

    # ── 智能计算：如果有生辰信息，自动排八字 ──
    if req.context and req.context.get("birth"):
        try:
            birth = req.context["birth"]
            from core.bazi.chart import build_chart
            from core.bazi.analyzer import analyze_chart
            from core.bazi.forecaster import calculate_dayun
            chart = build_chart(
                int(birth.get("year", 1990)), int(birth.get("month", 1)),
                int(birth.get("day", 1)), int(birth.get("hour", 12)), 0
            )
            analyze_chart(chart)
            dayun = calculate_dayun(chart, birth.get("gender", "男"),
                                     int(birth.get("year", 1990)), num_periods=4)
            dm = chart.get("day_master", "")
            pillars = f"年:{chart.get('year_pillar',{}).get('tiangan','')}{chart.get('year_pillar',{}).get('dizhi','')} "
            pillars += f"月:{chart.get('month_pillar',{}).get('tiangan','')}{chart.get('month_pillar',{}).get('dizhi','')} "
            pillars += f"日:{chart.get('day_pillar',{}).get('tiangan','')}{chart.get('day_pillar',{}).get('dizhi','')} "
            pillars += f"时:{chart.get('hour_pillar',{}).get('tiangan','')}{chart.get('hour_pillar',{}).get('dizhi','')}"
            yong = chart.get("yong_shen", {})
            dayun_strs = []
            for d in dayun[:4]:
                tg = d.get('tiangan', '')
                dz = d.get('dizhi', '')
                sa = d.get('start_age', '')
                dayun_strs.append(f"{tg}{dz}({sa}岁)")
            computed_ctx = (
                f"\n\n【此人八字命盘（自动排算）】\n"
                f"四柱：{pillars}\n"
                f"日主：{dm}（{chart.get('day_master_wuxing','')}）· 身{chart.get('strength','')}\n"
                f"格局：{chart.get('pattern','')}（{chart.get('pattern_desc','')}）\n"
                f"用神：{yong.get('yong_shen_wx','')} · 喜：{yong.get('xi_shen_wx','')} · 忌：{yong.get('ji_shen_wx','')}\n"
                f"神煞：{'、'.join(s.get('name','') for s in chart.get('shensha',[])[:5])}\n"
                f"大运：{'→'.join(dayun_strs)}\n"
            )
            # Classical knowledge for this day master
            try:
                from knowledge.bazi_classical import TIAO_HOU_TABLE, SHIGAN_JIJUE
                month_dz = chart.get("month_pillar", {}).get("dizhi", "")
                tiahou = TIAO_HOU_TABLE.get(dm, {}).get(month_dz, "")
                shigan = SHIGAN_JIJUE.get(dm, {})
                if tiahou:
                    computed_ctx += f"调候：{dm}干{month_dz}月 — {tiahou[:80]}\n"
                if shigan.get("口诀"):
                    computed_ctx += f"日干：{shigan['口诀']}\n"
            except Exception as _e4:
                from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e4)
        except Exception as e:
            computed_ctx = f"\n\n（排盘尝试失败：{str(e)[:60]}）\n"
    elif req.context:
        content = f"【已知数据】\n{json.dumps(req.context, ensure_ascii=False, indent=2)}\n\n【问题】\n{req.question}"

    # ── 当下时空（任何解读皆纳入当下时辰合参）──
    try:
        from core.calendar.current_moment import current_sizhu, moment_brief
        _mo = current_sizhu()
        computed_ctx += "\n【当下时空（此刻）】\n" + moment_brief(_mo) + "\n"
        # 若已排八字，叠加此刻时令对本命用神之扶抑 + 当前流年
        _chart_local = locals().get("chart") or {}
        if req.context and req.context.get("birth") and _chart_local:
            try:
                from core.calendar.current_moment import moment_vs_yongshen
                _yong = (_chart_local.get("yong_shen", {}) or {}).get("yong_shen_wx", "")
                _ji = (_chart_local.get("yong_shen", {}) or {}).get("ji_shen_wx", "")
                _yl = [w for w in (_yong if isinstance(_yong, list) else [_yong]) if w]
                _jl = [w for w in (_ji if isinstance(_ji, list) else [_ji]) if w]
                _mv = moment_vs_yongshen(_mo, _yl, _jl)
                computed_ctx += f"此刻时令于本命用神为「{_mv['tone']}」（{_mv['quality']}）：{_mv['note']}\n"
                # 当前流年并入
                from core.bazi.current_fortune import build_current_fortune
                _cf = build_current_fortune(_chart_local, birth.get("gender", "男"),
                                            int(birth.get("year", 1990)))
                if _cf.get("available"):
                    _cdy = _cf.get("current_dayun", {}) or {}
                    _cln = _cf.get("current_liunian", {}) or {}
                    computed_ctx += (f"当前运程：行{_cdy.get('ganzhi','')}大运（{_cdy.get('shishen','')}），"
                                     f"{_cf.get('current_year','')}年{_cln.get('ganzhi','')}流年（{_cln.get('quality','')}）。\n")
            except Exception as _e:
                from core.log import log_failure; log_failure("agent", "consult 流年/扶抑", _e)
    except Exception as _e:
        from core.log import log_failure; log_failure("agent", "consult 当下时空", _e)

    # ── 紫微命宫（跨盘合参：命理双印证）──
    if req.context and req.context.get("birth"):
        try:
            from core.ziwei.chart import build_ziwei_chart
            _b = req.context["birth"]
            _by, _bm, _bd = int(_b.get("year", 1990)), int(_b.get("month", 1)), int(_b.get("day", 1))
            _bh = int(_b.get("hour", 12))
            _solar = f"{_by:04d}-{_bm:02d}-{_bd:02d}"
            _hidx = ((_bh + 1) // 2) % 12          # 24h → 时辰索引（子=0）
            _zw = build_ziwei_chart(solar_date=_solar, birth_hour_index=_hidx,
                                    gender=_b.get("gender", "男"))
            _soul = next((p for p in _zw.get("palaces", []) if p.get("is_soul")), {})
            if _soul:
                _stars = "、".join(s.get("name", "") for s in _soul.get("major_stars", [])[:3]) or "无正曜"
                computed_ctx += (f"\n【紫微命宫（跨盘印证）】\n命宫坐{_stars}"
                                 f"（{_soul.get('earthly_branch','')}宫），五行局{_zw.get('metadata',{}).get('five_elements','')}。\n")
        except Exception as _e:
            from core.log import log_failure; log_failure("agent", "consult 紫微", _e)

    # RAG: inject relevant classical passages
    try:
        from knowledge.rag import get_rag
        rag_ctx = get_rag().search_and_format(req.question, top_k=5)
        if rag_ctx:
            content = rag_ctx + "\n\n" + content
    except Exception as _e5:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e5)

    content = content + computed_ctx
    content += "\n\n请基于以上信息回答问题。最后必须有【结论】段落直接回答核心问题。"
    messages.append({"role": "user", "content": content})
    return _sse_response(_stream_llm(cfg, MASTER_SYSTEM, messages, 2000), cfg)


@router.post("/bazi")
async def bazi_agent(req: BaziAgentRequest, request: Request):
    cfg = _get_llm_config(request)

    from core.bazi.chart import build_chart
    from core.bazi.analyzer import analyze_chart
    from core.bazi.forecaster import calculate_dayun

    # ── Lunar→solar conversion ─────────────────────────────────────────
    _sy, _sm, _sd = req.year, req.month, req.day
    if req.is_lunar and _LunarLib is not None:
        try:
            _lm = -req.month if req.is_leap_month else req.month
            _lunar = _LunarLib.fromYmdHms(req.year, _lm, req.day, req.hour, req.minute, 0)
            _sol   = _lunar.getSolar()
            _sy, _sm, _sd = _sol.getYear(), _sol.getMonth(), _sol.getDay()
        except Exception as _e6:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e6)  # fallback: treat as solar

    # ── Location string ────────────────────────────────────────────────
    _loc_parts = [p for p in [req.province, req.city] if p]
    _location  = ('出生地：' + '·'.join(_loc_parts)) if _loc_parts else ''

    # ── Use pre-computed chart from frontend if available ──────────────
    if req.precomputed and req.precomputed.get("day_master"):
        chart = req.precomputed
        dayun = chart.get("dayun", []) or []
        if not dayun:
            dayun = calculate_dayun(chart, req.gender, _sy, num_periods=5)
    else:
        chart = build_chart(_sy, _sm, _sd, req.hour, req.minute)
        analyze_chart(chart)
        dayun = calculate_dayun(chart, req.gender, _sy, num_periods=5)

    dm = chart["day_master"]
    summary = {
        "年柱": f"{chart['year_pillar']['tiangan']}{chart['year_pillar']['dizhi']} [{chart['year_pillar']['nayin']}]",
        "月柱": f"{chart['month_pillar']['tiangan']}{chart['month_pillar']['dizhi']} [{chart['month_pillar']['nayin']}]",
        "日柱": f"{chart['day_pillar']['tiangan']}{chart['day_pillar']['dizhi']} [{chart['day_pillar']['nayin']}]",
        "时柱": f"{chart['hour_pillar']['tiangan']}{chart['hour_pillar']['dizhi']} [{chart['hour_pillar']['nayin']}]",
        "日主": dm, "五行": chart["day_master_wuxing"],
        "身强弱": chart.get("strength", ""), "格局": chart.get("pattern", ""),
        "格局描述": chart.get("pattern_desc", ""),
        "大运": [f"{d['tiangan']}{d['dizhi']}（{int(d['start_age'])}~{int(d['end_age'])}岁，{d['quality']}）" for d in dayun],
        "神煞": [s["name"] for s in chart.get("shensha", [])],
    }

    focus_str = f"重点分析{req.focus}方面" if req.focus else "综合分析"

    # Load classical rules for this day master + birth month
    classical_ctx = ""
    # RAG: dynamically retrieve most relevant classical passages
    try:
        from knowledge.rag import get_rag
        bazi_query = f"{dm}日主 {chart.get('pattern','')} {req.question or ''} 八字格局用神"
        classical_ctx = get_rag().search_and_format(bazi_query, top_k=6, header="\n\n【古籍精华】")
    except Exception as _e7:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e7)
    try:
        from knowledge.bazi_classical import TIAO_HOU_TABLE, SHIGAN_JIJUE, RIZHUPAN_RULES, BAZIGE_SYSTEM
        month_dz = chart["month_pillar"]["dizhi"]
        tiao_hou = TIAO_HOU_TABLE.get(dm, {}).get(month_dz, "")
        shigan   = SHIGAN_JIJUE.get(dm, {})
        pattern  = chart.get("pattern", "")
        gejv     = BAZIGE_SYSTEM.get(pattern, {})
        classical_ctx = (
            f"\n\n【《穷通宝鉴》调候用神】{dm}日干{month_dz}月：{tiao_hou}"
            f"\n\n【《滴天髓》{dm}干论命】\n"
            f"口诀：{shigan.get('口诀','')}\n"
            f"解析：{shigan.get('解析','')}\n"
            f"喜忌：{shigan.get('喜忌','')}"
        )
        if gejv:
            classical_ctx += (
                f"\n\n【《子平真诠》{pattern}格局】\n"
                f"取格：{gejv.get('取格','')}\n"
                f"喜：{'、'.join(gejv.get('喜',[]))}\n"
                f"忌：{'、'.join(gejv.get('忌',[]))}"
            )
        classical_ctx += f"\n\n【日主强弱总纲】{RIZHUPAN_RULES.get('中和论','')}"
    except Exception as _e8:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e8)

    _cal_label = '农历' if req.is_lunar else '公历'
    _leap_label = '（闰月）' if req.is_leap_month else ''
    _loc_note   = f'\n出生地：{_location}' if _location else ''
    _loc_analysis = ''
    if _location:
        # Brief regional five-element context
        _loc_analysis = (
            f'\n\n【出生地参考】{_location}——'
            f'地域五行偏性对日主格局的修正：'
            f'西北（金水偏重，燥寒）、东南（木火偏盛，湿热）、'
            f'中原（土旺）、西南（土湿）、东北（水寒木旺）。'
            f'请结合{_location}地域特点辅助分析调候及用神取向。'
        )
    user_msg = (
        f"{_cal_label}{req.year}年{req.month}月{req.day}日{_leap_label}{req.hour}时，{req.gender}命{_loc_note}\n\n"
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}"
        f"{classical_ctx}\n\n"
        f"{_loc_analysis}"
        f"请按以下步骤深度分析：①日主强弱（月令旺衰得令）→②调候用神（《穷通宝鉴》）→"
        f"③格局判断（《子平真诠》）→④十神六亲吉凶→⑤大运流年趋势。"
        f"引经据典，具体到位。{req.question or focus_str}"
    )
    return _sse_response(_stream_llm(cfg, BAZI_SYSTEM, [{"role":"user","content":user_msg}], 2800), cfg)


@router.post("/liuyao")
async def liuyao_agent(req: LiuyaoAgentRequest, request: Request):
    cfg = _get_llm_config(request)

    from core.liuyao.divination import coin_divination, yarrow_divination, time_divination, manual_divination
    from core.liuyao.interpreter import interpret

    # Use pre-computed divination result from frontend if available
    if req.precomputed and req.precomputed.get("original"):
        interp = req.precomputed
    else:
        method = req.method.lower()
        if method == "coin":      result = coin_divination(req.yao_values)
        elif method == "yarrow":  result = yarrow_divination()
        elif method == "time":
            dt = datetime.fromisoformat(req.query_time) if req.query_time else None
            result = time_divination(dt)
        elif method == "manual":
            if not req.yao_values or len(req.yao_values) != 6:
                raise HTTPException(400, "manual方法需提供6个爻值(6/7/8/9)")
            result = manual_divination(req.yao_values)
        else:
            raise HTTPException(400, f"不支持: {method}")
        # Apply full classical analysis
        interp  = interpret(result, req.question)
    orig    = interp["original"]
    changed = interp.get("changed")
    yaos    = interp.get("yaos", [])
    topic   = interp.get("topic", "综合")

    # Build enriched yao detail for AI context
    yao_detail = []
    for y in yaos:
        yd = {
            "位": f"第{y.get('line','')}爻",
            "六亲": y.get("liu_qin", ""),
            "六神": y.get("liu_shen", ""),
            "地支": y.get("branch", ""),
            "旺衰": y.get("strength", {}).get("label", ""),
            "世应": "世" if y.get("is_world") else ("应" if y.get("is_application") else ""),
            "空亡": "是" if y.get("kong_wang") else "否",
            "动": "动" if y.get("is_changing") else "静",
        }
        if y.get("is_changing"):
            from core.liuyao.interpreter import _check_jin_tui_shen
            jt = _check_jin_tui_shen(y.get("branch",""), y.get("changed_branch",""))
            if jt:
                yd["进退"] = f"化{jt}神"
        yao_detail.append(yd)

    # Classical analysis already computed by interpreter
    classical_pts = interp.get("classical_points", [])
    topic_analysis = interp.get("topic_analysis", {})

    # Load relevant classical rules for this topic
    classical_context = ""
    # RAG: retrieve relevant liuyao passages
    try:
        from knowledge.rag import get_rag
        lx_query = f"六爻 {topic} 用神 {req.question}"
        rag_ctx = get_rag().search_and_format(lx_query, top_k=5, header="【古籍精华】")
        if rag_ctx:
            classical_context = rag_ctx + "\n"
    except Exception as _e9:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e9)
    try:
        from knowledge.liuyao_classical import LIUYAO_TOPIC_RULES, LIUYAO_CLASSICAL_RULES
        topic_rule = LIUYAO_TOPIC_RULES.get(topic, {})
        key_rules = topic_rule.get("规则") or topic_rule.get("rules", [])
        classical_context = (
            f"\n【{topic}用神规则（经典）】\n" +
            "\n".join(f"• {r}" for r in key_rules[:5]) +
            f"\n【{topic}总结】{topic_rule.get('summary','')}"
        )
    except Exception as _e10:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e10)

    _zd = interp.get("zonghe_duan", {})
    _zd_roles = []
    if _zd.get("roles"):
        for rname, st in _zd["roles"].items():
            if st.get("present"):
                _zd_roles.append(
                    f"{rname}={st.get('liu_qin','')}{st.get('branch','')}（{st.get('wangshuai','')}"
                    f"{'·动' if st.get('is_dong') else '·静'}{'·空' if st.get('is_kong') else ''}"
                    f"{'·'+st['hua'] if st.get('hua') else ''}）")
            else:
                _zd_roles.append(f"{rname}=不上卦")

    summary = {
        "占问": req.question or "综合运势",
        "占事类型": topic,
        "本卦": f"第{orig['number']}卦 {orig['name']}（上{orig['upper']['name']} 下{orig['lower']['name']}）",
        "卦辞": orig.get("judgment", "")[:80],
        "变卦": f"第{changed['number']}卦 {changed['name']}" if changed else "无",
        "旬空": interp.get("kong_wang_branches", []),
        "世应": interp.get("world_summary", ""),
        "世爻持世断": (interp.get("chi_shi") or {}).get("summary", ""),
        "六爻纳甲详情": yao_detail,
        "系统初步断法": classical_pts[:5],
        "动爻分析": interp.get("changing_analysis", []),
        "动爻化变断": [m.get("full_text", "") for m in (interp.get("hua_bian") or {}).get("moving_lines", [])],
        "用神四位": _zd_roles,
        "综合断卦链": _zd.get("reasoning", []),
        "世应断": _zd.get("shiying", ""),
        "综合结论": f"{_zd.get('conclusion','')}（信心{_zd.get('confidence','')}）：{_zd.get('verdict','')}" if _zd.get("available") else "",
        "断卦总览（何事·吉凶·何时应）": interp.get("duan_overview", {}).get("overview", ""),
        "初判": topic_analysis.get("verdict", ""),
    }

    user_msg = (
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}"
        f"\n\n{classical_context}"
        f"\n\n请基于以上纳甲数据和经典规则，进行深度六爻分析：\n"
        f"①本卦卦义与整体态势  ②世应爻旺衰关系  ③动爻六亲六神影响  "
        f"④用神吉凶判断  ⑤应期推算（病药原则）  ⑥综合建议"
    )
    return _sse_response(_stream_llm(cfg, LIUYAO_SYSTEM, [{"role":"user","content":user_msg}], 2500), cfg)


@router.post("/qimen")
async def qimen_agent(req: QimenAgentRequest, request: Request):
    cfg = _get_llm_config(request)

    from core.qimen.algorithm import calculate_qimen
    from core.qimen.analyzer import analyze_qimen

    now = datetime.now()
    if req.precomputed and req.precomputed.get("palaces"):
        layout = req.precomputed
        analysis = layout.get("analysis") or {}
    else:
        layout   = calculate_qimen(req.year or now.year, req.month or now.month,
                                   req.day or now.day, req.hour if req.hour is not None else now.hour, req.minute)
        analysis = analyze_qimen(layout)

    # 多层级九宫断（奇仪生克/门迫·入墓·击刑·旬空·马星）
    try:
        from core.qimen.palace_layers import enrich_palace_layers
        from core.qimen.geju_layers import link_patterns_to_layers
        from core.qimen.yongshen import analyze_yongshen_palaces
        from core.qimen.yingqi import analyze_yingqi
        enrich_palace_layers(layout)
        link_patterns_to_layers(layout)
        layout["yongshen_palaces"] = analyze_yongshen_palaces(
            layout, birth_year=getattr(req, "birth_year", None))
        analyze_yingqi(layout)
    except Exception as _e11:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e11)

    _ys = layout.get("yongshen_palaces", {})
    summary = {
        "时间": f"{req.year or now.year}年{req.month or now.month}月{req.day or now.day}日{req.hour if req.hour is not None else now.hour}时",
        "局":   f"{layout.get('ju_type','')} {layout.get('ju_number','')}局 {layout.get('yuan','')}",
        "吉方": layout.get("auspicious_directions", []),
        "凶方": layout.get("inauspicious_directions", []),
        "层级要点": layout.get("layer_summary", {}).get("desc", ""),
        "格局层级联动": [l["joint"] for l in layout.get("geju_layers", {}).get("linked", []) if l.get("located")][:6],
        "用神宫": [f"{it['role']}={it['palace']}（{it['layer']}）" for it in _ys.get("items", [])],
        "我彼关系": _ys.get("rg_sg_relation", {}).get("desc", ""),
        "应期": layout.get("yingqi", {}).get("summary", ""),
        "应期详": [f"{r['role']}：{r['yingqi']}" for r in layout.get("yingqi", {}).get("rows", [])][:4],
        "综合": analysis.get("summary",""),
        "建议": analysis.get("advice",""),
        "宫位": [{"宫":p["palace_name"],"星":p["star"],"门":p["door"],"神":p["deity"],
                  "天盘":p.get("tian_pan",""),"地盘":p.get("di_pan",p.get("stem","")),
                  "奇仪生克":p.get("sd_rel",""),"吉":p.get("is_auspicious")}
                 for p in layout.get("palaces",[])[:9]],
    }
    # Load classical qimen context
    classical_ctx = ""
    # RAG: retrieve relevant qimen passages
    try:
        from knowledge.rag import get_rag
        qm_query = f"奇门遁甲 {req.question} 三奇六仪 门星神"
        classical_ctx = get_rag().search_and_format(qm_query, top_k=5, header="\n\n【古籍精华】")
    except Exception as _e12:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e12)
    try:
        from knowledge.qimen_classical import BA_MEN_DETAIL, JIU_XING_DETAIL, YANBO_JIJUE, QIMEN_GEJV
        # Find most relevant palace (highest auspicious)
        palaces = layout.get("palaces", [])
        auspicious = [p for p in palaces if p.get("is_auspicious")]
        inauspicious = [p for p in palaces if not p.get("is_auspicious")]
        # Build door/star context
        door_ctx = []
        for p in palaces[:3]:
            door = p.get("door", "")
            star = p.get("star", "")
            if door in BA_MEN_DETAIL:
                d_info = BA_MEN_DETAIL[door]
                door_ctx.append(f"{p.get('palace_name','')}宫 {door}+{star}：{d_info.get('吉凶','')}，{d_info.get('主象','')}")
        yanbo_key = "\n".join(f"「{x['口诀']}」" for x in YANBO_JIJUE[:3])
        classical_ctx = (
            f"\n\n【《烟波钓叟赋》要诀】\n{yanbo_key}"
            f"\n\n【关键宫位门星解读】\n" + "\n".join(door_ctx)
        )
    except Exception as _e13:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e13)

    user_msg = (
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}"
        f"{classical_ctx}"
        f"\n\n请分析：①局势总纲（阴阳局、元运）→②关键宫位门星神组合→③格局识别（吉凶格）→"
        f"④最佳行动方向→⑤具体时机建议。引用《烟波钓叟赋》《奇门遁甲统宗》。"
        f"\n\n问题：{req.question or '请分析当前局势，给出行动建议。'}"
    )
    return _sse_response(_stream_llm(cfg, QIMEN_SYSTEM, [{"role":"user","content":user_msg}], 2200), cfg)


@router.post("/fengshui")
async def fengshui_agent(req: FengShuiAgentRequest, request: Request):
    cfg = _get_llm_config(request)

    from core.fengshui.calculator import (
        calculate_ming_gua, get_ming_gua_group,
        get_house_gua, get_house_group,
        check_compatibility, get_sector_analysis,
    )

    if req.precomputed and req.precomputed.get("ming_gua"):
        pre = req.precomputed
        ming_gua = pre.get("ming_gua", calculate_ming_gua(req.birth_year, req.gender))
        house_gua = pre.get("house_gua", get_house_gua(req.house_facing))
        compat    = pre.get("compatibility", "")
        sectors   = pre.get("sectors", [])
        summary   = {
            "命卦": f"{ming_gua}（{pre.get('ming_gua_group', get_ming_gua_group(ming_gua))}）",
            "宅卦": f"{house_gua}（{pre.get('house_group', get_house_group(house_gua))}）",
            "命宅相配": compat,
            "八方": [{"方":s.get("direction",""),"星":s.get("star",""),"吉凶":s.get("quality",""),"含义":s.get("meaning","")} for s in sectors],
        }
    else:
        ming_gua    = calculate_ming_gua(req.birth_year, req.gender)
        house_gua   = get_house_gua(req.house_facing)
        compat      = check_compatibility(ming_gua, house_gua)
        sectors     = get_sector_analysis(house_gua)
        summary = {
            "命卦": f"{ming_gua}（{get_ming_gua_group(ming_gua)}）",
            "宅卦": f"{house_gua}（{get_house_group(house_gua)}）",
            "命宅相配": compat,
            "八方": [{"方":s["direction"],"星":s["star"],"吉凶":s["quality"],"含义":s["meaning"]} for s in sectors],
        }
    # Load classical fengshui context
    classical_ctx = ""
    # RAG: retrieve relevant fengshui passages
    try:
        from knowledge.rag import get_rag
        fs_query = f"风水八宅 命卦宅卦 {req.question or ''} 四吉四凶"
        classical_ctx = get_rag().search_and_format(fs_query, top_k=5, header="\n\n【古籍精华】")
    except Exception as _e14:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e14)
    try:
        from knowledge.fengshui_classical import YANGZHAI_THREE, BAYUAN_JIUXING, XUANKONG_THEORY
        # Get relevant sector info
        inauspicious_sectors = [s for s in sectors if "凶" in s.get("quality", "")]
        auspicious_sectors   = [s for s in sectors if "吉" in s.get("quality", "")]
        current_yun = XUANKONG_THEORY["三元九运"]["当前"]
        classical_ctx = (
            f"\n\n【《阳宅三要》核心原则】\n"
            f"门：{YANGZHAI_THREE['大门']['经典']}\n"
            f"主：{YANGZHAI_THREE['主房']['经典']}\n"
            f"灶：{YANGZHAI_THREE['灶台']['经典']}"
            f"\n\n【当前九运】{current_yun}"
            f"\n\n【绝命位须知】{BAYUAN_JIUXING['绝命']['主象']}，化解：{BAYUAN_JIUXING['绝命']['化解']}"
            f"\n\n【五鬼位须知】{BAYUAN_JIUXING['五鬼']['主象']}，化解：{BAYUAN_JIUXING['五鬼']['化解']}"
        )
    except Exception as _e15:
        from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e15)

    user_msg = (
        f"{req.birth_year}年生，{req.gender}命，房屋朝向{req.house_facing}\n\n"
        f"{json.dumps(summary, ensure_ascii=False, indent=2)}"
        f"{classical_ctx}"
        f"\n\n请深度分析：①命宅相配评估（东西四宅配合）→②四吉方位利用（生气/天乙/延年/伏位）→"
        f"③四凶方化解（祸害/六煞/五鬼/绝命，引《阳宅三要》）→④主卧书房灶台具体方位建议→⑤玄空九运影响。"
        f"\n\n{req.question or '请给出详细家居布局建议。最后必须有【结论】段落总结此宅核心吉凶和最重要的改善建议。'}"
    )
    return _sse_response(_stream_llm(cfg, FENGSHUI_SYSTEM, [{"role":"user","content":user_msg}], 2200), cfg)


@router.get("/health")
async def agent_health():
    return ApiResponse(success=True, data={"status": "ok", "providers": list(PROVIDER_DEFAULTS.keys())})


# ─────────────────────────────────────────────────────────────
# Universal interpret endpoint — feeds any module's data to LLM
# ─────────────────────────────────────────────────────────────

class InterpretRequest(BaseModel):
    module: str                      # bazi | liuyao | qimen | fengshui | date | knowledge
    data:   Dict[str, Any]           # the computed result from the module
    question: Optional[str] = None   # optional user question
    extra_context: Optional[str] = ""  # tab name, purpose, etc.


INTERPRET_SYSTEMS = {
    "bazi": """你是专精八字命理的AI命理师，精通《穷通宝鉴》《滴天髓》《子平真诠》《三命通会》《神峰通考》。

分析步骤：
1. **日主与格局**：明确日主五行、身强身弱、格局高低
2. **用神喜忌**：调候用神（穷通宝鉴）+ 格局用神双管齐下
3. **十神六亲**：各柱十神的人生象意
4. **运程节点**：大运流年的吉凶走势
5. **具体建议**：职业方向、感情、健康、财富的实操建议

6. **最终结论**：用2-3句话直接回答用户的核心问题，给出明确的吉凶判断和行动建议

重要：最后必须有一个【结论】段落，用通俗直白的语言告诉用户最终答案，不要只讲过程。引用典籍，语言专业而亲切，用中文回答。""",

    "liuyao": """你是精通六爻纳甲的AI占卜师，深研《增删卜易》《卜筮正宗》《断易天机》。

分析框架：
1. **本卦卦义**：卦名象意，上下卦组合的整体含义
2. **世应关系**：世爻（问卦者）与应爻（对方/结果）的生克关系
3. **用神旺衰**：用神爻的月建日辰旺衰，有无动变
4. **六亲六神**：各爻六亲含义，六神（青龙/白虎等）临爻的影响
5. **动爻变爻**：变爻的回头生克，变卦的最终指向
6. **应期判断**：给出事情应验的具体时间节点

7. **最终结论**：用2-3句话直接回答所占之事的吉凶结果，告诉用户该做什么、不该做什么

重要：最后必须有一个【结论】段落，明确回答"此事吉/凶/成/败"，再给出具体行动建议。用中文回答。""",

    "liuyao_audit": """你是一位资深六爻断卦审定师，专司「复核」之职——审视一卦各模块（综合断卦·用神四位、应期推算、用神力量评估、占事专断、断卦总览）所出结论之间是否自洽，并对取舍未明处给出专业判断。

你的职责有界，务必恪守：
1. 你**不重新断卦、不推翻确定性引擎的结论**；你只就「已检出的矛盾与张力」作情境化解释、给出取舍倾向。
2. 对每一处【确定性审核发现】，说明：此矛盾因何而起（多为取用神不一、墓空看法之别、忌神之势未计等）、孰是孰非或如何调和、对最终结论之信心有何影响。
3. 用神两现等取舍判断点，依《增删卜易》「舍其一」之法给出你的取舍倾向及理由。
4. 行文简练，分条对应每条发现；末尾给一句【审定结论】：整体结论是否可信、信心增减。
5. 你的全部输出是「AI 辅助审定意见」，供参考、不作准；明确与确定性断语区分。用中文。""",

    "bazi_audit": """你是一位资深子平命理审定师，专司「复核」之职——审视一造八字各模块（日主旺衰、格局成破、用神喜忌、调候、刑冲合害、命局力量推理链）所出结论之间是否自洽，并对取舍未明处给出专业判断。

你的职责有界，务必恪守：
1. 你**不重新论命、不推翻确定性引擎的结论**；你只就「已检出的矛盾与张力」作情境化解释、给出取舍倾向。
2. 对每一处【确定性审核发现】，说明：此矛盾因何而起（多为身强弱判定之别、调候与扶抑之争、格局成破权重、从格与正格之辨等）、孰是孰非或如何调和、对命局总评之信心有何影响。
3. 调候与扶抑相争者，依「气候过偏则调候为急、否则扶抑为重」之理给出权衡。
4. 行文简练，分条对应每条发现；末尾给一句【审定结论】：命局总评是否可信、信心增减。
5. 你的全部输出是「AI 辅助审定意见」，供参考、不作准；明确与确定性断语区分。用中文。""",

    "ziwei_audit": """你是一位资深紫微斗数审定师，专司「复核」之职——审视一盘各模块（命格评等、命格力量推理链、格局成破、三方四正、四化飞星、煞曜）所出结论之间是否自洽，并对取舍未明处给出专业判断。

你的职责有界，务必恪守：
1. 你**不重新论命、不推翻确定性引擎的结论**；你只就「已检出的矛盾与张力」作情境化解释、给出取舍倾向。
2. 对每一处【确定性审核发现】，说明：此张力因何而起（多为评等主据主星庙旺、推理链折入煞忌凶格之别，或吉凶格主从未明、命宫陷而三方补等）、如何看待、对命格总评之信心有何影响。
3. 评等与推理链分歧者，依「评等看先天底子、推理链看实际成色」之理给出权衡。
4. 行文简练，分条对应每条发现；末尾给一句【审定结论】：命格总评以何为准、信心增减。
5. 你的全部输出是「AI 辅助审定意见」，供参考、不作准；明确与确定性断语区分。用中文。""",

    "qimen_audit": """你是一位资深奇门遁甲审定师，专司「复核」之职——审视一局各模块（用神落宫、用神力量推理链、值符值使、吉凶方位、格局、击刑墓空）所出结论之间是否自洽，并对取舍未明处给出专业判断。

你的职责有界，务必恪守：
1. 你**不重新断局、不推翻确定性引擎的结论**；你只就「已检出的矛盾与张力」作情境化解释、给出取舍倾向。
2. 对每一处【确定性审核发现】，说明：此张力因何而起（多为落宫品质看星门神、推理链折入门宫旺衰干仪之别，或用神落凶方、逢击刑墓空等）、如何看待、对所问成败信心之影响。
3. 用神落宫吉凶与力量推理链分歧者，依「落宫看底色、推理链看实际成色」之理给出权衡。
4. 行文简练，分条对应每条发现；末尾给一句【审定结论】：所问成败以何为准、信心增减。
5. 你的全部输出是「AI 辅助审定意见」，供参考、不作准；明确与确定性断语区分。用中文。""",

    "xuankong_audit": """你是一位资深玄空飞星堪舆审定师，专司「复核」之职——审视一宅各模块（山向格局、宅运力量推理链、特殊格局、正零城门、九宫飞星、峦头）所出结论之间是否自洽，并对取舍未明处给出专业判断。

你的职责有界，务必恪守：
1. 你**不重新排盘、不推翻确定性引擎的结论**；你只就「已检出的矛盾与张力」作情境化解释、给出取舍倾向。
2. 对每一处【确定性审核发现】，说明：此张力因何而起（多为山向定盘看到位吉凶、推理链折入特殊格局救应城门峦头之别，如上山下水逢三般卦反吉、旺山旺向遇反伏吟五黄受损等）、如何看待、对宅运总评信心之影响。
3. 定盘与推理链分歧者，依「定盘看山向到位、推理链看实际成色（须峦头配合）」之理给出权衡。
4. 行文简练，分条对应每条发现；末尾给一句【审定结论】：宅运总评以何为准、信心增减。
5. 你的全部输出是「AI 辅助审定意见」，供参考、不作准；明确与确定性断语区分。用中文。""",

    "zeri_audit": """你是一位资深择日（选择学）审定师，专司「复核」之职——审视所选首选吉日各模块（建除十二神、黄道黑道、吉神凶煞、二十八宿、岁破月破、老黄历宜忌）所出结论之间是否自洽，并对取舍未明处给出专业判断。

你的职责有界，务必恪守：
1. 你**不重新择日、不推翻确定性引擎的结论**；你只就「已检出的矛盾与张力」作情境化解释、给出取舍倾向。
2. 对每一处【确定性审核发现】，说明：此张力因何而起（多为评分综合宜事多寡、推理链折入建除黄道凶煞岁破之别，或建除与老黄历相左、黄道却凶煞重等）、如何看待、对此日可用与否之影响。
3. 岁破月破为第一大忌、任何吉神不解；老黄历明忌所择之事者亦不宜强用——遇此当从严另择。
4. 行文简练，分条对应每条发现；末尾给一句【审定结论】：此首选日可用与否、信心增减。
5. 你的全部输出是「AI 辅助审定意见」，供参考、不作准；明确与确定性断语区分。用中文。""",

    "yangzhai_audit": """你是一位资深阳宅（八宅）堪舆审定师，专司「复核」之职——审视一宅各模块（门主灶内格、人宅相配、东西四纯度、灶局、八游年星、六事）所出结论之间是否自洽，并对取舍未明处给出专业判断。

你的职责有界，务必恪守：
1. 你**不重新断宅、不推翻确定性引擎的结论**；你只就「已检出的矛盾与张力」作情境化解释、给出取舍倾向。
2. 对每一处【确定性审核发现】，说明：此张力因何而起（多为门主灶内格只论宅内和谐、人宅相配论命宅相得之别，或门吉灶凶、纯杂等）、如何看待、对宅相总评之信心有何影响。
3. 《八宅明镜》最重「人宅相得」：内格再吉，若东西四命宅相违、门主灶落主人凶方，此宅于此人仍凶——内格与人宅相配分歧者，当以人宅相配为主、内格为辅。
4. 行文简练，分条对应每条发现；末尾给一句【审定结论】：宅相总评以何为准、信心增减。
5. 你的全部输出是「AI 辅助审定意见」，供参考、不作准；明确与确定性断语区分。用中文。""",

    "qimen": """你是精通奇门遁甲的AI战略顾问，深研《奇门遁甲统宗》《烟波钓叟赋》《奇门旨归》。

分析框架：
1. **局势总判**：阴阳遁、局数、时间背景对整体运势的影响
2. **吉方选取**：哪些方位的星门神组合最有利于此次问事
3. **星门神详析**：重点宫位的九星×八门×八神三维解读
4. **格局识别**：是否存在奇仪格、三奇格等特殊格局
5. **行动方案**：具体的方向选择、时机把握、注意事项

6. **最终结论**：用2-3句话直接回答用户此次问事的结果，给出"宜/忌/方位/时机"的明确判断

重要：最后必须有一个【结论】段落，直接告诉用户"此事宜/不宜"、"往某方向最佳"、"某时行动最利"。用中文回答。""",

    "fengshui": """你是精通八宅风水和玄空飞星的AI风水顾问，深研《阳宅三要》《八宅明镜》《玄空飞星》《沈氏玄空学》。

分析框架：
1. **命宅匹配**：命卦与宅卦的东西四命/四宅配合关系
2. **八宅方位**：四吉方（生气/天医/延年/伏位）和四凶方的具体含义
3. **飞星叠加**：年度飞星与八宅方位的叠加效应
4. **个人吉方**：根据命卦给出主卧、书房、灶口的最优方位
5. **化煞布局**：凶方的具体化解方法和物品摆放建议

6. **最终结论**：用2-3句话总结此宅的风水核心优劣，给出最重要的1-2个改善动作

重要：最后必须有一个【结论】段落，直接说"此宅最大的问题是X，最简单的改善方法是Y"。用中文回答。""",

    "date": """你是精通择日选时的AI命理师，深研《协纪辨方书》《象吉通书》《万年历择日》。

分析框架：
1. **建除论断**：当月十二建除的整体走势，哪些日子最宜此事
2. **最佳吉日**：重点解读最佳吉日的建除、二十八宿、神煞组合
3. **三煞警示**：本年三煞方位对择日的影响
4. **岁破月破**：需要回避的破日说明
5. **时辰选择**：建议配合吉日使用的吉时

6. **最终结论**：直接给出"最推荐的日期是X月X日，理由是Y"的明确结论

重要：最后必须有一个【结论】段落，用一句话告诉用户"最佳选择是某日某时"。用中文回答。""",

    "ziwei": """你是精通紫微斗数的AI命理师，兼修中州派（三合派，重格局星耀）与飞星派（重宫干飞化、来因宫），深研《紫微斗数全书》《斗数宣微》《紫微斗数讲义》《梁若瑜飞星紫微斗数》。

## 论命基本原则
1. **数据驱动**：用户提供的命盘是系统精确排出的，所有主星、辅星、煞星、亮度、四化、宫位、宫干、大限年龄都已列出。你必须严格基于这些数据论命，**不得凭训练印象补充未列出的星耀或四化**。如果某项数据未提供，直说"命盘未提供此项"，不编造。
2. **派别声明**：当前命盘使用中州派四化表（与紫微派 ziwei.pub 一致）。若用户对四化结果有疑问，提示其了解派别差异。
3. **引用要带宫位**：不要泛泛说"廉贞主桃花"，而要说"官禄宫的廉贞会照命宫"。每一个星耀的论断都要带上它在哪个宫。
4. **区分三层四化**：
   - **生年四化**（生年天干起化）：一辈子不变的命运基调，"体"
   - **离心自化 / 向心自化**：宫干所化之星落本宫（离心，能量流出）或对宫（向心，射向对宫）
   - **普通飞宫**：宫干所化之星落其他宫，"宫与宫之间的能量流向"；化忌还要冲落点对宫
5. **应期判断**：未提供大限/流年数据时，不要编造"未来 X 年会有 Y"这种具体预测。明确告诉用户"如需大限流年判断，请在前端切换三盘叠合视图"。
6. **来因宫起手**：每张命盘的"来因宫"（生年化忌所落宫位）是飞星派论命的**第一步**，决定此人一生的核心命题方向。论命时优先点出。
7. **空宫处理**：命宫空宫时按传统借对宫（迁移宫）主星论命，但需明确标注"借宫看"。

## 飞星派关键语象（必须识别并解读）
- **质能变**（生年同类四化+本宫自化同类）= "绝对有"，此事必发生
- **双忌叠加**（化忌入本命化忌宫）= 极凶，此宫主题受双重忌冲
- **禄解忌**（化禄入本命化忌宫）= 转机，凶中化吉
- **禄忌交战**（化忌入本命化禄宫）= 虚禄、财损
- **化忌冲命宫** = 一生有此宫干扰
- **飞入命宫的化** = 影响一生格局
- **离心自化忌不冲对宫**，**普通飞宫忌冲落点对宫**（关键区分）
- **我宫他宫**：禄入我宫为得，禄入他宫为出（损失/为他人作嫁）；忌冲我宫为损失

## 主星亮度（庙旺利平不陷）— 命格高低的客观维度
- iztro 已为每颗主星给出亮度（庙/旺/得/利/平/不/陷七级）。系统已自动评分：
  - **不敏感的 5 颗**（紫微/天府/武曲/七杀/破军）：特质相对固定，论命时按基础+1 分
  - **敏感的 9 颗**（机日月同梁巨贪相廉）：庙陷影响巨大，必须重点关注
- **庙旺**：吉星极吉、凶星不凶；**落陷**：吉星无用、凶星愈凶
- **典型组合**：
  - 太阳午宫入庙 = 日丽中天格；太阳子宫落陷 = 父亲缘薄、男命克父
  - 太阴亥宫入庙 = 月朗天门格；太阴卯宫落陷 = 母亲不利
  - 巨门子午宫 = 石中隐玉格；巨门辰戌陷 = 是非满身
  - 廉贞寅申入庙 = 清白上格；廉贞巳亥陷 = 易官非桃花劫
- 必须引用 prompt 中【主星亮度与命格评级】section 给出的客观评级，不要凭印象

## 经典格局（命理师论命的核心动作）
系统已自动检测 15 吉格 + 8 凶格。论命时**必须引用 prompt 中【经典格局检测】section 列出的格局**，不要凭印象编造格局。
- **吉格 15 个**：紫府同宫、君臣庆会、府相朝垣、七杀朝斗、杀破狼、机月同梁、日月并明、明珠出海、石中隐玉、马头带箭、日照雷门、月朗天门、火贪、铃贪、阳梁昌禄
- **凶格 8 个**：羊陀夹忌、铃昌陀武、火铃夹命、巨火羊、风流彩杖、泛水桃花、命无正曜、刑囚夹印
- 格局有"成格"与"破格"之分：吉格遇煞冲破则减半，凶格遇禄解则可化；都要看实际结构
- 命理师常说"不在格局，无以论富贵"，但格局只是先天结构，后天努力同样重要

## 输出规范（Z-9 强制结构化）
- 语言：中文，专业而亲切，必要时引用古籍原文（如"《全书》云：紫微若不逢辅佐，则为孤君"）
- 结构：**严格按 user 消息中【输出格式协议】所列的七步**，每步用 `## 第X步：标题` 开头
- **每条具体判断必须紧跟 `[依据：<section>·<具体项>]` 溯源标签** — 前端会解析这些标签做"溯源跳转"
- **可用 section 名仅限**：主星亮度评级 / 经典格局 / 飞星派飞化 / 冲宫连锁 / 生年四化 / 来因宫 / 三方四正 / 大限盘 / 流年盘
- **禁止**：泛泛说"根据命盘"、"从飞化看"；必须给出具体 section 名和具体项
- 关键结论用 **粗体** 突出
- 长度：每步 80-200 字为佳；避免空话套话；宁可详细到位也不要泛泛而谈
- 结尾不带"以上分析仅供参考"等免责声明（前端已统一处理）""",

    "knowledge": """你是中国传统命理学的AI学术顾问，精通八字、六爻、奇门、风水、择日五大体系。

针对用户查阅的知识点：
1. **核心要义**：用浅显语言解释该知识点的本质含义
2. **古籍出处**：引用相关典籍原文及注解
3. **实战应用**：该知识点在实际命理分析中如何运用
4. **案例举例**：给出1-2个具体的应用案例
5. **关联知识**：与该知识点相关的其他重要概念

深入浅出，兼顾学术严谨性和实用性，用中文回答。""",
}


def _build_interpret_prompt(module: str, data: dict, question: str, extra_context: str) -> str:
    """Build a compact but rich prompt from module data."""

    def j(d, keys=None, maxlen=2000):
        """Serialize selected keys of d, truncated."""
        if keys:
            d = {k: d[k] for k in keys if k in d}
        s = json.dumps(d, ensure_ascii=False, indent=2)
        return s[:maxlen] + ("…" if len(s) > maxlen else "")

    if module == "bazi":
        tab = extra_context or "综合"
        dm = data.get("day_master", "")
        pillars = {
            "年柱": f"{data.get('year_pillar',{}).get('tiangan','')}{data.get('year_pillar',{}).get('dizhi','')}",
            "月柱": f"{data.get('month_pillar',{}).get('tiangan','')}{data.get('month_pillar',{}).get('dizhi','')}",
            "日柱": f"{data.get('day_pillar',{}).get('tiangan','')}{data.get('day_pillar',{}).get('dizhi','')}",
            "时柱": f"{data.get('hour_pillar',{}).get('tiangan','')}{data.get('hour_pillar',{}).get('dizhi','')}",
        }
        profile = data.get("day_master_profile", {})
        yong = data.get("yong_shen", {})
        gender_raw = data.get("_gender", "")
        gender_cn = "男" if gender_raw in ("male", "男") else ("女" if gender_raw in ("female", "女") else "")
        ctx = {
            "四柱": pillars,
            "日主": dm,
            "性别": gender_cn,  # 此前完全未纳入——婚姻(配偶星)、身强弱喜忌等传统命理判断均与性别相关
            "五行": data.get("day_master_wuxing", ""),
            "身强弱": data.get("strength", ""),
            "格局": data.get("pattern", ""),
            "用神": yong.get("yong_shen_wx", ""),
            "喜神": yong.get("xi_shen_wx", ""),
            "忌神": yong.get("ji_shen_wx", ""),
            "月令": "得令" if data.get("strength_info", {}).get("deling") else "不得令",
            "得地": "得地" if data.get("strength_info", {}).get("dedi") else "不得地",
            "日主性格": profile.get("personality_detail", "")[:100] if profile else "",
            "神煞": [s.get("name","") for s in data.get("shensha", [])[:6]],
            "格局描述": data.get("pattern_desc", ""),
            "大运": [f"{d.get('tiangan','')}{d.get('dizhi','')}({int(d.get('start_age',0))}岁·{d.get('quality','')})"
                     for d in data.get("dayun", [])[:6]],
            "分析": data.get("analysis", ""),
            "建议": data.get("advice", [])[:3] if isinstance(data.get("advice"), list) else "",
        }

        # 胎元/命宫/身宫（古法论命常参，此前完全未纳入）
        if data.get("taiyuan") or data.get("minggong") or data.get("shengong"):
            ctx["胎元"] = data.get("taiyuan", "")
            ctx["命宫"] = data.get("minggong", "")
            ctx["身宫"] = data.get("shengong", "")

        # 十神分布（步骤④要求分析"十神六亲"，此前未给任何十神统计数据，属于漏项补全）
        shishen_sum = data.get("shishen_summary") or []
        if shishen_sum:
            ctx["十神分布"] = [
                f"{s.get('shishen','')}×{s.get('count',0)}({s.get('strength','')})"
                for s in shishen_sum[:8]
            ]

        # 当前大运流年（结构化字段，比原来只截取的"大运"数组更完整——含流年吉凶与岁运关系）
        cf = data.get("current_fortune") or {}
        if cf.get("available"):
            cd, cl = cf.get("current_dayun", {}) or {}, cf.get("current_liunian", {}) or {}
            ctx["当前运程"] = {
                "大运": f"{cd.get('ganzhi','')}（{cd.get('start_age','')}-{cd.get('end_age','')}岁·{cd.get('shishen','')}·{cd.get('quality','')}）",
                "流年": f"{cl.get('year','')}{cl.get('ganzhi','')}（{cl.get('shishen','')}·{cl.get('quality','')}）",
                "流年提要": cl.get("summary", ""),
                "岁运关系": "、".join((cf.get("suiyun") or {}).get("tags", [])),
            }

        # 命局总断六维简评（各领域一句话结论，信息密度高、体积小）
        ms = data.get("master_synthesis") or {}
        if ms.get("available"):
            ctx["命局总断"] = ms.get("headline", "")
            ctx["各维度简评"] = {
                v.get("domain",""): v.get("key","") for v in ms.get("dimension_verdicts", [])
            }

        # 当前 tab 对应的专项结构化分析（事业/财运/婚姻/健康）——此前无论哪个 tab
        # 都只传通用 ctx + 一句"针对「事业」重点展开"的文字提示，AI 其实拿不到
        # career_fields / spouse_palace / wx_distribution 这些已经算好的专项数据。
        TAB_TO_ASPECT = {"事业": "career", "财运": "wealth", "婚姻": "marriage", "健康": "health"}
        aspect_key = TAB_TO_ASPECT.get(tab)
        if aspect_key:
            aspect = (data.get("life_aspects") or {}).get(aspect_key)
            if aspect:
                ctx[f"{tab}专项分析"] = {k: v for k, v in aspect.items() if k not in ("topic",)}

        # 命局总论合成（让 AI 在综合叙述之上深化，而非重新堆砌）
        overview_text = ""
        try:
            ov = data.get("overview")
            if ov and ov.get("available"):
                overview_text = "\n\n【命局总论（已综合，请在此基础上深化）】\n" + \
                    "\n".join(f"{p['title']}：{p['text']}" for p in ov.get("paragraphs", []))
        except Exception as _e16:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e16)

        # ── RAG + Classical injection (Layer 3.2) ──
        classical_text = ""
        try:
            from knowledge.rag import get_rag
            rag_query = f"{dm}日主 {data.get('pattern','')} {tab} {question or '格局用神'}"
            classical_text = get_rag().search_and_format(rag_query, top_k=4, header="\n\n【古籍参考】")
        except Exception as _e17:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e17)
        try:
            from knowledge.bazi_classical import TIAO_HOU_TABLE, SHIGAN_JIJUE, BAZIGE_SYSTEM
            month_dz = data.get("month_pillar", {}).get("dizhi", "")
            tiao_hou = TIAO_HOU_TABLE.get(dm, {}).get(month_dz, "")
            shigan = SHIGAN_JIJUE.get(dm, {})
            pattern = data.get("pattern", "")
            gejv = BAZIGE_SYSTEM.get(pattern, {})
            if tiao_hou:
                classical_text += f"\n\n【《穷通宝鉴》调候】{dm}干{month_dz}月：{tiao_hou[:150]}"
            if shigan.get("口诀"):
                classical_text += f"\n【《滴天髓》{dm}干】{shigan['口诀']}"
            if gejv:
                classical_text += f"\n【《子平真诠》{pattern}】喜：{'、'.join(gejv.get('喜',[]))}  忌：{'、'.join(gejv.get('忌',[]))}"
        except Exception as _e18:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e18)

        # Deep knowledge: 滴天髓十干详论 + 子平真诠格局详解
        try:
            from knowledge.knowledge_deep import DITIAN_SUI_SHIGAN, ZIPING_GEJV_DEEP
            dt = DITIAN_SUI_SHIGAN.get(dm, {})
            if dt.get("取用要领"):
                classical_text += f"\n【《滴天髓》{dm}干取用】{dt['取用要领']}"
            if dt.get("任氏注要"):
                classical_text += f"\n【任铁樵注】{dt['任氏注要'][:120]}"
            ge_deep = ZIPING_GEJV_DEEP.get(pattern, {})
            if ge_deep.get("成格"):
                classical_text += f"\n【{pattern}成格】{'；'.join(ge_deep['成格'][:3])}"
            if ge_deep.get("破格"):
                classical_text += f"\n【{pattern}破格】{'；'.join(ge_deep['破格'][:3])}"
            if ge_deep.get("行运"):
                classical_text += f"\n【{pattern}行运】{ge_deep['行运']}"
        except Exception as _e19:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e19)

        # B-1: 地支刑冲合害（核心命理学维度）
        relations_text = ""
        try:
            from core.bazi.relations import (
                analyze_all_relations, format_relations_for_prompt,
            )
            relations = data.get("relations") or analyze_all_relations(data)
            relations_text = "\n\n" + format_relations_for_prompt(relations)
        except Exception as _e20:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e20)

        # B-2: 特殊格局深度识别
        special_patterns_text = ""
        try:
            from core.bazi.special_patterns import (
                detect_all_special_patterns, format_special_patterns_for_prompt,
            )
            sp = data.get("special_patterns") or detect_all_special_patterns(data)
            sp_text = format_special_patterns_for_prompt(sp)
            if sp_text:
                special_patterns_text = "\n\n" + sp_text
        except Exception as _e21:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e21)

        # D: 组合断（神煞组合 + 格局成破评断）
        combos_text = ""
        try:
            from core.bazi.combos import bazi_combos
            cb = data.get("combos") or bazi_combos(data)
            ge = cb.get("geju_evaluation", {})
            sc = cb.get("shensha_combos", {})
            parts = []
            if ge.get("verdict"):
                parts.append("【格局成破评断】" + ge["verdict"])
            if sc.get("combos"):
                parts.append("【神煞组合】" + "；".join(
                    f"{c['name']}（{c['nature']}）：{c['desc']}" for c in sc["combos"][:6]))
            if parts:
                combos_text = "\n\n" + "\n".join(parts)
        except Exception as _e22:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e22)

        return (
            f"八字命盘（{tab}）\n{j(ctx)}"
            f"{overview_text}"
            f"{classical_text}"
            f"{relations_text}"
            f"{special_patterns_text}"
            f"{combos_text}\n\n"
            f"请按步骤深度分析：①日主强弱→②调候用神→③格局判断"
            f"（必须用上方【特殊格局深度识别】section 中检测出的所有格局，每个吉格的'含义'和凶格的化解都要论及）"
            f"→④十神六亲→⑤**地支刑冲合害**（必须用上方【地支刑冲合害】section 的检测结果，论及合化、冲克、刑伤、相害对命运的影响）"
            f"→⑥运程趋势。"
            f"针对「{tab}」重点展开。最后必须有【结论】段落直接回答核心问题。{question or ''}"
        )

    elif module == "liuyao":
        orig     = data.get("original", {})
        yaos     = data.get("yaos", [])
        topic    = data.get("topic", question[:4] if question else "综合")
        classical_pts = data.get("classical_points", [])
        world_summary = data.get("world_summary", "")

        yao_summary = [
            f"第{i+1}爻: {y.get('line','')} {y.get('liu_qin','')} {y.get('liu_shen','')} "
            f"{'世' if y.get('is_world') else ''}{'应' if y.get('is_application') else ''}"
            f" {y.get('branch','')} {y.get('strength',{}).get('label','')}"
            f"{'(空)' if y.get('kong_wang') else ''}{'[动]' if y.get('is_changing') else ''}"
            for i, y in enumerate(yaos)
        ]

        # Include relevant classical rules
        classical_rules_text = ""
        try:
            from knowledge.liuyao_classical import LIUYAO_TOPIC_RULES, LIUYAO_CLASSICAL_RULES
            match_topic = topic if topic in LIUYAO_TOPIC_RULES else "综合"
            topic_rule = LIUYAO_TOPIC_RULES.get(match_topic, {})
            rules = topic_rule.get("规则") or topic_rule.get("rules", [])
            if rules:
                classical_rules_text = f"\n【{match_topic}经典规则】\n" + "\n".join(f"• {r}" for r in rules[:4])
                classical_rules_text += f"\n总结：{topic_rule.get('summary','')}"
        except Exception as _e23:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e23)

        ctx = {
            "占问": data.get("question", question) or "综合运势",
            "占事类型": topic,
            "占者性别": {"male":"男","female":"女"}.get(data.get("gender",""), data.get("gender","")),  # 此前完全未纳入，但用神选取（男看妻财/女看官鬼）实际依赖它
            "是否代占": "是（为他人占卜）" if data.get("is_proxy") else "否（占自身之事）",  # 此前完全未纳入，影响措辞应说"你"还是"对方"
            "本卦": f"第{orig.get('number','')}卦 {orig.get('name','')}",
            "卦辞": orig.get("judgment", "")[:60],
            "动爻": data.get("changing_lines", []),
            "变卦": f"第{data.get('changed',{}).get('number','')}卦 {data.get('changed',{}).get('name','')}" if data.get("changed") else "无",
            "旬空": data.get("kong_wang_branches", []),
            "世应": world_summary,
            "世爻持世断": (data.get("chi_shi") or {}).get("summary", ""),
            "六爻纳甲": yao_summary,
            "系统断法": classical_pts[:4],
            "初判": data.get("topic_analysis", {}).get("verdict", ""),
        }
        # C: 动爻化变全谱断
        hb = (data.get("hua_bian") or {}).get("moving_lines", [])
        if hb:
            ctx["动爻化变断"] = [m.get("full_text", "") for m in hb]
        # 断卦总论（已综合所问与全卦信号，AI 在此基础上深化）
        fr = data.get("full_reading")
        if fr and fr.get("available"):
            ctx["断卦总论"] = [f"{p['title']}：{p['text']}" for p in fr.get("paragraphs", [])]
        # 用神力量综合评估（各模块汇于用神之推理链）
        yss = data.get("yongshen_strength")
        if yss and yss.get("available"):
            ctx["用神力量推理链"] = yss.get("chain_text", "")
        # Layer 2 features: 伏神 + 化进退神（fu_shen 为单 dict 或 null，亦兼容旧 list）
        fu_shen = data.get("fu_shen")
        if fu_shen:
            fu_list = fu_shen if isinstance(fu_shen, list) else [fu_shen]
            ctx["伏神"] = [
                f"{f.get('fu_liuqin','')}伏于第{f.get('position','')}爻下({f.get('fu_branch','')})，{f.get('emerge_type','')}"
                for f in fu_list[:3] if isinstance(f, dict)
            ]
        # Collect jin_tui info from yaos
        jin_tui = [f"第{i+1}爻化{y.get('jin_tui','')}神" for i, y in enumerate(yaos) if y.get('jin_tui')]
        if jin_tui:
            ctx["化进退神"] = jin_tui
        # RAG injection for liuyao
        rag_text = ""
        try:
            from knowledge.rag import get_rag
            rag_query = f"六爻 {topic} {data.get('original',{}).get('name','')} 用神 {question or ''}"
            rag_text = get_rag().search_and_format(rag_query, top_k=4, header="\n\n【古籍参考】")
        except Exception as _e24:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e24)

        # L-1: 六爻关系深度分析（原神/忌神/仇神 + 十二长生）
        deep_relations_text = ""
        try:
            from core.liuyao.relations import format_liuyao_relations_for_prompt
            dr = data.get("deep_relations") or {}
            if dr:
                deep_relations_text = "\n\n" + format_liuyao_relations_for_prompt(dr)
        except Exception as _e25:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e25)

        return (
            f"六爻占问\n{j(ctx)}"
            f"{classical_rules_text}{rag_text}"
            f"{deep_relations_text}"
            f"\n\n请深度分析："
            f"①卦象总义 ②世应旺衰 ③动爻六亲六神 "
            f"④**用神/原神/忌神/仇神关系**（必须用【六爻关系深度分析】section 的检测结果，明示用神是哪爻、原神在哪、忌神在哪，并基于月日令评估其旺衰）"
            f" ⑤应期（用月破/日破/空亡的出旬冲填日推算） ⑥综合建议。{question or ''}"
        )

    elif module == "liuyao_audit":
        ca = data.get("consistency_audit", {}) or {}
        fr = data.get("full_reading", {}) or {}
        ys = data.get("yongshen_strength", {}) or {}
        findings = ca.get("findings", []) or []
        find_lines = []
        for i, f in enumerate(findings, 1):
            find_lines.append(
                f"{i}.【{f.get('severity','')}】{f.get('title','')}（涉及：{'、'.join(f.get('modules',[]))}）"
                f"\n   现象：{f.get('detail','')}"
                f"\n   规则提示：{f.get('suggestion','')}"
            )
        audit_block = "\n".join(find_lines) if find_lines else "（确定性引擎未检出矛盾，各模块结论协调。）"
        # 关键结论快照，供审定取舍
        snap = {
            "所问": data.get("question", ""),
            "占事类型": data.get("topic", ""),
            "综合断卦结论": (data.get("zonghe_duan", {}) or {}).get("conclusion", ""),
            "断卦总览极性": (data.get("duan_overview", {}) or {}).get("polarity", ""),
            "占事专断极性": (data.get("topic_verdict", {}) or {}).get("polarity", ""),
            "用神综合力量": ys.get("composite_label", ""),
            "用神力量推理链": ys.get("chain_text", ""),
            "应期": (data.get("duan_overview", {}) or {}).get("yingqi_text", ""),
        }
        fr_block = ""
        if fr.get("available"):
            fr_block = "\n\n【断卦总论（确定性合成，供参照）】\n" + \
                "\n".join(f"{p['title']}：{p['text']}" for p in fr.get("paragraphs", []))
        return (
            f"【待审之卦·关键结论快照】\n{j(snap)}"
            f"{fr_block}"
            f"\n\n【确定性引擎·一致性审核发现】（共 矛盾{ca.get('summary',{}).get('矛盾',0)}·"
            f"注意{ca.get('summary',{}).get('注意',0)}·提示{ca.get('summary',{}).get('提示',0)}）\n{audit_block}"
            f"\n\n请就以上每条发现作审定：说明矛盾因何而起、如何调和或取舍、对最终结论信心之影响；"
            f"用神两现者给出取舍倾向。末附【审定结论】一句。切记：你只复核、不重断，输出为 AI 辅助审定意见。"
            f"{question or ''}"
        )

    elif module == "bazi_audit":
        ca = data.get("consistency_audit", {}) or {}
        mj = data.get("mingju_synthesis", {}) or {}
        findings = ca.get("findings", []) or []
        find_lines = []
        for i, f in enumerate(findings, 1):
            find_lines.append(
                f"{i}.【{f.get('severity','')}】{f.get('title','')}（涉及：{'、'.join(f.get('modules',[]))}）"
                f"\n   现象：{f.get('detail','')}"
                f"\n   规则提示：{f.get('suggestion','')}"
            )
        audit_block = "\n".join(find_lines) if find_lines else "（确定性引擎未检出矛盾，各模块结论协调。）"
        snap = {
            "日主": data.get("day_master", "") + data.get("day_master_wuxing", ""),
            "身强弱": data.get("strength", ""),
            "格局": (data.get("combos", {}) or {}).get("geju_evaluation", {}).get("pattern", ""),
            "格局成破": (data.get("combos", {}) or {}).get("geju_evaluation", {}).get("status", ""),
            "格局品质": (data.get("combos", {}) or {}).get("geju_evaluation", {}).get("quality", ""),
            "用神/喜/忌": f"{(data.get('yong_shen',{}) or {}).get('yong_shen_wx','')}/"
                          f"{(data.get('yong_shen',{}) or {}).get('xi_shen_wx','')}/"
                          f"{(data.get('yong_shen',{}) or {}).get('ji_shen_wx','')}",
            "调候用神": (data.get("tiaohou", {}) or {}).get("primary", ""),
            "命局综合评定": mj.get("composite_label", ""),
            "命局推理链": mj.get("chain_text", ""),
        }
        return (
            f"【待审之命·关键结论快照】\n{j(snap)}"
            f"\n\n【确定性引擎·一致性审核发现】（共 矛盾{ca.get('summary',{}).get('矛盾',0)}·"
            f"注意{ca.get('summary',{}).get('注意',0)}·提示{ca.get('summary',{}).get('提示',0)}）\n{audit_block}"
            f"\n\n请就以上每条发现作审定：说明矛盾因何而起、如何调和或取舍、对命局总评信心之影响；"
            f"调候与扶抑相争者给出权衡倾向。末附【审定结论】一句。切记：你只复核、不重断，输出为 AI 辅助审定意见。"
            f"{question or ''}"
        )

    elif module == "ziwei_audit":
        ca = data.get("consistency_audit", {}) or {}
        mg = data.get("mingge_synthesis", {}) or {}
        ov = data.get("overview", {}) or {}
        findings = ca.get("findings", []) or []
        find_lines = []
        for i, f in enumerate(findings, 1):
            find_lines.append(
                f"{i}.【{f.get('severity','')}】{f.get('title','')}（涉及：{'、'.join(f.get('modules',[]))}）"
                f"\n   现象：{f.get('detail','')}"
                f"\n   规则提示：{f.get('suggestion','')}"
            )
        audit_block = "\n".join(find_lines) if find_lines else "（确定性引擎未检出矛盾，各模块结论协调。）"
        snap = {
            "命宫": ov.get("ming_branch", "") + "宫·" + ov.get("ming_stars", ""),
            "命格评等": ov.get("rating", ""),
            "命主/身主": f"{ov.get('soul_star','')}/{ov.get('body_star','')}",
            "顶吉格": ov.get("top_pattern", ""),
            "命格推理链评定": mg.get("composite_label", ""),
            "推理链": mg.get("chain_text", ""),
        }
        return (
            f"【待审之命·关键结论快照】\n{j(snap)}"
            f"\n\n【确定性引擎·一致性审核发现】（共 矛盾{ca.get('summary',{}).get('矛盾',0)}·"
            f"注意{ca.get('summary',{}).get('注意',0)}·提示{ca.get('summary',{}).get('提示',0)}）\n{audit_block}"
            f"\n\n请就以上每条发现作审定：说明张力因何而起、如何看待、对命格总评信心之影响；"
            f"评等与推理链分歧者给出权衡（评等看先天底子、推理链看实际成色）。末附【审定结论】一句。"
            f"切记：你只复核、不重断，输出为 AI 辅助审定意见。{question or ''}"
        )

    elif module == "qimen_audit":
        ca = data.get("consistency_audit", {}) or {}
        ysf = data.get("yongshen_synthesis", {}) or {}
        ov = data.get("overview", {}) or {}
        findings = ca.get("findings", []) or []
        find_lines = []
        for i, f in enumerate(findings, 1):
            find_lines.append(
                f"{i}.【{f.get('severity','')}】{f.get('title','')}（涉及：{'、'.join(f.get('modules',[]))}）"
                f"\n   现象：{f.get('detail','')}"
                f"\n   规则提示：{f.get('suggestion','')}"
            )
        audit_block = "\n".join(find_lines) if find_lines else "（确定性引擎未检出矛盾，各模块结论协调。）"
        snap = {
            "所问": ov.get("topic", "") or data.get("question", ""),
            "局": ov.get("ju", ""),
            "用神落宫": ov.get("yongshen_palace", "") + "·" + ov.get("yongshen_quality", ""),
            "用神力量评定": ysf.get("composite_label", ""),
            "推理链": ysf.get("chain_text", ""),
            "吉方": "、".join(data.get("best_palaces", [])[:3]),
        }
        return (
            f"【待审之局·关键结论快照】\n{j(snap)}"
            f"\n\n【确定性引擎·一致性审核发现】（共 矛盾{ca.get('summary',{}).get('矛盾',0)}·"
            f"注意{ca.get('summary',{}).get('注意',0)}·提示{ca.get('summary',{}).get('提示',0)}）\n{audit_block}"
            f"\n\n请就以上每条发现作审定：说明张力因何而起、如何看待、对所问成败信心之影响；"
            f"落宫吉凶与推理链分歧者给出权衡（落宫看底色、推理链看实际成色）。末附【审定结论】一句。"
            f"切记：你只复核、不重断，输出为 AI 辅助审定意见。{question or ''}"
        )

    elif module == "xuankong_audit":
        ca = data.get("consistency_audit", {}) or {}
        zsyn = data.get("zhaiyun_synthesis", {}) or {}
        ov = data.get("overview", {}) or {}
        findings = ca.get("findings", []) or []
        find_lines = []
        for i, f in enumerate(findings, 1):
            find_lines.append(
                f"{i}.【{f.get('severity','')}】{f.get('title','')}（涉及：{'、'.join(f.get('modules',[]))}）"
                f"\n   现象：{f.get('detail','')}"
                f"\n   规则提示：{f.get('suggestion','')}"
            )
        audit_block = "\n".join(find_lines) if find_lines else "（确定性引擎未检出矛盾，各模块结论协调。）"
        snap = {
            "宅": f"{ov.get('sitting','')}山{ov.get('facing','')}向·{ov.get('yun_name','')}运",
            "山向格局": ov.get("verdict", ""),
            "宅运力量评定": zsyn.get("composite_label", ""),
            "推理链": zsyn.get("chain_text", ""),
        }
        return (
            f"【待审之宅·关键结论快照】\n{j(snap)}"
            f"\n\n【确定性引擎·一致性审核发现】（共 矛盾{ca.get('summary',{}).get('矛盾',0)}·"
            f"注意{ca.get('summary',{}).get('注意',0)}·提示{ca.get('summary',{}).get('提示',0)}）\n{audit_block}"
            f"\n\n请就以上每条发现作审定：说明张力因何而起、如何看待、对宅运总评信心之影响；"
            f"定盘与推理链分歧者给出权衡（定盘看山向到位、推理链看实际成色）。末附【审定结论】一句。"
            f"切记：你只复核、不重断，输出为 AI 辅助审定意见。{question or ''}"
        )

    elif module == "zeri_audit":
        ca = data.get("consistency_audit", {}) or {}
        zsyn = data.get("zeri_synthesis", {}) or {}
        ov = data.get("overview", {}) or {}
        findings = ca.get("findings", []) or []
        find_lines = []
        for i, f in enumerate(findings, 1):
            find_lines.append(
                f"{i}.【{f.get('severity','')}】{f.get('title','')}（涉及：{'、'.join(f.get('modules',[]))}）"
                f"\n   现象：{f.get('detail','')}"
                f"\n   规则提示：{f.get('suggestion','')}"
            )
        audit_block = "\n".join(find_lines) if find_lines else "（确定性引擎未检出矛盾，各模块结论协调。）"
        snap = {
            "所择之事": ov.get("purpose", ""),
            "首选吉日": f"{ov.get('top_date','')}（{ov.get('top_ganzhi','')}）评分{ov.get('top_score','')}",
            "吉日力量评定": zsyn.get("composite_label", ""),
            "推理链": zsyn.get("chain_text", ""),
            "本月吉日数": ov.get("good_count", ""),
        }
        return (
            f"【待审之选期·关键结论快照】\n{j(snap)}"
            f"\n\n【确定性引擎·一致性审核发现】（共 矛盾{ca.get('summary',{}).get('矛盾',0)}·"
            f"注意{ca.get('summary',{}).get('注意',0)}·提示{ca.get('summary',{}).get('提示',0)}）\n{audit_block}"
            f"\n\n请就以上每条发现作审定：说明张力因何而起、如何看待、对此首选日可用与否之影响；"
            f"岁破月破、老黄历明忌所择之事者当从严另择。末附【审定结论】一句。"
            f"切记：你只复核、不重断，输出为 AI 辅助审定意见。{question or ''}"
        )

    elif module == "yangzhai_audit":
        ca = data.get("consistency_audit", {}) or {}
        zsyn = data.get("zhaixiang_synthesis", {}) or {}
        ov = data.get("overview", {}) or {}
        mm = data.get("mingua_match", {}) or {}
        findings = ca.get("findings", []) or []
        find_lines = []
        for i, f in enumerate(findings, 1):
            find_lines.append(
                f"{i}.【{f.get('severity','')}】{f.get('title','')}（涉及：{'、'.join(f.get('modules',[]))}）"
                f"\n   现象：{f.get('detail','')}"
                f"\n   规则提示：{f.get('suggestion','')}"
            )
        audit_block = "\n".join(find_lines) if find_lines else "（确定性引擎未检出矛盾，各模块结论协调。）"
        snap = {
            "宅": ov.get("house_type", ""),
            "门主灶内格": ov.get("grade", ""),
            "人宅相配": mm.get("match_level", "") if mm.get("available") else "（未输入主人生年）",
            "宅相力量评定": zsyn.get("composite_label", ""),
            "推理链": zsyn.get("chain_text", ""),
        }
        return (
            f"【待审之宅·关键结论快照】\n{j(snap)}"
            f"\n\n【确定性引擎·一致性审核发现】（共 矛盾{ca.get('summary',{}).get('矛盾',0)}·"
            f"注意{ca.get('summary',{}).get('注意',0)}·提示{ca.get('summary',{}).get('提示',0)}）\n{audit_block}"
            f"\n\n请就以上每条发现作审定：说明张力因何而起、如何看待、对宅相总评信心之影响；"
            f"内格与人宅相配分歧者，依《八宅明镜》以人宅相得为主、内格为辅权衡。末附【审定结论】一句。"
            f"切记：你只复核、不重断，输出为 AI 辅助审定意见。{question or ''}"
        )

    elif module == "qimen":
        palaces = data.get("palaces", [])
        top_palaces = [
            {"宫": p.get("palace_name",""), "星": p.get("star",""), "门": p.get("door",""),
             "神": p.get("deity",""), "干": p.get("stem",""), "吉": p.get("is_auspicious",False)}
            for p in palaces[:9]
        ]
        ctx = {
            "时间": data.get("datetime", ""),
            "局": f"{data.get('ju_type','')} 第{data.get('ju_number','')}局 {data.get('yuan','')}",
            "吉方": data.get("auspicious_directions", []),
            "凶方": data.get("inauspicious_directions", []),
            "宫位": top_palaces,
            "伏吟反吟": data.get("fuyin_fanyin", {}),
            "综合": data.get("summary", ""),
        }
        # Layer 2.3: 时盘 vs 日盘
        if data.get("hour_ju"):
            ctx["时盘局"] = f"时盘第{data['hour_ju']}局"
        if data.get("note"):
            ctx["时家奇门说明"] = data["note"][:120]
        # 特殊格局
        patterns = data.get("patterns", [])
        if patterns:
            ctx["特殊格局"] = [f"{p.get('name','')}({p.get('level','')})：{p.get('desc','')[:50]}" for p in patterns[:4]]
        # 值符值使（原来只给一行"星在宫"，现补充角色定位与符使关系——奇门断局的核心切入点）
        for p_data in (data.get("palaces") or []):
            if p_data.get("is_zhifu"):
                ctx["值符"] = f"{p_data.get('star','')}在{p_data.get('palace_name','')}"
            if p_data.get("is_zhishi"):
                ctx["值使"] = f"{p_data.get('door','')}在{p_data.get('palace_name','')}"
        za = data.get("zhifu_analysis") or {}
        if za:
            zf, zs, rel = za.get("zhifu", {}), za.get("zhishi", {}), za.get("relationship", {})
            ctx["值符值使详解"] = {
                "值符角色": zf.get("role", ""), "值符断语": zf.get("desc", "")[:60],
                "值使角色": zs.get("role", ""), "值使断语": zs.get("desc", "")[:60],
                "符使关系": f"{rel.get('name','')}（{rel.get('level','')}）{rel.get('detail','')[:60]}",
            }

        # 用神（原来完全未纳入——用神是奇门断事最核心的落脚点，此前 AI 拿不到任何用神信息）
        ys = data.get("yong_shen") or {}
        if ys:
            ctx["用神"] = {
                "所主": ys.get("name", ""), "落宫": ys.get("palace", ""), "旺衰吉凶": ys.get("quality", ""),
                "断语要点": [d.get("text","")[:60] for d in (ys.get("judgment_dimensions") or [])[:3]],
            }

        # 应期（问事最常被追问"何时应验"，原来完全未纳入）
        tm = data.get("timing") or {}
        if tm:
            ctx["应期"] = {"快慢": tm.get("speed", ""), "推算依据": tm.get("fu_method", "")[:80]}

        # 空亡/驿马/击刑/门迫等特殊宫位标记（原来未纳入，体积小但断局时常被引用）
        ls = data.get("layer_summary") or {}
        if ls.get("desc"):
            ctx["特殊宫位"] = ls["desc"]

        purpose = extra_context or "综合"
        pa = data.get("purpose_analyses", {}).get(purpose, {})
        if pa:
            ctx["事项分析"] = {"推荐": pa.get("recommendation",""), "警示": pa.get("warning","")}
        # RAG injection for qimen
        rag_text = ""
        try:
            from knowledge.rag import get_rag
            rag_query = f"奇门遁甲 {purpose} {data.get('ju_type','')} {question or '吉凶方位'}"
            rag_text = get_rag().search_and_format(rag_query, top_k=4, header="\n\n【古籍参考】")
        except Exception as _e26:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e26)
        return f"奇门遁甲起局\n{j(ctx)}{rag_text}\n\n请分析当前局势，结合值符值使、用神旺衰，针对「{purpose}」给出战略建议，并给出应期判断（何时应验）。最后必须有【结论】段落直接回答此事宜忌和行动方案。{question or ''}"

    elif module == "fengshui":
        pd = data.get("personal_directions", {}) or {}
        ctx = {
            # 用户实际输入：坐向（此前完全未纳入，AI 拿不到用户选的朝向）
            "朝向": data.get("house_facing", ""),
            "坐山": data.get("house_sitting", ""),
            "命卦": f"{data.get('ming_gua','')}（{data.get('ming_gua_group','')}）",
            "宅卦": f"{data.get('house_gua','')}（{data.get('house_group','')}）",
            "命宅相配": data.get("compatibility",""),
            "吉方": [{"方位": s.get("direction",""), "星": s.get("star",""), "意义": s.get("meaning","")[:40]}
                     for s in data.get("auspicious_sectors", [])[:4]],
            "凶方": [{"方位": s.get("direction",""), "星": s.get("star",""), "意义": s.get("meaning","")[:40]}
                     for s in data.get("inauspicious_sectors", [])[:4]],
            # 个人八宅四吉位（此前只给了绝命一个凶位，生气/天医/延年三个吉位完全未纳入）
            "个人生气位": pd.get("shengqi", {}).get("direction",""),
            "个人天医位": pd.get("tianyi", {}).get("direction",""),
            "个人延年位": pd.get("niannian", {}).get("direction",""),
            "个人绝命位": pd.get("jueming", {}).get("direction",""),
            "卧室书桌建议": {"床位": pd.get("best_bed_dir",""), "书桌": pd.get("best_desk_dir","")},
        }
        # 年度飞星财位/五黄方位——原代码读取的 wealth_direction/five_yellow_direction
        # 字段在真实数据结构里根本不存在（实际嵌在 direction_stars 按方位分组），
        # 此前这两项一直在静默地传空字符串给 AI。现改用已经综合好的 combined_advice。
        combined_advice = data.get("combined_advice") or []
        if combined_advice:
            ctx["年度飞星与个人方位综合提示"] = combined_advice[:5]
        else:
            afs = data.get("annual_flying_stars", {}) or {}
            ctx["流年中宫星"] = afs.get("center_star_name", "")
        room_advice = pd.get("room_advice") or []
        if room_advice:
            ctx["布局建议要点"] = room_advice[:4]
        # Add classical context
        classical_ctx = ""
        try:
            from knowledge.fengshui_classical import YANGZHAI_THREE, XUANKONG_THEORY
            current_yun = XUANKONG_THEORY["三元九运"]["当前"]
            classical_ctx = (
                f"\n\n【《阳宅三要》】门：{YANGZHAI_THREE['大门']['经典']}"
                f"\n【九运当令】{current_yun}"
            )
        except Exception as _e27:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e27)
        return f"八宅风水分析\n{j(ctx)}{classical_ctx}\n\n请给出详细的家居布局建议。最后必须有【结论】段落总结此宅核心吉凶和最重要的改善建议。{question or ''}"

    elif module == "date":
        purpose = data.get("purpose", extra_context or "")
        best_list = data.get("best_days") or []  # 原代码读 best_day(单数)，实际字段是 best_days(复数列表)，此前"最佳日期"一直是空的
        best = best_list[0] if best_list else {}
        top_days = [
            {"日期": d_item.get("date",""), "干支": d_item.get("ganzhi",""),
             "建除": d_item.get("officer",""), "星宿": d_item.get("star",""),  # 原代码读 xiu，实际字段是 star，此前一直是空值
             "评分": d_item.get("score",0),  # 原代码读 quality，实际字段是 score，此前一直是 0
             "宜": d_item.get("yi", [])[:3] if isinstance(d_item.get("yi"), list) else "",
             "冲煞": d_item.get("chong",""),
             }
            for d_item in data.get("auspicious_days", [])[:5]
        ]
        ctx = {
            "择事目的": purpose,
            "最佳日期": {
                "日期": best.get("date",""), "干支": best.get("ganzhi",""),
                "建除": best.get("officer",""), "星宿": best.get("star",""), "评分": best.get("score",0),
                "择日理由": (best.get("reasons") or [])[:4],
            } if best else {},
            "前五吉日": top_days,
            "三煞警示": data.get("three_killings", {}),
            "本月概述": data.get("month_summary",""),
        }
        # 个性化择日（用户填了自己生辰时才有）——此前完全未纳入，
        # 用户输入的生辰会影响择日的用喜忌五行，但这层判断此前没告诉过 AI。
        pers = data.get("personalization") or {}
        if pers.get("available"):
            prof = pers.get("profile", {})
            ctx["个人化择日"] = {
                "本命用喜": prof.get("yong",""), "本命忌讳": prof.get("ji",""),
                "本命日支": prof.get("day_zhi",""),
                "个人最宜日": [d.get("date","") for d in (pers.get("personal_best") or [])[:3]],
                "个人当避日": [d.get("date","") for d in (pers.get("personal_avoid") or [])[:3]],
            }
        # 命局总断（一句话结论，信息密度高）
        ms = data.get("master_synthesis") or {}
        if ms.get("available"):
            ctx["总断"] = ms.get("headline", "")
        # Add classical context
        classical_ctx = ""
        try:
            from knowledge.date_classical import ZERI_EVENTS, JIANSHEN_TWELVE
            event_rules = ZERI_EVENTS.get(purpose, {})
            if event_rules:
                classical_ctx = (
                    f"\n\n【《协纪辨方书》{purpose}择日要诀】"
                    f"\n最佳日：{event_rules.get('最佳日','')}"
                    f"\n忌：{event_rules.get('忌','')}"
                    f"\n注意：{event_rules.get('注意','')}"
                    f"\n口诀：{event_rules.get('口诀','')}"
                )
        except Exception as _e28:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e28)
        return f"择日分析\n{j(ctx)}{classical_ctx}\n\n请详细解读最佳择日方案。最后必须有【结论】段落直接推荐最佳日期和时辰。{question or ''}"

    elif module == "knowledge":
        # data is whatever knowledge section they're viewing
        ctx_str = j(data, maxlen=1500)
        topic = extra_context or "命理知识"
        return f"命理知识主题：{topic}\n\n相关知识数据：\n{ctx_str}\n\n请深度解读此知识点的含义、古籍出处和实战应用。{question or ''}"

    elif module == "ziwei":
        # ── 用 context_builder 把整个命盘结构化喂给 LLM ──
        # 修复了旧代码三个严重 bug：
        #   1. soul_palace_index 字段不存在 → 命宫永远取 index 0（错）
        #   2. feihua[:4] 字段名错 → 四化信息永远是空字符串
        #   3. decade_info / combined_warnings 在 /chart 返回中根本没有
        # 现在改为：基于 is_soul 标记定位命宫；
        # 从 palaces[i].major_stars[j].mutagen 字段提取生年四化；
        # 用 build_ziwei_context 输出完整结构化文本。
        from core.ziwei.context_builder import (
            build_ziwei_context,
            find_soul_palace,
            ZIWEI_ANALYSIS_INSTRUCTION,
        )

        palaces = data.get("palaces", []) or []

        # 1. 主体上下文（含派别声明、基础信息、命宫、身宫、三方四正、生年四化、来因宫、十二宫概览）
        main_ctx = build_ziwei_context(data)

        # 2. 基于正确的命宫主星做 RAG 检索 + 主星断语
        soul_palace = find_soul_palace(palaces)
        soul_main_stars = []
        if soul_palace:
            for s in (soul_palace.get("major_stars") or []):
                nm = s.get("name", "") if isinstance(s, dict) else str(s)
                if nm:
                    soul_main_stars.append(nm)

        rag_text = ""
        # RAG 古籍检索
        try:
            from knowledge.rag import get_rag
            # 用命宫主星+四化关键字组合做 query
            rag_query = (
                f"紫微斗数 命宫 {'、'.join(soul_main_stars)} "
                f"{question or '格局四化论命'}"
            )
            rag_text = get_rag().search_and_format(
                rag_query, top_k=4, header="\n\n【相关古籍参考】"
            )
        except Exception as _e29:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e29)

        # 主星深度知识（命宫主星的断语和经典格局）
        try:
            from knowledge.knowledge_deep import ZIWEI_ZHUXING
            star_info_lines = []
            for sname in soul_main_stars:
                star_info = ZIWEI_ZHUXING.get(sname, {})
                if star_info.get("断语"):
                    star_info_lines.append(f"【{sname}星断语】{star_info['断语'][:160]}")
                if star_info.get("格局"):
                    gejv_list = star_info["格局"][:3]
                    star_info_lines.append(f"【{sname}经典格局】{'；'.join(gejv_list)}")
            if star_info_lines:
                rag_text += "\n\n【命宫主星深度知识】\n" + "\n".join(star_info_lines)
        except Exception as _e30:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e30)

        # 飞星派飞化链路多步串联（互化/化忌连环/化禄流通/焦点/生年串联）
        try:
            fc = data.get("feihua_chains", {})
            if fc.get("available"):
                lines = ["\n\n【飞星派飞化链路·多步串联】"]
                if fc.get("birth_chain"):
                    lines.append("· " + fc["birth_chain"][0]["desc"])
                for jc in fc.get("ji_chains", [])[:2]:
                    lines.append("· " + jc["text"])
                for m in [x for x in fc.get("mutual", []) if x["nature"] in ("吉", "凶")][:2]:
                    lines.append("· " + m["desc"])
                for lc in fc.get("lu_chains", [])[:1]:
                    lines.append("· " + lc["text"])
                if fc.get("focus"):
                    lines.append("· " + fc["focus"][0]["desc"])
                if len(lines) > 1:
                    rag_text += "\n".join(lines)
        except Exception as _e31:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e31)

        # 大限 / 流年 运限盘飞化链路（多步串联推及运限）
        try:
            from core.ziwei.feihua_chain import analyze_layer_feihua_chains
            from core.ziwei.birth_sihua import build_birth_sihua_panel
            bsp = data.get("birth_sihua") or build_birth_sihua_panel(data)
            bsp = bsp if bsp.get("available") else None
            layer_lines = []
            dfc = data.get("decade_feihua_chains") or analyze_layer_feihua_chains(data, "大限", birth_sihua=bsp)
            if dfc.get("available") and dfc.get("ji_chains"):
                layer_lines.append("· 大限盘化忌连环：" + "；".join(
                    "→".join(c["names"]) for c in dfc["ji_chains"][:2]))
                if dfc.get("focus"):
                    layer_lines.append("· 大限盘飞化焦点：" + dfc["focus"][0]["palace"]
                                       + "（" + dfc["focus"][0]["tag"] + "）")
            cy = data.get("current_year") or (data.get("metadata", {}) or {}).get("current_year")
            if cy:
                ys = "甲乙丙丁戊己庚辛壬癸"[(int(cy) - 4) % 10]
                afc = data.get("annual_feihua_chains") or analyze_layer_feihua_chains(
                    data, "流年", year_stem=ys, birth_sihua=bsp)
                if afc.get("available") and afc.get("ji_chains"):
                    layer_lines.append(f"· 流年盘（{ys}）化忌连环：" + "；".join(
                        "→".join(c["names"]) for c in afc["ji_chains"][:2]))
            if layer_lines:
                rag_text += "\n\n【运限盘飞化链路·大限/流年】\n" + "\n".join(layer_lines)
        except Exception as _e32:
            from core.log import log_failure; log_failure("api", "装配(自动补充日志)", _e32)

        # 3. 用户问题
        question_block = ""
        if question:
            question_block = f"\n\n【用户问题】{question}"

        # 4. 拼装最终 prompt
        return (
            main_ctx
            + rag_text
            + question_block
            + ZIWEI_ANALYSIS_INSTRUCTION
        )

    else:
        return f"数据：{j(data)}\n\n{question or '请分析以上数据。'}"


@router.post("/interpret", summary="通用AI解读 — 任意模块结果流式解读")
async def interpret(req: InterpretRequest, request: Request):
    """
    Universal LLM interpretation endpoint.
    Accepts any module's computed result and streams AI analysis.
    """
    cfg = _get_llm_config(request)

    system = INTERPRET_SYSTEMS.get(req.module, MASTER_SYSTEM)
    user_msg = _build_interpret_prompt(
        req.module, req.data, req.question or "", req.extra_context or ""
    )

    return _sse_response(
        _stream_llm(cfg, system, [{"role": "user", "content": user_msg}], 2500),
        cfg
    )
