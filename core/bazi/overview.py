"""
core/bazi/overview.py
=====================
八字·命局总论合成器。

各模块各出「词条」（用神、格局、神煞、刑冲…），但论命之要在于把这些串成
一段连贯、扣住此命主的整体叙述——日主立命 → 身之强弱 → 格之成破 →
用神趋避 → 格局亮点 → 支中动象 → 一生大局。

本合成器只对既有结构化结果做编织（不引入新断法），输出一段总论叙述，
供前端置顶呈现、亦可入 AI 上下文，呼应「综合engine优于平铺查表」之原则。
"""
from __future__ import annotations
from typing import Dict, Any, List


def _first(seq, default=""):
    return seq[0] if seq else default


def synthesize_overview(chart: Dict[str, Any]) -> Dict[str, Any]:
    """把命盘各结构化结果编织成连贯总论。"""
    dm = chart.get("day_master", "")
    dm_wx = chart.get("day_master_wuxing", "")
    prof = chart.get("day_master_profile", {}) or {}
    strength = chart.get("strength", "")
    si = chart.get("strength_info", {}) or {}
    pattern = chart.get("pattern", "")
    geju = (chart.get("combos", {}) or {}).get("geju_evaluation", {}) or {}
    ys = chart.get("yong_shen", {}) or {}
    sp = chart.get("special_patterns", {}) or {}
    rel = (chart.get("relations", {}) or {}).get("summary", {}) or {}
    tiaohou = chart.get("tiaohou", {}) or {}

    paras: List[Dict[str, str]] = []

    # 1. 日主立命
    symbol = prof.get("symbol", "")
    traits = prof.get("core_traits", "")
    deling = si.get("deling")
    deqi = si.get("deqi")
    ling = "得令当时" if deling else ("月令生身、得气不得令" if deqi else "失令")
    p1 = (f"{dm}{dm_wx}日主"
          + (f"，{symbol}" if symbol else "") + "。"
          + (f"{traits}。" if traits else "")
          + f"生月{ling}，日主之势属「{strength}」"
          + (f"（帮身{si.get('help_score','?')}、泄耗{si.get('drain_score','?')}）" if si else "")
          + "，此为一生气数之本。")
    paras.append({"title": "日主立命", "text": p1})

    # 2. 格局成破
    status = geju.get("status", "")
    verdict = geju.get("verdict", "")
    if pattern:
        p2 = f"命成「{pattern}」"
        if status:
            p2 += f"，{status}"
        p2 += "。"
        if verdict:
            p2 += verdict if verdict.endswith(("。", "！")) else verdict + "。"
        paras.append({"title": "格局成破", "text": p2})

    # 3. 用神趋避（指南针）
    yw, xw, jw = ys.get("yong_shen_wx"), ys.get("xi_shen_wx"), ys.get("ji_shen_wx")
    if yw:
        p3 = f"论趋避，全局以{yw}为用"
        if xw and xw != yw:
            p3 += f"、{xw}为喜"
        if jw:
            p3 += f"，最忌{jw}"
        p3 += "。"
        ana = ys.get("analysis", "")
        if ana:
            p3 += ana if ana.endswith("。") else ana + "。"
        # 调候点睛
        th_primary = tiaohou.get("primary")
        if th_primary:
            in_chart = tiaohou.get("primary_in_chart")
            p3 += (f"调候之神{th_primary}"
                   + ("已透干得用，寒暖燥湿调适。" if in_chart else "未现于命，岁运逢之则发。"))
        paras.append({"title": "用神趋避", "text": p3})

    # 4. 格局亮点（最显著的一两个特殊格局）
    matched = sp.get("matched", []) or []
    if matched:
        top = matched[:2]
        bits = []
        for m in top:
            nm = m.get("name", "")
            interp = m.get("interpretation", "")
            short = interp.split("—")[-1].strip() if "—" in interp else interp
            short = short.split("。")[0] + "。" if "。" in short else short
            bits.append(f"{'吉象' if m.get('auspicious') else '凶象'}「{nm}」——{short}")
        p4 = "命中尤可注目者：" + "　".join(bits)
        paras.append({"title": "格局亮点", "text": p4})

    # 5. 支中动象（关键合/冲）
    kb = rel.get("key_blessings", []) or []
    kw = rel.get("key_warnings", []) or []
    if kb or kw:
        parts = []
        if kb:
            parts.append("吉：" + _first(kb))
        if kw:
            parts.append("忌：" + _first(kw))
        p5 = "地支动象——" + "；".join(parts) + "。此为命局暗藏之牵动，逢岁运填引则应。"
        paras.append({"title": "支中动象", "text": p5})

    # 5.5 当前运程（大运流年并入 — 后天之时）
    cf = chart.get("current_fortune", {}) or {}
    if cf.get("available"):
        cdy = cf.get("current_dayun", {}) or {}
        cln = cf.get("current_liunian", {}) or {}
        help_map = {"扶用": "助旺用神、为顺境之运", "助忌": "助起忌神、宜守不宜进", "中性": "于命局用忌无显著助损"}
        pcf = (f"现行{cdy.get('ganzhi','')}大运（{cdy.get('start_age','')}-{cdy.get('end_age','')}岁，{cdy.get('shishen','')}），"
               f"{help_map.get(cdy.get('help',''), '')}。")
        if cln.get("ganzhi"):
            pcf += f"{cf.get('current_year','')}年逢{cln.get('ganzhi','')}（{cln.get('shishen','')}·{cln.get('quality','')}）。"
        if cf.get("suiyun_brief"):
            pcf += cf["suiyun_brief"][:40]
        paras.append({"title": "当前运程", "text": pcf})

    # 6. 一生大局（收束）
    quality = geju.get("quality", "")
    tone = {
        "吉": "格正用真，一生大局向上，宜顺势而为、守正待时。",
        "中": "格局有成有破、得失相参，一生在趋用避忌间见高低，重在扬长补短。",
        "凶": "格损用伤，一生多费周折，尤须借岁运补救、avoid犯其所忌。",
    }.get(quality, "综观全局，趋用神之乡则顺、犯忌神之地则滞，吉凶随运而转。")
    tone = tone.replace("avoid", "切忌")
    paras.append({"title": "一生大局", "text": tone})

    # 摘要一句（用于 AI/分享）
    summary = f"{dm}{dm_wx}日主·{strength}·{pattern}" + (f"（{status}）" if status else "")
    if yw:
        summary += f"，用{yw}忌{jw or '—'}"

    return {
        "available": bool(paras),
        "headline": summary,
        "quality": quality or "中",          # 吉/中/凶 —— 供前端定盘着色
        "day_master": f"{dm}{dm_wx}",
        "pattern": pattern,
        "pattern_status": status,
        "yong_shen_wx": yw,
        "ji_shen_wx": jw,
        "verdict_line": tone,                # 一生大局一句，作定盘结语
        "paragraphs": paras,
    }
