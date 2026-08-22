"""
core/qimen/master_synthesis.py
==============================
奇门遁甲·综合断（总汇合参 — 全功能激活后的最终汇总层）。

奇门一局答一事：既排三元局数、定用神落宫、检格局、析值符值使、判吉凶方、推应期，
须汇为一处：用神落宫之吉凶、格局之利害、最佳方位与时辰，成一明确「综合断」。
单点（用神落宫/格局/值符值使/吉凶方/应期）→ 组合 → 汇总（成败+方位时辰+提示）。
"""
from __future__ import annotations
from typing import Dict, Any, List

_Q_MAP = {"大吉": "吉", "吉": "吉", "小吉": "吉", "平": "中", "中": "中",
          "小凶": "凶", "凶": "凶", "大凶": "凶"}


def _q(text: str) -> str:
    t = str(text or "")
    for k in ("大吉", "大凶", "小吉", "小凶", "吉", "凶", "平", "中"):
        if k in t:
            return _Q_MAP.get(k, "中")
    return "中"


def build_qimen_master_synthesis(result: Dict[str, Any]) -> Dict[str, Any]:
    purpose = result.get("purpose", "") or result.get("question", "")
    ju_type = result.get("ju_type", "")
    ju_num = result.get("ju_number", "")
    jieqi = result.get("jieqi", "")
    yuan = result.get("yuan", "")
    ys = result.get("yong_shen", {}) or {}
    patterns = result.get("patterns", []) or []
    zhifu = (result.get("zhifu_analysis", {}) or {}).get("zhifu", {}) or {}
    best = result.get("best_palaces", []) or []
    worst = result.get("worst_palaces", []) or []
    timing = result.get("timing", {}) or {}

    if not ys.get("name") and not ju_type:
        return {"available": False}

    dims: List[Dict[str, str]] = []

    # ① 用神落宫（核心）
    yq = _q(ys.get("quality", ""))
    if ys.get("name"):
        dims.append({"dim": "用神落宫", "quality": yq,
                     "verdict": f"{purpose}以{ys.get('name', '')}为用神，落{ys.get('palace', '')}，{ys.get('quality', '')}。"})

    # ② 格局
    aus = [p for p in patterns if isinstance(p, dict) and p.get("level") in ("吉", "大吉")]
    inaus = [p for p in patterns if isinstance(p, dict) and p.get("level") in ("凶", "大凶")]
    if aus or inaus:
        bits = []
        if aus:
            bits.append("吉格：" + "、".join(p.get("name", "") for p in aus[:3]))
        if inaus:
            bits.append("凶格：" + "、".join(p.get("name", "") for p in inaus[:3]))
        pq = "吉" if len(aus) > len(inaus) else ("凶" if len(inaus) > len(aus) else "中")
        dims.append({"dim": "格局", "quality": pq, "verdict": "；".join(bits) + "。"})

    # ③ 值符值使
    if zhifu.get("star"):
        dims.append({"dim": "值符", "quality": _q(zhifu.get("wangshuai", "")),
                     "verdict": f"值符{zhifu.get('star', '')}落{zhifu.get('palace', '')}（{zhifu.get('wangshuai', '')}），{str(zhifu.get('role', ''))[:24]}。"})

    # ④ 吉凶方位
    if best or worst:
        dims.append({"dim": "趋避方位", "quality": "中",
                     "verdict": f"吉方：{('、'.join(best[:4])) or '无'}；凶方：{('、'.join(worst[:3])) or '无'}。趋吉方行动、避凶方谋事。"})

    # ⑤ 应期
    if timing:
        ttext = timing.get("summary", "") or timing.get("desc", "") or ""
        if ttext:
            dims.append({"dim": "应期", "quality": "中", "verdict": str(ttext)[:48]})

    # ── 综合断 ──
    if yq == "吉" and not inaus:
        overall_q, headline = "吉", f"用神{ys.get('name', '')}得地、{ys.get('quality', '')}，谋此{purpose}可成，趋{(best[0] if best else '吉方')}行动则顺。"
    elif yq == "凶" or (inaus and not aus):
        overall_q, headline = "凶", f"用神或格局不利（{('、'.join(p.get('name', '') for p in inaus[:2])) if inaus else ys.get('quality', '')}），谋此{purpose}多阻，宜守或另择时方。"
    else:
        overall_q, headline = "中", f"用神{ys.get('quality', '')}、格局吉凶相参，谋此{purpose}须趋吉方吉时、避其凶格。"

    # ── 汇总段落 ──
    paras: List[str] = []
    paras.append(headline)
    body = "；".join(d["verdict"].rstrip("。") for d in dims if d["dim"] in ("用神落宫", "格局", "值符"))
    if body:
        paras.append("合而论之：" + body + "。")
    paras.append(f"此{ju_type}{ju_num}局（{jieqi}{yuan}），奇门之断以用神落宫为主、格局值符为辅、"
                 "趋吉方避凶方而动、依应期定迟速，方为全断。")

    # 当下时辰（局时即起局之刻，所断即应此时空）
    try:
        from core.calendar.current_moment import moment_dimension
        from datetime import datetime as _dtm
        _now = None
        dts = result.get("datetime", "")
        if dts:
            try:
                _now = _dtm.fromisoformat(str(dts).replace("/", "-")[:16])
            except Exception:
                _now = None
        md = moment_dimension("divination", _now)
        dims.append(md["dimension"])
        paras.append(md["paragraph"])
        # 有效时间段：时家奇门一局只管一时辰（2时），逾此即换局。明示此局之时辰窗口。
        if _now is not None:
            _h = _now.hour
            # 时辰起讫（子时跨日：23–次日1）
            _bounds = [(23, 1, "子"), (1, 3, "丑"), (3, 5, "寅"), (5, 7, "卯"),
                       (7, 9, "辰"), (9, 11, "巳"), (11, 13, "午"), (13, 15, "未"),
                       (15, 17, "申"), (17, 19, "酉"), (19, 21, "戌"), (21, 23, "亥")]
            _name, _s, _e = "子", 23, 1
            for s, e, nm in _bounds:
                if (s <= _h < e) or (nm == "子" and (_h >= 23 or _h < 1)):
                    _name, _s, _e = nm, s, e
                    break
            paras.append(
                f"有效时间段：时家奇门一局只管一时辰——此局起于{_name}时"
                f"（{_s:02d}:00–{_e:02d}:00{'，次日' if _name == '子' else ''}），"
                f"逾此时辰则气数已迁、当另起一局；故所断吉凶趋避皆应于此时辰之内，"
                f"行事须趁此局之吉方吉时。"
            )
    except Exception as _e1:
        from core.log import log_failure; log_failure("qimen", "装配(自动补充日志)", _e1)

    advice = (f"趋{(best[0] if best else '吉方')}方位与时辰行动" +
              (f"，避{worst[0]}方" if worst else "") +
              (f"；防{inaus[0].get('name', '')}之凶" if inaus else "") + "。")

    return {
        "available": True,
        "headline": headline,
        "overall_quality": overall_q,
        "purpose": purpose,
        "ju": f"{ju_type}{ju_num}局·{jieqi}{yuan}",
        "dimension_verdicts": dims,
        "integrated_paragraphs": paras,
        "master_advice": advice,
    }
