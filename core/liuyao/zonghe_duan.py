"""
core/liuyao/zonghe_duan.py
==========================
六爻·综合断卦（用神—原神—忌神—仇神 四位生克总断）。

六爻之断，全在用神一字：先定用神，次推原神（生用神者）、忌神（克用神者）、
仇神（生忌神者），合月建日辰之旺衰、动静、空破墓绝，方成吉凶之总断。

原 deep_relations 之 yong_yuan_ji_chou 与 summary 在用神为世/应（非六亲名）时
落空，本模块补足之，并据《增删卜易》《卜筮正宗》断卦法则，产出：
  · 四位定位与状态（爻位·六亲·五行·旺衰·动静·空破墓）
  · 断语链（用神有力否、原神生扶否、忌神克否、动化吉凶、世应生克）
  · 吉凶总断 + 信心度

复用 najia 已标之每爻（branch/element/liu_qin/is_world/is_changing/kong_wang/
changed_branch）与 relations 之四位五行判定，与排卦同源。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.constants import DIZHI_WUXING, WUXING_SHENG, WUXING_KE
from core.liuyao.relations import identify_yuanshen_jishen_choushen

# 六冲
_CHONG = {
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
}
# 五行墓库（地支）
_MU = {"木": "未", "火": "戌", "金": "丑", "水": "辰", "土": "辰"}


def _wx(branch: str) -> str:
    return DIZHI_WUXING.get(branch, "")


def _wangshuai(branch: str, month_zhi: str, day_zhi: str) -> Dict[str, Any]:
    """以月建日辰断某爻地支之旺衰，返回 force 与 label 及状态标记。"""
    wx = _wx(branch)
    force = 0
    notes: List[str] = []
    for src, label in ((month_zhi, "月建"), (day_zhi, "日辰")):
        if not src:
            continue
        swx = _wx(src)
        if branch == src:
            force += 2; notes.append(f"临{label}")
        elif WUXING_SHENG.get(swx) == wx:
            force += 1; notes.append(f"{label}生")
        elif WUXING_KE.get(swx) == wx:
            force -= 2; notes.append(f"{label}克")
        elif WUXING_SHENG.get(wx) == swx:
            force -= 1; notes.append(f"泄于{label}")
        elif WUXING_KE.get(wx) == swx:
            force -= 1; notes.append(f"耗于{label}")
    # 月破
    yuepo = (month_zhi and _CHONG.get(branch) == month_zhi)
    ripo = (day_zhi and _CHONG.get(branch) == day_zhi)
    if yuepo:
        force -= 2; notes.append("月破")
    if force >= 2:
        label = "旺相"
    elif force >= 0:
        label = "中和"
    elif force > -3:
        label = "休囚"
    else:
        label = "无气"
    return {"force": force, "label": label, "notes": notes,
            "yuepo": bool(yuepo), "ripo": bool(ripo)}


def _entombed(branch: str, month_zhi: str, day_zhi: str) -> bool:
    """用神入墓于日（或自身坐墓）——简判：用神五行墓库 == 日辰。"""
    wx = _wx(branch)
    return bool(day_zhi and _MU.get(wx) == day_zhi)


def _locate_yong(yaos: List[Dict], spec: List[str]) -> Dict[str, Any]:
    """据用神规范（六亲名 / 世爻 / 应爻）定位用神爻。"""
    spec = spec or ["世爻"]
    primary = spec[0]

    if primary == "世爻":
        y = next((x for x in yaos if x.get("is_world")), None)
        return {"yao": y, "name": "世爻", "liu_qin": y.get("liu_qin", "") if y else "", "fu": False}
    if primary == "应爻":
        y = next((x for x in yaos if x.get("is_application")), None)
        return {"yao": y, "name": "应爻", "liu_qin": y.get("liu_qin", "") if y else "", "fu": False}

    # 六亲用神：可能多现，取持世 > 发动 > 临爻首现
    cand = [x for x in yaos if x.get("liu_qin") == primary]
    if not cand:
        return {"yao": None, "name": primary, "liu_qin": primary, "fu": True}  # 伏神/不上卦
    chosen = next((x for x in cand if x.get("is_world")), None) \
        or next((x for x in cand if x.get("is_changing")), None) \
        or cand[0]
    return {"yao": chosen, "name": primary, "liu_qin": primary, "fu": False}


def _role_state(yao: Optional[Dict], month_zhi: str, day_zhi: str,
                kong: List[str]) -> Dict[str, Any]:
    """评一爻（用神/原神/忌神）之完整状态。"""
    if not yao:
        return {"present": False, "desc": "不上卦（伏藏）"}
    branch = yao.get("branch", "")
    ws = _wangshuai(branch, month_zhi, day_zhi)
    is_kong = yao.get("kong_wang") or (branch in (kong or []))
    is_dong = bool(yao.get("is_changing"))
    entomb = _entombed(branch, month_zhi, day_zhi)
    # 动而化回头生克 / 进退
    hua = ""
    if is_dong and yao.get("changed_branch"):
        cb = yao["changed_branch"]
        ow, cw = _wx(branch), _wx(cb)
        if WUXING_SHENG.get(cw) == ow:
            hua = "化回头生（吉）"
        elif WUXING_KE.get(cw) == ow:
            hua = "化回头克（凶）"
        elif cb == branch:
            hua = "化伏吟"
        elif _CHONG.get(cb) == branch:
            hua = "化反吟（冲）"
        elif ow == cw:
            hua = "化进/退神"
    return {
        "present": True, "branch": branch, "wuxing": _wx(branch),
        "liu_qin": yao.get("liu_qin", ""),
        "position": yao.get("position", 0),
        "wangshuai": ws["label"], "force": ws["force"], "ws_notes": ws["notes"],
        "is_kong": bool(is_kong), "is_dong": is_dong,
        "yuepo": ws["yuepo"], "ripo": ws["ripo"], "entombed": entomb,
        "hua": hua,
        "liu_shen": yao.get("liu_shen", ""),
    }


def _strong(state: Dict[str, Any]) -> bool:
    """该爻是否有力（旺相且不空不破不墓）。"""
    if not state.get("present"):
        return False
    if state.get("is_kong") or state.get("yuepo") or state.get("entombed"):
        return False
    return state.get("force", 0) >= 1


def analyze_zonghe_duan(yaos: List[Dict], yong_shen_spec: List[str],
                        month_zhi: str, day_zhi: str,
                        kong: Optional[List[str]] = None,
                        topic: str = "") -> Dict[str, Any]:
    """六爻综合断卦总入口。"""
    kong = kong or []
    loc = _locate_yong(yaos, yong_shen_spec)
    yong_yao = loc["yao"]

    if not yong_yao:
        return {
            "available": True, "yong_shen": loc["name"], "fu_shen": True,
            "verdict": f"用神（{loc['name']}）不上卦、伏而不现——其事隐伏未发，"
                       f"须看伏神得提拔出伏之时方有应，目下未可遽断。",
            "conclusion": "待时", "confidence": "低",
            "roles": {}, "reasoning": ["用神不上卦，伏藏待出。"],
        }

    yong_wx = yong_yao.get("element") or _wx(yong_yao.get("branch", ""))
    yyjc = identify_yuanshen_jishen_choushen(yong_wx)
    yuan_wx = yyjc.get("原神_wx", "")
    ji_wx = yyjc.get("忌神_wx", "")
    chou_wx = yyjc.get("仇神_wx", "")

    def _first_by_wx(wx: str) -> Optional[Dict]:
        cand = [y for y in yaos if (y.get("element") or _wx(y.get("branch", ""))) == wx]
        if not cand:
            return None
        return next((y for y in cand if y.get("is_changing")), None) or cand[0]

    yong_state = _role_state(yong_yao, month_zhi, day_zhi, kong)
    yuan_state = _role_state(_first_by_wx(yuan_wx), month_zhi, day_zhi, kong)
    ji_state = _role_state(_first_by_wx(ji_wx), month_zhi, day_zhi, kong)
    chou_state = _role_state(_first_by_wx(chou_wx), month_zhi, day_zhi, kong)

    # ── 断卦逻辑 ──
    reasoning: List[str] = []
    score = 0

    # 1) 用神本体
    yname = loc["name"] + (f"（{yong_state['liu_qin']}{yong_state['branch']}）" if yong_state.get("liu_qin") else f"（{yong_state['branch']}）")
    if _strong(yong_state):
        score += 2
        reasoning.append(f"用神{yname}{yong_state['wangshuai']}（{('、'.join(yong_state['ws_notes']) or '得气')}），用神有力，事有根基。")
    else:
        bad = []
        if yong_state.get("is_kong"): bad.append("空亡")
        if yong_state.get("yuepo"): bad.append("月破")
        if yong_state.get("entombed"): bad.append("入墓")
        if yong_state.get("force", 0) < 0: bad.append(yong_state["wangshuai"])
        score -= 2
        reasoning.append(f"用神{yname}{('、'.join(bad) or '失气')}——用神无力，事乏根基，须赖原神生扶或日月填实。")

    # 用神动化
    if yong_state.get("hua"):
        if "吉" in yong_state["hua"]:
            score += 1; reasoning.append(f"用神发动{yong_state['hua']}，吉象增益。")
        elif "凶" in yong_state["hua"]:
            score -= 2; reasoning.append(f"用神发动{yong_state['hua']}，反伤其本，凶。")
        elif "反吟" in yong_state["hua"]:
            score -= 1; reasoning.append("用神化反吟，事多反复。")
        elif "伏吟" in yong_state["hua"]:
            score -= 1; reasoning.append("用神化伏吟，事滞呻吟难展。")

    # 2) 原神（生用神）
    if yuan_state.get("present"):
        if yuan_state.get("is_dong") and _strong(yuan_state):
            score += 2; reasoning.append(f"原神（{yuan_state['liu_qin']}{yuan_state['branch']}）发动且{yuan_state['wangshuai']}，生扶用神有力——大吉、有救。")
        elif yuan_state.get("is_dong"):
            score += 1; reasoning.append(f"原神发动而力弱（{yuan_state['wangshuai']}{'·空' if yuan_state['is_kong'] else ''}），有心生扶而力不足。")
        elif _strong(yuan_state):
            score += 1; reasoning.append(f"原神（{yuan_state['liu_qin']}{yuan_state['branch']}）{yuan_state['wangshuai']}静守，为用神之后援。")
        else:
            reasoning.append(f"原神休囚{'·空' if yuan_state['is_kong'] else ''}，生扶之力薄。")
    else:
        reasoning.append("原神不上卦，用神缺生扶之源。")

    # 3) 忌神（克用神）
    if ji_state.get("present"):
        if ji_state.get("is_dong") and _strong(ji_state):
            score -= 3; reasoning.append(f"⚠ 忌神（{ji_state['liu_qin']}{ji_state['branch']}）发动且{ji_state['wangshuai']}，克伤用神有力——此为大忌，主败、主灾。")
        elif ji_state.get("is_dong"):
            score -= 1; reasoning.append(f"忌神发动而力弱（{ji_state['wangshuai']}{'·空' if ji_state['is_kong'] else ''}），克力有限，为患不深。")
        elif _strong(ji_state):
            score -= 1; reasoning.append(f"忌神（{ji_state['liu_qin']}{ji_state['branch']}）{ji_state['wangshuai']}但静而不动，暂未发难，伏患宜防。")
        else:
            reasoning.append("忌神休囚不动，不能为害。")
    else:
        reasoning.append("忌神不上卦，无克用之患。")

    # 4) 仇神（生忌神/克原神）
    if chou_state.get("present") and chou_state.get("is_dong") and _strong(chou_state):
        score -= 1; reasoning.append(f"仇神（{chou_state['liu_qin']}{chou_state['branch']}）发动，党助忌神、克制原神，助纣为虐。")

    # 5) 世应
    world = next((y for y in yaos if y.get("is_world")), None)
    appl = next((y for y in yaos if y.get("is_application")), None)
    shiying = ""
    if world and appl:
        wwx, awx = _wx(world.get("branch", "")), _wx(appl.get("branch", ""))
        if WUXING_KE.get(wwx) == awx:
            shiying = "世克应——我处主动、事在掌控，求谋多由我得。"
        elif WUXING_KE.get(awx) == wwx:
            shiying = "应克世——对方占先、我受其制，谋事费力。"
        elif WUXING_SHENG.get(awx) == wwx:
            shiying = "应生世——对方助我、外来有援，事多顺遂。"
        elif WUXING_SHENG.get(wwx) == awx:
            shiying = "世生应——我付出于人、为他人作嫁。"
        else:
            shiying = "世应比和——彼此和顺、其事易谐。"

    # ── 结论 ──
    if score >= 3:
        conclusion, conf = "吉", "高" if score >= 5 else "中"
        verdict = "用神得时得地、生扶有力，所占之事可成、吉。"
    elif score >= 1:
        conclusion, conf = "偏吉", "中"
        verdict = "用神尚可、吉多于凶，事可成而须费些周折。"
    elif score >= -1:
        conclusion, conf = "中（吉凶参半）", "中"
        verdict = "吉凶相参、成败各半，须待日月引动、看应期消息方明。"
    elif score >= -3:
        conclusion, conf = "偏凶", "中"
        verdict = "用神乏力或忌神得势，事多阻逆、凶多于吉，宜守不宜进。"
    else:
        conclusion, conf = "凶", "高" if score <= -5 else "中"
        verdict = "用神无力、忌神动克，所占之事难成、凶，宜及早避让改图。"

    return {
        "available": True,
        "yong_shen": loc["name"], "yong_liuqin": yong_state.get("liu_qin", ""),
        "yong_wx": yong_wx,
        "fu_shen": False,
        "roles": {
            "用神": yong_state, "原神": yuan_state,
            "忌神": ji_state, "仇神": chou_state,
        },
        "role_wx": {"原神": yuan_wx, "忌神": ji_wx, "仇神": chou_wx},
        "reasoning": reasoning,
        "shiying": shiying,
        "score": score,
        "conclusion": conclusion, "confidence": conf,
        "verdict": verdict + (("　" + shiying) if shiying else ""),
    }
