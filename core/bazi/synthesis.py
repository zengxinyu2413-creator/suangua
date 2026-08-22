"""
core/bazi/synthesis.py
======================
八字·命局力量综合推理链（子模块互助集成层）。

仿六爻 yongshen_synthesis 之法：八字诸子模块（日主旺衰、格局成破、用神喜忌、
调候、刑冲合害）原各自成断，本引擎将其汇于一条可见推理链——以日主强弱立基，
叠加格局之成破救应、用神调候之到位与否、刑冲之损益，每一因子标明【来源模块·
利/害/中·权重】，合成「命局综合评定」。使分析路径显式、子模块互助而非各算各的。
"""
from __future__ import annotations
from typing import Dict, Any, List

_WX = ("木", "火", "土", "金", "水")


def synthesize_mingju(chart: Dict[str, Any]) -> Dict[str, Any]:
    dm = chart.get("day_master", "")
    dm_wx = chart.get("day_master_wuxing", "")
    strength = chart.get("strength", "")
    si = chart.get("strength_info", {}) or {}
    ge = (chart.get("combos", {}) or {}).get("geju_evaluation", {}) or {}
    ys = chart.get("yong_shen", {}) or {}
    th = chart.get("tiaohou", {}) or {}
    rel = (chart.get("relations", {}) or {}).get("summary", {}) or {}

    if not dm:
        return {"available": False}

    factors: List[Dict[str, Any]] = []
    score = 0  # 命局成局得用之综合力

    # ── 一、日主强弱立基（状态，非利害） ──
    mstat = si.get("monthly_status", "")
    deling = si.get("deling")
    deqi = si.get("deqi")
    help_s = si.get("help_score", 0)
    drain_s = si.get("drain_score", 0)
    base_notes = []
    base_notes.append(f"月令{mstat or '—'}" + ("（得令）" if deling else "（不得令）"))
    base_notes.append("坐支通根" if deqi else "不通根")
    base_notes.append(f"帮扶力{help_s}对克泄耗{drain_s}")
    factors.append({
        "module": "日主旺衰",
        "factor": f"日主{dm}{dm_wx}",
        "polarity": "中",
        "weight": 0,
        "note": "；".join(base_notes) + f" ⟹ {strength}",
    })

    # ── 二、格局成破救应 ──
    pattern = ge.get("pattern", chart.get("pattern", ""))
    quality = ge.get("quality", "")
    cheng = ge.get("cheng_hit", []) or []
    po = ge.get("po_hit", []) or []
    jiu = ge.get("jiu", "")
    for c in cheng:
        score += 2
        factors.append({"module": "格局成破", "factor": f"成格·{pattern}", "polarity": "利",
                         "weight": 2, "note": c})
    for p in po:
        score -= 2
        factors.append({"module": "格局成破", "factor": f"破格·{pattern}", "polarity": "害",
                         "weight": -2, "note": p})
    if po and jiu:
        score += 1
        factors.append({"module": "格局成破", "factor": "破而有救", "polarity": "利",
                         "weight": 1, "note": jiu[:60] + ("…" if len(jiu) > 60 else "")})

    # ── 三、用神 + 调候到位 ──
    yw = ys.get("yong_shen_wx", "")
    jw = ys.get("ji_shen_wx", "")
    if yw:
        factors.append({"module": "用神喜忌", "factor": f"用神取{yw}", "polarity": "中",
                        "weight": 0, "note": (ys.get("analysis", "") or "")[:56]})
    th_primary = th.get("primary", "")
    th_in = th.get("primary_in_chart")
    if th_primary:
        if th_in:
            score += 2
            factors.append({"module": "调候", "factor": f"调候用神{th_primary}透/在局", "polarity": "利",
                            "weight": 2, "note": "寒暖燥湿得调，命局气候中和，用神得力"})
        else:
            score -= 2
            factors.append({"module": "调候", "factor": f"调候用神{th_primary}不上卦", "polarity": "害",
                            "weight": -2, "note": "调候之神缺位，气候失衡，需岁运补之方显"})

    # ── 四、刑冲合害损益 ──
    n_chong = rel.get("total_chong", 0)
    n_xing = rel.get("total_xing", 0)
    n_he = rel.get("total_he", 0)
    warns = rel.get("key_warnings", []) or []
    bless = rel.get("key_blessings", []) or []
    if n_chong or n_xing:
        score -= 1
        w = warns[0] if warns else f"{n_chong}冲{n_xing}刑"
        factors.append({"module": "刑冲合害", "factor": f"{n_chong}冲{n_xing}刑动荡", "polarity": "害",
                        "weight": -1, "note": w.replace("⚠ ", "")[:56]})
    if n_he and bless:
        score += 1
        factors.append({"module": "刑冲合害", "factor": f"{n_he}合相生", "polarity": "利",
                        "weight": 1, "note": bless[0].replace("✓ ", "")[:56]})

    # ── 五、命局综合评定（先天之体，不计后天运）──
    if score >= 4:
        label, desc = "命局上佳", "格成用真、调候得宜，根基稳固，一生大局向上。"
    elif score >= 1:
        label, desc = "命局中平偏上", "格局有成、用神可取，然不无瑕疵，趋用避忌则吉。"
    elif score >= -1:
        label, desc = "命局中平", "成破相参、得失互见，全凭岁运扶抑，重在扬长补短。"
    elif score >= -3:
        label, desc = "命局偏弱", "格局有损或用神失力，一生多费周折，尤须岁运补救。"
    else:
        label, desc = "命局受损", "格破用伤、刑冲交加，根基不固，须大运得力方转。"

    # ── 六、当前运程（后天之时）：大运流年并入，单列不改先天命局评定 ──
    cf = chart.get("current_fortune", {}) or {}
    fortune_factor = None
    if cf.get("available"):
        cdy = cf.get("current_dayun", {}) or {}
        helpv = cdy.get("help", "")
        if helpv == "扶用":
            fpol, fnote = "利", "现行大运扶起用神，先天命局得后天之助，宜进取"
        elif helpv == "助忌":
            fpol, fnote = "害", "现行大运助起忌神，宜守成避险、不宜妄动"
        else:
            fpol, fnote = "中", "现行大运于命局用忌无显著助损，平运守常"
        fortune_factor = {"module": "当前大运（后天）",
                          "factor": f"{cdy.get('ganzhi','')}运（{cdy.get('shishen','')}）",
                          "polarity": fpol, "weight": 0, "note": fnote}
        factors.append(fortune_factor)

    # 推理链文字
    seg = [f"日主{dm}{dm_wx}（{strength}）"]
    for f in factors[1:]:
        if f.get("module") == "当前大运（后天）":
            continue
        pol = {"利": "＋", "害": "－", "中": "·"}.get(f["polarity"], "·")
        seg.append(f"〔{f['module']}〕{pol}{f['factor']}")
    chain_text = "　→　".join(seg) + f"　⟹　{label}（先天综合力{score:+d}）"
    if fortune_factor:
        fpol = {"利": "＋", "害": "－", "中": "·"}.get(fortune_factor["polarity"], "·")
        cln = cf.get("current_liunian", {}) or {}
        chain_text += f"　‖后天‖　〔当前大运〕{fpol}{fortune_factor['factor']}"
        if cln.get("ganzhi"):
            chain_text += f" · {cf.get('current_year','')}年{cln.get('ganzhi','')}（{cln.get('quality','')}）"

    return {
        "available": True,
        "day_master": f"{dm}{dm_wx}",
        "strength": strength,
        "pattern": pattern,
        "quality": quality,
        "yong_shen_wx": yw,
        "ji_shen_wx": jw,
        "factors": factors,
        "composite_score": score,
        "composite_label": label,
        "composite_desc": desc,
        "current_fortune_note": fortune_factor["note"] if fortune_factor else "",
        "chain_text": chain_text,
    }
