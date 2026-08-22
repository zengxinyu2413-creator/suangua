"""
core/fengshui/yangzhai_perspectives.py
======================================
阳宅三要·多视角整合解读（子模块必尽其用·无孤儿）。

  ① 门主灶三要 —— 门主局 × 灶局 × 三要关系
  ② 人宅相配 —— 命卦 × 游年吉凶（八宅明镜命根）
  ③ 东西四纯度 —— 纯杂 × 卦组
  ④ 八游年星 —— 八星详解（生气天医…绝命五鬼）
  ⑤ 六事安置 —— 路井灶厕碓磨畜栏
  ⑥ 楼层穿宫 —— 楼层五行 × 穿宫九星
"""
from __future__ import annotations
from typing import Dict, Any, List


def build_perspectives(result: Dict[str, Any]) -> Dict[str, Any]:
    if not result or not result.get("grade"):
        return {"available": False}

    mzj = result.get("menzhu_ju", {}) or {}
    zaoju = result.get("zao_ju", {}) or {}
    rel = result.get("relations", {}) or {}
    mm = result.get("mingua_match", {}) or {}
    pur = result.get("purity", {}) or {}
    sref = result.get("star_reference", {}) or {}
    ls = result.get("liushi_guide", {}) or {}
    fl = result.get("floor_guide", {}) or {}

    lenses: List[Dict[str, Any]] = []

    # ① 门主灶三要
    bits = [f"门主局：{mzj.get('ming','')}（{mzj.get('younian','')}·{mzj.get('level','')}）"]
    if zaoju.get("quality"):
        bits.append(f"灶局：主灶{zaoju.get('zhu_zao_star','')}、门灶{zaoju.get('men_zao_star','')}、灶口{zaoju.get('mouth_star','')}（{zaoju.get('quality','')}）")
    lenses.append({
        "id": "sanyao", "title": "门主灶三要", "icon": "要",
        "modules": ["门主局", "灶局", "三要关系"],
        "text": "从门主灶三要论——" + "；".join(bits) + "。门纳气、主居人、灶养命，三者游年相得为吉宅之本。",
    })

    # ② 人宅相配
    if mm.get("available"):
        my, zy, zaoy = mm.get("men_younian", {}), mm.get("zhu_younian", {}), mm.get("zao_younian", {})
        bits = [f"主人{mm.get('ming_gua','')}命（{mm.get('ming_group','')}）配{mm.get('house_group','').replace('卦','宅')}：{mm.get('match_level','')}",
                f"门{my.get('younian','')}（{my.get('ji_xiong','')}）·主{zy.get('younian','')}（{zy.get('ji_xiong','')}）·灶{zaoy.get('younian','')}（{zaoy.get('ji_xiong','')}）"]
        txt = "从人宅相配论——" + "；".join(bits) + "。此《八宅明镜》之命根：东四命住东四宅、门主灶居本命四吉方为要。"
    else:
        txt = "从人宅相配论——未输入主人生年，无以断命卦人宅相配；建议补入生年性别，方得《八宅明镜》人宅相得之全断。"
    lenses.append({
        "id": "renzhai", "title": "人宅相配", "icon": "命",
        "modules": ["命卦", "游年吉凶"], "text": txt,
    })

    # ③ 东西四纯度
    lenses.append({
        "id": "chundu", "title": "东西四纯度", "icon": "纯",
        "modules": ["纯杂", "卦组"],
        "text": "从东西四纯度论——" + (pur.get("desc", "") or "门主灶纯杂待考") + "。纯一则气专吉力聚，驳杂则气散吉力分。",
    })

    # ④ 八游年星
    if sref:
        ji = [f"{k}({v.get('jiuxing','')})" for k, v in sref.items() if v.get("level", "") in ("上吉", "中吉", "小吉")]
        xiong = [f"{k}({v.get('jiuxing','')})" for k, v in sref.items() if "凶" in v.get("level", "")]
        bits = []
        if ji:
            bits.append("四吉：" + "、".join(ji[:4]))
        if xiong:
            bits.append("四凶：" + "、".join(xiong[:4]))
        txt = "从八游年星论——" + "；".join(bits) + "。八宅以大游年翻卦，八星定方位吉凶，宜吉方起居、凶方厕库。"
    else:
        txt = "从八游年星论——八星详解待补。"
    lenses.append({
        "id": "youxing", "title": "八游年星", "icon": "星",
        "modules": ["八星详解"], "text": txt,
    })

    # ⑤ 六事安置
    items = ls.get("items", {}) or {}
    if items:
        names = "、".join(list(items.keys()))
        txt = f"从六事安置论——已纳{names}诸事之宜忌方。路井灶厕碓磨畜栏各有所宜之方，宜吉方者吉、忌方者凶。"
    else:
        txt = "从六事安置论——六事安置待断。"
    lenses.append({
        "id": "liushi", "title": "六事安置", "icon": "事",
        "modules": ["路井灶厕碓磨畜栏"], "text": txt,
    })

    # ⑥ 楼层穿宫
    bits = []
    if fl:
        bits.append("楼层：" + (fl.get("desc") or fl.get("summary") or str(fl))[:36])
    else:
        bits.append("未输入楼层，宜补以断楼层五行生克")
    lenses.append({
        "id": "louceng", "title": "楼层穿宫", "icon": "层",
        "modules": ["楼层五行", "穿宫九星"],
        "text": "从楼层穿宫论——" + "；".join(bits) + "。楼层配宅命五行、穿宫九星定层运，宜层生宅、忌层克宅。",
    })

    coverage = {}
    for ln in lenses:
        for m in ln["modules"]:
            coverage[m] = ln["title"]

    return {"available": True, "house_type": result.get("house_type", ""),
            "lenses": lenses, "coverage": coverage}
