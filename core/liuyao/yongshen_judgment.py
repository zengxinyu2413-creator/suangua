"""六爻用神落爻多维断语合成器
————————————————————————————————————————————————————————————
将用神之「现伏 × 旺衰 × 动静化象 × 空破墓 × 元神 × 忌神 × 世应」织为多维
具体断语，并据《增删卜易》成败法则合成综合成败断。处理用神现卦 / 伏藏 /
仅化爻三态。数据取自 zonghe_duan.roles（用神/原神/忌神已富集）及 fu_shen，
不另造，只组合 + 按古法生克方向判定。

六亲生克（固定）：父→兄→子→财→官→父（生）；父→子→官→兄→财→父（克）。
故：用神财，原神子孙(生财)、忌神兄弟(克财)；用神官，原神财、忌神子孙；
    用神父，原神官、忌神财；用神子，原神兄、忌神父；用神兄，原神父、忌神官。
"""
from typing import Dict, Any, List, Optional

# 六亲相生/相克（用于独立校验 roles 之原神忌神方向）
_LQ_SHENG = {"父母": "兄弟", "兄弟": "子孙", "子孙": "妻财", "妻财": "官鬼", "官鬼": "父母"}
_LQ_KE = {"父母": "子孙", "子孙": "官鬼", "官鬼": "兄弟", "兄弟": "妻财", "妻财": "父母"}

# 旺衰 label → 粗略力量值（与 strength.label 同源）
_WS_FORCE = {"旺": 2, "相": 1, "休": -1, "囚": -2, "死": -2}


def _locate_role_from_yaos(yaos: list, target_lq: str) -> dict:
    """roles 未填（用神伏时常见）时，从 yaos 按六亲定位原神/忌神爻并评其态。
    取力量最强之同六亲爻为代表（多爻则择旺动者）。"""
    cands = [y for y in yaos if y.get("liu_qin") == target_lq]
    if not cands:
        return {"present": False, "liu_qin": target_lq}

    def _f(y):
        lab = (y.get("strength") or {})
        lab = lab.get("label", "") if isinstance(lab, dict) else str(lab)
        base = _WS_FORCE.get(lab, 0)
        if y.get("is_changing"):
            base += 1   # 动则力显
        return base
    best = max(cands, key=_f)
    lab = (best.get("strength") or {})
    lab = lab.get("label", "") if isinstance(lab, dict) else str(lab)
    return {
        "present": True, "liu_qin": target_lq, "branch": best.get("branch", ""),
        "position": best.get("position", 0),
        "force": _WS_FORCE.get(lab, 0),
        "is_dong": bool(best.get("is_changing")),
        "is_kong": bool(best.get("kong_wang")),
        "yuepo": False, "entombed": False,
    }



def expected_yuanshen(yong_lq: str) -> str:
    """用神之原神 = 生用神之六亲（_LQ_SHENG 之逆）。"""
    for k, v in _LQ_SHENG.items():
        if v == yong_lq:
            return k
    return ""


def expected_jishen(yong_lq: str) -> str:
    """用神之忌神 = 克用神之六亲（_LQ_KE 之逆）。"""
    for k, v in _LQ_KE.items():
        if v == yong_lq:
            return k
    return ""


def _force_label(force: int) -> str:
    if force >= 2:
        return "旺相有力"
    if force >= 1:
        return "得气中和偏旺"
    if force == 0:
        return "中平"
    if force >= -1:
        return "衰弱"
    return "休囚无力"


