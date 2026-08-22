"""
core/fengshui/xuankong_perspectives.py
======================================
玄空飞星·多视角整合解读（子模块必尽其用·无孤儿）。

  ① 山向格局 —— 三盘格局 × 力量推理链
  ② 特殊格局 —— 七星打劫/三般卦/五黄 × 反伏吟
  ③ 正零城门 —— 正零神 × 城门 × 收山出煞
  ④ 九宫吉凶 —— 各宫飞星判断（财丁病位分布）
  ⑤ 峦头形理 —— 砂水宜忌 × 旺衰方
  ⑥ 化解流年 —— 化解法 × 流年警示 × 太岁
"""
from __future__ import annotations
from typing import Dict, Any, List

_DIR8 = {"1": "北", "2": "西南", "3": "东", "4": "东南", "6": "西北", "7": "西", "8": "东北", "9": "南"}


def build_perspectives(chart: Dict[str, Any]) -> Dict[str, Any]:
    if not chart or not chart.get("verdict"):
        return {"available": False}

    verdict = chart.get("verdict", "")
    zsyn = chart.get("zhaiyun_synthesis", {}) or {}
    sps = chart.get("special_patterns", []) or []
    ff = chart.get("fan_fu_yin", {}) or {}
    zls = chart.get("zheng_ling_shen", {}) or {}
    cm = chart.get("chengmen", {}) or {}
    pj = chart.get("palace_judgments", {}) or {}
    lt = chart.get("luantou_summary", {}) or {}
    remedies = chart.get("remedies", []) or []
    annual = chart.get("annual_warnings", []) or []
    taisui = chart.get("taisui", {}) or {}
    shoushan = chart.get("shoushan_chusha", {}) or {}

    lenses: List[Dict[str, Any]] = []

    # ① 山向格局
    bits = [f"三盘合断得「{verdict}」"]
    if zsyn.get("available"):
        bits.append(f"综合力量评「{zsyn.get('composite_label','')}」（{zsyn.get('composite_desc','')[:24]}）")
    lenses.append({
        "id": "geju", "title": "山向格局", "icon": "盘",
        "modules": ["三盘格局", "力量推理链"],
        "text": "从山向格局论——" + "；".join(bits) + "。此为一宅丁财之根本格局。",
    })

    # ② 特殊格局
    bits = []
    good = [s.get("name", "") for s in sps if s.get("level", "").startswith("auspicious")]
    bad = [s.get("name", "") for s in sps if s.get("level", "").startswith("inauspicious")]
    if good:
        bits.append("吉格：" + "、".join(good[:3]))
    if bad:
        bits.append("凶象：" + "、".join(bad[:3]))
    if ff.get("has_fan_fu_yin"):
        bits.append("犯反吟伏吟——主反复动荡")
    lenses.append({
        "id": "tege", "title": "特殊格局", "icon": "格",
        "modules": ["七星打劫三般卦五黄", "反伏吟"],
        "text": "从特殊格局论——" + ("；".join(bits) if bits else "无显著特殊格局") + "。特殊格局或救凶局、或破吉局，最宜留意。",
    })

    # ③ 正零城门
    bits = []
    zs = zls.get("zhengshen", {}) or {}
    if zs:
        bits.append(f"正神在{zs.get('zhengshen_dir','')}（宜静宜高），零神在{zs.get('lingshen_dir','')}（宜动宜水）")
    if cm.get("desc"):
        bits.append("城门：" + cm["desc"][:36])
    if shoushan.get("desc"):
        bits.append("收山出煞：" + str(shoushan["desc"])[:30])
    lenses.append({
        "id": "zhengling", "title": "正零城门", "icon": "门",
        "modules": ["正零神", "城门", "收山出煞"],
        "text": "从正零城门论——" + ("；".join(bits) if bits else "正零城门待考") + "。正零得用、城门得诀，乃催财旺丁之关窍。",
    })

    # ④ 九宫吉凶
    bits = []
    if pj:
        wang_gong, sha_gong = [], []
        for k, v in pj.items():
            nat = v.get("nature", "")
            d = _DIR8.get(str(k), f"{k}宫")
            if nat.startswith("auspicious"):
                wang_gong.append(f"{d}（{v.get('short','')[:8]}）")
            elif nat.startswith("inauspicious"):
                sha_gong.append(f"{d}（{v.get('short','')[:8]}）")
        if wang_gong:
            bits.append("吉旺之宫：" + "、".join(wang_gong[:3]))
        if sha_gong:
            bits.append("凶煞之宫：" + "、".join(sha_gong[:3]))
    lenses.append({
        "id": "jiugong", "title": "九宫吉凶", "icon": "宫",
        "modules": ["各宫飞星判断"],
        "text": "从九宫吉凶论——" + ("；".join(bits) if bits else "各宫平和") + "。各宫飞星定财丁病位之分布，布局当趋吉宫、避煞宫。",
    })

    # ⑤ 峦头形理
    bits = []
    if lt.get("wang_directions"):
        bits.append("当运旺方：" + "、".join(lt["wang_directions"][:4]) + "（宜水宜动）")
    if lt.get("shuai_directions"):
        bits.append("衰死方：" + "、".join(lt["shuai_directions"][:3]) + "（宜山宜静）")
    lenses.append({
        "id": "luantou", "title": "峦头形理", "icon": "峦",
        "modules": ["砂水宜忌", "旺衰方"],
        "text": "从峦头形理论——" + ("；".join(bits) if bits else "峦头待勘") + "。理气须配峦头，旺方见水、衰方见山，方为形理兼备。",
    })

    # ⑥ 化解流年
    bits = []
    if remedies:
        rtexts = [r if isinstance(r, str) else r.get("desc", r.get("text", "")) for r in remedies]
        bits.append("化解：" + "；".join(t[:24] for t in rtexts[:2]))
    if annual:
        atexts = [a if isinstance(a, str) else a.get("desc", a.get("text", "")) for a in annual]
        bits.append("流年警示：" + "；".join(t[:24] for t in atexts[:2]))
    if taisui.get("dir") or taisui.get("desc"):
        bits.append("太岁：" + str(taisui.get("desc", taisui.get("dir", "")))[:24])
    lenses.append({
        "id": "huajie", "title": "化解流年", "icon": "解",
        "modules": ["化解法", "流年警示", "太岁"],
        "text": "从化解流年论——" + ("；".join(bits) if bits else "本运无须特别化解") + "。凶煞之位以化解物制之，流年飞星叠加须随年调整。",
    })

    coverage = {}
    for ln in lenses:
        for m in ln["modules"]:
            coverage[m] = ln["title"]

    return {"available": True, "verdict": verdict, "lenses": lenses, "coverage": coverage}
