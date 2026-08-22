"""
core/liuyao/master_synthesis.py
===============================
六爻·综合总断（总汇合参 — 全功能激活后的最终汇总层）。

六爻一卦答一问；既装卦纳甲、定世应用神、析动爻应期，须将「用神旺衰、世应向背、
动爻生克、卦型合冲、应期迟速」诸单点之断，汇为一明确总断：成与不成、迟速何时、
关键所在。单点（各维之断）→ 组合（用神×世应×动爻趋势）→ 汇总（成败+应期+提示）。
"""
from __future__ import annotations
from typing import Dict, Any, List

_STRONG = {"旺", "相", "临日", "临月", "得生", "有气"}
_WEAK = {"休", "囚", "死", "空", "破", "墓", "绝", "无气"}


def _find_yaos(yaos, pred):
    return [y for y in yaos if pred(y)]


def build_liuyao_master_synthesis(result: Dict[str, Any]) -> Dict[str, Any]:
    yaos = result.get("yaos", []) or []
    fr = result.get("full_reading", {}) or {}
    if not yaos or not fr.get("available"):
        return {"available": False}

    question = result.get("question", "") or fr.get("question", "")
    topic = fr.get("topic", "")
    # 用神：以 full_reading.yong_shen_name 为准（与 topic/yingqi 同源，自占类为世爻）
    yong_name = (fr.get("yong_shen_name", "")
                 or fr.get("yong_liuqin", "")
                 or (result.get("yingqi", {}) or {}).get("yong_shen_name", ""))
    yong_position = fr.get("yong_position", "")   # 世爻/应爻（用神为爻位时）
    # 用于在卦中定位用神爻：爻位用神按世/应定位，六亲用神按六亲定位
    yong_liuqin = fr.get("yong_liuqin", "")
    polarity = fr.get("polarity", "")        # 吉/凶/待
    hex_type = result.get("hex_type", "")
    yingqi = result.get("yingqi", {}) or {}
    topic_an = result.get("topic_analysis", {}) or {}

    dims: List[Dict[str, str]] = []

    # ① 用神状态（爻位用神按世/应定位，六亲用神按六亲定位）
    if yong_position == "世爻":
        yong_yaos = _find_yaos(yaos, lambda y: y.get("is_world"))
    elif yong_position == "应爻":
        yong_yaos = _find_yaos(yaos, lambda y: y.get("is_application"))
    else:
        yong_yaos = _find_yaos(yaos, lambda y: y.get("liu_qin") == yong_liuqin)
    # 用神显示名：爻位用神标「世爻(临六亲)」，六亲用神直标六亲
    yong_label = (f"{yong_position}（临{yong_liuqin}）" if yong_position else yong_name) or "—"
    yong_q = "中"
    if yong_yaos:
        yong = yong_yaos[0]
        _st_raw = yong.get("strength", "")
        st = (_st_raw.get("label", "") if isinstance(_st_raw, dict) else str(_st_raw))
        kw = yong.get("kong_wang")
        strong = any(k in st for k in _STRONG)
        weak = any(k in st for k in _WEAK) or kw
        yong_q = "吉" if (strong and not weak) else ("凶" if weak and not strong else "中")
        dims.append({"dim": "用神", "quality": yong_q,
                     "verdict": f"用神{yong_label}（{yong.get('branch', '')}{yong.get('element', '')}）{st or '中和'}"
                                + ("，逢空" if kw else "") + "。"})
    else:
        dims.append({"dim": "用神", "quality": "中", "verdict": f"用神{yong_label}不上卦，须看伏神。"})

    # ② 世应向背
    world = next((y for y in yaos if y.get("is_world")), None)
    appl = next((y for y in yaos if y.get("is_application")), None)
    if world and appl:
        wq = "中"
        dims.append({"dim": "世应", "quality": wq,
                     "verdict": f"世{world.get('liu_qin', '')}（{world.get('branch', '')}）、"
                                f"应{appl.get('liu_qin', '')}（{appl.get('branch', '')}），观其生克向背。"})

    # ③ 动爻
    moving = _find_yaos(yaos, lambda y: y.get("is_changing"))
    if moving:
        mv_bits = "、".join(f"{y.get('position')}爻{y.get('liu_qin', '')}" for y in moving)
        dims.append({"dim": "动爻", "quality": "中",
                     "verdict": f"{mv_bits}发动，动则有变，引动事机。"})
    else:
        dims.append({"dim": "动爻", "quality": "中", "verdict": "六爻安静，事缓而无大变，宜守待时。"})

    # ④ 卦型
    if hex_type:
        ht_q = "吉" if "六合" in hex_type else ("凶" if "六冲" in hex_type else "中")
        ht_note = {"六合卦": "事易成、宜合", "六冲卦": "事多散、宜冲开"}.get(hex_type, "")
        dims.append({"dim": "卦型", "quality": ht_q,
                     "verdict": f"{hex_type}，{ht_note}。" if ht_note else f"{hex_type}。"})

    # ⑤ 应期
    if yingqi.get("available"):
        dims.append({"dim": "应期", "quality": "中",
                     "verdict": yingqi.get("summary", "") or "应期可推，详见应期分析。"})
    else:
        dims.append({"dim": "应期", "quality": "中",
                     "verdict": "用神不上卦或无纳甲，应期难定，宜俟用神显象。"})

    # ── 综合成败断 ──
    pol_map = {"吉": ("吉", "用神有力、卦象相宜，此事可成，宜进取把握。"),
               "凶": ("凶", "用神失力或卦象相违，此事难成，宜守不宜强求。"),
               "待": ("中", "用神中和、吉凶未定，事在迟速进退之间，须察动爻引动与应期。")}
    overall_q, headline = pol_map.get(polarity, ("中", "卦象吉凶相参，宜细察用神世应而后断。"))
    # 用神状态修正
    if yong_q == "吉" and overall_q == "中":
        headline = "用神得力，事有可成之机，把握应期则吉。"
        overall_q = "吉"
    elif yong_q == "凶" and overall_q == "中":
        headline = "用神失力，此事多阻，宜缓图或另谋。"

    # 用神七维断为成败主依据（现伏×旺衰×动静化象×空破墓×元神×忌神×世应 → 综合成败）。
    # 总断以七维断为纲，使「总断 = 用神断」，二者一致不相违。
    yj = result.get("yongshen_judgment") or {}
    if yj.get("available"):
        _lv_map = {"auspicious": "吉", "inauspicious": "凶", "neutral": "中"}
        yj_q = _lv_map.get(yj.get("verdict_level"), "中")
        overall_q = yj_q                      # 七维断定调
        headline = yj.get("verdict", headline)
        # 七维断单列一维，置于用神维之后，呈现成败之据
        dims.append({"dim": "用神七维断", "quality": yj_q,
                     "verdict": f"用神{yj.get('yong_shen_name','')}（{yj.get('present_state','')}）"
                                f"七维合参（净分{yj.get('net_score', 0)}）：{yj.get('verdict','')}"})

    # ── 汇总段落 ──
    paras: List[str] = []
    paras.append(f"所占「{question or topic}」，以{yong_label}为用神。" + headline)
    # 主题分析之专断（若有，为更具体之成败论）
    if topic_an.get("verdict"):
        paras.append("就事论之：" + topic_an["verdict"])
    dim_bits = "；".join(d["verdict"].rstrip("。") for d in dims if d["dim"] in ("用神", "世应", "动爻", "卦型"))
    if dim_bits:
        paras.append("合而观之：" + dim_bits + "。")
    if yingqi.get("available"):
        paras.append("应期：" + (yingqi.get("summary", "") or "见应期分析"))

    # 当下时辰（六爻占时即基准：当下 = 占卦时刻，所断即应此占时，故须锚定 divine_date 而非服务器现在）
    try:
        from core.calendar.current_moment import moment_dimension
        from datetime import datetime as _dt
        _cast = result.get("divine_date")
        _cast_dt = _dt.fromisoformat(_cast) if _cast else None
        md = moment_dimension("divination", now=_cast_dt)
        dims.append(md["dimension"])
        paras.append(md["paragraph"])
    except Exception as _e1:
        from core.log import log_failure; log_failure("liuyao", "装配(自动补充日志)", _e1)

    # 有效时间段：任何起卦皆有时间影响与有效期——自占卦时刻起算，事机于应期前后了结；
    # 过此应期而事未验，则此卦效力已尽，当另占。明示「起算点→应期止」之时间窗口。
    try:
        from datetime import datetime as _dt2
        _cast = result.get("divine_date")
        _prim = yingqi.get("primary") if isinstance(yingqi, dict) else None
        if _cast and _prim and _prim.get("date"):
            _cast_d = _dt2.fromisoformat(_cast).strftime("%Y-%m-%d")
            _yq_date = _prim.get("date"); _yq_gz = _prim.get("ganzhi", "")
            _ahead = _prim.get("days_ahead")
            _scope = _prim.get("scope", "日")
            _ahead_txt = (f"约{_ahead}{_scope}后" if isinstance(_ahead, int) else "")
            paras.append(
                f"有效时间段：此卦自占卦之时（{_cast_d}）起算，所断之应期落于{_yq_date}"
                f"（{_yq_gz}{_scope}{('，' + _ahead_txt) if _ahead_txt else ''}）——"
                f"事机当于此应期前后见分晓；过此而事未验，则此卦效力已尽，宜就所问另占。"
            )
    except Exception as _e2:
        from core.log import log_failure; log_failure("liuyao", "装配(自动补充日志)", _e2)

    advice = result.get("advice", "") or fr.get("paragraphs", [{}])[-1].get("text", "") if fr.get("paragraphs") else ""
    advice = (advice or "宜以用神旺衰为主、动变应期为辅，吉则进、凶则避、待则察机而动。")[:80]

    return {
        "available": True,
        "headline": headline,
        "overall_quality": overall_q,
        "question": question or topic,
        "yong_shen": yong_label,
        "dimension_verdicts": dims,
        "integrated_paragraphs": paras,
        "master_advice": advice,
    }
