"""
core/liuyao/yongshen_synthesis.py
=================================
六爻·用神力量综合评估 —— 子模块互助逻辑的显式集成层。

各子模块各探一信号：旺衰（月日）定基力，动变（回头生克/进退）增减其势，
三合三会（合起）聚力，空破墓为病。然基础力量（force）仅出于月日，动变与
合局虽各自侦测，却未回馈到用神之核心评估——是谓「各探各的、未相辅助」。

本层把诸信号汇于用神一身，逐条标明【出自何模块·利害几何】，合成一个综合力量
判断，并产出一条「推理链」——使「子模块之间如何互相辅助」既被构建、亦被呈现。

只汇集既有结构化结果（zonghe_duan / hua_bian / sanhe_sanhui），不重算。
"""
from __future__ import annotations
from typing import Dict, Any, List

_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 生
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}      # 克

# 局名 → 五行
_JU_WX = {
    "申子辰": "水", "北方水会": "水", "亥子丑": "水",
    "寅午戌": "火", "南方火会": "火", "巳午未": "火",
    "巳酉丑": "金", "西方金会": "金", "申酉戌": "金",
    "亥卯未": "木", "东方木会": "木", "寅卯辰": "木",
}


def _ju_wuxing(loc: Dict[str, Any]) -> str:
    nm = loc.get("name", "")
    for k, wx in _JU_WX.items():
        if k in nm or nm in k:
            return wx
    # 据 branches 推
    brs = "".join(loc.get("branches", []))
    for k, wx in _JU_WX.items():
        if all(b in brs for b in k):
            return wx
    return ""


