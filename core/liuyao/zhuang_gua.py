"""
core/liuyao/zhuang_gua.py
=========================
六爻·静态断语库三件套（不依赖摇卦日辰，纯由卦象定式生成）：

  一、64 卦装卦定式 —— 每卦六爻之纳甲地支、五行、六亲、世应间，
      复用 najia.py 的纳甲/八宫/世应引擎，与动态排盘完全同源。

  二、64 卦世爻六亲持世断 —— 由各卦世位之六亲，取《卜筮正宗》《黄金策》
      持世口诀（载于 knowledge.liuyao_classical），再叠世位（八纯/游魂/归魂）
      与卦型（六冲/六合）之纤旨。

  三、384 爻六亲分类应事断 —— 64×6 爻，按"用神—元神—忌神—仇神—制忌"
      五神体系（六亲生克之五连环）逐爻定位，对求财/婚姻/求官/考试/求子/
      失物等"单一用神"之事直接定吉凶；对占病/占讼则用"世应·官鬼·子孙"
      专框。再叠爻位高下（初为始足、五为君路、上为终极）之义。

      —— 此乃火珠林纳甲法之正脉：六爻应事不主周易爻辞，而主纳甲六亲之
         生克持值；故本库以六亲定式立断，方合六爻实占。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.liuyao.hexagram_data import HEXAGRAM_DATA, HEXAGRAM_TRIGRAM_MAPPING
from core.liuyao.najia import (
    NAJIA_BRANCHES, HEXAGRAM_PALACE, PALACE_ELEMENT,
    PALACE_POS_TO_WORLD, _get_world_line, get_liu_qin,
    LIU_QIN_MEANINGS,
)
from core.constants import DIZHI_WUXING

# ─────────────────────────────────────────────────────────────
# 0. 常量
# ─────────────────────────────────────────────────────────────
POS_NAMES = ["初", "二", "三", "四", "五", "上"]

# 八宫卦位 → 卦型名
PALACE_POS_TYPE: Dict[int, str] = {
    1: "八纯卦", 2: "一世卦", 3: "二世卦", 4: "三世卦",
    5: "四世卦", 6: "五世卦", 7: "游魂卦", 8: "归魂卦",
}

# 爻位高下之义（六爻位序）
POS_MEANING: Dict[int, str] = {
    1: "初爻为事之始、为足、为基、为远、为下属邻里",
    2: "二爻为宅、为内、为妻位、为乡里中馈",
    3: "三爻为门户、内外之交、为手足近身",
    4: "四爻为外户、为大门、为人事心腹",
    5: "五爻为君位、为尊、为主事、为道路官长",
    6: "上爻为事之终、为极、为宗庙、为头、为墙尽远方",
}

# 六亲生克五连环（与五行同构，独立于宫）
#   生：父母→兄弟→子孙→妻财→官鬼→父母
#   克：父母→子孙→官鬼→兄弟→妻财→父母
LIU_QIN_SHENG: Dict[str, str] = {
    "父母": "兄弟", "兄弟": "子孙", "子孙": "妻财", "妻财": "官鬼", "官鬼": "父母",
}
LIU_QIN_KE: Dict[str, str] = {
    "父母": "子孙", "子孙": "官鬼", "官鬼": "兄弟", "兄弟": "妻财", "妻财": "父母",
}
_SHENG_BY = {v: k for k, v in LIU_QIN_SHENG.items()}   # 生我者
_KE_BY = {v: k for k, v in LIU_QIN_KE.items()}         # 克我者


def _five_roles(yong: str) -> Dict[str, str]:
    """给定用神六亲，返回五神 → 六亲名 的映射。"""
    ji = _KE_BY[yong]        # 克用者 = 忌神
    yuan = _SHENG_BY[yong]   # 生用者 = 元神
    chou = _SHENG_BY[ji]     # 生忌者 = 仇神
    zhi = _KE_BY[ji]         # 克忌者 = 制忌(护用)之神
    return {yong: "用神", yuan: "元神", ji: "忌神", chou: "仇神", zhi: "制忌"}


_ROLE_VERDICT: Dict[str, Dict[str, str]] = {
    "用神": {"q": "★用神",
            "d": "为所占之主象，事之成败全系此爻——旺相生扶则成，休囚空破则败。"},
    "元神": {"q": "○吉助",
            "d": "为元神，生扶用神。此爻旺动则用神得力、事更有把握。"},
    "制忌": {"q": "○吉护",
            "d": "能克制忌神、护卫用神。此爻旺动则忌神受制，反成助力。"},
    "忌神": {"q": "✕忌动",
            "d": "为忌神，克伤用神。此爻旺动则用神受克、事多阻坏，最忌发动。"},
    "仇神": {"q": "△慎",
            "d": "为仇神，生扶忌神（帮凶）。此爻动则忌神得力、伤用加倍，宜静。"},
}

# 单一用神之事（含性别分支）
#   value: 用神六亲，或 ("male": 六亲, "female": 六亲)
SINGLE_YONG_TOPICS: Dict[str, Any] = {
    "求财": "妻财",
    "婚姻": {"male": "妻财", "female": "官鬼"},
    "求官": "官鬼",
    "考试": "父母",
    "求子": "子孙",
    "失物": "妻财",
    "家宅": "父母",      # 以父母为宅舍栋宇之主
    "行人": "妻财",      # 常以财为行人音信（亦视所占之人，从简取财）
}

TOPIC_LABEL: Dict[str, str] = {
    "求财": "求财经商", "婚姻": "婚姻嫁娶", "求官": "求官仕途",
    "考试": "考试功名", "求子": "求子嗣", "失物": "失物寻贼",
    "家宅": "家宅居止", "行人": "行人音信",
    "疾病": "疾病占身", "官讼": "官非词讼",
}


def _yong_for(topic: str, gender: str) -> Optional[str]:
    v = SINGLE_YONG_TOPICS.get(topic)
    if v is None:
        return None
    if isinstance(v, dict):
        return v["female" if gender in ("female", "女") else "male"]
    return v


# ─────────────────────────────────────────────────────────────
# 1. 装卦定式
# ─────────────────────────────────────────────────────────────

def build_zhuang_gua(num: int) -> Dict[str, Any]:
    """返回某卦（京房卦序 1-64）的完整装卦定式。"""
    if num not in HEXAGRAM_TRIGRAM_MAPPING:
        return {"success": False, "error": f"卦序无效：{num}"}
    lower_n, upper_n = HEXAGRAM_TRIGRAM_MAPPING[num]
    palace, pos = HEXAGRAM_PALACE[num]
    world, app = _get_world_line(num)
    palace_wx = PALACE_ELEMENT.get(palace, "")
    zhi6 = NAJIA_BRANCHES[lower_n]["inner"] + NAJIA_BRANCHES[upper_n]["outer"]

    rows: List[Dict[str, Any]] = []
    for i, zhi in enumerate(zhi6):
        p = i + 1
        wx = DIZHI_WUXING.get(zhi, "")
        qin = get_liu_qin(palace, zhi)
        role = "世" if p == world else ("应" if p == app else "")
        rows.append({
            "position": p,
            "name": f"{POS_NAMES[i]}爻",
            "zhi": zhi,
            "wuxing": wx,
            "liu_qin": qin,
            "shi_ying": role,
        })
    return {
        "success": True,
        "number": num,
        "gua_name": HEXAGRAM_DATA[num]["name"],
        "palace": palace,
        "palace_wuxing": palace_wx,
        "palace_position": pos,
        "gua_type": PALACE_POS_TYPE.get(pos, ""),
        "world_line": world,
        "application_line": app,
        "rows": rows,
    }


# ─────────────────────────────────────────────────────────────
# 2. 世爻六亲持世断
# ─────────────────────────────────────────────────────────────

def chi_shi_judgment(num: int) -> Dict[str, Any]:
    """某卦之世爻六亲持世断（口诀 + 解析 + 世位卦型纤旨）。"""
    zg = build_zhuang_gua(num)
    if not zg.get("success"):
        return zg
    world = zg["world_line"]
    shi_row = next(r for r in zg["rows"] if r["position"] == world)
    qin = shi_row["liu_qin"]

    from knowledge.liuyao_classical import LIUYAO_WORLD_APP
    base = LIUYAO_WORLD_APP["世爻持世断法"].get(f"{qin}持世", {})

    # 世位 / 卦型 纤旨
    gua_type = zg["gua_type"]
    pos_note = {
        "八纯卦": "世居上爻、本宫纯卦，气势纯一，所主之事根深而显，吉凶皆重。",
        "游魂卦": "世居四爻、游魂主出，心神不定、事多游移走作、在外不在内。",
        "归魂卦": "世居三爻、归魂主返，事终归本、人心思安守旧、宜静不宜动。",
    }.get(gua_type, f"世居{POS_NAMES[world-1]}爻（{gua_type}），所主在{POS_MEANING[world].split('为',1)[-1]}。")

    return {
        "success": True,
        "number": num,
        "gua_name": zg["gua_name"],
        "world_line": world,
        "world_liu_qin": qin,
        "world_zhi": shi_row["zhi"],
        "world_wuxing": shi_row["wuxing"],
        "kou_jue": base.get("口诀", ""),
        "jie_xi": base.get("解析", ""),
        "pos_note": pos_note,
        "summary": (
            f"{zg['gua_name']}卦世在{POS_NAMES[world-1]}爻，{qin}持世（{shi_row['zhi']}{shi_row['wuxing']}）。"
            f"{base.get('解析', '')}　{pos_note}"
        ),
    }


# ─────────────────────────────────────────────────────────────
# 3. 384 爻六亲分类应事断
# ─────────────────────────────────────────────────────────────

def _yingshi_single(qin: str, topic: str, gender: str) -> Optional[Dict[str, str]]:
    """单一用神之事：返回该六亲在此事中的五神角色断。"""
    yong = _yong_for(topic, gender)
    if not yong:
        return None
    roles = _five_roles(yong)
    role = roles[qin]
    rv = _ROLE_VERDICT[role]
    return {"topic": topic, "label": TOPIC_LABEL[topic],
            "role": role, "quality": rv["q"], "desc": rv["d"], "yong": yong}


# 占病专框：六亲在占病（自占）中的定位
_DISEASE_ROLE: Dict[str, Dict[str, str]] = {
    "官鬼": {"q": "✕病符", "d": "官鬼为病、为鬼祟。临爻动则病势加、病因显，最忌持世临身。"},
    "子孙": {"q": "★医药", "d": "子孙为医药、为解神。旺动克官鬼，则药到病除、凶可化吉。"},
    "妻财": {"q": "△忌动", "d": "妻财生官鬼（病），又克父母（医书药材）。财动则助病、伤药，占病所忌。"},
    "父母": {"q": "○药材", "d": "父母为医书药石、为调护。得力则医护有方；衰则医药难继。"},
    "兄弟": {"q": "△阻", "d": "兄弟主阻隔、克财耗气。临之主饮食不进、克财耗损、病中破费。"},
}

# 占讼专框：六亲在占讼（自占）中的定位
_LAWSUIT_ROLE: Dict[str, Dict[str, str]] = {
    "官鬼": {"q": "✕官法", "d": "官鬼为官府、为法、为对方之势。旺克世则我屈，宜求子孙制之。"},
    "子孙": {"q": "★解神", "d": "子孙为和解、为解神、能克官鬼。旺动则讼可平、刑可解、逢凶化吉。"},
    "父母": {"q": "○状词", "d": "父母为状词文书、为案卷。旺则文书有力；动则文书纷起、讼牵连。"},
    "妻财": {"q": "△贿用", "d": "妻财为使费贿赂、为财物之争。财动生官鬼，反助官府之势。"},
    "兄弟": {"q": "△助讼", "d": "兄弟为同党、为口舌是非、为破耗。临之主多口舌、破财、有人助讼。"},
}


def yao_yingshi(num: int, gender: str = "male") -> Dict[str, Any]:
    """某卦六爻之分类应事断（每爻按其六亲对各事定位）。"""
    zg = build_zhuang_gua(num)
    if not zg.get("success"):
        return zg

    lines: List[Dict[str, Any]] = []
    for r in zg["rows"]:
        p = r["position"]
        qin = r["liu_qin"]
        topics: List[Dict[str, str]] = []
        # 单一用神之事
        for t in ("求财", "婚姻", "求官", "考试", "求子", "失物", "家宅", "行人"):
            j = _yingshi_single(qin, t, gender)
            if j:
                topics.append(j)
        # 占病
        dz = _DISEASE_ROLE.get(qin)
        if dz:
            topics.append({"topic": "疾病", "label": TOPIC_LABEL["疾病"],
                           "role": "病框", "quality": dz["q"], "desc": dz["d"]})
        # 占讼
        lz = _LAWSUIT_ROLE.get(qin)
        if lz:
            topics.append({"topic": "官讼", "label": TOPIC_LABEL["官讼"],
                           "role": "讼框", "quality": lz["q"], "desc": lz["d"]})

        qin_m = LIU_QIN_MEANINGS.get(qin, {})
        lines.append({
            "position": p,
            "name": r["name"],
            "zhi": r["zhi"],
            "wuxing": r["wuxing"],
            "liu_qin": qin,
            "shi_ying": r["shi_ying"],
            "liu_qin_meaning": qin_m.get("meaning", ""),
            "pos_meaning": POS_MEANING[p],
            "topics": topics,
            "summary": (
                f"{r['name']}{qin}{r['zhi']}{r['wuxing']}"
                f"{('·'+r['shi_ying']) if r['shi_ying'] else ''}："
                f"{qin_m.get('meaning','')}。{POS_MEANING[p]}。"
            ),
        })
    return {
        "success": True,
        "number": num,
        "gua_name": zg["gua_name"],
        "gender": "female" if gender in ("female", "女") else "male",
        "lines": lines,
    }


# ─────────────────────────────────────────────────────────────
# 4. 单卦综合（装卦 + 持世 + 应事）
# ─────────────────────────────────────────────────────────────

def analyze_gua_static(num: int, gender: str = "male") -> Dict[str, Any]:
    zg = build_zhuang_gua(num)
    if not zg.get("success"):
        return zg
    return {
        "success": True,
        "zhuang_gua": zg,
        "chi_shi": chi_shi_judgment(num),
        "yao_yingshi": yao_yingshi(num, gender=gender),
    }


def all_64_table(gender: str = "male") -> Dict[int, Dict[str, Any]]:
    """预生成全 64 卦静态断（供前端目录 / 测试覆盖）。"""
    return {n: analyze_gua_static(n, gender=gender) for n in range(1, 65)}
