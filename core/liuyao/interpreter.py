"""
core/liuyao/interpreter.py
==========================
Applies classical LiuYao rules from the knowledge library to enriched
yao data and produces structured professional analysis.

Sources applied:
  《增删卜易》《卜筮正宗》《易隐》《火珠林》《黄金策》
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.liuyao.hexagram_data import HEXAGRAM_DATA
from core.constants import TRIGRAMS, DIZHI_INDEX, DIZHI_WUXING, WUXING_KE, WUXING_SHENG
from core.log import log_failure


# ─────────────────────────────────────────────────────────────
# 1. Topic matching — map question keywords → liuyao topic rules
# ─────────────────────────────────────────────────────────────

_TOPIC_MAP: Dict[str, str] = {
    "官司诉讼": ["官司","诉讼","打官司","法院","起诉","律师","纠纷","判决","赔偿","仲裁","胜诉","败诉"],
    "求医疾病": ["病","医","健康","手术","治疗","痊愈","身体","检查","诊断","康复","药","住院"],
    "考试功名": ["考试","功名","学历","文凭","录取","入学","高考","考研","成绩","分数","金榜"],
    "婚姻感情": ["婚","恋","感情","对象","结婚","爱","姻缘","追","分手","离婚","桃花","缘分","伴侣"],
    "求官仕途": ["升职","升迁","晋升","职位","公务","录用","考核","考编","考公","职场","仕途","官职","升官","求职","工作","找工作","面试","入职","就业","上班","谋职","offer","录取通知","当官","谋官"],
    "求子嗣":  ["孩子","生育","怀孕","子嗣","要孩子","生孩子","备孕","求子"],
    "找人行人": ["找人","行人","失踪","下落","联系","寻找","归来","消息","人回","何时归","回来","会不会回","回不回","走失","离家","出走"],
    "失物寻物": ["失物","丢失","找东西","寻物","遗失","丢了","寻回","失窃"],
    "家宅风水": ["家宅","住宅","搬家","装修","风水","家庭","房子","居家","买房"],
    "出行远行": ["出行","旅行","出差","远行","旅游","出门","路途","行程","航班","能否成行"],
    "求财":    ["财","钱","生意","投资","收入","赚","金融","股","贷款","利润","薪","借","求财","财运"],
    "天气占候": ["天气","下雨","晴天","气候","风","雨","明天","后天"],
}

def _match_topic(question: str) -> str:
    for topic, keywords in _TOPIC_MAP.items():
        if any(k in question for k in keywords):
            return topic
    return "综合"


def _get_topic_rules(topic: str) -> Optional[Dict]:
    try:
        from knowledge.liuyao_classical import LIUYAO_TOPIC_RULES
        return LIUYAO_TOPIC_RULES.get(topic)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# 2. Core yong-shen determination
# ─────────────────────────────────────────────────────────────

# Static yong-shen table (gender-neutral topics)
_TOPIC_YONG_SHEN: Dict[str, List[str]] = {
    # 古书《增删卜易》《卜筮正宗》标准
    "求财":    ["妻财", "子孙"],   # 妻财为用，子孙为原神（生财之源）
    "求官仕途": ["官鬼", "父母"],   # 官鬼为用，父母为原神（印星生官）
    "考试功名": ["父母", "官鬼"],   # 父母为用神（文书印星），官鬼为原神
    "婚姻感情": ["妻财", "官鬼"],   # 按性别分（见 _TOPIC_YONG_SHEN_GENDER）
    "求医疾病": ["世爻", "子孙"],   # 世为本人，子孙为药、为医
    "出行远行": ["世爻", "父母"],   # 世为本人，父母为车船舟舆
    "官司诉讼": ["世爻", "应爻"],   # 世应相争
    "求子嗣":  ["子孙"],            # 子孙为子女
    "找人行人": ["应爻"],            # 应爻代表远方之人（注：寻找具体身份的人需用对应六亲）
    "失物寻物": ["妻财"],            # 妻财为财物（注：失物类型不同用神也不同）
    "家宅风水": ["父母", "世爻"],   # 父母为家宅，世为本人
    "综合":    ["世爻"],
}

# Gender-specific overrides (topic → {male: [...], female: [...]})
_TOPIC_YONG_SHEN_GENDER: Dict[str, Dict[str, List[str]]] = {
    # 婚姻感情: 男占以妻财为用神, 女占以官鬼为用神
    "婚姻感情": {
        "male":   ["妻财"],
        "female": ["官鬼"],
    },
    # 求子嗣: 女占加官鬼(夫星)辅助判断
    "求子嗣": {
        "male":   ["子孙"],
        "female": ["子孙", "官鬼"],
    },
    # 官司诉讼: 自占vs代占不同用神
    "官司诉讼": {
        "male":   ["世爻", "应爻"],
        "female": ["世爻", "应爻"],
    },
}

# 代占(proxy divination) 用神: 占者世爻代表问卦人，应爻代表被问者
_TOPIC_YONG_SHEN_PROXY: Dict[str, List[str]] = {
    "求财":    ["应爻", "妻财"],   # 代他人求财，应爻为当事人
    "婚姻感情":["应爻", "官鬼"],
    "求医疾病":["应爻", "子孙"],   # 被代占者(应爻)的健康
    "官司诉讼":["应爻", "世爻"],
}


def get_yong_shen(topic: str, gender: str = "male",
                  is_proxy: bool = False) -> List[str]:
    """
    Return the yong-shen (用神) list for a given topic, gender, and proxy flag.
    
    Classical rules:
    - 婚姻感情: 男占妻财为用神, 女占官鬼为用神 (《增删卜易》)
    - 代占: 用神取应爻所代表的六亲 (《卜筮正宗》)
    - 其他: 以静态表为准
    """
    if is_proxy and topic in _TOPIC_YONG_SHEN_PROXY:
        return _TOPIC_YONG_SHEN_PROXY[topic]

    gender_key = "female" if gender in ("female", "女") else "male"
    if topic in _TOPIC_YONG_SHEN_GENDER:
        return _TOPIC_YONG_SHEN_GENDER[topic].get(gender_key,
               _TOPIC_YONG_SHEN.get(topic, ["世爻"]))

    return _TOPIC_YONG_SHEN.get(topic, ["世爻"])



# ─────────────────────────────────────────────────────────────
# 伏神 / 飞神 Analysis
# ─────────────────────────────────────────────────────────────

def _find_fu_shen(
    yaos: List[Dict],
    palace_trigram: str,
    yong_shen_liuqin: str,
) -> Optional[Dict[str, Any]]:
    """
    Find the 伏神 (hidden god) for a given 六亲 type.

    In professional liuyao, if the 用神 (useful god) is absent from
    the hexagram's visible lines, it may be hidden (伏) under one of
    the six lines as a 伏神. The 伏神 can still participate if
    the 飞神 (the visible line that covers it) allows it to emerge.

    Returns dict with 伏神 info or None if 用神 is already visible.
    """
    from core.liuyao.najia import NAJIA_BRANCHES, PALACE_ELEMENT, get_liu_qin

    # Check if yong_shen is already visible in the hexagram
    visible_liuqin = {y.get("liu_qin") for y in yaos}
    if yong_shen_liuqin in visible_liuqin:
        return None   # 用神出现在卦中，无需找伏神

    # 伏神: the 宫卦 (original trigram's 6 branches) provides the hidden positions
    # Each position has a default branch from the palace's internal/external lines
    palace_branches_inner = NAJIA_BRANCHES.get(palace_trigram, {}).get("inner", [])
    palace_branches_outer = NAJIA_BRANCHES.get(palace_trigram, {}).get("outer", [])
    palace_all = palace_branches_inner + palace_branches_outer  # pos 1→6

    fu_candidates = []
    for i, pal_branch in enumerate(palace_all):
        pal_wx = _get_wuxing_from_branch(pal_branch)
        pal_liuqin = get_liu_qin(palace_trigram, pal_branch)
        if pal_liuqin == yong_shen_liuqin:
            # Found 伏神 position
            pos       = i + 1
            fei_yao   = yaos[i] if i < len(yaos) else {}
            fei_zhi   = fei_yao.get("branch", "")
            fei_wx    = _get_wuxing_from_branch(fei_zhi)
            fei_liuqin= fei_yao.get("liu_qin", "")

            # 飞伏关系判定（古书：《增删卜易·飞伏吉凶论》）
            # 1) 飞生伏 → 伏得长生，最吉，伏神有力（"长生扶起"）
            # 2) 伏生飞 → 伏神泄气，凶（"泄气难出"）
            # 3) 飞克伏 → 飞神压制伏神，凶（"飞来克伏，事不成"，俗称"出暴"是误解）
            # 4) 伏克飞 → 伏神反克飞神，可出，吉（"克出"）
            # 5) 比和 → 伏神有同类相助，待时可出
            from core.constants import WUXING_KE, WUXING_SHENG
            if WUXING_SHENG.get(fei_wx, "") == pal_wx:
                emerge = "飞生伏 — 长生扶起，伏神得力，最吉"
                emerge_severity = "auspicious"
            elif WUXING_SHENG.get(pal_wx, "") == fei_wx:
                emerge = "伏生飞 — 伏神泄气难出，凶"
                emerge_severity = "warning"
            elif WUXING_KE.get(fei_wx, "") == pal_wx:
                emerge = "飞克伏 — 飞神克制伏神，事难成，凶"
                emerge_severity = "warning"
            elif WUXING_KE.get(pal_wx, "") == fei_wx:
                emerge = "伏克飞 — 伏神反克飞出，可期，吉"
                emerge_severity = "auspicious"
            elif fei_wx == pal_wx:
                emerge = "飞伏比和 — 同类相助，待冲飞日出伏"
                emerge_severity = "neutral"
            else:
                emerge = "正伏 — 关系一般，须冲飞神出伏"
                emerge_severity = "neutral"

            fu_candidates.append({
                "position":        pos,
                "fu_branch":       pal_branch,
                "fu_liuqin":       pal_liuqin,
                "fu_wx":           pal_wx,
                "fei_branch":      fei_zhi,
                "fei_liuqin":      fei_liuqin,
                "emerge_type":     emerge,
                "emerge_severity": emerge_severity,
                "desc": (
                    f"用神{yong_shen_liuqin}伏于第{pos}爻之下（{pal_branch}），"
                    f"飞神为{fei_liuqin}（{fei_zhi}），{emerge}。"
                    f"须待{fei_zhi}冲动之日，伏神方能出现应事。"
                ),
            })

    return fu_candidates[0] if fu_candidates else None


def _get_wuxing_from_branch(branch: str) -> str:
    """Get wuxing element from a DiZhi branch."""
    ZHI_WX = {
        "子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
        "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水",
    }
    return ZHI_WX.get(branch, "")


def _find_yao_by_liuqin(yaos: List[Dict], liuqin: str) -> Optional[Dict]:
    return next((y for y in yaos if y.get("liu_qin") == liuqin), None)


# ─────────────────────────────────────────────────────────────
# 3. Classical rule application
# ─────────────────────────────────────────────────────────────

def _get_six_combine_class(hex_type: str) -> str:
    if hex_type == "六合":
        return "六合卦：诸事聚合，婚姻易成，谋事可就，感情融洽"
    if hex_type == "六冲":
        return "六冲卦：诸事散乱，出行不宜，感情有分，事情反复"
    return ""


def _apply_classical_rules(yaos: List[Dict], world_yao: Optional[Dict],
                            app_yao: Optional[Dict], kong_wang: List[str],
                            changing: List[Dict], topic: str) -> List[str]:
    """
    Apply classical rules to produce analysis points.
    Returns list of analysis strings.
    """
    points = []

    # ── 世爻分析 ──
    if world_yao:
        wq = world_yao.get("liu_qin", "")
        ws = world_yao.get("strength", {}).get("label", "")
        wb = world_yao.get("branch", "")
        wk = world_yao.get("kong_wang", False)
        wg = world_yao.get("liu_shen", "")
        is_changing_world = world_yao.get("is_changing", False)

        # 世爻旺衰
        if ws in ("旺", "相"):
            points.append(f"世爻{wq}爻（{wb}）{ws}，身强有力，"
                          f"《卜筮正宗》云：世爻旺相最为强，作事亨通大吉昌")
        elif ws in ("休", "囚", "死"):
            points.append(f"世爻{wq}爻（{wb}）{ws}，身弱力衰，"
                          f"谋事宜守不宜攻，须得生扶方可奋进")

        # 世爻空亡
        if wk:
            points.append(f"世爻（{wb}）落旬空，《黄金策》云：心退悔兮世空，"
                          f"问卦者心意不定、做事乏力，须待出空后再图")

        # 世爻动
        if is_changing_world:
            points.append(f"世爻发动，《增删卜易》云：世应不宜动，"
                          f"世爻动主本人三心二意、左顾右盼，事情反复")

        # 六神临世
        if wg == "白虎":
            points.append(f"白虎临世爻，主凶险血光，诸事宜防意外")
        elif wg == "玄武":
            points.append(f"玄武临世爻，主有暗谋、心思不正，防欺骗")
        elif wg == "青龙":
            points.append(f"青龙临世爻，贵人扶助，诸事顺遂")
        elif wg == "腾蛇":
            points.append(f"腾蛇临世爻，主虚惊烦恼，事多反复")

    # ── 应爻分析 ──
    if app_yao:
        aq = app_yao.get("liu_qin", "")
        ab = app_yao.get("branch", "")
        ak = app_yao.get("kong_wang", False)
        if ak:
            points.append(f"应爻（{ab}）空亡，对方无诚意或有障碍，"
                          f"所求之人或事暂时无法落实")

        # 世应生克关系
        if world_yao and app_yao:
            w_wx = DIZHI_WUXING.get(world_yao.get("branch", ""), "")
            a_wx = DIZHI_WUXING.get(app_yao.get("branch", ""), "")
            if w_wx and a_wx:
                if WUXING_KE.get(w_wx) == a_wx:
                    points.append(f"世克应：己方强势主动，对方处于被动，"
                                  f"《卜筮正宗》云：世旺克应，我胜")
                elif WUXING_KE.get(a_wx) == w_wx:
                    points.append(f"应克世：对方强势，己方处于被动，"
                                  f"《卜筮正宗》云：应旺克世，彼胜")
                elif WUXING_SHENG.get(a_wx) == w_wx:
                    points.append(f"应生世：对方助力，双方有情，事情可就")
                elif WUXING_SHENG.get(w_wx) == a_wx:
                    points.append(f"世生应：己方资助对方，损己利人，"
                                  f"《卜筮正宗》谓之反德扶人，所求不易")

    # ── 动爻分析 ──
    if len(changing) == 1:
        y = changing[0]
        yq = y.get("liu_qin", "")
        yb = y.get("branch", "")
        yg = y.get("liu_shen", "")
        points.append(f"独发一爻（第{y.get('line','')}爻 {yq}爻 {yb}）动，"
                      f"《增删卜易》云：独发易取——此爻为本卦断事之关键，"
                      f"《火珠林》云：动爻急如火")
        if yg == "白虎":
            points.append(f"独发爻逢白虎，主凶险速发，尤防血光意外")
        elif yg == "青龙":
            points.append(f"独发爻逢青龙，贵人主动相助，事情可期")

    elif len(changing) == 0:
        points.append("六爻皆静，《增删卜易》云：六爻安静，以本卦卦辞论断，"
                      "事情稳定少变，以世爻所在六亲论吉凶")
    elif len(changing) >= 5:
        points.append("爻动过多（五、六爻皆动），《增删卜易》云：乱动难寻，"
                      "吉凶交错，须以之卦为准，重新论断")

    # ── 用神空亡检查 ──
    yong_shen_names = _TOPIC_YONG_SHEN.get(topic, ["世爻"])
    for ys_name in yong_shen_names:
        if ys_name == "世爻":
            continue
        ys_yao = _find_yao_by_liuqin(yaos, ys_name)
        if ys_yao:
            if ys_yao.get("kong_wang"):
                points.append(f"用神{ys_name}爻（{ys_yao.get('branch','')}）旬空，"
                               f"《黄金策》云：伏神空亡，凡事不利，"
                               f"须待出空之期，方有希望")
            ys_s = ys_yao.get("strength", {}).get("label", "")
            if ys_s in ("旺", "相"):
                points.append(f"用神{ys_name}爻旺相有力，所问之事有望成就")
            elif ys_s in ("死",):
                points.append(f"用神{ys_name}爻死绝无气，所问之事难以成就，"
                               f"须待其旺相之月日再图")

    # ── 兄弟动（克财）——特别警示 ──
    if topic == "求财":
        for y in changing:
            if y.get("liu_qin") == "兄弟":
                points.append(f"兄弟爻（{y.get('branch','')}）发动，"
                               f"《火珠林》云：兄动，事不实，难成，且财被克截，"
                               f"防他人争财或合伙破散")

    # ── 子孙动（化官）——求官警示 ──
    if topic in ("求官仕途", "考试功名"):
        for y in changing:
            if y.get("liu_qin") == "子孙":
                points.append(f"子孙爻（{y.get('branch','')}）发动克官鬼，"
                               f"《火珠林》云：忌子孙持世，不中，"
                               f"官职功名受阻，需化解")

    return points


# ─────────────────────────────────────────────────────────────
# 4. Timing analysis (应期推算) using classical rules
# ─────────────────────────────────────────────────────────────

def _calc_timing(yaos: List[Dict], topic: str, changing: List[Dict],
                 kong_wang: List[str],
                 gender: str = "male",
                 is_proxy: bool = False) -> Dict[str, Any]:
    """
    Generate timing guidance using classical liuyao rules.
    
    完整应期推算（《增删卜易·应期门》《卜筮正宗·应期总论》）：
    
      ★ 用神为本：以用神所在爻的状态决定应期类型
      
      用神动：
        · 旺动：应日时
        · 衰动：应月或得生扶之日
        · 化进神：应于进神所化之地支日
        · 化退神：应于退神之地支日（事必反复）
        · 化回头生：应于化神冲之日（事必成）
        · 化回头克：应于化神冲之日（事必败）
      
      用神静（不动但旺）：
        · 静而旺：逢冲之日应（"动以冲应"）
        · 静而衰：逢冲之日不能动，应等生扶之日
        · 暗动：逢日辰冲而起，逢合实之日应
      
      用神空：
        · 旺空：出旬之日填实而应
        · 衰空：永空（不能应）
        · 冲空：被日冲之爻填实而应
      
      用神月破：
        · 出月之后填实方应
        · 大事不应（月破不堪用）
      
      用神墓库：
        · 入墓：逢冲墓之日开墓而出
        · 化墓：化神为墓，须冲墓日方应
      
      用神伏藏：
        · 飞克伏：永不出（事不成）
        · 飞生伏：长生之日出
        · 冲飞之日：伏神出现
    """
    timing: Dict[str, Any] = {}

    ys_names = get_yong_shen(topic, gender, is_proxy)
    ys_name  = ys_names[0] if ys_names else "世爻"
    timing["yong_shen_name"] = ys_name

    rules: List[str] = []

    # ── 1. 动爻进退神 + 化回头生克 ────────────────────────────────
    for y in changing:
        yb  = y.get("branch", "")
        yq  = y.get("liu_qin", "")
        yst = y.get("strength", {})
        strength_label = yst.get("label", "") if isinstance(yst, dict) else str(yst)
        changed_b = y.get("changed_branch", "")
        is_yong = (yq == ys_name)
        
        # 进退神
        jin = _check_jin_tui_shen(yb, changed_b)
        if jin == "进":
            rules.append(
                f"【进神】{yq}爻（{yb}）化进神→{changed_b}，动而益壮，"
                f"应期在{changed_b}日或{changed_b}月"
            )
        elif jin == "退":
            rules.append(
                f"【退神】{yq}爻（{yb}）化退神→{changed_b}，气势渐衰，"
                f"应期须等用神另得生扶之日"
            )
        
        # 化回头生/克（仅在动爻和化爻都有时检查）
        if yb and changed_b and yb != changed_b:
            yb_wx = _get_wuxing_from_branch(yb)
            cb_wx = _get_wuxing_from_branch(changed_b)
            if yb_wx and cb_wx:
                # 化神生本爻：化回头生（吉）
                if WUXING_SHENG.get(cb_wx) == yb_wx:
                    chong_cb = _get_chong(changed_b)
                    rules.append(
                        f"【化回头生】{yq}爻（{yb}）动化{changed_b}，化神反生本爻，"
                        f"事必成；应期在{chong_cb}日冲化神或{changed_b}日"
                    )
                # 化神克本爻：化回头克（凶）
                elif WUXING_KE.get(cb_wx) == yb_wx:
                    chong_cb = _get_chong(changed_b)
                    rules.append(
                        f"【化回头克】{yq}爻（{yb}）动化{changed_b}，化神反克本爻，"
                        f"事必败；应期在{chong_cb}日冲化神或{changed_b}日见凶"
                    )
                # 化神墓库本爻（化入墓）
                if _is_mu_ku(yb_wx, changed_b):
                    chong_cb = _get_chong(changed_b)
                    rules.append(
                        f"【化入墓】{yq}爻（{yb}）动化入{changed_b}墓，"
                        f"事被埋藏；须{chong_cb}日冲开墓库方应"
                    )

    # ── 2. 用神空亡应期（分旺空/衰空）──────────────────────────────
    if kong_wang:
        # 检查用神是否落空
        ys_yao_now = None
        for y in yaos:
            if y.get("liu_qin") == ys_name:
                ys_yao_now = y
                break
        if ys_yao_now and ys_yao_now.get("kong_wang"):
            yb = ys_yao_now.get("branch", "")
            chong_yb = _get_chong(yb)
            lbl = ys_yao_now.get("strength", {}).get("label", "")
            if lbl in ("旺", "相"):
                rules.append(
                    f"【旺空可填实】用神{ys_name}（{yb}）{lbl}落空，"
                    f"《卜筮正宗》云：旺空不真空，应于出旬后或{yb}日填实"
                )
            else:
                rules.append(
                    f"【衰空难应】用神{ys_name}（{yb}）{lbl}落空，"
                    f"《卜筮正宗》云：衰空真空，事难应；唯逢{chong_yb}日冲空起爻或出旬可看"
                )
        else:
            zhi0 = kong_wang[0]
            chong0 = _get_chong(zhi0)
            rules.append(
                f"【卦中旬空】卦中有旬空（{'/'.join(kong_wang)}），"
                f"事在出旬后方验；或{chong0}日冲实{zhi0}空，亦可应期"
            )

    # ── 3. 用神静爻逢冲（含暗动判定）────────────────────────────────
    ys_yao = None
    for y in yaos:
        if y.get("liu_qin") == ys_name and not y.get("is_changing"):
            ys_yao = y
            break
    if ys_yao:
        yb    = ys_yao.get("branch", "")
        chong = _get_chong(yb)
        yst   = ys_yao.get("strength", {})
        lbl   = yst.get("label", "") if isinstance(yst, dict) else str(yst)
        if chong:
            # 旺爻逢冲 = 动；衰爻逢冲 = 散
            if lbl in ("旺", "相"):
                rules.append(
                    f"【冲动应期】{ys_name}爻（{yb}，{lbl}）静而有气，"
                    f"逢{chong}日冲动即为应期（旺逢冲为暗动，必应）"
                )
            else:
                rules.append(
                    f"【冲散难应】{ys_name}爻（{yb}，{lbl}）衰而逢冲，"
                    f"《增删卜易》云：衰逢冲则散，须先得生扶之日，再冲方应"
                )
        # 应期缓急
        if lbl in ("旺", "相"):
            rules.append(f"【速应】{ys_name}爻旺相，所问之事可在旬日内应验")
        elif lbl in ("休", "囚", "死"):
            shengfu_zhi = _get_sheng_from(yb)
            rules.append(
                f"【迟应】{ys_name}爻{lbl}，事迟，"
                f"须待{shengfu_zhi}日（生扶用神）方应"
            )

    # ── 4. 六合/六冲卦型 ──────────────────────────────────────────────
    hex_type = ""   # populated by annotate_with_najia if available
    if hex_type == "六合":
        rules.append("【六合卦】六合之卦诸事顺遂，惟合处逢冲方应，以冲动之日为期")
    elif hex_type == "六冲":
        rules.append("【六冲卦】六冲之卦事多散漫，离多聚少，应期较快但难持久")

    # ── 5. 病药通则 ──────────────────────────────────────────────────
    rules.append(
        "【病药通则】空破墓合为病（阻碍），出空填实冲墓为药（解除）；"
        "急事应日时，寻常事应月，大事应年"
    )

    timing["rules_applied"] = rules
    timing["summary"] = (
        f"用神{ys_name}爻" +
        (f"（{ys_yao['branch']}）" if ys_yao else "") +
        "；" +
        (f"空亡出旬后应验" if kong_wang else "无旬空") +
        "；详见各条规则"
    )
    return timing


# 地支墓库（古书：木墓未、火墓戌、金墓丑、水墓辰、土墓辰戌丑未）
_MU_KU = {
    "木": "未", "火": "戌", "金": "丑", "水": "辰",
}

def _is_mu_ku(yong_wx: str, target_branch: str) -> bool:
    """判定 target_branch 是否为 yong_wx 的墓库"""
    return _MU_KU.get(yong_wx) == target_branch


def _get_sheng_from(branch: str) -> str:
    """返回生此 branch 的地支（用神衰时，生扶之日）"""
    # 五行生我：水生木、木生火、火生土、土生金、金生水
    SHENG_FROM = {
        "木": "水", "火": "木", "土": "火", "金": "土", "水": "金",
    }
    wx = _get_wuxing_from_branch(branch)
    sheng_wx = SHENG_FROM.get(wx, "")
    # 该五行的代表地支（用旺位）
    WX_TO_WANG_ZHI = {
        "木": "卯", "火": "午", "土": "未", "金": "酉", "水": "子",
    }
    return WX_TO_WANG_ZHI.get(sheng_wx, "")


# 进退神表 — 经典四进神（《增删卜易》《卜筮正宗》）
#
# 严格四正进神（古书通用）：
#   进神: 同五行地支向前进一位 (寅→卯木, 巳→午火, 申→酉金, 亥→子水)
#   退神: 同五行地支向后退一位 (卯→寅木, 午→巳火, 酉→申金, 子→亥水)
#
# 四库土进退（部分流派）：辰→丑, 丑→戌, 戌→未, 未→辰
#   注：《卜筮正宗》主"土无进退"，故此项归为扩展（默认不启用）；
#       《增删卜易》偶有用，需根据具体卦师传承决定。
#       此处保留以便扩展，但 _check_jin_tui_shen 默认仅用四正。
_JIN_SHEN_ZHENGZONG = {
    "寅": "卯", "巳": "午", "申": "酉", "亥": "子",   # 四正进神（古书通用）
}
_TUI_SHEN_ZHENGZONG = {v: k for k, v in _JIN_SHEN_ZHENGZONG.items()}

# 四库土进退（扩展，部分流派支持）
_JIN_SHEN_TUKU = {
    "辰": "丑", "丑": "戌", "戌": "未", "未": "辰",
}
_TUI_SHEN_TUKU = {v: k for k, v in _JIN_SHEN_TUKU.items()}

# 合并版（兼容旧测试）
_JIN_SHEN = {**_JIN_SHEN_ZHENGZONG, **_JIN_SHEN_TUKU}
_TUI_SHEN = {v: k for k, v in _JIN_SHEN.items()}


def _check_jin_tui_shen(orig_zhi: str, changed_zhi: str, strict: bool = False) -> str:
    """
    判断动爻化出是否构成进神或退神。
    
    Args:
        orig_zhi:    原爻地支
        changed_zhi: 化出地支
        strict:      True=只用四正（古书《卜筮正宗》通用），
                     False=含四库土进退（部分流派支持，更宽松）
    
    返回 "进" / "退" / ""
    """
    jin_table = _JIN_SHEN_ZHENGZONG if strict else _JIN_SHEN
    tui_table = _TUI_SHEN_ZHENGZONG if strict else _TUI_SHEN
    if jin_table.get(orig_zhi) == changed_zhi:
        return "进"
    if tui_table.get(orig_zhi) == changed_zhi:
        return "退"
    return ""

# 六冲表
_CHONG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
          "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}

def _get_chong(zhi: str) -> str:
    return _CHONG.get(zhi, "")


# ─────────────────────────────────────────────────────────────
# 5. Build topic-specific analysis using classical rules
# ─────────────────────────────────────────────────────────────

def _build_topic_analysis(yaos: List[Dict], topic: str,
                          changing: List[Dict], kong_wang: List[str],
                          hex_type: str,
                          gender: str = "male",
                          is_proxy: bool = False) -> Dict[str, Any]:
    """
    Apply topic-specific classical rules and return structured analysis.
    """
    # Resolve 用神名 first — needed for both early-return and normal path
    gender_key = "female" if gender in ("female","女") else "male"
    if topic in _TOPIC_YONG_SHEN_GENDER:
        ys_names_raw = _TOPIC_YONG_SHEN_GENDER[topic][gender_key]
    elif is_proxy and topic in ("求医疾病",):
        ys_names_raw = ["应爻"]
    else:
        ys_names_raw = _TOPIC_YONG_SHEN.get(topic, ["世爻"])

    # Primary 用神 name —— 与 _calc_timing / yingqi 同源（get_yong_shen[0]），
    # 杜绝顶层取「首个非世应类神」致与 timing 不一致（如求医自占：用世爻，非子孙）。
    _ys_primary_list = get_yong_shen(topic, gender, is_proxy)
    _primary_ys_name = _ys_primary_list[0] if _ys_primary_list else (
        next((n for n in ys_names_raw if n not in ("世爻", "应爻")),
             ys_names_raw[0] if ys_names_raw else "世爻")
    )

    analysis = {
        "topic":           topic,
        "verdict":         "",
        "key_points":      [],
        "timing":          {},
        "classical_ref":   "",
        "yong_shen_name":  _primary_ys_name,   # always set at top level
    }

    topic_rules = _get_topic_rules(topic)
    if not topic_rules:
        return analysis

    # (Gender/proxy already resolved above)

    key_points = []

    # Get primary yong shen yao (visible in hex)
    primary_ys = None
    primary_ys_name = ""
    for ys_name in ys_names_raw:
        if ys_name in ("世爻", "应爻"):
            continue
        y = _find_yao_by_liuqin(yaos, ys_name)
        if y:
            primary_ys = y
            primary_ys_name = ys_name
            break

    # 伏神 check: if 用神 not visible, look for it hidden under palace lines
    fu_shen_info = None
    palace_trig  = ""  # will be provided by caller context
    if primary_ys is None and primary_ys_name == "" and ys_names_raw:
        main_ys_name = next((n for n in ys_names_raw if n not in ("世爻","应爻")), "")
        if main_ys_name:
            # Try to find 伏神 using all parameters passed in
            pass  # 伏神 resolved via analysis["fu_shen"] set below

    # Apply the first 4 topic rules
    rules = topic_rules.get("规则") or topic_rules.get("rules", [])
    for r in rules[:4]:
        key_points.append(r)

    # Verdict based on primary yong shen
    if primary_ys:
        ys_strength = primary_ys.get("strength", {}).get("label", "")
        ys_kong = primary_ys.get("kong_wang", False)
        ys_q = primary_ys.get("liu_qin", "")
        ys_b = primary_ys.get("branch", "")

        if ys_kong:
            analysis["verdict"] = f"用神{ys_q}爻旬空，所谋之事落空或难以实现，待出空后再图"
        elif ys_strength in ("旺", "相"):
            analysis["verdict"] = f"用神{ys_q}爻（{ys_b}）旺相有力，{topic_rules.get('summary','所谋可成')}"
        elif ys_strength in ("死",):
            analysis["verdict"] = f"用神{ys_q}爻（{ys_b}）死绝，{topic}之谋难以成就，须待旺相之时"
        else:
            analysis["verdict"] = topic_rules.get("summary", "需结合全卦参断")
    else:
        analysis["verdict"] = topic_rules.get("summary", "")

    # 六合/六冲 overlay
    combine_note = _get_six_combine_class(hex_type)
    if combine_note:
        key_points.insert(0, combine_note)

    analysis["key_points"] = key_points
    analysis["timing"] = _calc_timing(yaos, topic, changing, kong_wang, gender=gender, is_proxy=is_proxy)
    analysis["classical_ref"] = (
        topic_rules.get("卜筮正宗") or
        topic_rules.get("增删卜易") or
        topic_rules.get("火珠林") or
        topic_rules.get("黄金策") or ""
    )

    return analysis


# ─────────────────────────────────────────────────────────────
# 6. Main interpret function
# ─────────────────────────────────────────────────────────────


def interpret(result: Dict[str, Any], question: str = "", gender: str = "male", is_proxy: bool = False,
              explicit_topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Enrich a divination result with professional classical analysis.
    Uses the najia-annotated yao data + liuyao_classical knowledge library.
    
    Args:
        result:         divination result
        question:       user's question text (used for topic auto-detection)
        gender:         "male" / "female"
        is_proxy:       是否代占
        explicit_topic: 显式指定的主题（优先于 question 推断）
    """
    orig    = result["original"]
    changed = result.get("changed")
    yaos    = result.get("yaos", [])
    kong    = result.get("kong_wang_branches", [])
    hex_type = result.get("hex_type", "")   # 六合/六冲 etc.

    orig_num  = orig["number"]
    orig_data = HEXAGRAM_DATA.get(orig_num, {})

    # ── Basic hexagram info ──
    upper_nature = TRIGRAMS.get(orig["upper"]["name"], {}).get("nature", "")
    lower_nature = TRIGRAMS.get(orig["lower"]["name"], {}).get("nature", "")

    # ── Find world / application yaos ──
    world_pos = result.get("world_line", 0)
    app_pos   = result.get("application_line", 0)
    world_yao = next((y for y in yaos if y.get("is_world")),    None)
    app_yao   = next((y for y in yaos if y.get("is_application")), None)
    changing  = [y for y in yaos if y.get("is_changing")]

    # ── Topic matching ──
    # 显式 topic 优先；非规范键则按关键词归一化（婚姻→婚姻感情、财运→求财…），
    # 仍匹配不到才从 question 推断。修复：简写/别名 topic 曾落默认世爻、绕过性别专用神。
    if explicit_topic and explicit_topic in _TOPIC_YONG_SHEN:
        topic = explicit_topic
    elif explicit_topic and _match_topic(explicit_topic) != "综合":
        topic = _match_topic(explicit_topic)
    else:
        topic = _match_topic(question)

    # ── Classical rule analysis ──
    classical_points = _apply_classical_rules(
        yaos, world_yao, app_yao, kong, changing, topic
    )

    # ── Topic-specific analysis ──
    topic_analysis = _build_topic_analysis(
        yaos, topic, changing, kong, hex_type,
        gender=gender, is_proxy=is_proxy
    )

    # ── 伏神分析 (hidden god) ──────────────────────────────────────────────────
    palace_trig = result.get("palace_trigram", "")
    fu_shen_result = None
    if palace_trig and topic and topic != "综合":
        # Resolve gender-aware yong shen name for 伏神 lookup
        gender_key = "female" if gender in ("female","女") else "male"
        if topic in _TOPIC_YONG_SHEN_GENDER:
            ys_for_fu = _TOPIC_YONG_SHEN_GENDER[topic][gender_key][0]
        else:
            ys_names = _TOPIC_YONG_SHEN.get(topic, ["世爻"])
            ys_for_fu = next((n for n in ys_names if n not in ("世爻","应爻")), "")

        if ys_for_fu:
            fu_shen_result = _find_fu_shen(yaos, palace_trig, ys_for_fu)

    # ── Hexagram introduction ──
    intro = (
        f"本卦第{orig_num}卦【{orig_data.get('name','')}卦】，"
        f"上{orig['upper']['name']}（{upper_nature}）下{orig['lower']['name']}（{lower_nature}）。"
    )
    body  = orig_data.get("interpretation", orig_data.get("judgment", ""))

    # ── Changing lines + 化气 analysis ──
    # 伏吟/反吟（爻级·自化）由 core.liuyao.hua_bian 检测并入卦（动化同支为伏吟、动化六冲为反吟）；
    # 旧 _detect_fuyin_fanyin 以「全静」误判伏吟、读不存在的 yaos_raw、结果亦弃用，已移除。

    if changing:
        line_texts = []
        for y in changing:
            pos  = y.get("line", "")
            text = orig_data.get("lines", {}).get(pos, "")
            qin  = y.get("liu_qin", "")
            shen = y.get("liu_shen", "")
            # Apply flying/hidden god rule
            jin = _check_jin_tui_shen(y.get("branch", ""), y.get("changed_branch", ""))
            jin_note = f"，化{'进' if jin=='进' else '退'}神" if jin else ""
            line_texts.append(f"第{pos}爻{qin}爻（{shen}）动{jin_note}：{text}")
        change_section = "【动爻详析】" + "；".join(line_texts)

        if changed:
            ch_data = HEXAGRAM_DATA.get(changed["number"], {})
            change_section += (
                f"\n【变卦】第{changed['number']}卦【{ch_data.get('name','')}卦】，"
                f"{ch_data.get('interpretation', '')[:80]}。"
            )
    else:
        change_section = "【六爻皆静】以本卦卦辞论断，事情平稳少变。"

    # ── World / Application summary ──
    world_summary = ""
    if world_yao:
        wq = world_yao.get("liu_qin", "")
        wb = world_yao.get("branch", "")
        ws = world_yao.get("strength", {}).get("label", "")
        wg = world_yao.get("liu_shen", "")
        wk = "（旬空！）" if world_yao.get("kong_wang") else ""
        world_summary = f"世爻：{wq}爻 {wb} {ws}{wk}，{wg}临爻"
    if app_yao:
        aq = app_yao.get("liu_qin", "")
        ab = app_yao.get("branch", "")
        ak = "（旬空！）" if app_yao.get("kong_wang") else ""
        world_summary += f" ‖ 应爻：{aq}爻 {ab}{ak}"

    # ── Six Gods analysis ──
    try:
        from knowledge.liuyao_classical import LIUYAO_SIX_GODS
        gods_active = []
        for y in changing:
            g = y.get("liu_shen", "")
            q = y.get("liu_qin", "")
            b = y.get("branch", "")
            if g and g in LIUYAO_SIX_GODS:
                god_info = LIUYAO_SIX_GODS[g]
                dynamic_key = f"临{q}"
                meaning = god_info.get(dynamic_key, god_info.get("口诀", ""))
                gods_active.append(f"{g}临{q}爻（{b}）动：{meaning}")
        gods_section = "【六神动爻】" + "；".join(gods_active) if gods_active else ""
    except Exception:
        gods_section = ""

    # ── 伏神 section ─────────────────────────────────────────────────────────
    fu_shen_section = ""
    if fu_shen_result:
        fu_shen_section = f"【伏神】{fu_shen_result['desc']}"

    # ── Build full interpretation ──
    parts = [intro, body, change_section]
    if world_summary:
        parts.append(f"【世应】{world_summary}")
    if gods_section:
        parts.append(gods_section)
    if fu_shen_section:
        parts.append(fu_shen_section)
    if classical_points:
        parts.append("【经典断法】" + "。".join(classical_points[:5]))
    interpretation = "\n\n".join(p for p in parts if p)

    # ── Advice ──
    advice_lines = []
    if topic_analysis.get("verdict"):
        advice_lines.append(topic_analysis["verdict"])
    if topic_analysis.get("timing", {}).get("general"):
        advice_lines.append(topic_analysis["timing"]["general"])
    if topic_analysis.get("timing", {}).get("kong_wang_timing"):
        advice_lines.append(topic_analysis["timing"]["kong_wang_timing"])
    advice = "；".join(advice_lines) or "宜审时度势，以诚信处世。"

    # ── Attach all to result ──
    result["question"]       = question
    result["topic"]          = topic
    result["interpretation"] = interpretation
    result["advice"]         = advice
    result["topic_analysis"] = topic_analysis
    result["classical_points"] = classical_points
    result["world_summary"]  = world_summary
    result["fu_shen"]         = fu_shen_result
    # ── C-1: 静态持世断（由本卦世爻六亲取持世口诀，与装卦库同源）──
    try:
        from core.liuyao.zhuang_gua import chi_shi_judgment
        result["chi_shi"] = chi_shi_judgment(orig_num)
    except Exception as _e:
        log_failure("liuyao", "持世断(chi_shi)", _e)
    # ── C-2: 动爻化变全谱（逐爻成文断）──
    try:
        from core.liuyao.hua_bian import analyze_hua_bian
        result["hua_bian"] = analyze_hua_bian(
            yaos, kong_wang=kong, topic=topic, gender=gender,
        )
    except Exception as _e:
        log_failure("liuyao", "动爻化变全谱(hua_bian)", _e)
    result["changing_analysis"] = [
        {
            "position": y.get("position", 0),
            "line":     y.get("line", ""),
            "liu_qin":  y.get("liu_qin", ""),
            "liu_shen": y.get("liu_shen", ""),
            "branch":   y.get("branch", ""),
            "changed_branch": y.get("changed_branch", ""),
            "changed_liu_qin": y.get("changed_liu_qin", ""),
            "jin_tui":  _check_jin_tui_shen(y.get("branch", ""), y.get("changed_branch", "")),
            "kong_wang": y.get("kong_wang", False),
            "strength": y.get("strength", {}).get("label", "") if isinstance(y.get("strength"), dict) else "",
        }
        for y in changing
    ]

    # ── L-1: 六爻关系深度分析（原神/忌神/仇神 + 十二长生 + 卦变细化） ──
    try:
        from core.liuyao.relations import analyze_liuyao_deep_relations
        # 用神信息
        ys_list = get_yong_shen(topic, gender, is_proxy=is_proxy) or []
        yong_shen_info = None
        if ys_list:
            yong_shen_info = {
                "liuqin": ys_list[0] if isinstance(ys_list, list) else ys_list,
            }
        # 月日地支
        month_zhi = result.get("month_zhi", "")
        day_zhi = result.get("day_zhi", "")
        # 变卦爻
        changed_yaos = None
        if result.get("changed"):
            # changed 是变卦信息，对应每爻变化后的地支已在 yao 的 changed_branch
            changed_yaos = []
            for y in yaos:
                cb = y.get("changed_branch", "")
                if cb:
                    changed_yaos.append({"branch": cb, "liu_qin": y.get("liu_qin", "")})
                else:
                    changed_yaos.append({"branch": y.get("branch", ""), "liu_qin": y.get("liu_qin", "")})

        deep_rel = analyze_liuyao_deep_relations(
            yaos, changed_yaos=changed_yaos,
            yong_shen_info=yong_shen_info,
            month_zhi=month_zhi, day_zhi=day_zhi,
        )
        result["deep_relations"] = deep_rel
    except Exception as _e:
        log_failure("liuyao", "用神/原神/忌神/仇神深度关系(deep_relations)", _e)

    # ── 综合断卦（用神—原神—忌神—仇神 四位生克总断 + 吉凶结论） ──
    try:
        from core.liuyao.zonghe_duan import analyze_zonghe_duan
        ys_spec = get_yong_shen(topic, gender, is_proxy=is_proxy) or ["世爻"]
        result["zonghe_duan"] = analyze_zonghe_duan(
            yaos, ys_spec,
            result.get("month_zhi", ""), result.get("day_zhi", ""),
            kong=result.get("kong_wang_branches", []),
            topic=topic,
        )
    except Exception as _e:
        log_failure("liuyao", "综合断卦(zonghe_duan)", _e)

    # ── 占事专用断语（14类各套专门看点） ──
    try:
        from core.liuyao.topic_templates import build_topic_verdict
        tv = build_topic_verdict(topic, result.get("zonghe_duan", {}), yaos)
        result["topic_verdict"] = tv
        # 回填 topic_analysis.verdict（原常为空）
        if tv.get("available") and tv.get("verdict"):
            if isinstance(result.get("topic_analysis"), dict) and not result["topic_analysis"].get("verdict"):
                result["topic_analysis"]["verdict"] = tv["verdict"]
    except Exception as _e:
        log_failure("liuyao", "占事专断(topic_verdict)", _e)

    # ── 高级特性集成：卦身、独发独静、化合化冲 ──
    try:
        from core.liuyao.advanced_features import (
            get_gua_shen, find_guashen_in_chart, get_shi_shen,
            analyze_dong_jing, analyze_hua_he_chong,
        )
        # 找世爻
        world_pos = next((i+1 for i, y in enumerate(yaos) if y.get("is_world")), 3)
        world_y = next((y for y in yaos if y.get("is_world")), yaos[2] if len(yaos) > 2 else {})
        # 世爻阴阳取爻性（阳爻/阴爻）——安卦身诀「阳世从子、阴世从午」之阳世/阴世即世爻为阳爻/阴爻。
        # 旧版读 type/yin_yang（爻无此键）→ world_yy 恒「阴」→ 阳世卦卦身全算错（误用从午起）。
        world_yy = "阳" if (world_y.get("line") == "阳"
                            or str(world_y.get("yao_type", "")).endswith("阳")) else "阴"
        world_zhi = world_y.get("branch", "")
        
        # 卦身
        gs = get_gua_shen(world_pos, world_yy)
        gs_in_chart = find_guashen_in_chart(
            [{"zhi": y.get("branch", "")} for y in yaos],
            gs["zhi"]
        )
        result["gua_shen"] = {**gs, "in_chart": gs_in_chart}
        
        # 世身（完整：含卦中位置 + 月令旺衰）
        month_zhi_for_shishen = result.get("month_zhi", "")
        day_zhi_for_shishen = result.get("day_zhi", "")
        result["shi_shen"] = get_shi_shen(world_pos, world_zhi,
                                            yaos=yaos,
                                            month_zhi=month_zhi_for_shishen,
                                            day_zhi=day_zhi_for_shishen)
        
        # 独发独静
        result["dong_jing_analysis"] = analyze_dong_jing([
            {"dong": bool(y.get("is_changing") or y.get("is_moving") or y.get("type") == "moving"),
             "zhi": y.get("branch", "")}
            for y in yaos
        ])
        
        # 化合化冲
        result["hua_he_chong"] = analyze_hua_he_chong([
            {"dong": bool(y.get("is_changing") or y.get("is_moving") or y.get("type") == "moving"),
             "zhi": y.get("branch", ""),
             "changed_zhi": y.get("changed_branch", "")}
            for y in yaos
        ])
    except Exception as e:
        log_failure("liuyao", "化合冲(hua_he_chong)", e)

    # ── 应期精算（古法应期门 → 具体公历日期）────────────────────────────────
    try:
        from core.liuyao.yingqi_calculator import calculate_yingqi
        from datetime import datetime as _dt
        # 解析占卦时刻
        _dd = result.get("divine_date")
        if _dd:
            try:
                divine_dt = _dt.fromisoformat(_dd)
            except Exception:
                divine_dt = _dt.now()
        else:
            divine_dt = _dt.now()
        # 用神名（topic_analysis.timing 已有，否则按 topic 取）
        ys_name = (topic_analysis.get("timing", {}) or {}).get("yong_shen_name", "")
        if not ys_name:
            _ys = get_yong_shen(topic, gender, is_proxy=is_proxy) or []
            ys_name = _ys[0] if _ys else "世爻"
        result["yingqi"] = calculate_yingqi(
            yaos=yaos,
            yong_shen_name=ys_name,
            day_zhi=result.get("day_zhi", ""),
            month_zhi=result.get("month_zhi", ""),
            kong_wang=result.get("kong_wang_branches", []),
            divine_date=divine_dt,
        )
    except Exception:
        result["yingqi"] = {"available": False, "reason": "应期推算异常"}

    # ── 断卦总览（综合断卦 × 应期联动：何事·吉凶·何时应） ──
    try:
        from core.liuyao.duan_overview import build_duan_overview
        result["duan_overview"] = build_duan_overview(
            result.get("zonghe_duan", {}), result.get("yingqi", {}),
            topic=topic, question=question,
        )
    except Exception as _e:
        log_failure("liuyao", "断卦总论(duan_overview)", _e)

    return result
