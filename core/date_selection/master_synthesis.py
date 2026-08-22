"""
core/date_selection/master_synthesis.py
=======================================
择日·综合总论（总汇合参 — 全功能激活后的最终汇总层）。

择日既论月令、扫逐日宜忌、排通用吉日、按本命八字个性化、避岁破三煞，须汇为一处：
本月吉日丰歉、通用首选、合本命之个人首选、必避之凶日，成一明确「择日总论」。
单点（月令/通用首选/个人首选/忌避）→ 组合 → 汇总（总评 + 首选 + 避忌）。
"""
from __future__ import annotations
from typing import Dict, Any, List


def build_date_master_synthesis(result: Dict[str, Any]) -> Dict[str, Any]:
    purpose = result.get("purpose", "")
    best = result.get("best_days", []) or []
    inaus = result.get("inauspicious_days", []) or []
    pz = result.get("personalization", {}) or {}
    tk = result.get("three_killings", "")
    month_jieqi = result.get("month_jieqi", "")
    all_days = result.get("all_days", []) or []

    if not all_days:
        return {"available": False}

    n_good = len(result.get("auspicious_days", []) or [])
    n_total = len(all_days)

    dims: List[Dict[str, str]] = []

    # ① 月令丰歉
    if n_good >= n_total * 0.4:
        mq, mtext = "吉", f"本月（{month_jieqi}）吉日较丰，{n_good}/{n_total} 日可取，择期从容。"
    elif n_good >= max(1, n_total * 0.15):
        mq, mtext = "中", f"本月（{month_jieqi}）吉日适中，{n_good}/{n_total} 日可取，须精挑。"
    else:
        mq, mtext = "凶", f"本月（{month_jieqi}）吉日稀少，{n_good}/{n_total} 日可取，宜另择月或慎选。"
    dims.append({"dim": "月令丰歉", "quality": mq, "verdict": mtext})

    # ②神煞总论（汇逐日「择事专属断」为本月神煞合参）
    from collections import Counter
    yi_days, ji_days, ban_days = [], [], []
    sup_counter, agn_counter = Counter(), Counter()
    for d in all_days:
        sp = d.get("shensha_purpose") or {}
        lv = sp.get("level")
        if lv == "宜":
            yi_days.append((d, sp.get("net", 0)))
            for s in sp.get("support", []):
                sup_counter[s["name"]] += 1
        elif lv == "忌":
            ji_days.append((d, sp.get("net", 0)))
            for a in sp.get("against", []):
                agn_counter[a["name"]] += 1
        elif lv == "参半":
            ban_days.append(d)
    if yi_days or ji_days:
        top_sup = "、".join(n for n, _ in sup_counter.most_common(4))
        top_agn = "、".join(n for n, _ in agn_counter.most_common(4))
        best_ss = sorted(yi_days, key=lambda x: -x[1])[:3]
        worst_ss = sorted(ji_days, key=lambda x: x[1])[:3]
        bss = "、".join(f"{d.get('date','')[5:]}（{d.get('ganzhi','')}）" for d, _ in best_ss)
        wss = "、".join(f"{d.get('date','')[5:]}（{d.get('ganzhi','')}）" for d, _ in worst_ss)
        sstext = (f"以神煞论「{purpose}」：本月正利者 {len(yi_days)} 日、正忌者 {len(ji_days)} 日、吉凶交杂 {len(ban_days)} 日。"
                  + (f"常助此事之吉神为{top_sup}；" if top_sup else "")
                  + (f"常忌此事之凶煞为{top_agn}。" if top_agn else "")
                  + (f"神煞最宜之日：{bss}。" if bss else "")
                  + (f"神煞正忌当避：{wss}。" if wss else ""))
        ssq = "吉" if len(yi_days) >= len(ji_days) else "凶"
        dims.append({"dim": "神煞总论", "quality": ssq, "verdict": sstext})

    # ② 通用首选
    if best:
        bt = "、".join(f"{b.get('date', '')[5:]}（{b.get('ganzhi', '')}）" for b in best[:3])
        dims.append({"dim": "通用首选", "quality": "吉", "verdict": f"通用吉日首选：{bt}。"})

    # ③ 个人首选（八字个性化）
    has_personal = pz.get("available") and pz.get("personal_best")
    if has_personal:
        prof = pz.get("profile", {})
        pb = pz["personal_best"]
        pt = "、".join(f"{b['date'][5:]}（{b['ganzhi']}·合{b['combined_score']}）" for b in pb[:3])
        dims.append({"dim": "个人首选", "quality": "吉",
                     "verdict": f"以本命（用神{prof.get('yong', '')}、日支{prof.get('day_zhi', '')}）配，合本命首选：{pt}。"})
        if pz.get("personal_avoid"):
            av = "、".join(f"{a['date'][5:]}（{a['ganzhi']}）" for a in pz["personal_avoid"][:2])
            dims.append({"dim": "个人忌避", "quality": "凶",
                         "verdict": f"通用虽吉、然冲克本命，宜避：{av}。"})

    # ④ 忌避（岁破三煞）
    avoid_bits = []
    if tk:
        avoid_bits.append(f"三煞在{tk}")
    if inaus:
        avoid_bits.append(f"另有 {len(inaus)} 个凶日（岁破/月破/受死等）须避")
    if avoid_bits:
        dims.append({"dim": "忌避", "quality": "凶", "verdict": "；".join(avoid_bits) + "。"})

    # ── 综合总评 ──
    overall_q = mq
    if has_personal:
        headline = f"为「{purpose}」择期：本月吉日{('丰' if mq == '吉' else '适中' if mq == '中' else '歉')}；通用与合本命之吉日已分列，宜取个人首选、避其冲克。"
    else:
        headline = f"为「{purpose}」择期：本月吉日{('丰' if mq == '吉' else '适中' if mq == '中' else '歉')}；通用吉日已列，补本人生辰可再择合本命之日。"

    # ── 汇总段落 ──
    paras: List[str] = []
    paras.append(headline)
    body = "；".join(d["verdict"].rstrip("。") for d in dims if d["dim"] in ("通用首选", "个人首选", "个人忌避", "忌避", "神煞总论"))
    if body:
        paras.append("具体而论：" + body + "。")
    paras.append("择日之要，先avoid岁破三煞与受死之凶，次取建除黄道之吉，终以本命八字用神冲合定其合身之日——三者备方为全吉。".replace("avoid", "避"))

    # 当下时辰（以此刻为择吉基准）
    try:
        from core.calendar.current_moment import moment_dimension
        md = moment_dimension("dateref")
        dims.append(md["dimension"])
        paras.append(md["paragraph"])
    except Exception as _e1:
        from core.log import log_failure; log_failure("date_selection", "装配(自动补充日志)", _e1)

    advice = ("取个人首选之日、避冲克本命之日为上。" if has_personal
              else "补全本人生辰（年月日）即可按八字用神/冲克过滤出合本命之吉日。")

    return {
        "available": True,
        "headline": headline,
        "overall_quality": overall_q,
        "purpose": purpose,
        "dimension_verdicts": dims,
        "integrated_paragraphs": paras,
        "master_advice": advice,
    }
