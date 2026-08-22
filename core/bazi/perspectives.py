"""
core/bazi/perspectives.py
=========================
八字·多视角整合解读（子模块必尽其用·无孤儿）。

仿六爻 perspectives：八字所算之每一子模块，皆须组合进对命主之解释，
不得算而不用、沦为孤立面板。数子模块拼为「一个视角」，各成专业观照：

  ① 格局成败 —— 格局评定 × 成破救应 × 特殊格局
  ② 强弱用神 —— 日主旺衰 × 用神喜忌 × 调候
  ③ 十神性情 —— 十神统计 × 日主性情
  ④ 刑冲会合 —— 干支刑冲合害（动象损益）
  ⑤ 神煞应验 —— 神煞所主吉凶
  ⑥ 宫位根基 —— 命宫 × 身宫 × 胎元 × 人元司令

并随附 coverage：列明每一子模块归于何视角，以备核查「尽其用」。
"""
from __future__ import annotations
from typing import Dict, Any, List


def build_perspectives(chart: Dict[str, Any]) -> Dict[str, Any]:
    dm = chart.get("day_master", "")
    if not dm:
        return {"available": False}

    dm_wx = chart.get("day_master_wuxing", "")
    lenses: List[Dict[str, Any]] = []

    # ① 格局成败视角
    ge = (chart.get("combos", {}) or {}).get("geju_evaluation", {}) or {}
    gcb = chart.get("geju_cheng_bai", {}) or {}
    sp = chart.get("special_patterns", {}) or {}
    bits = []
    pat = ge.get("pattern", chart.get("pattern", ""))
    if pat:
        bits.append(f"本命{pat}，{ge.get('status','') or '格局'}，品评「{ge.get('quality','中')}」")
    if ge.get("cheng_hit"):
        bits.append("成于：" + "、".join(ge["cheng_hit"][:2]))
    if ge.get("po_hit"):
        bits.append("破于：" + "、".join(ge["po_hit"][:2]))
    if ge.get("jiu") and ge.get("po_hit"):
        bits.append("救应：" + ge["jiu"].split("；")[0].split("。")[0])
    matched = sp.get("matched", []) or []
    aus = [m["name"] for m in matched if m.get("auspicious")]
    inaus = [m["name"] for m in matched if not m.get("auspicious")]
    if aus:
        bits.append("更得吉局：" + "、".join(aus[:3]))
    if inaus:
        bits.append("然带凶局：" + "、".join(inaus[:3]))
    lenses.append({
        "id": "geju", "title": "格局成败", "icon": "◈",
        "modules": ["格局评定", "成破救应", "特殊格局"],
        "text": "从格局成败论——" + "；".join(bits) + "。此定一命之高低贵贱、成败枢机。",
    })

    # ② 强弱用神视角
    si = chart.get("strength_info", {}) or {}
    ys = chart.get("yong_shen", {}) or {}
    th = chart.get("tiaohou", {}) or {}
    bits = []
    bits.append(f"日主{dm}{dm_wx}，月令{si.get('monthly_status','')}"
                + ("、得令" if si.get("deling") else "、失令")
                + ("、通根" if si.get("deqi") else "、不通根")
                + f"，综评{chart.get('strength','')}")
    if ys.get("yong_shen_wx"):
        bits.append(f"取{ys['yong_shen_wx']}为用、喜{ys.get('xi_shen_wx','')}、忌{ys.get('ji_shen_wx','')}")
    if th.get("primary"):
        bits.append(f"调候须{th['primary']}"
                    + ("（在局，气候得调）" if th.get("primary_in_chart") else "（不上卦，待运补）"))
    lenses.append({
        "id": "qiangruo", "title": "强弱用神", "icon": "☯",
        "modules": ["日主旺衰", "用神喜忌", "调候"],
        "text": "从强弱用神论——" + "；".join(bits) + "。此明趋避之方、扶抑之道。",
    })

    # ③ 十神性情视角
    ss = chart.get("shishen_summary", []) or []
    prof = chart.get("day_master_profile", {}) or {}
    bits = []
    if ss:
        ranked = sorted(ss, key=lambda x: -x.get("count", 0))
        top = ranked[0]
        bits.append(f"十神以{top['shishen']}最众（{top['count']}见，{top.get('strength','')}）")
        if len(ranked) > 1 and ranked[1].get("count"):
            bits.append(f"次为{ranked[1]['shishen']}")
        absent = [s["shishen"] for s in ss if s.get("count", 0) == 0]
        if absent:
            bits.append("阙者：" + "、".join(absent[:3]))
    traits = prof.get("core_traits") or prof.get("strengths")
    if traits:
        t = "、".join(traits[:3]) if isinstance(traits, list) else str(traits)
        bits.append(f"日主性情：{t}")
    lenses.append({
        "id": "shishen", "title": "十神性情", "icon": "⚖",
        "modules": ["十神统计", "日主性情"],
        "text": "从十神性情论——" + "；".join(bits) + "。此察才性所偏、六亲之厚薄。",
    })

    # ④ 刑冲会合视角
    rel = (chart.get("relations", {}) or {}).get("summary", {}) or {}
    bits = []
    th_he, th_ch, th_xing = rel.get("total_he", 0), rel.get("total_chong", 0), rel.get("total_xing", 0)
    bits.append(f"支中{th_he}合、{th_ch}冲、{th_xing}刑")
    for w in (rel.get("key_warnings", []) or [])[:2]:
        bits.append(w.replace("⚠ ", ""))
    for b in (rel.get("key_blessings", []) or [])[:1]:
        bits.append(b.replace("✓ ", ""))
    lenses.append({
        "id": "xingchong", "title": "刑冲会合", "icon": "✕",
        "modules": ["干支刑冲合害"],
        "text": "从刑冲会合论——" + "；".join(bits) + "。此观一生动荡聚散、吉凶之引动。",
    })

    # ⑤ 神煞应验视角
    sha = chart.get("shensha", []) or []
    bits = []
    if sha:
        names = []
        for s in sha[:6]:
            names.append(f"{s.get('name','')}（{s.get('pillar','')}{s.get('dizhi','')}）")
        bits.append("命带" + "、".join(names))
        if len(sha) > 6:
            bits.append(f"等共{len(sha)}神煞")
    else:
        bits.append("命无显著神煞")
    lenses.append({
        "id": "shensha", "title": "神煞应验", "icon": "✦",
        "modules": ["神煞"],
        "text": "从神煞应验论——" + "；".join(bits) + "。神煞为辅，须合格局用神参看，不可执一而断。",
    })

    # ⑥ 宫位根基视角
    mg = chart.get("minggong", {}) or {}
    shg = chart.get("shengong", {}) or {}
    ty = chart.get("taiyuan", {}) or {}
    rys = chart.get("renyuan_siling", {}) or {}
    bits = []
    if mg.get("label"):
        bits.append(f"命宫{mg['label']}（先天禀赋之位）")
    if shg.get("label"):
        bits.append(f"身宫{shg['label']}（后天趋向之位）")
    if ty.get("label"):
        bits.append(f"胎元{ty['label']}（受胎之根）")
    if rys.get("phase"):
        bits.append(f"人元{rys['phase']}（月令司权之神）")
    lenses.append({
        "id": "gongwei", "title": "宫位根基", "icon": "宫",
        "modules": ["命宫", "身宫", "胎元", "人元司令"],
        "text": "从宫位根基论——" + "；".join(bits) + "。此溯先天之禀、后天之向、受气之深浅。",
    })

    # ⑦ 运程时序（大运流年并入 — 后天之时）
    cf = chart.get("current_fortune", {}) or {}
    if cf.get("available"):
        cdy = cf.get("current_dayun", {}) or {}
        cln = cf.get("current_liunian", {}) or {}
        rec = cf.get("recent_years", []) or []
        tbits = [f"现行{cdy.get('ganzhi','')}大运（{cdy.get('start_age','')}-{cdy.get('end_age','')}岁，{cdy.get('shishen','')}，{cdy.get('quality','')}）"]
        if cln.get("ganzhi"):
            tbits.append(f"{cf.get('current_year','')}年{cln.get('ganzhi','')}（{cln.get('shishen','')}·{cln.get('quality','')}）")
        if rec:
            tbits.append("近年：" + "、".join(f"{r['year']}{r['ganzhi']}({r['quality']})" for r in rec[:4]))
        txt = ("从运程时序论——" + "；".join(tbits) +
               "。先天定格局高低，后天之大运流年定其何时起伏、何事应验；" +
               (cf.get("suiyun_brief", "")[:36] if cf.get("suiyun_brief") else "岁运相参，趋吉避凶在乎其时。"))
    else:
        txt = "从运程时序论——未输入完整生辰或无法起运；补全生辰即可断现行大运、流年与近年运势，知命局何时起伏。"
    lenses.append({
        "id": "yuncheng", "title": "运程时序", "icon": "运",
        "modules": ["大运", "流年", "岁运组合"],
        "text": txt,
    })

    coverage = {}
    for ln in lenses:
        for m in ln["modules"]:
            coverage[m] = ln["title"]

    return {
        "available": True,
        "day_master": f"{dm}{dm_wx}",
        "lenses": lenses,
        "coverage": coverage,
    }