def synthesize_yongshen_strength(result: Dict[str, Any]) -> Dict[str, Any]:
    """汇集旺衰×动变×合局×空破墓于用神，输出带出处的综合力量评估与推理链。"""
    zd = result.get("zonghe_duan", {}) or {}
    roles = zd.get("roles", {}) or {}
    yr = roles.get("用神", {}) or {}
    if not yr.get("present"):
        return {"available": False}

    yong_lq = yr.get("liu_qin", "")
    yong_branch = yr.get("branch", "")
    yong_wx = yr.get("wuxing", "")
    yong_pos = yr.get("position", 0)
    base_force = yr.get("force", 0)

    factors: List[Dict[str, Any]] = []  # {source, label, polarity(利/害/中), weight}

    # ① 旺衰（月日令）—— 基力
    for note in (yr.get("ws_notes", []) or []):
        pol = "利" if any(k in note for k in ("临", "生")) else (
            "害" if any(k in note for k in ("克", "泄", "耗", "破")) else "中")
        w = 0
        if "临" in note:
            w = 2
        elif "生" in note:
            w = 1
        elif "克" in note or "破" in note:
            w = -2
        elif "泄" in note or "耗" in note:
            w = -1
        factors.append({"source": "旺衰·月日令", "label": note, "polarity": pol, "weight": w})
    if not yr.get("ws_notes"):
        factors.append({"source": "旺衰·月日令", "label": "月日无生克",
                        "polarity": "中", "weight": 0})

    # ② 空破墓 —— 病（条件性，待解）
    if yr.get("is_kong"):
        factors.append({"source": "空破墓·病", "label": "用神旬空——气虚待填实",
                        "polarity": "害", "weight": -1})
    if yr.get("yuepo"):
        factors.append({"source": "空破墓·病", "label": "用神月破——力损待出月或填合",
                        "polarity": "害", "weight": -2})
    if yr.get("entombed"):
        factors.append({"source": "空破墓·病", "label": "用神入墓——气闭待冲墓开库",
                        "polarity": "害", "weight": -1})

    # ③ 动变（回头生克 / 进退）—— 自身发动之果
    hua = yr.get("hua", "")
    if yr.get("is_dong"):
        if "回头生" in hua:
            factors.append({"source": "动变·回头", "label": "用神发动化回头生——动而得化神生扶，势增",
                            "polarity": "利", "weight": 2})
        elif "回头克" in hua:
            factors.append({"source": "动变·回头", "label": "用神发动化回头克——动而受化神回克，先成后败",
                            "polarity": "害", "weight": -2})
        elif "进/退" in hua or "进神" in hua:
            factors.append({"source": "动变·进退", "label": "用神化进退神——须辨进神增力、退神减势",
                            "polarity": "中", "weight": 0})
        elif "反吟" in hua:
            factors.append({"source": "动变·反吟", "label": "用神化反吟——反复不定、事多变更",
                            "polarity": "害", "weight": -1})
        elif "伏吟" in hua:
            factors.append({"source": "动变·伏吟", "label": "用神化伏吟——呻吟难安、迟滞忧疑",
                            "polarity": "害", "weight": -1})
        else:
            factors.append({"source": "动变", "label": "用神发动——主事有变动",
                            "polarity": "中", "weight": 0})

    # ④ 他爻发动对用神（原神动生用 / 忌神动克用）—— 跨爻互助
    yaos = result.get("yaos", [])
    yuan_lq = (roles.get("原神", {}) or {}).get("liu_qin", "")
    ji_lq = (roles.get("忌神", {}) or {}).get("liu_qin", "")
    for y in yaos:
        if not y.get("is_changing") or y.get("position") == yong_pos:
            continue
        lq = y.get("liu_qin", "")
        if lq == yuan_lq and yuan_lq:
            factors.append({"source": "四位·原神动", "label": f"原神（{lq}{y.get('branch','')}）发动生用——源头有助",
                            "polarity": "利", "weight": 1})
        elif lq == ji_lq and ji_lq:
            factors.append({"source": "四位·忌神动", "label": f"忌神（{lq}{y.get('branch','')}）发动克用——阻力当前",
                            "polarity": "害", "weight": -1})

    # ⑤ 三合三会（合起用神）—— 聚力
    ss = result.get("sanhe_sanhui", {}) or {}
    for loc in (ss.get("sanhe", []) or []) + (ss.get("sanhui", []) or []):
        if yong_pos in (loc.get("positions", []) or []):
            ju_wx = _ju_wuxing(loc)
            nm = loc.get("name", "局")
            if ju_wx and (ju_wx == yong_wx or _SHENG.get(ju_wx) == yong_wx):
                factors.append({"source": "三合三会·合起",
                                "label": f"用神入「{nm}」（{ju_wx}）——合起或生扶用神，聚力大增",
                                "polarity": "利", "weight": 2})
            elif ju_wx and _SHENG.get(yong_wx) == ju_wx:
                factors.append({"source": "三合三会·泄气",
                                "label": f"用神入「{nm}」（{ju_wx}）然用神生局——化泄其气，力反减",
                                "polarity": "害", "weight": -1})
            elif ju_wx and _KE.get(ju_wx) == yong_wx:
                factors.append({"source": "三合三会·克用",
                                "label": f"用神入「{nm}」（{ju_wx}）然局五行克用——化合反伤",
                                "polarity": "害", "weight": -1})
            else:
                factors.append({"source": "三合三会",
                                "label": f"用神涉「{nm}」之局——气有所聚",
                                "polarity": "中", "weight": 0})
            break

    # ⑥ 持世（结构性有利，不计力但记之）
    main_yong = next((y for y in yaos if y.get("liu_qin") == yong_lq and y.get("is_world")), None)
    structural = ""
    if main_yong:
        structural = "用神持世——事系于己、主动权在我"

    # ── 综合：月日基力 + 月日之外各模块修正 ──
    extra = sum(f["weight"] for f in factors if not f["source"].startswith("旺衰"))
    composite = base_force + extra

    if composite >= 3:
        comp_label, comp_desc = "综合大有力", "用神得月日生扶、复有动变合局之助，力量充沛，所求易遂"
    elif composite >= 1:
        comp_label, comp_desc = "综合有力", "用神总体有气，虽或有小病，得助可成"
    elif composite >= -1:
        comp_label, comp_desc = "综合中和", "用神力量参半，成败系于应期能否得力引动"
    else:
        comp_label, comp_desc = "综合无力", "用神受制多端，气衰力弱，所求难遂，须待岁运补益"

    # 推理链文本（显式呈现模块如何互相辅助）
    chain_parts = [f"用神{yong_lq}{yong_branch}（基力{base_force:+d}·{yr.get('wangshuai','')}）"]
    for f in factors:
        if f["source"].startswith("旺衰"):
            continue
        sign = "＋" if f["weight"] > 0 else ("－" if f["weight"] < 0 else "·")
        chain_parts.append(f"〔{f['source']}〕{sign}{f['label']}")
    chain_parts.append(f"⟹ {comp_label}（综合力{composite:+d}）")
    chain_text = "　→　".join(chain_parts)

    return {
        "available": True,
        "yong_liuqin": yong_lq,
        "yong_branch": yong_branch,
        "base_force": base_force,
        "composite_force": composite,
        "composite_label": comp_label,
        "composite_desc": comp_desc,
        "structural": structural,
        "factors": factors,
        "chain_text": chain_text,
    }
