"""
core/fengshui/yangzhai_sanyao.py
================================
《阳宅三要》（清·赵九峰）门、主、灶三要断法。

原书纲领："看阳宅之法，先看大门，次看主房，后看灶。"
  · 门 —— 一宅纳气之口，为君、为主导。宅之东西四，以门分。
  · 主 —— 主房（一家之主所居、最高大之屋），为一宅之尊。
  · 灶 —— 灶位（火门），主一家饮食祸福、妇人疾病。

断法（大游年翻卦）：
  1. 以【门】起伏位，翻卦数到【主】，得游年星 —— 论"门主"之吉凶。
  2. 以【主】起伏位，翻卦数到【灶】，得游年星 —— 论"主灶"之吉凶。
  3. 门、主、灶三者宜同属东四卦（坎离震巽）或同属西四卦（乾坤艮兑）；
     纯者吉，驳杂者凶。

游年八星（与九星对应）：
  生气-贪狼木(上吉)  天医-巨门土(中吉)  延年-武曲金(中吉)  伏位-辅弼木(小吉/平)
  绝命-破军金(大凶)  五鬼-廉贞火(大凶)  六煞-文曲水(次凶)  祸害-禄存土(次凶)

本模块复用 calculator.py 的 EIGHT_MANSION 游年表与 SECTOR_QUALITY，
保证与八宅明镜/玄空模块同源一致。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.fengshui.calculator import (
    EIGHT_MANSION, SECTOR_QUALITY,
    EAST_FOUR_HOUSE, WEST_FOUR_HOUSE,
    SITTING_GUA, FACING_TO_SITTING,
)

# ─────────────────────────────────────────────────────────────
# 卦 / 方位 / 洛书数 / 五行 / 人物 对照
# ─────────────────────────────────────────────────────────────

# 卦号（洛书数）→ 卦名
GUA_NUM_NAME: Dict[int, str] = {
    1: "坎", 2: "坤", 3: "震", 4: "巽",
    6: "乾", 7: "兑", 8: "艮", 9: "离",
}
GUA_NAME_NUM: Dict[str, int] = {v: k for k, v in GUA_NUM_NAME.items()}

# 卦号 → 八方位
GUA_NUM_DIR: Dict[int, str] = {
    1: "北", 2: "西南", 3: "东", 4: "东南",
    6: "西北", 7: "西", 8: "东北", 9: "南",
}
DIR_GUA_NUM: Dict[str, int] = {v: k for k, v in GUA_NUM_DIR.items()}

# 卦五行
GUA_WUXING: Dict[str, str] = {
    "坎": "水", "离": "火", "震": "木", "巽": "木",
    "乾": "金", "兑": "金", "坤": "土", "艮": "土",
}
# 卦象人物（用于断应何人）
GUA_PERSON: Dict[str, str] = {
    "乾": "父/老男/家主", "坤": "母/老妇/女主",
    "震": "长男", "巽": "长女", "坎": "中男", "离": "中女",
    "艮": "少男", "兑": "少女",
}

# 游年星 → 九星 / 五行 / 简断
YOUNIAN_STAR: Dict[str, Dict[str, str]] = {
    "生气": {"jiuxing": "贪狼", "wuxing": "木", "level": "上吉",
             "duan": "主旺丁、发福最快，利事业婚姻子嗣"},
    "天医": {"jiuxing": "巨门", "wuxing": "土", "level": "中吉",
             "duan": "主健康、得贵人、财帛丰盈，病人遇之即愈"},
    "延年": {"jiuxing": "武曲", "wuxing": "金", "level": "中吉",
             "duan": "主长寿、夫妻和合、家道兴隆"},
    "伏位": {"jiuxing": "辅弼", "wuxing": "木", "level": "小吉",
             "duan": "主平稳守成、小财、安宁，力较缓"},
    "祸害": {"jiuxing": "禄存", "wuxing": "土", "level": "次凶",
             "duan": "主口舌是非、官讼、退气、慢性疾病"},
    "六煞": {"jiuxing": "文曲", "wuxing": "水", "level": "次凶",
             "duan": "主桃花酒色、破财、是非、损丁"},
    "五鬼": {"jiuxing": "廉贞", "wuxing": "火", "level": "大凶",
             "duan": "主火灾、官非、横祸、失财、怪异"},
    "绝命": {"jiuxing": "破军", "wuxing": "金", "level": "大凶",
             "duan": "最凶，主重病、绝嗣、损丁、败绝"},
}
JI_STARS = {"生气", "天医", "延年", "伏位"}
XIONG_STARS = {"祸害", "六煞", "五鬼", "绝命"}


# ─────────────────────────────────────────────────────────────
# 输入归一化
# ─────────────────────────────────────────────────────────────

# 接受的别名 → 标准卦名
_ALIAS_TO_GUA: Dict[str, str] = {}
for _n in GUA_NAME_NUM:
    _ALIAS_TO_GUA[_n] = _n
for _num, _n in GUA_NUM_NAME.items():
    _ALIAS_TO_GUA[str(_num)] = _n
for _dir, _num in DIR_GUA_NUM.items():
    _ALIAS_TO_GUA[_dir] = GUA_NUM_NAME[_num]
# 方位别名
_ALIAS_TO_GUA.update({
    "正北": "坎", "正南": "离", "正东": "震", "正西": "兑",
    "东北方": "艮", "西北方": "乾", "西南方": "坤", "东南方": "巽",
})


def _to_gua_name(value: str) -> Optional[str]:
    """把卦名/方位/洛书数等输入归一化为标准卦名（坎坤震巽乾兑艮离）。"""
    if value is None:
        return None
    v = str(value).strip()
    return _ALIAS_TO_GUA.get(v)


# ── 二十四山 → 卦 + 三元龙（地/天/人元）──
# 顺序：壬子癸 丑艮寅 甲卯乙 辰巽巳 丙午丁 未坤申 庚酉辛 戌乾亥
TWENTY_FOUR_SHAN: Dict[str, Dict[str, str]] = {}
_SHAN_SEQ = [
    ("壬", "坎", "地"), ("子", "坎", "天"), ("癸", "坎", "人"),
    ("丑", "艮", "地"), ("艮", "艮", "天"), ("寅", "艮", "人"),
    ("甲", "震", "地"), ("卯", "震", "天"), ("乙", "震", "人"),
    ("辰", "巽", "地"), ("巽", "巽", "天"), ("巳", "巽", "人"),
    ("丙", "离", "地"), ("午", "离", "天"), ("丁", "离", "人"),
    ("未", "坤", "地"), ("坤", "坤", "天"), ("申", "坤", "人"),
    ("庚", "兑", "地"), ("酉", "兑", "天"), ("辛", "兑", "人"),
    ("戌", "乾", "地"), ("乾", "乾", "天"), ("亥", "乾", "人"),
]
for _i, (_shan, _gua, _yuan) in enumerate(_SHAN_SEQ):
    TWENTY_FOUR_SHAN[_shan] = {"gua": _gua, "yuan": _yuan, "idx": _i}


def parse_door(value: str) -> Dict[str, Any]:
    """
    解析门向输入：支持八卦名、八方位、二十四山名、洛书数。
    返回 {gua, shan?, yuan?}。二十四山可辨三元龙、供兼向判断。
    """
    v = str(value).strip()
    if v in TWENTY_FOUR_SHAN:
        info = TWENTY_FOUR_SHAN[v]
        return {"gua": info["gua"], "shan": v, "yuan": info["yuan"]}
    g = _to_gua_name(v)
    return {"gua": g, "shan": None, "yuan": None} if g else {"gua": None}


def _younian_between(from_gua: str, to_gua: str) -> str:
    """以 from_gua 起伏位，翻卦数到 to_gua，返回游年星。"""
    from_num = GUA_NAME_NUM[from_gua]
    to_dir = GUA_NUM_DIR[GUA_NAME_NUM[to_gua]]
    return EIGHT_MANSION[from_num][to_dir]


def _group(gua: str) -> str:
    return "东四" if GUA_NAME_NUM[gua] in EAST_FOUR_HOUSE else "西四"


def _gua_brief(gua: str) -> Dict[str, str]:
    return {
        "gua": gua,
        "direction": GUA_NUM_DIR[GUA_NAME_NUM[gua]],
        "wuxing": GUA_WUXING[gua],
        "group": _group(gua) + "卦",
        "person": GUA_PERSON[gua],
    }


def _relation(from_gua: str, to_gua: str, label: str) -> Dict[str, Any]:
    """构造一对关系（门→主 / 主→灶 / 门→灶）的完整断语。"""
    star = _younian_between(from_gua, to_gua)
    info = YOUNIAN_STAR[star]
    is_ji = star in JI_STARS
    return {
        "label": label,
        "from": from_gua,
        "to": to_gua,
        "younian": star,
        "jiuxing": info["jiuxing"],
        "star_wuxing": info["wuxing"],
        "level": info["level"],
        "quality": "吉" if is_ji else "凶",
        "is_auspicious": is_ji,
        "judgment": f"{from_gua}{('门' if label.startswith('门') else '主')}配{to_gua}"
                    f"{('主' if '主' in label.split('→')[1] else '灶')}"
                    f"得【{star}·{info['jiuxing']}】（{info['level']}）：{info['duan']}",
    }


# ─────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────

def analyze_yangzhai_sanyao(
    men: str,
    zhu: str,
    zao: str,
    zao_facing: Optional[str] = None,
) -> Dict[str, Any]:
    """
    《阳宅三要》门主灶三要综合断。

    参数
    ----
    men        : 大门所在卦/方位（坎坤震巽乾兑艮离 或 北南东西…）
    zhu        : 主房所在卦/方位
    zao        : 灶位所在卦/方位
    zao_facing : 灶口所向卦/方位（可选，吉者灶口宜向本命/本宅之吉方）

    返回
    ----
    完整三要分析：宅型、门主/主灶/门灶三关系、东西四纯杂、总断、调整建议。
    """
    # ── 门向精解：二十四山 + 三元龙 + 兼向（门支持24山名）──
    door_info = parse_door(men)
    men_g = door_info.get("gua")
    zhu_g = _to_gua_name(zhu)
    zao_g = _to_gua_name(zao)
    if not (men_g and zhu_g and zao_g):
        bad = [n for n, ok in [("门", men_g), ("主", zhu_g), ("灶", zao_g)]
               if not ok]
        return {"success": False,
                "error": f"无法识别{'/'.join(bad)}的卦位（请输入八卦、八方位或二十四山名）"}

    door_shan = door_info.get("shan")
    door_yuan = door_info.get("yuan")
    jian_note = ""
    if door_shan and door_yuan in ("地", "人"):
        jian_note = (f"门立{door_shan}山（{door_yuan}元龙），属偏向；"
                     f"立向宜清纯，过三度则兼{('左' if door_yuan=='地' else '右')}邻卦，气杂主驳。")

    # ── 宅型：阳宅三要以【门】分东西四宅 ──
    house_group = _group(men_g)
    house_type = f"{men_g}门·{house_group}宅"
    if door_shan:
        house_type = f"{door_shan}山{men_g}门·{house_group}宅"

    # ── 八宅宅型总论 ──
    from core.fengshui.yangzhai_data import (
        get_menzhu_ju, get_house_overview, get_zao_full, get_star_full,
    )
    house_overview = get_house_overview(men_g)

    # ── 三组关系 ──
    men_zhu = _relation(men_g, zhu_g, "门→主")
    zhu_zao = _relation(zhu_g, zao_g, "主→灶")
    men_zao = _relation(men_g, zao_g, "门→灶")

    # ── 门主局详断（《阳宅三要》64 局断语库）──
    menzhu_detail = get_menzhu_ju(men_g, zhu_g)

    # ── 灶完整断（512 局之灶环）：灶座(主灶+门灶) + 灶口向 ──
    zao_mouth_star = ""
    zao_facing_g = _to_gua_name(zao_facing) if zao_facing else None
    if zao_facing_g:
        zao_mouth_star = _younian_between(men_g, zao_facing_g)  # 门→灶口向 游年
    zao_detail = get_zao_full(men_zao["younian"], zhu_zao["younian"], zao_mouth_star)

    # ── 东西四纯杂 ──
    groups = {_group(men_g), _group(zhu_g), _group(zao_g)}
    is_pure = (len(groups) == 1)
    purity = {
        "pure": is_pure,
        "men_group": _group(men_g) + "卦",
        "zhu_group": _group(zhu_g) + "卦",
        "zao_group": _group(zao_g) + "卦",
        "desc": ("门主灶三者同属" + _group(men_g) + "卦，宅气纯一，吉"
                 if is_pure else
                 "门主灶东西四卦驳杂，气场混乱，主家宅不宁、损丁破财"),
    }

    # ── 总断评分 ──
    # 门主为重（权重 3），主灶次之（权重 2），门灶参考（权重 1），纯杂加减
    def _score(rel):  # 吉星正分、凶星负分，按级别加权
        lvl = rel["level"]
        base = {"上吉": 3, "中吉": 2, "小吉": 1,
                "次凶": -2, "大凶": -3}.get(lvl, 0)
        return base

    raw = _score(men_zhu) * 3 + _score(zhu_zao) * 2 + _score(men_zao) * 1
    raw += 4 if is_pure else -4
    # 归一到 0-100
    score = max(0, min(100, round(50 + raw * 2.6)))

    if score >= 80 and men_zhu["is_auspicious"] and zhu_zao["is_auspicious"] and is_pure:
        grade, verdict = "上吉之宅", "门主相得、主灶相生、东西四纯一，三要俱吉，主丁财两旺、家道昌隆。"
    elif score >= 65 and men_zhu["is_auspicious"]:
        grade, verdict = "次吉之宅", "门主为吉，根基尚稳；惟主灶或纯杂略有瑕疵，宜微调灶位以全其吉。"
    elif score >= 45:
        grade, verdict = "平常之宅", "三要吉凶参半，平稳无大起落，须以调整灶位、化解凶方求进。"
    elif men_zhu["younian"] == "绝命" or zhu_zao["younian"] == "绝命":
        grade, verdict = "大凶之宅", "门主或主灶犯【绝命·破军】，最忌；主重病损丁，宜亟改门、移主或迁灶。"
    else:
        grade, verdict = "凶宅", "门主灶配卦驳杂或多犯凶星，主是非破财、疾病不宁，须重点改灶、化煞。"

    # ── 调整建议 ──
    advice: List[str] = []
    if not men_zhu["is_auspicious"]:
        # 找门的吉方供安主
        good_dirs = [GUA_NUM_NAME[GUA_NAME_NUM[g]]
                     for g in GUA_NAME_NUM
                     if _younian_between(men_g, g) in ("生气", "天医", "延年")]
        good_pos = "、".join(
            f"{g}({GUA_NUM_DIR[GUA_NAME_NUM[g]]}方·{_younian_between(men_g, g)})"
            for g in good_dirs)
        advice.append(f"门主犯【{men_zhu['younian']}】不吉：主房宜移至{men_g}门之吉方——{good_pos}。")
    if not zhu_zao["is_auspicious"]:
        good_dirs = [g for g in GUA_NAME_NUM
                     if _younian_between(zhu_g, g) in ("生气", "天医", "延年")]
        good_pos = "、".join(
            f"{g}({GUA_NUM_DIR[GUA_NAME_NUM[g]]}方·{_younian_between(zhu_g, g)})"
            for g in good_dirs)
        advice.append(f"主灶犯【{zhu_zao['younian']}】不吉：灶位宜移至主房之吉方——{good_pos}；"
                      f"灶乃养命之源，尤忌坐凶方。")
    if not is_pure:
        advice.append("东西四驳杂：以门定宅，主、灶宜尽量收归与门同组之卦位（"
                      + ("东四卦：坎北/离南/震东/巽东南" if house_group == "东四"
                         else "西四卦：乾西北/坤西南/艮东北/兑西") + "）。")
    if zao_facing:
        zf = _to_gua_name(zao_facing)
        if zf:
            face_star = _younian_between(men_g, zf)
            ok = face_star in JI_STARS
            advice.append(
                f"灶口向{zf}（{GUA_NUM_DIR[GUA_NAME_NUM[zf]]}方）："
                f"相对门得【{face_star}】，{'吉，灶口纳吉气' if ok else '凶，灶口宜改向门之吉方纳生气/天医'}。")
    if not advice:
        advice.append("三要俱合，维持现局即可；可于生气方（"
                      + f"{[GUA_NUM_NAME[GUA_NAME_NUM[g]] + GUA_NUM_DIR[GUA_NAME_NUM[g]] for g in GUA_NAME_NUM if _younian_between(men_g, g) == '生气'][0]}"
                      + "）安主卧、书房以助旺。")

    return {
        "success": True,
        "method": "《阳宅三要》门主灶大游年断法（含二十四山门向 · 64门主局 · 灶座灶口）",
        "house_type": house_type,
        "house_group": house_group + "卦宅",
        "house_overview": house_overview,
        "door_detail": {
            "shan": door_shan, "yuan": door_yuan, "jian_note": jian_note,
        },
        "men": _gua_brief(men_g),
        "zhu": _gua_brief(zhu_g),
        "zao": _gua_brief(zao_g),
        "relations": {
            "men_zhu": men_zhu,
            "zhu_zao": zhu_zao,
            "men_zao": men_zao,
        },
        "menzhu_ju": menzhu_detail,
        "zao_ju": zao_detail,
        "purity": purity,
        "score": score,
        "grade": grade,
        "verdict": verdict,
        "advice": advice,
        "star_reference": YOUNIAN_STAR,
    }


def get_best_layout(men: str) -> Dict[str, Any]:
    """给定门卦，列出该门的八方游年（供布主、布灶择吉）。"""
    men_g = _to_gua_name(men)
    if not men_g:
        return {"success": False, "error": "无法识别门卦"}
    rows = []
    for g in GUA_NAME_NUM:
        star = _younian_between(men_g, g)
        info = YOUNIAN_STAR[star]
        rows.append({
            "gua": g,
            "direction": GUA_NUM_DIR[GUA_NAME_NUM[g]],
            "group": _group(g) + "卦",
            "younian": star,
            "jiuxing": info["jiuxing"],
            "level": info["level"],
            "is_auspicious": star in JI_STARS,
            "use": SECTOR_QUALITY.get(star, {}).get("advice", ""),
        })
    rows.sort(key=lambda r: {"上吉": 0, "中吉": 1, "小吉": 2,
                             "次凶": 3, "大凶": 4}.get(r["level"], 9))
    return {"success": True, "men": men_g,
            "men_group": _group(men_g) + "卦宅", "layout": rows}


def synthesize_full_judgment(men: str, zhu: str, zao: str,
                             zao_facing: Optional[str] = None,
                             floor: Optional[int] = None,
                             jin: Optional[int] = None,
                             liushi: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    512 门主灶局·整局成文断（可选附楼层五行、穿宫九星、六事安置）。
    将门主局、灶座、灶口、东西四纯杂熔为一段连贯断语，并给整局定名、定级。

    liushi : 可选六事安置 {"井":"巽","厕":"艮",...}，附《阳宅十书·论六事》断。
    """
    base = analyze_yangzhai_sanyao(men, zhu, zao, zao_facing=zao_facing)
    if not base.get("success"):
        return base

    mz = base["menzhu_ju"]
    zao_ju = base["zao_ju"]
    men_g, zhu_g, zao_g = base["men"]["gua"], base["zhu"]["gua"], base["zao"]["gua"]
    zhu_zao_star = base["relations"]["zhu_zao"]["younian"]
    men_zao_star = base["relations"]["men_zao"]["younian"]

    # 整局定名：门X主Y灶Z
    ju_name = f"{men_g}门{zhu_g}主{zao_g}灶局"

    # 整局成文：门主→灶→纯杂→总评，连贯叙述
    seg = []
    seg.append(f"此{ju_name}，{base['house_type']}。")
    seg.append(f"门主一节，{mz.get('ming', '')}：{mz.get('zong', '')}"
               f"人丁则{mz.get('ding', '')}财禄则{mz.get('cai', '')}")
    seg.append(f"灶座一节，灶居{zao_g}（主灶得{zhu_zao_star}、门灶得{men_zao_star}）："
               f"{ZAO_SEAT_DESC(zhu_zao_star)}")
    if zao_facing:
        zf = _to_gua_name(zao_facing)
        if zf:
            mouth_star = _younian_between(men_g, zf)
            from core.fengshui.yangzhai_data import ZAO_MOUTH
            seg.append(f"灶口向{zf}，对门得{mouth_star}：{ZAO_MOUTH.get(mouth_star, {}).get('d', '')}")
    seg.append(("三者东西四纯一，气脉清贞；" if base["purity"]["pure"]
                else "三者东西四驳杂，气脉混淆；") + base["verdict"])

    full_text = "".join(seg)

    # 整局定级：综合门主级 + 灶座级
    lvl_map = {"上吉": 3, "中吉": 2, "小吉": 1, "平": 0, "次凶": -2, "大凶": -3}
    mz_lvl = lvl_map.get(mz.get("level", "平"), 0)
    zao_lvl = zao_ju.get("seat_level", 0)
    pure_adj = 1 if base["purity"]["pure"] else -1
    total = mz_lvl * 2 + zao_lvl + pure_adj
    if total >= 6:
        ju_grade = "上上局"
    elif total >= 3:
        ju_grade = "上吉局"
    elif total >= 1:
        ju_grade = "次吉局"
    elif total >= -1:
        ju_grade = "平常局"
    elif total >= -4:
        ju_grade = "凶局"
    else:
        ju_grade = "大凶局"

    base["full_ju"] = {
        "ju_name": ju_name,
        "ju_grade": ju_grade,
        "full_text": full_text,
    }

    # ── 可选：楼层五行 + 穿宫九星 ──
    if floor is not None or jin is not None:
        from core.fengshui.yangzhai_floors import (
            analyze_floor, best_floors, chuangong_jiuxing,
        )
        if floor is not None:
            base["floor"] = analyze_floor(men_g, int(floor))
        base["floor_guide"] = best_floors(men_g)
        if jin is not None:
            base["chuangong"] = chuangong_jiuxing(men_g, int(jin))

    # ── 可选：六事安置（《阳宅十书·论六事》）──
    from core.fengshui.yangzhai_liushi import liushi_best_positions, analyze_liushi
    base["liushi_guide"] = liushi_best_positions(men_g)
    if liushi:
        base["liushi"] = analyze_liushi(men_g, liushi)
    return base


def ZAO_SEAT_DESC(star: str) -> str:
    from core.fengshui.yangzhai_data import ZAO_SEAT
    return ZAO_SEAT.get(star, {}).get("d", "")
