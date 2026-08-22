"""
core/date_selection/perspectives.py
===================================
择日·多视角整合解读（子模块必尽其用·无孤儿）。

  ① 首选吉日 —— 建除黄道宜忌 × 力量推理链
  ② 神煞值日 —— 吉神 × 凶煞 × 彭祖百忌
  ③ 方位避忌 —— 三煞 × 喜财福神方 × 胎神
  ④ 冲合旬空 —— 日支冲 × 旬空 × 岁破月破
  ⑤ 全月吉凶 —— 吉日分布 × 忌避之日
  ⑥ 个人配合 —— 本命冲克（年命）× 择时建议
"""
from __future__ import annotations
from typing import Dict, Any, List


def build_perspectives(result: Dict[str, Any]) -> Dict[str, Any]:
    best = result.get("best_days", []) or []
    ausp = result.get("auspicious_days", []) or []
    inausp = result.get("inauspicious_days", []) or []
    top = best[0] if best else (ausp[0] if ausp else None)
    if not top:
        return {"available": False}

    syn = result.get("zeri_synthesis", {}) or {}
    purpose = result.get("purpose", "")
    lenses: List[Dict[str, Any]] = []

    # ① 首选吉日
    bits = [f"首选{top.get('date','')}（{top.get('ganzhi','')}）{top.get('officer','')}日、{top.get('star','')}宿，评分{top.get('score','')}"]
    if syn.get("available"):
        bits.append(f"力量评「{syn.get('composite_label','')}」")
    yi = top.get("yi", []) or []
    if yi:
        bits.append("宜：" + "、".join(str(y) for y in yi[:4]))
    lenses.append({
        "id": "topday", "title": "首选吉日", "icon": "吉",
        "modules": ["建除黄道宜忌", "力量推理链"],
        "text": "从首选吉日论——" + "；".join(bits) + "。此为本月择「" + purpose + "」之最优良辰。",
    })

    # ② 神煞值日
    bits = []
    js = []
    if top.get("tiande"):
        js.append("天德")
    if top.get("yuede"):
        js.append("月德")
    js += [str(x) for x in (top.get("ji_shen", []) or [])[:3]]
    js = list(dict.fromkeys(j for j in js if j))
    if js:
        bits.append("吉神：" + "、".join(js[:4]))
    xs = top.get("xiong_sha", []) or []
    if xs:
        bits.append("凶煞：" + "、".join(str(x) for x in xs[:4]))
    pz = []
    if top.get("peng_zu_gan"):
        pz.append(str(top["peng_zu_gan"]))
    if top.get("peng_zu_zhi"):
        pz.append(str(top["peng_zu_zhi"]))
    if pz:
        bits.append("彭祖百忌：" + "；".join(p[:18] for p in pz))
    lenses.append({
        "id": "shensha", "title": "神煞值日", "icon": "煞",
        "modules": ["吉神", "凶煞", "彭祖百忌"],
        "text": "从神煞值日论——" + ("；".join(bits) if bits else "神煞平和") + "。吉神能解凶、凶煞须避忌，彭祖百忌为细则。",
    })

    # ③ 方位避忌
    bits = []
    if result.get("three_killings"):
        bits.append("三煞在" + str(result["three_killings"]) + "（忌动土修造）")
    pos = []
    for k, lab in [("xi_shen", "喜神"), ("cai_shen", "财神"), ("fu_shen", "福神"), ("yang_gui", "阳贵")]:
        if top.get(k):
            pos.append(f"{lab}{top[k]}")
    if pos:
        bits.append("吉神方：" + "、".join(pos))
    if top.get("tai_shen"):
        bits.append("胎神占" + str(top["tai_shen"]) + "（孕家忌动）")
    lenses.append({
        "id": "fangwei", "title": "方位避忌", "icon": "方",
        "modules": ["三煞", "喜财福神方", "胎神"],
        "text": "从方位避忌论——" + ("；".join(bits) if bits else "方位无忌") + "。举事座向宜趋吉神方、避三煞与胎神方。",
    })

    # ④ 冲合旬空
    bits = []
    if top.get("chong"):
        bits.append("此日冲" + str(top["chong"]) + "（属此者忌用此日）")
    if top.get("xun_kong"):
        bits.append("旬空" + str(top["xun_kong"]) + "（落空之事难成）")
    breakers = [d for d in (result.get("all_days", []) or []) if d.get("is_year_breaker") or d.get("is_month_breaker")]
    if breakers:
        bits.append(f"本月岁破月破{len(breakers)}日，百事不宜")
    lenses.append({
        "id": "chong", "title": "冲合旬空", "icon": "冲",
        "modules": ["日支冲", "旬空", "岁破月破"],
        "text": "从冲合旬空论——" + ("；".join(bits) if bits else "无显著冲空") + "。冲者避其属相、空者忌谋空事、岁破月破务必避之。",
    })

    # ⑤ 全月吉凶
    bits = [f"本月吉日 {len(ausp)} 天"]
    if best:
        bits.append("上选 " + "、".join(d.get("date", "")[5:] for d in best[:3]))
    if inausp:
        bits.append(f"忌避 {len(inausp)} 天")
    lenses.append({
        "id": "month", "title": "全月吉凶", "icon": "月",
        "modules": ["吉日分布", "忌避之日"],
        "text": "从全月吉凶论——" + "；".join(bits) + "。通月统观，便于在吉日中再依时辰、个人择优。",
    })

    # ⑥ 个人配合
    pz = result.get("personalization", {}) or {}
    if pz.get("available"):
        prof = pz.get("profile", {})
        pb = pz.get("personal_best", [])
        bits = [f"本命用神{prof.get('yong','')}、忌神{prof.get('ji','')}，本命日支{prof.get('day_zhi','')}"]
        if pb:
            bits.append("合本命之首选：" + "、".join(
                f"{b['date'][5:]}({b['ganzhi']}·通用{b['base_score']}{'+' if b['personal_score']>=0 else ''}{b['personal_score']}={b['combined_score']})"
                for b in pb[:3]))
        if pz.get("personal_avoid"):
            bits.append("个人不宜（通用吉但冲克本命）：" + "、".join(
                f"{a['date'][5:]}({a['ganzhi']})" for a in pz["personal_avoid"][:2]))
        txt = ("从个人配合论——" + "；".join(bits) +
               "。此乃据本人八字用神喜忌与命支冲合，于通用吉日中再择「日扶其用、不犯其冲」者，方为合本命之真吉。")
    else:
        chong = str(top.get("chong", ""))
        txt = (f"从个人配合论——所选之日冲{chong or '（无）'}，生肖属此者宜避；"
               f"输入本人生辰（年月日），即可据八字用神/冲克过滤出合本命之吉日，并避本命之冲克。")
    lenses.append({
        "id": "personal", "title": "个人配合", "icon": "人",
        "modules": ["本命用神冲克", "择时建议"],
        "text": txt,
    })

    coverage = {}
    for ln in lenses:
        for m in ln["modules"]:
            coverage[m] = ln["title"]

    return {"available": True, "purpose": purpose, "lenses": lenses, "coverage": coverage}
