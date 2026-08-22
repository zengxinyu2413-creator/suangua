"""
core/liuyao/full_reading.py
===========================
六爻·完整断卦合成器 —— 把「所问之事」与卦中一切信号织成一篇答案。

六爻之占，全为答一问而设。然各信号（用神四位、持世临应、旺衰空破墓、动爻
化变、三合三会、六神、伏神、应期）多各列一面板，未并入对所问之事的回答。
本合成器以「所问」为纲，依次纳入：

  ① 所问与用神 —— 何事、取何六亲为用、缘由。
  ② 用神态势 —— 旺衰、空破墓、持世/临应、所临六神。
  ③ 卦中动象 —— 用神动则化进退/回头生克；他爻发动之生克用神（原神助、
     忌神阻、子孙损官之类），逐一收束其对所问之影响。
  ④ 合局之势 —— 三合三会是否合起用神或助忌。
  ⑤ 四位生克 —— 原神/忌神/仇神之力（承综合断）。
  ⑥ 世应之机 —— 求测人与事的态势。
  ⑦ 应期 —— 何时见验。
  ⑧ 结论 —— 成败吉凶，扣题而断、附行止之宜。

只编织既有结构化结果，不引入新算法，与排盘同源。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

# 六神临用神之象
_LIU_SHEN = {
    "青龙": "临青龙——主喜庆、正派、酒色，吉神临之事添祥瑞",
    "朱雀": "临朱雀——主文书、口舌、信息，利文书消息，亦防口角是非",
    "勾陈": "临勾陈——主田土、迟滞、牵缠，事多拖延、缓而难急",
    "螣蛇": "临螣蛇——主虚惊、缠绕、怪异，心绪不宁、事有反复牵连",
    "白虎": "临白虎——主刚猛、凶丧、疾病伤灾，吉则武威、凶则血光",
    "玄武": "临玄武——主暗昧、私情、盗失、阴私，事多暗中进行或防小人暗算",
}

_TOPIC_YONG_NOTE = {
    "求官仕途": "官鬼为用（官职功名），父母为原神（文书印绶），子孙为忌（伤官损官）",
    "求财": "妻财为用（财物利益），子孙为原神（生财之源），兄弟为忌（劫财夺利）",
    "婚姻感情": "男以妻财、女以官鬼为用，父母为媒证、子孙伤官星",
    "疾病健康": "以官鬼为病、子孙为医药为用，忌官鬼旺动",
    "求职工作": "官鬼为用（职位），父母为原神（聘书契约），子孙为忌",
    "找人行人": "应爻或所代之六亲为用，看其动静生克",
}

# 地支六冲 / 六合（用于判本卦卦体之合冲）
_CHONG = {frozenset(p) for p in
          [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]}
_HE = {frozenset(p) for p in
       [("子","丑"),("寅","亥"),("卯","戌"),("辰","酉"),("巳","申"),("午","未")]}

# 卦体合冲对所问之事的吉凶取向（成事类 vs 散脱类）
_HE_CHONG_TOPIC = {
    "六合": {
        "成": "六合之卦，诸事聚合、谋望可就，于所问大为有利，惟合处逢冲之日方应",
        "散": "六合之卦主聚合纠缠，若所求在脱身解困，则合反成羁绊、难以遽解",
    },
    "六冲": {
        "成": "六冲之卦，诸事散乱、离多聚少，谋事反复难成，纵成亦不长久，应期虽速宜防虚发",
        "散": "六冲之卦主冲散，若所求在脱身、避祸、分离，则冲散正合其宜、反为吉象",
    },
}
_SAN_TOPICS = {"疾病健康", "官司诉讼", "find人行人"}  # 以散脱为吉之类


def _gua_he_chong(branches: List[str]) -> str:
    """据六爻纳甲地支判本卦六冲/六合卦。"""
    if len(branches) < 6 or not all(branches):
        return ""
    pairs = [frozenset((branches[0], branches[3])),
             frozenset((branches[1], branches[4])),
             frozenset((branches[2], branches[5]))]
    if all(p in _CHONG for p in pairs):
        return "六冲"
    if all(p in _HE for p in pairs):
        return "六合"
    return ""


def _yao_tag(y: Dict[str, Any]) -> str:
    t = []
    if y.get("is_world"):
        t.append("持世")
    if y.get("is_application"):
        t.append("临应")
    return "、".join(t)


def _find_yong_yaos(yaos: List[Dict], yong_lq: str) -> List[Dict]:
    return [y for y in yaos if y.get("liu_qin") == yong_lq]


def build_full_reading(result: Dict[str, Any]) -> Dict[str, Any]:
    """以所问为纲，织全卦信号成篇。"""
    yaos = result.get("yaos", [])
    if not yaos:
        return {"available": False}

    do = result.get("duan_overview", {}) or {}
    zd = result.get("zonghe_duan", {}) or {}
    ta = result.get("topic_analysis", {}) or {}
    topic = result.get("topic", "") or "综合"
    question = result.get("question", "")
    yong_lq = do.get("yong_liuqin") or (zd.get("roles", {}).get("用神", {}) or {}).get("liu_qin", "")
    # 用神判定以 topic_analysis.timing 为准（与 yingqi 同源，正确处理「自占以世为用」），
    # 退而用顶层 yong_shen_name，杜绝 full_reading 另取类神致不一致。
    yong_position = ""        # 世爻/应爻（若用神为爻位）
    ta_yong = (ta.get("timing", {}) or {}).get("yong_shen_name", "") or ta.get("yong_shen_name", "")
    if ta_yong:
        if ta_yong in ("世爻", "应爻"):
            yong_position = ta_yong
            _wa = "is_world" if ta_yong == "世爻" else "is_application"
            _yao = next((y for y in yaos if y.get(_wa)), None)
            if _yao and _yao.get("liu_qin"):
                yong_lq = _yao["liu_qin"]   # 世/应爻所临六亲
        else:
            yong_lq = ta_yong
    polarity = do.get("polarity") or zd.get("conclusion", "")
    roles = zd.get("roles", {}) or {}

    paras: List[Dict[str, str]] = []

    # ① 所问与用神
    if yong_position:
        yong_note = f"自占以{yong_position}为用神（{yong_position}临{yong_lq}）"
    else:
        yong_note = _TOPIC_YONG_NOTE.get(topic, f"以{yong_lq}为用神")
    p1 = (f"所问「{question or topic}」，归为「{topic}」一类，{yong_note}。"
          if yong_lq else f"所问「{question or topic}」。")
    paras.append({"title": "所问与用神", "text": p1})

    # ② 用神态势（旺衰 + 空破墓 + 持世临应 + 六神）
    yong_yaos = _find_yong_yaos(yaos, yong_lq)
    yr = roles.get("用神", {}) or {}
    if yong_yaos or yr:
        bits = []
        ws = yr.get("wangshuai", "")
        if ws:
            note = "、".join(yr.get("ws_notes", []) or [])
            bits.append(f"用神{yong_lq}{yr.get('branch','')}{ws}" + (f"（{note}）" if note else ""))
        # 空破墓
        flaws = []
        if yr.get("is_kong"):
            flaws.append("旬空")
        if yr.get("yuepo"):
            flaws.append("月破")
        if yr.get("ripo"):
            flaws.append("日破")
        if yr.get("entombed"):
            flaws.append("入墓")
        if flaws:
            bits.append("然用神" + "、".join(flaws) + "，气受其制，须待冲填解之")
        # 持世/临应 + 六神（取主用神爻）
        main = next((y for y in yong_yaos if y.get("is_world")), None) \
            or next((y for y in yong_yaos if y.get("is_application")), None) \
            or (yong_yaos[0] if yong_yaos else None)
        if main:
            tag = _yao_tag(main)
            if "持世" in tag:
                bits.append("用神持世——所问之事系于己身，求测人即主事之人，用神有力则事在掌握、易成")
            elif "临应" in tag:
                bits.append("用神临应——事机在对方或身外，成败多由他人、外缘而定")
            ls = main.get("liu_shen", "")
            if ls in _LIU_SHEN:
                bits.append(_LIU_SHEN[ls])
        if bits:
            paras.append({"title": "用神态势", "text": "。".join(bits) + "。"})
    # 用神不上卦：伏神
    if not yong_yaos:
        fu = result.get("fu_shen")
        if fu and (isinstance(fu, dict)):
            fu_lq = fu.get("fu_liuqin", "")
            if fu_lq == yong_lq or not yong_lq:
                emerge = fu.get("emerge_type", "")
                sev = fu.get("emerge_severity", "")
                txt = (f"用神{yong_lq}不上卦，伏于{fu.get('fei_liuqin','')}{fu.get('fei_branch','')}之下"
                       f"（伏神{fu.get('fu_branch','')}）。伏而有用，须待其出伏方应"
                       + (f"——{emerge}" if emerge else "")
                       + ("，伏神得出、所问可期" if sev == "auspicious"
                          else "，出伏不利、须防其变" if sev == "inauspicious" else "。"))
                paras.append({"title": "用神伏藏", "text": txt})
        else:
            paras.append({"title": "用神伏藏",
                          "text": f"用神{yong_lq}不上卦，又无伏神可寻，所问之事无根，难以成就，须待用神临值之月日另图。"})

    # ③ 卦中动象（用神动 + 他爻发动对用神之生克）
    moving = [y for y in yaos if y.get("is_changing")]
    hb = result.get("hua_bian", {}) or {}
    hb_lines = {m.get("position"): m for m in (hb.get("moving_lines", []) or [])}
    if moving:
        dyn_bits = []
        for y in moving:
            pos = y.get("position")
            lq = y.get("liu_qin", "")
            chg_lq = y.get("changed_liu_qin", "")
            facet = hb_lines.get(pos, {})
            ft = facet.get("tendency", "")
            role = "用神" if lq == yong_lq else (
                "原神" if lq == (roles.get("原神", {}) or {}).get("liu_qin") else (
                "忌神" if lq == (roles.get("忌神", {}) or {}).get("liu_qin") else lq))
            seg = f"{role}（{lq}{y.get('branch','')}）发动化{chg_lq}{y.get('changed_branch','')}"
            # 化象提要
            facets = facet.get("facets", []) or []
            key_facet = next((f for f in facets if any(k in f.get("type","") for k in ("回头","进神","退神","化墓","化绝","化空"))), None)
            if key_facet:
                seg += "，" + key_facet.get("type", "")
            if ft:
                seg += f"（{ft}）"
            # topic 关键：求官见子孙动
            if role == "忌神" and topic in ("求官仕途", "求职工作") and lq == "子孙":
                seg += "——子孙动则伤官损功名，于求官不利，所幸"
                seg += ("化忌出而力减" if chg_lq != "子孙" else "其势仍在，须防")
            dyn_bits.append(seg)
        paras.append({"title": "卦中动象",
                      "text": "卦中" + f"{len(moving)}爻发动：" + "；".join(dyn_bits) + "。动则有变，所问之事非静局可定，吉凶随动象转移。"})
    else:
        paras.append({"title": "卦中动象",
                      "text": "卦逢尽静，六爻安然无动——近期无大变，所问之事当以用神旺衰、日月生克、世应向背定其吉凶，待冲值之日方有动机。"})

    # ④' 卦体合冲（六冲/六合卦）—— 对成败之高层取向
    branches = [y.get("branch", "") for y in yaos]
    hc = _gua_he_chong(branches)
    if hc:
        kind = "散" if topic in _SAN_TOPICS else "成"
        note = _HE_CHONG_TOPIC.get(hc, {}).get(kind, "")
        if note:
            paras.append({"title": "卦体合冲", "text": f"本卦为{hc}卦——{note}。"})

    # ④ 合局
    ss = result.get("sanhe_sanhui", {}) or {}
    locals_ = (ss.get("sanhe", []) or []) + (ss.get("sanhui", []) or [])
    if locals_:
        loc = locals_[0]
        nm = loc.get("name", "")
        wx = ""
        # 局之五行是否生克用神
        p4 = f"卦成「{nm}」之局，气聚一方，力量倍增"
        yr_wx = yr.get("wuxing", "")
        # 简断：局含用神爻位则合起用神
        yong_positions = {y.get("position") for y in yong_yaos}
        if set(loc.get("positions", [])) & yong_positions:
            p4 += "，且用神入局——合起用神、其力大增，于所问大为有助"
        else:
            p4 += "，须辨其五行是生用神抑或助忌神，再定吉凶"
        paras.append({"title": "合局之势", "text": p4 + "。"})

    # ⑤ 四位生克（承综合断 reasoning，去重用神已述）
    reasons = [r for r in (zd.get("reasoning", []) or []) if "用神" not in r[:3]]
    if reasons:
        paras.append({"title": "四位生克", "text": "　".join(reasons)})

    # ⑥ 世应
    if zd.get("verdict"):
        v = zd["verdict"]
        # 取世应那一句
        shi_ying = next((s for s in v.split("　") if "世" in s or "应" in s), "")
        if shi_ying:
            paras.append({"title": "世应之机", "text": shi_ying.strip("。") + "。"})

    # ⑦ 应期
    yq_text = do.get("yingqi_text", "")
    if yq_text:
        paras.append({"title": "应期", "text": yq_text})

    # ⑧ 结论（扣题）
    concl = polarity or "吉凶参半"
    advice_map = {
        "吉": f"综观全卦，所问「{question or topic}」其象为吉——用神得地、生扶有情，事可望成，宜把握应期、顺势进取。",
        "凶": f"综观全卦，所问「{question or topic}」其象偏凶——用神受制、阻力当前，事多蹉跎，宜守不宜进、待时而动、预为之备。",
    }
    p8 = advice_map.get(concl,
                        f"综观全卦，所问「{question or topic}」吉凶参半——成败系于用神能否乘应期得力，宜审时度势、量力而行。")
    paras.append({"title": "结论", "text": p8})

    # 摘要：用神为世/应爻时明示「用世爻（临X）」，避免误读临神为用神（如求医"用官鬼"易误为病象作用神）
    if yong_position:
        yong_disp = f"{yong_position}" + (f"（临{yong_lq}）" if yong_lq else "")
    else:
        yong_disp = yong_lq
    summary = f"{topic}·用{yong_disp}·{concl}" + (f"·应{do.get('primary_ganzhi','')}" if do.get("primary_ganzhi") else "")

    return {
        "available": True,
        "question": question,
        "topic": topic,
        "yong_liuqin": yong_lq,
        "yong_position": yong_position,                       # 世爻/应爻（用神为爻位时）
        "yong_shen_name": yong_position or yong_lq,            # 权威用神名（与 topic_analysis 一致）
        "polarity": concl,
        "headline": summary,
        "paragraphs": paras,
    }
