"""
core/qimen/analyzer.py
======================
奇门遁甲断事核心引擎 — 完整经典理论实现
整合四盘体系：天（九星）× 地（九宫）× 人（八门）× 神（八神）
核心断法：值符值使体系、用神取法、格局检测、应期推算
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple

from core.constants import BAMEN_AUSPICIOUS

# ─────────────────────────────────────────────────────────────
# 五行生克常量
# ─────────────────────────────────────────────────────────────
_WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

_GONG_WX = {
    "坎一宫": "水", "坤二宫": "土", "震三宫": "木", "巽四宫": "木",
    "中五宫": "土", "乾六宫": "金", "兑七宫": "金", "艮八宫": "土", "离九宫": "火",
}

_TIANGAN_WX = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

_MEN_WX = {
    "开门": "金", "惊门": "金",
    "休门": "水",
    "生门": "土", "死门": "土",
    "伤门": "木", "杜门": "木",
    "景门": "火",
}

_XING_WX = {
    "天蓬": "水", "天芮": "土", "天冲": "木", "天辅": "木", "天禽": "土",
    "天心": "金", "天柱": "金", "天任": "土", "天英": "火",
}

_SHEN_WX = {
    "值符": "土", "腾蛇": "火", "太阴": "金", "六合": "木",
    "白虎": "金", "玄武": "水", "九地": "土", "九天": "金",
}

def _wx_rel(a: str, b: str) -> str:
    """Return relationship: 生/克/同/无"""
    if not a or not b: return "无"
    if a == b: return "同"
    if _WX_SHENG.get(a) == b: return "生"
    if _WX_KE.get(a) == b: return "克"
    if _WX_SHENG.get(b) == a: return "被生"
    if _WX_KE.get(b) == a: return "被克"
    return "无"


# ─────────────────────────────────────────────────────────────
# Load classical knowledge (lazy, with fallback)
# ─────────────────────────────────────────────────────────────
def _load_classical():
    try:
        from knowledge.qimen_classical import (
            BA_MEN_DETAIL, JIU_XING_DETAIL, BA_SHEN, QIMEN_GEJV,
            SAN_QI_LIU_YI, YANBO_JIJUE, ZHIFU_ZHISHI, YONG_SHEN_QIFA,
            YINGQI_TUISUAN, JIU_GONG_DETAIL, SIBAO_XITONG,
        )
        return {
            "bamen": BA_MEN_DETAIL, "jiuxing": JIU_XING_DETAIL,
            "bashen": BA_SHEN,       "gejv": QIMEN_GEJV,
            "sanqi": SAN_QI_LIU_YI, "yanbo": YANBO_JIJUE,
            "zhifushi": ZHIFU_ZHISHI, "yongshen": YONG_SHEN_QIFA,
            "yingqi": YINGQI_TUISUAN, "jiugong": JIU_GONG_DETAIL,
            "sibao": SIBAO_XITONG,
        }, True
    except Exception:
        return {k: {} for k in ["bamen","jiuxing","bashen","gejv","sanqi",
                                 "yanbo","zhifushi","yongshen","yingqi","jiugong","sibao"]}, False


# ─────────────────────────────────────────────────────────────
# Palace quality scoring (四维综合评分)
# ─────────────────────────────────────────────────────────────
def _score_palace(star_nature: str, door_nature: str, deity_nature: str,
                  stem: str, gong_wx: str) -> Tuple[str, int]:
    """
    Score palace on 5-point scale using classical 四盘 logic.
    Returns (quality_label, score_0_to_10)
    """
    # Base score from three layers
    scores = {
        "大吉": 3, "吉": 2, "次吉": 1, "小吉": 1,
        "中平": 0, "平": 0,
        "小凶": -1, "凶": -2, "大凶": -3,
    }
    total = (scores.get(star_nature, 0)
           + scores.get(door_nature, 0)
           + scores.get(deity_nature, 0))

    # Stem modifier: 三奇 big boost, 庚/己 penalty
    if stem in ("乙", "丙", "丁"):
        total += 2
    elif stem == "庚":
        total -= 2
    elif stem == "己":
        total -= 1
    elif stem in ("戊", "壬"):
        total += 1

    # Map to label
    if total >= 5:   quality = "大吉"
    elif total >= 3: quality = "吉"
    elif total >= 1: quality = "小吉"
    elif total == 0: quality = "平"
    elif total >= -2: quality = "凶"
    else:            quality = "大凶"

    return quality, max(0, total + 5)


# ─────────────────────────────────────────────────────────────
# Detect special patterns (格局检测)
# ─────────────────────────────────────────────────────────────
def _detect_patterns(layout: Dict, palaces: List[Dict], ck: Dict) -> List[Dict]:
    """Detect classical QiMen patterns from layout data."""
    gejv_db = ck.get("gejv", {})
    patterns = []

    # Fuyin / Fanyin —— 由 detect_fuyin_fanyin 按局数/遁判定（旧版读 layout.get("fuyin")
    # 键错配恒 None、伏吟反吟大凶格从不进格局列表；现直接以局数判，纳入 patterns）。
    try:
        from core.qimen.purpose_analysis import detect_fuyin_fanyin
        _ff = detect_fuyin_fanyin(layout.get("ju_number", 1),
                                  layout.get("ju_type", "阳遁") == "阳遁")
    except Exception:
        _ff = {}
    if _ff.get("type") == "伏吟":
        g = gejv_db.get("伏吟", {})
        patterns.append({
            "name": "伏吟",
            "level": "大凶",
            "desc": g.get("应事", _ff.get("desc") or "万事停滞，原地踏步，宜静守待时"),
            "kou": g.get("口诀", "伏吟之局最难行，万事停滞莫强动"),
        })
    if _ff.get("type") == "反吟":
        g = gejv_db.get("反吟", {})
        patterns.append({
            "name": "反吟",
            "level": "大凶",
            "desc": g.get("应事", _ff.get("desc") or "反覆动荡，进退两难，事与愿违"),
            "kou": g.get("口诀", "反吟之局事颠倒，进退两难莫轻动"),
        })

    # Check star/door relationship (星克门吉，门克星凶)
    for p in palaces:
        star_wx = _XING_WX.get(p.get("star", ""), "")
        door_wx = _MEN_WX.get(p.get("door", ""), "")
        if star_wx and door_wx:
            if _WX_KE.get(star_wx) == door_wx:
                patterns.append({
                    "name": f"星克门·{p['palace_name']}",
                    "level": "吉",
                    "desc": f"{p['palace_name']}宫：{p['star']}（{star_wx}）克{p['door']}（{door_wx}），星克门主吉，天时助人和",
                    "kou": "星克门吉天助人，谋事顺遂吉自来",
                })
            elif _WX_KE.get(door_wx) == star_wx:
                patterns.append({
                    "name": f"门克星·{p['palace_name']}",
                    "level": "凶",
                    "desc": f"{p['palace_name']}宫：{p['door']}（{door_wx}）克{p['star']}（{star_wx}），门克星主凶，人和逆天时有阻",
                    "kou": "门克星凶人胜天，虽成有损要防险",
                })

    # San qi de shi (三奇得使)
    zhishi_palace = next((p for p in palaces if p.get("is_zhishi")), None)
    if zhishi_palace:
        stem = zhishi_palace.get("stem", "")
        if stem in ("乙", "丙", "丁"):
            qi_names = {"乙": "天奇", "丙": "地奇", "丁": "人奇"}
            patterns.append({
                "name": "三奇得使",
                "level": "大吉",
                "desc": f"值使门宫有{stem}（{qi_names.get(stem, '')}）临之，三奇得使大吉，贵人主动相助，谋事必成",
                "kou": "三奇得使诸事吉，贵人相助无阻隔",
            })

    return patterns  # Return ALL detected patterns (no truncation, frontend handles display)


# ─────────────────────────────────────────────────────────────
# Zhifu/Zhishi analysis (值符值使核心断法)
# ─────────────────────────────────────────────────────────────
def _analyze_zhifu_zhishi(palaces: List[Dict], ck: Dict) -> Dict[str, Any]:
    """
    Core analysis: 值符（全局领袖）× 值使门（执行关键）
    This is the heart of QiMen divination.
    """
    zhifu  = next((p for p in palaces if p.get("is_zhifu")), None)
    zhishi = next((p for p in palaces if p.get("is_zhishi")), None)
    if not zhifu or not zhishi:
        return {}

    fu_star_wx  = _XING_WX.get(zhifu.get("star", ""), "")
    shi_door_wx = _MEN_WX.get(zhishi.get("door", ""), "")
    fu_gong_wx  = _GONG_WX.get(zhifu.get("palace_name", ""), "")
    shi_gong_wx = _GONG_WX.get(zhishi.get("palace_name", ""), "")

    # Relationship between 值符 and 值使
    rel = _wx_rel(fu_star_wx, shi_door_wx)
    rel_desc_map = {
        "生":   ("符生使", "大吉", "值符星生值使门，贵人全力支持执行，事情顺遂"),
        "被生": ("使生符", "次吉", "值使门生值符星，费力可成，需耗费更多精力"),
        "克":   ("符克使", "吉",   "值符克值使，虽有阻力但正常前进，可成"),
        "被克": ("使克符", "大凶", "值使克值符，执行阻碍长远，事情极难成功"),
        "同":   ("符使同气", "吉",  "符使五行相同，方向一致，事情稳定可成"),
    }
    rel_info = rel_desc_map.get(rel, ("无明显关系", "平", "符使关系平和，需结合用神判断"))
    rel_name, rel_level, rel_detail = rel_info

    # 值符 strength (旺衰)
    fu_wangshuai = _wx_rel(fu_gong_wx, fu_star_wx)
    fu_strong = fu_wangshuai in ("生", "同")

    # 值使 strength
    shi_door = zhishi.get("door", "")
    shi_door_auspicious = shi_door in ("开门", "休门", "生门")

    return {
        "zhifu": {
            "star":      zhifu.get("star", ""),
            "palace":    zhifu.get("palace_name", ""),
            "stem":      zhifu.get("stem", ""),
            "deity":     zhifu.get("deity", ""),
            "wangshuai": "旺" if fu_strong else "衰",
            "role":      "全局领袖，代表长远前景",
            "desc":      ck.get("jiuxing", {}).get(zhifu.get("star", ""), {}).get("断法", ""),
        },
        "zhishi": {
            "door":      shi_door,
            "palace":    zhishi.get("palace_name", ""),
            "stem":      zhishi.get("stem", ""),
            "star":      zhishi.get("star", ""),
            "auspicious": shi_door_auspicious,
            "role":      "当下执行，代表近期事务结果",
            "yanbo":     ck.get("bamen", {}).get(shi_door, {}).get("烟波", ""),
            "desc":      ck.get("bamen", {}).get(shi_door, {}).get("详解", ""),
        },
        "relationship": {
            "name":   rel_name,
            "level":  rel_level,
            "detail": rel_detail,
        },
        "verdict":      _build_verdict(zhifu, zhishi, rel_name, rel_level, fu_strong, shi_door_auspicious),
        "priority":     "值使为第一要素（近期），值符为第二要素（长远）。先看值使，再参值符。",
        "classical_ref": "《奇门统宗》：静则只查值符、值使、时干，看其生克衰旺如何",
    }


def _build_verdict(zhifu: Dict, zhishi: Dict, rel: str, level: str,
                   fu_strong: bool, shi_auspicious: bool) -> str:
    """Build human-readable verdict from zhifu/zhishi analysis."""
    shi_door = zhishi.get("door", "")
    fu_star  = zhifu.get("star", "")

    if level == "大凶":
        return f"值使门（{shi_door}）克制值符星（{fu_star}），执行力逆转长远方向，事情极难成功，慎重行事。"
    elif level in ("大吉", "吉"):
        return (f"值符（{fu_star}）{'旺相有力' if fu_strong else '虽偏弱'}，"
                f"{'值使门（' + shi_door + '）为吉门，' if shi_auspicious else ''}"
                f"二者关系为{rel}，长远前景{'乐观' if fu_strong else '一般'}，"
                f"{'当下执行顺利' if shi_auspicious else '执行有所阻力'}。")
    else:
        return f"值符（{fu_star}）与值使门（{shi_door}）关系平和，需结合用神与宫位综合判断。"


# ─────────────────────────────────────────────────────────────
# Purpose-based yong shen analysis (用神取法)
# ─────────────────────────────────────────────────────────────
def _analyze_yong_shen(palaces: List[Dict], question: str, ck: Dict,
                       purpose: str = "", day_gan: str = "", hour_gan: str = "") -> Dict[str, Any]:
    """据用事（purpose 优先，question 关键词回退）取用神及其落宫。

    用神取法以《奇门法穷》《烟波钓叟赋》用事门为据：求财生门、事业开门、
    婚姻休门（六合）、疾病天芮、失物玄武……由 PURPOSE_LOGIC 统一管理；
    官司另法：日干为我、时干为彼，比二宫强弱定胜负（见 _analyze_guansi）。
    """
    from core.qimen.purpose_analysis import PURPOSE_LOGIC

    question = question or ""
    purpose = (purpose or "").strip()

    # ① 由 question 关键词推定用事类别（映射到 PURPOSE_LOGIC 之中文键）
    _Q2P = [
        (["求财", "财运", "投资", "经商", "生意", "赚钱", "买卖"], "求财"),
        (["感情", "恋爱", "桃花", "对象"],                       "感情"),
        (["婚姻", "婚嫁", "结婚", "嫁娶"],                       "婚姻"),
        (["事业", "升职", "求官", "职位", "工作", "仕途", "升迁"], "事业"),
        (["出行", "旅游", "出国", "远行", "行程", "搬家"],        "出行"),
        (["疾病", "看病", "求医", "手术", "病情", "可治", "治病", "得病", "生病"], "疾病"),
        (["健康", "养生", "身体"],                              "健康"),
        (["考试", "学习", "求学", "考研", "学业"],               "学业"),
        (["官司", "诉讼", "打官司", "纠纷"],                     "官司"),
        (["失物", "丢失", "寻物"],                              "失物"),
        (["寻人", "找人"],                                     "寻人"),
        (["胜负", "比赛", "竞争", "输赢"],                       "胜负"),
        (["谋事", "计划", "能否成"],                            "谋事"),
    ]
    topic = ""
    if purpose in PURPOSE_LOGIC:
        topic = purpose          # 明确指定用事，优先
    # purpose 为非规范键（如"诉讼/求职求官/考试/求医"）时，亦以关键词归并到规范用事，
    # 杜绝静默回退求财致用神错配（曾："求职求官"→生门"求财谋利用神"）。
    if not topic and purpose:
        for keywords, t in _Q2P:
            if any(k in purpose for k in keywords):
                topic = t
                break
    if not topic:
        for keywords, t in _Q2P:
            if any(k in question for k in keywords):
                topic = t
                break
    if not topic:
        topic = "谋事"           # 无可归并者一律按通用「谋事干求」，不再误默认求财

    logic = PURPOSE_LOGIC.get(topic, PURPOSE_LOGIC.get("谋事", {}))

    # 官司/胜负另法：日干为我、时干为彼，比二宫强弱定胜负（《奇门法穷·词讼/竞斗章》）
    if topic in ("官司", "胜负") and day_gan and hour_gan:
        return _analyze_guansi(palaces, day_gan, hour_gan, logic, topic=topic)

    # 寻人另法：以时干为所寻之人，观其落宫门星断远近归否（《奇门法穷·寻人章》）
    if topic == "寻人" and hour_gan:
        return _analyze_xunren(palaces, hour_gan, logic)

    best_doors = logic.get("best_doors", ["生门"]) or ["生门"]
    best_stars = logic.get("best_stars", []) or []
    worst_doors = logic.get("worst_doors", []) or []
    worst_stars = logic.get("worst_stars", []) or []
    primary_door = best_doors[0]

    # ② 定位用神所在之宫
    #   古法用神类神有别：求财/事业/婚姻/出行以「门」为用，
    #   学业以天辅（文昌）、疾病以天芮（病符）、失物以玄武（盗神）——以「星/神」为用。
    #   故 PURPOSE_LOGIC 可显式标 yong_shen{type,marker,label}；缺省回退门。
    ys_spec = logic.get("yong_shen")
    yong_palace = None
    used_marker = primary_door
    explicit_name = ""
    if ys_spec:
        _field = {"star": "star", "door": "door", "deity": "deity", "stem": "di_pan"}.get(
            ys_spec.get("type", "door"), "door")
        _marker = ys_spec.get("marker", "")
        yong_palace = next((p for p in palaces if _marker and _marker in str(p.get(_field, ""))), None)
        if yong_palace:
            used_marker = _marker
            explicit_name = f"{_marker}（{ys_spec.get('label', logic.get('title','') + '用神')}）"
    # 门类用神（或星/神用神不上盘时）走门定位
    if yong_palace is None:
        yong_palace = next((p for p in palaces if primary_door in p.get("door", "")), None)
        used_marker = primary_door
        # 主用神门不上盘则取次门
        if yong_palace is None and len(best_doors) > 1:
            for d in best_doors[1:]:
                yong_palace = next((p for p in palaces if d in p.get("door", "")), None)
                if yong_palace:
                    used_marker = d
                    break

    # ③ 据落宫星门神与吉凶门星，评用神品质
    quality = "平"
    _polarity = (ys_spec.get("polarity", "auspicious") if ys_spec and yong_palace and explicit_name
                else "auspicious")
    if yong_palace:
        q0 = yong_palace.get("quality", "平")
        star = yong_palace.get("star", "")
        door = yong_palace.get("door", "")
        if _polarity == "adverse":
            # 逆向用神（病符天芮 / 盗神玄武）：以五行论病符/盗神是否受制——
            #   宫克用神(木克土)、用神生宫泄气(土生金) → 受制/泄 → 吉（病退/物可寻）；
            #   宫生用神(火生土)、比和(土土) → 得生/得地 → 凶（病重/难寻）；
            #   用神克宫(土克水) → 耗力 → 平。
            _KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
            _POS_WX = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火"}
            _yong_wx = _XING_WX.get(used_marker) or _SHEN_WX.get(used_marker) or ""
            _gong_wx = _POS_WX.get(yong_palace.get("position"), "")
            if not _yong_wx or not _gong_wx:
                quality = "平"
            elif _KE.get(_gong_wx) == _yong_wx or _WX_SHENG.get(_yong_wx) == _gong_wx:
                quality = "吉"      # 受制 / 泄气 → 病退、物可寻
            elif _WX_SHENG.get(_gong_wx) == _yong_wx or _gong_wx == _yong_wx:
                quality = "凶"      # 得生 / 得地 → 病重、难寻
            else:
                quality = "平"      # 用神克宫，耗力
        else:
            # 顺向用神：落宫本身吉凶 + 是否逢忌门忌星 微调
            bad_hit = (any(w in door for w in worst_doors) or any(w in star for w in worst_stars))
            good_hit = (any(g in star for g in best_stars))
            if bad_hit:
                quality = "凶" if "吉" in q0 else ("大凶" if "凶" in q0 else "平")
            elif good_hit and "吉" in q0:
                quality = "大吉"
            else:
                quality = q0

    if explicit_name:
        name = explicit_name
    else:
        name = f"{primary_door}（{logic.get('title','')}用神）"
        if used_marker != primary_door:
            name = f"{used_marker}（{primary_door}不上盘，取次用）"

    return {
        "topic":   topic,
        "name":    name,
        "palace":  yong_palace.get("palace_name", "未上盘") if yong_palace else "未上盘",
        "quality": quality,
        "rules":   logic.get("principle", ""),
        "best":    logic.get("advanced", ""),
    }


def _analyze_guansi(palaces: List[Dict], day_gan: str, hour_gan: str,
                    logic: Dict, topic: str = "官司") -> Dict[str, Any]:
    """官司/胜负用神另法：日干为我、时干为彼，比二宫旺衰吉凶 + 干五行生克定胜负。
    《奇门法穷》：我宫旺、彼宫衰，又我克彼，则我胜；反之则负。"""
    _XUNSHOU = {"甲": "戊"}   # 甲遁不上盘，以值符六仪戊代（旬首近似）

    def _locate(gan):
        g = _XUNSHOU.get(gan, gan)
        return next((p for p in palaces
                     if p.get("di_pan") == g or p.get("stem") == g), None)

    me = _locate(day_gan)       # 我方（日干）
    other = _locate(hour_gan)   # 对方（时干）

    def _pscore(p):
        # 落宫吉凶分（score 已含门星神综合）；缺则以 quality 粗估
        if not p:
            return -99
        s = p.get("score")
        if isinstance(s, (int, float)):
            return s
        q = p.get("quality", "平")
        return {"大吉": 2, "吉": 1, "平": 0, "凶": -1, "大凶": -2}.get(q, 0)

    sm, so = _pscore(me), _pscore(other)

    # 干五行生克（我=日干 vs 彼=时干）
    _KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
    wx_me = _TIANGAN_WX.get(day_gan, "")
    wx_ot = _TIANGAN_WX.get(hour_gan, "")
    ke_rel = ""
    if wx_me and wx_ot:
        if _KE.get(wx_me) == wx_ot:
            ke_rel = "我克彼"      # 利我（制得住对方）
        elif _KE.get(wx_ot) == wx_me:
            ke_rel = "彼克我"      # 不利（受制于人）
        elif _WX_SHENG.get(wx_me) == wx_ot:
            ke_rel = "我生彼"      # 泄我（耗力，略不利）
        elif _WX_SHENG.get(wx_ot) == wx_me:
            ke_rel = "彼生我"      # 利我（得对方之助/对方让步）

    # 综合：宫位强弱差 + 生克倾向
    edge = (sm - so)
    if ke_rel == "我克彼":
        edge += 1.5
    elif ke_rel == "彼克我":
        edge -= 1.5
    elif ke_rel == "我生彼":
        edge -= 0.5
    elif ke_rel == "彼生我":
        edge += 0.5

    _is_sf = (topic == "胜负")
    if edge >= 1.5:
        quality = "吉"
        verdict = ("我方占优，宜主动进取，胜算较大" if _is_sf
                   else "我方得理得势，宜进取，胜算较大")
    elif edge <= -1.5:
        quality = "凶"
        verdict = ("对方居优，我方不利，宜避其锋、另择吉时再战" if _is_sf
                   else "对方居优，我方受制，宜守宜和，强争不利")
    else:
        quality = "平"
        verdict = ("双方旗鼓相当，胜负在毫厘，宜抢占吉方吉时" if _is_sf
                   else "双方势均，胜负未明，宜求和解或择吉时再图")

    me_pname = me.get("palace_name", "未上盘") if me else "未上盘"
    ot_pname = other.get("palace_name", "未上盘") if other else "未上盘"
    name = (f"日干{day_gan}（我·{me_pname}）⚔ 时干{hour_gan}（彼·{ot_pname}）"
            + (f"，{ke_rel}" if ke_rel else ""))

    return {
        "topic":   topic,
        "name":    name,
        "palace":  me_pname,                 # 以我方落宫为主用神宫
        "other_palace": ot_pname,            # 对方落宫
        "quality": quality,
        "verdict": verdict,
        "me_score": sm, "other_score": so, "ke_relation": ke_rel,
        "rules":   logic.get("principle", f"{topic}以日干为我、时干为彼，比二宫旺衰吉凶定胜负。"),
        "best":    logic.get("advanced", ""),
    }


def _analyze_xunren(palaces: List[Dict], hour_gan: str, logic: Dict) -> Dict[str, Any]:
    """寻人用神：以时干为所寻之人，观其落宫门星断远近、归否。
    《奇门法穷·寻人章》：临生门、休门、开门则近而易归；临死门、绝则凶；逢驿马、冲宫则远走他方。"""
    _XUNSHOU = {"甲": "戊"}
    g = _XUNSHOU.get(hour_gan, hour_gan)
    p = next((x for x in palaces if x.get("di_pan") == g or x.get("stem") == g), None)

    if not p:
        return {
            "topic": "寻人", "name": f"时干{hour_gan}（所寻之人·未上盘）",
            "palace": "未上盘", "quality": "平",
            "verdict": "所寻之人用神未明现，音讯难寻，宜另择时再占。",
            "rules": logic.get("principle", ""), "best": logic.get("advanced", ""),
        }

    door = p.get("door", "")
    pname = p.get("palace_name", "")
    q0 = p.get("quality", "平")
    _JI_MEN = ("生门", "休门", "开门")    # 三吉门
    _XIONG_MEN = ("死门", "伤门", "惊门")
    is_ma = ("驿马" in str(p.get("notes", "")) or p.get("is_horse"))

    if any(m in door for m in _JI_MEN):
        quality = "吉"
        verdict = f"所寻之人临{door}于{pname}，门吉气顺，其人安好、近在可寻，不日可归或得音讯。"
    elif "死门" in door:
        quality = "凶"
        verdict = f"所寻之人临死门于{pname}，主凶，恐有险厄或音讯断绝，宜速寻、报官求助。"
    elif any(m in door for m in _XIONG_MEN):
        quality = "凶" if "凶" in q0 else "平"
        verdict = f"所寻之人临{door}于{pname}，其人或有惊扰阻滞、行踪不定，寻之费力。"
    elif is_ma:
        quality = "平"
        verdict = f"所寻之人逢驿马于{pname}，主远行他方、动而难定，须往远处或动向上寻。"
    else:
        quality = "平"
        verdict = (f"所寻之人落{pname}（{door or '无门'}），"
                   + ("门为杜塞，其人或自隐踪迹、暂难露面，宜耐心待时。" if "杜门" in door
                      else "气象平和，假以时日可寻。"))

    return {
        "topic":   "寻人",
        "name":    f"时干{hour_gan}（所寻之人·{pname}临{door or '无门'}）",
        "palace":  pname,
        "quality": quality,
        "verdict": verdict,
        "rules":   logic.get("principle", "寻人以时干为所寻之人，观落宫门星断远近归否。"),
        "best":    logic.get("advanced", ""),
    }


# ─────────────────────────────────────────────────────────────
# Timing analysis (应期推算)
# ─────────────────────────────────────────────────────────────
def _analyze_timing(zhifu_palace: Optional[Dict], zhishi_palace: Optional[Dict],
                    ck: Dict) -> Dict[str, str]:
    """Apply 《奇门法穷》 timing rules."""
    yq = ck.get("yingqi", {})

    # Determine speed from zhishi door quality
    shi_door = zhishi_palace.get("door", "") if zhishi_palace else ""
    zhifu_stem = zhifu_palace.get("stem", "") if zhifu_palace else ""

    if shi_door in ("死门", "惊门") or zhifu_stem == "庚":
        speed = "应月甚至应年（值使凶门或庚阻，事情迟缓）"
        speed_reason = "值使逢凶门或庚金阻格"
    elif shi_door in ("开门", "生门", "休门"):
        speed = "应日或应时辰（值使吉门，事情快速应验）"
        speed_reason = "值使临三吉门，力量旺盛"
    else:
        speed = "应日至应月（中性，视用神旺衰而定）"
        speed_reason = "格局中等平稳"

    # Key timing method from 《奇门法穷》
    fu_stem_info = ""
    if zhifu_palace:
        palace = zhifu_palace.get("palace_name", "")
        stem   = zhifu_palace.get("stem", "")
        fu_stem_info = f"值符（{stem}）临{palace}，按值符相冲法推算：该宫地支相冲之日月为应期"

    return {
        "speed":       speed,
        "speed_reason": speed_reason,
        "fu_method":   fu_stem_info or "值符落宫参照《奇门法穷》值符相冲法",
        "shi_method":  f"值使门（{shi_door}）旺衰决定应期快慢，" + (
            "吉门旺相则快，死惊凶门则慢" if shi_door else "综合判断"),
        "general":     yq.get("总则", "先定地支，后配天干。先以值符落宫定应期，后以值使门落宫定应期。"),
        "three_methods": yq.get("三法", {}),
        "fu_shi_order": yq.get("符使先后", "符应主先，使应主后"),
    }


# ─────────────────────────────────────────────────────────────
# Main analyze function
# ─────────────────────────────────────────────────────────────
def analyze_qimen(layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    奇门遁甲完整断事分析
    四盘体系 × 值符值使断法 × 用神取法 × 格局检测 × 应期推算
    """
    palaces = layout["palaces"]
    question = layout.get("question", "")
    purpose = layout.get("purpose", "")
    ck, has_classical = _load_classical()

    bamen_db  = ck["bamen"]
    jiuxing_db = ck["jiuxing"]
    bashen_db  = ck["bashen"]
    yanbo_db   = ck["yanbo"]

    enriched = []

    for p in palaces:
        star   = p.get("star", "")
        door   = p.get("door", "")
        deity  = p.get("deity", "")
        stem   = p.get("stem", "")
        palace_name = p.get("palace_name", "")
        gong_wx = _GONG_WX.get(palace_name, "")

        # Get classical data
        c_door  = bamen_db.get(door, {})
        c_star  = jiuxing_db.get(star, {})
        c_deity = bashen_db.get(deity, {})

        star_nature  = c_star.get("吉凶")  or ("吉" if star in ("天心","天辅","天任","天禽") else
                                                "次吉" if star == "天冲" else
                                                "凶" if star in ("天蓬","天芮","天柱") else "中")
        door_nature  = c_door.get("吉凶")  or ("大吉" if door in ("开门","休门","生门") else
                                                "大凶" if door == "死门" else
                                                "小凶" if door in ("伤门","惊门","杜门") else "中")
        deity_nature = c_deity.get("属性") or ("吉" if deity in ("值符","太阴","六合","九天","九地") else "凶")

        quality, score = _score_palace(star_nature, door_nature, deity_nature, stem, gong_wx)

        # Detailed classical notes (四盘三才合参)
        star_desc  = c_star.get("主象", star + "星")
        door_desc  = c_door.get("主象", door)
        deity_desc = c_deity.get("主象", deity + "神")
        star_kou   = c_star.get("临宫口诀", "")
        door_yanbo = c_door.get("烟波", "")

        # Star-door WX relationship (星克门/门克星)
        star_wx  = _XING_WX.get(star, "")
        door_wx  = _MEN_WX.get(door, "")
        sd_rel   = _wx_rel(star_wx, door_wx)
        sd_note  = ""
        if sd_rel == "克":
            sd_note = f"★星克门（{star_wx}克{door_wx}），天时助人和，主吉"
        elif sd_rel == "被克":
            sd_note = f"▲门克星（{door_wx}克{star_wx}），逆天时，主有阻"

        # Stem (奇仪) info
        stem_info = ""
        if stem in ("乙", "丙", "丁"):
            qi_name = {"乙": "天奇（大吉）", "丙": "地奇（大吉）", "丁": "人奇（吉）"}
            stem_info = f"三奇 {stem}·{qi_name.get(stem, '')} — 贵人相助"
        elif stem == "庚":
            stem_info = "庚·太白（大凶）— 阻格损伤"
        elif stem == "戊":
            stem_info = "戊·值符本气（吉）— 稳健中正"

        # Gong-door WX relationship
        gong_door_rel = _wx_rel(gong_wx, door_wx)

        # Full classical notes
        notes = f"【{star}】{star_desc} | 【{door}】{door_desc} | 【{deity}】{deity_desc}"
        if stem_info: notes += f" | {stem_info}"
        if sd_note:   notes += f"\n{sd_note}"
        if door_yanbo: notes += f"\n《烟波》：{door_yanbo}"
        if star_kou:   notes += f"\n口诀：{star_kou}"

        enriched.append({
            **p,
            "quality":       quality,
            "score":         score,
            "star_nature":   star_nature,
            "door_nature":   door_nature,
            "deity_nature":  deity_nature,
            "star_meaning":  star_desc,
            "door_meaning":  door_desc,
            "deity_meaning": deity_desc,
            "door_yanbo":    door_yanbo,
            "star_kou":      star_kou,
            "stem_info":     stem_info,
            "sd_rel":        sd_note,
            "gong_wx":       gong_wx,
            "notes":         notes,
            "is_auspicious": quality in ("大吉", "吉", "小吉"),
            # Classical detail fields
            "star_detail":   c_star.get("断法", ""),
            "door_detail":   c_door.get("详解", ""),
            "door_yi":       c_door.get("宜", []),
            "door_ji":       c_door.get("忌", []),
            "deity_detail":  c_deity.get("断法", ""),
            "deity_renwu":   c_deity.get("人事", ""),
        })

    best  = [p for p in enriched if p["quality"] in ("大吉", "吉", "小吉")]
    worst = [p for p in enriched if p["quality"] in ("大凶", "凶")]

    # 格局检测：合并简单格局 + 完整 30+ 格局
    patterns = _detect_patterns(layout, enriched, ck)
    
    # ─── 加入 calculate_qimen 的完整格局（30+ 种）───
    layout_patterns = layout.get("patterns", []) or []
    existing_names = {p["name"] for p in patterns}
    for ep in layout_patterns:
        if ep.get("name") and ep["name"] not in existing_names:
            # 转换 severity → level 兼容前端
            sev = ep.get("severity", "")
            lv_map = {
                "auspicious_great": "大吉",
                "auspicious": "吉",
                "mixed": "吉凶参半",
                "inauspicious": "凶",
                "inauspicious_great": "大凶",
            }
            ep_norm = {
                "name": ep["name"],
                "level": lv_map.get(sev, ep.get("level", "平")),
                "severity": sev,
                "desc": ep.get("desc", ""),
                "kou": ep.get("kou", ep.get("source", "")),
                "source": ep.get("source", ""),
                "direction": ep.get("direction", ""),
            }
            patterns.append(ep_norm)
            existing_names.add(ep["name"])

    # 值符值使断法 (mark zhifu/zhishi)
    zhifu_palace  = next((p for p in enriched if p.get("is_zhifu")), None)
    zhishi_palace = next((p for p in enriched if p.get("is_zhishi")), None)
    zhifu_analysis = _analyze_zhifu_zhishi(enriched, ck)

    # 用神分析
    yong_shen = _analyze_yong_shen(enriched, question, ck, purpose,
                                   day_gan=layout.get("day_gan", "") or "",
                                   hour_gan=layout.get("hour_gan", "") or "")

    # 用神落宫多维断语（门×星×神×旺衰×神煞），深化用神之断
    # 官司/胜负/寻人自有专断（日干vs时干/时干远近），故仅对门星神类用神合成。
    if yong_shen.get("topic") not in ("官司", "胜负", "寻人"):
        try:
            from core.qimen.yongshen_judgment import synthesize_yongshen_judgment
            _yp = next((p for p in enriched
                        if p.get("palace_name") == yong_shen.get("palace")), None)
            _yj = synthesize_yongshen_judgment(yong_shen, _yp, yong_shen.get("topic", ""))
            if _yj.get("paragraph"):
                yong_shen["judgment_dimensions"] = _yj["dimensions"]
                yong_shen["judgment"] = _yj["paragraph"]
        except Exception as _e1:
            from core.log import log_failure; log_failure("qimen", "装配(自动补充日志)", _e1)

    # 应期推算
    timing = _analyze_timing(zhifu_palace, zhishi_palace, ck)

    # Summary and advice
    summary = _build_summary_full(layout, best, worst, zhifu_analysis, patterns)
    advice  = _build_advice_full(layout, best, worst, patterns, zhifu_analysis, yong_shen)

    # Top 3 yanbo quotes relevant to current layout
    yanbo_notes = [x["口诀"] for x in ck.get("yanbo", [{}])[:3]] if ck.get("yanbo") else []

    return {
        **layout,
        "palaces":      enriched,
        "summary":      summary,
        "advice":       advice,
        "best_palaces": [p["palace_name"] for p in best],
        "worst_palaces":[p["palace_name"] for p in worst],
        "patterns":     patterns,
        "zhifu_analysis": zhifu_analysis,
        "yong_shen":    yong_shen,
        "timing":       timing,
        "yanbo_notes":  yanbo_notes,
        "has_classical": has_classical,
        "sibao_desc":   "天盘九星（天时）× 人盘八门（人和）× 地盘九宫（地利）× 神盘八神（神助）",
    }