def synthesize_yongshen_judgment(result: Dict[str, Any]) -> Dict[str, Any]:
    """合成用神多维断语。返回 {available, yong_shen_name, present_state,
    dimensions:[{dim,text,polarity}], verdict, verdict_level, paragraph}。"""
    zd = result.get("zonghe_duan", {}) or {}
    roles = zd.get("roles", {}) or {}
    yr = roles.get("用神", {}) or {}
    yuan = roles.get("原神", {}) or {}
    ji = roles.get("忌神", {}) or {}
    yaos = result.get("yaos", []) or []
    fu = result.get("fu_shen") or {}

    dims: List[Dict[str, str]] = []
    score = 0.0
    present = bool(yr.get("present"))

    # 用神六亲（现则取 roles，伏则取 fu_shen）
    if present:
        yong_lq = yr.get("liu_qin", "")
        yong_branch = yr.get("branch", "")
        yong_pos = yr.get("position", 0)
    elif fu.get("fu_liuqin"):
        yong_lq = fu.get("fu_liuqin", "")
        yong_branch = fu.get("fu_branch", "")
        yong_pos = fu.get("position", 0)
    else:
        return {"available": False}

    # ① 现伏
    if present:
        is_world = any(y.get("is_world") and y.get("position") == yong_pos for y in yaos)
        is_app = any(y.get("is_application") and y.get("position") == yong_pos for y in yaos)
        wa = "，临世爻（己身得之、事在掌握）" if is_world else (
             "，临应爻（在彼方、须察对方意向）" if is_app else "")
        dims.append({"dim": "用神现伏",
                     "text": f"用神{yong_lq}（{yong_branch}）现于第{yong_pos}爻{wa}，用神现卦、其事有象可凭。",
                     "polarity": "利"})
        score += 0.5
    else:
        et = fu.get("emerge_type", "")
        good = fu.get("emerge_severity") == "auspicious"
        dims.append({"dim": "用神现伏",
                     "text": f"用神{yong_lq}（{yong_branch}）伏于第{yong_pos}爻飞神"
                             f"（{fu.get('fei_liuqin','')}{fu.get('fei_branch','')}）之下，{et}。"
                             f"伏神须待出伏（冲飞、值日、生扶）方能应事。",
                     "polarity": "利" if good else "害"})
        score += 0.3 if good else -0.8

    # ② 旺衰得令
    force = yr.get("force", 0) if present else 0
    wsn = yr.get("ws_notes", []) if present else []
    if present:
        good_ws = [n for n in wsn if any(k in n for k in ("临", "生"))]
        bad_ws = [n for n in wsn if any(k in n for k in ("克", "泄", "耗", "破"))]
        txt = f"用神{_force_label(force)}（{('、'.join(wsn)) if wsn else '月日无生克'}）。"
        dims.append({"dim": "旺衰得令", "text": txt,
                     "polarity": "利" if force > 0 else ("害" if force < 0 else "中")})
        score += force
    else:
        dims.append({"dim": "旺衰得令", "text": "用神伏藏，旺衰以伏神论，须俟出伏之时再较月日生克。", "polarity": "中"})

    # ③ 动静化象
    if present:
        hua = yr.get("hua", "")
        if yr.get("is_dong"):
            if "回头生" in hua:
                dims.append({"dim": "动静化象", "text": "用神发动化回头生——动而得化神生扶，其势愈增、事易成。", "polarity": "利"})
                score += 2
            elif "回头克" in hua:
                dims.append({"dim": "动静化象", "text": "用神发动化回头克——动而受化神回克，先动后伤、先成后败，慎之。", "polarity": "害"})
                score -= 2
            elif "进神" in hua:
                dims.append({"dim": "动静化象", "text": "用神化进神——气势递进、其事渐成，应在进神值日。", "polarity": "利"})
                score += 1
            elif "退神" in hua:
                dims.append({"dim": "动静化象", "text": "用神化退神——气势渐退、其事渐消，须另得生扶方挽。", "polarity": "害"})
                score -= 1
            elif "反吟" in hua:
                dims.append({"dim": "动静化象", "text": "用神化反吟——反复不定、事多变更，难以一举而成。", "polarity": "害"})
                score -= 1
            elif "伏吟" in hua:
                dims.append({"dim": "动静化象", "text": "用神化伏吟——呻吟难安、迟滞忧疑，宜静待。", "polarity": "害"})
                score -= 1
            else:
                dims.append({"dim": "动静化象", "text": "用神发动——主事有变动、不主守常。", "polarity": "中"})
        else:
            dims.append({"dim": "动静化象", "text": "用神安静——主事守常、无大变动，吉凶以旺衰生克断。", "polarity": "中"})

    # ④ 空破墓绝
    if present:
        flaws = []
        if yr.get("is_kong"):
            flaws.append("旬空（气虚待填实出旬）")
        if yr.get("yuepo"):
            flaws.append("月破（力损待出月或逢合）")
        if yr.get("entombed"):
            flaws.append("入墓（气闭待冲墓开库）")
        if flaws:
            dims.append({"dim": "空破墓绝", "text": "用神逢" + "、".join(flaws) + "——病也，须待解病之期方验。", "polarity": "害"})
            score -= len(flaws)
        else:
            dims.append({"dim": "空破墓绝", "text": "用神不犯空破墓——无此障，气脉通畅。", "polarity": "利"})
            score += 0.5

    # ⑤ 元神（原神）—— roles 未填（用神伏）时从 yaos 自定位
    exp_yuan = expected_yuanshen(yong_lq)
    if not yuan.get("present"):
        yuan = _locate_role_from_yaos(yaos, exp_yuan)
    yuan_lq = yuan.get("liu_qin", "") or exp_yuan
    if yuan.get("present"):
        yforce = yuan.get("force", 0)
        ydong = yuan.get("is_dong")
        yflaw = yuan.get("is_kong") or yuan.get("yuepo") or yuan.get("entombed")
        if yforce > 0 and ydong and not yflaw:
            t = f"原神（{yuan_lq}{yuan.get('branch','')}）旺而发动、生用有力——源头活水，用神得继、其事有根。"
            pol = "利"; score += 1.5
        elif yflaw or yforce < 0:
            t = f"原神（{yuan_lq}{yuan.get('branch','')}）休囚或自陷空破——源头无力，纵生用神亦杯水车薪。"
            pol = "害"; score -= 1
        else:
            t = f"原神（{yuan_lq}{yuan.get('branch','')}）安静中平——生用之力平平，不增不减。"
            pol = "中"
        dims.append({"dim": "元神生扶", "text": t, "polarity": pol})
    else:
        dims.append({"dim": "元神生扶",
                     "text": f"原神（{exp_yuan}）不上卦——用神无源头生扶，纵旺难以为继，宜得日月或动爻补生。",
                     "polarity": "害"})
        score -= 0.5

    # ⑥ 忌神 —— roles 未填（用神伏）时从 yaos 自定位
    exp_ji = expected_jishen(yong_lq)
    if not ji.get("present"):
        ji = _locate_role_from_yaos(yaos, exp_ji)
    ji_lq = ji.get("liu_qin", "") or exp_ji
    if ji.get("present"):
        jforce = ji.get("force", 0)
        jdong = ji.get("is_dong")
        jflaw = ji.get("is_kong") or ji.get("yuepo") or ji.get("entombed")
        if jforce > 0 and jdong and not jflaw:
            t = f"忌神（{ji_lq}{ji.get('branch','')}）旺而发动、克用有力——大忌！阻力当头，用神受戕、事多败。"
            pol = "害"; score -= 2
        elif jflaw or jforce < -1:
            t = f"忌神（{ji_lq}{ji.get('branch','')}）休囚空破、自顾不暇——克用无力，阻力可解。"
            pol = "利"; score += 1
        elif jdong:
            t = f"忌神（{ji_lq}{ji.get('branch','')}）虽动而不旺——克用有限，须防其得令之时。"
            pol = "中"
        else:
            t = f"忌神（{ji_lq}{ji.get('branch','')}）安静——暂不为害，忌其逢值逢冲而发。"
            pol = "中"
        dims.append({"dim": "忌神克制", "text": t, "polarity": pol})
    else:
        dims.append({"dim": "忌神克制",
                     "text": f"忌神（{exp_ji}）不上卦——无克用之神，用神少一重阻力，吉。",
                     "polarity": "利"})
        score += 0.5

    # ⑦ 世应（求测人 vs 对方/事体）
    wp = next((y for y in yaos if y.get("is_world")), None)
    if wp and present:
        same = wp.get("position") == yong_pos
        if same:
            dims.append({"dim": "世应关系", "text": "用神即临世——所求即己、最为亲切，吉凶系于用神一身。", "polarity": "利"})
        else:
            # 世与用神生克（粗判）
            dims.append({"dim": "世应关系",
                         "text": f"世居第{wp.get('position')}爻（{wp.get('liu_qin','')}{wp.get('branch','')}），"
                                 f"用神在第{yong_pos}爻——须察世用生克：世生用、用生世或世用比和则亲，世克用则求之费力。",
                         "polarity": "中"})

    # ⑧ 综合成败
    if score >= 2.5:
        verdict, level = "用神得力、生扶有源、忌神无力——其事可成，宜进取，应在用神值日或填实出空之期。", "auspicious"
    elif score <= -2.0:
        verdict, level = "用神失地、或伏或破、忌神当道——其事多舛，宜守、宜待时，强求徒劳。", "inauspicious"
    else:
        verdict, level = "用神吉凶相参、成败在乎人事——宜谋定后动，待用神得令、忌神受制之期再图。", "neutral"

    paragraph = "综断：" + verdict + "　" + "；".join(d["text"].rstrip("。") for d in dims) + "。"

    # 角色校验（独立核对 roles 之原神忌神方向是否合古法）
    role_check = {
        "yuanshen_ok": (not yuan.get("present")) or yuan_lq == exp_yuan,
        "jishen_ok": (not ji.get("present")) or ji_lq == exp_ji,
        "expected_yuanshen": exp_yuan, "expected_jishen": exp_ji,
    }

    return {
        "available": True,
        "yong_shen_name": yong_lq,
        "present_state": "现" if present else "伏",
        "dimensions": dims,
        "verdict": verdict,
        "verdict_level": level,
        "net_score": round(score, 1),
        "paragraph": paragraph,
        "role_check": role_check,
    }