def _build_summary_full(layout: Dict, best: List, worst: List,
                        zf: Dict, patterns: List) -> str:
    ju_type   = layout.get("ju_type", "")
    ju_number = layout.get("ju_number", "")
    yuan      = layout.get("yuan", "")
    best_str  = "、".join(p["palace_name"] for p in best[:3]) or "无"
    worst_str = "、".join(p["palace_name"] for p in worst[:2]) or "无"
    verdict   = zf.get("relationship", {}).get("detail", "") if zf else ""

    base = (f"当前为{ju_type}第{ju_number}局（{yuan}），"
            f"吉方：{best_str}，凶方：{worst_str}。")
    if verdict:
        base += f" 值符值使：{verdict}"
    if patterns:
        pats = "、".join(f"【{p['name']}】{p['level']}" for p in patterns[:2])
        base += f" 特殊格局：{pats}。"
    return base


def _build_advice_full(layout: Dict, best: List, worst: List, patterns: List,
                        zf: Dict, ys: Dict) -> str:
    # Pattern override for major bad patterns
    for pat in patterns:
        if pat.get("level") == "大凶" and pat["name"] in ("伏吟", "反吟"):
            return (f"【{pat['name']}格】{pat['desc']}。"
                    f"{pat.get('kou', '')}。当前宜静守待时，万事不宜轻动。")

    if not best:
        return "当前格局偏弱，宜静守。《烟波》：时不至者不可强行。"

    top = best[0]
    door = top.get("door", "")
    yanbo = top.get("door_yanbo", "")
    door_yi = top.get("door_yi", [])

    # Main direction advice
    shi_verdict = zf.get("verdict", "") if zf else ""
    yi_str = "、".join(door_yi[:3]) if door_yi else door

    advice = (f"最佳宫位：{top['palace_name']}（{door} × {top.get('star','')} × {top.get('deity','')}）。"
              f"此宫宜：{yi_str}。")

    if shi_verdict:
        advice += f" {shi_verdict}"
    if yanbo:
        advice += f" 《烟波》：{yanbo}"

    # Yong shen note
    if ys.get("topic") and ys.get("palace"):
        advice += (f" 就{ys['topic']}而言，用神（{ys['name'][:4]}）"
                   f"在{ys['palace']}，格局{'有利' if ys.get('quality') in ('大吉','吉') else '需谨慎'}。")

    return advice
