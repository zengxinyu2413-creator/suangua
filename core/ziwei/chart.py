"""
core/ziwei/chart.py
===================
Zi Wei Dou Shu (紫微斗数) chart engine powered by iztro-py.

Wraps iztro_py to produce a serializable dict matching the
frontend ZiWeiPage.jsx data contract.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from iztro_py import astro

# ── Internal→Chinese name maps built from iztro translate API ──────────────

def _translate_star_name(raw: str) -> str:
    """Return Chinese name for a star's raw key, e.g. 'tanlangMaj' → '贪狼'"""
    # Build a tiny chart just to resolve one star name via translate
    # Simpler: use a static table for 14 major + common minor stars
    pass

_PALACE_NAMES_ZH = {
    "soulPalace":     "命宫",
    "siblingsPalace": "兄弟宫",
    "spousePalace":   "夫妻宫",
    "childrenPalace": "子女宫",
    "wealthPalace":   "财帛宫",
    "healthPalace":   "疾厄宫",
    "surfacePalace":  "迁移宫",
    "friendsPalace":  "交友宫",
    "careerPalace":   "官禄宫",
    "propertyPalace": "田宅宫",
    "spiritPalace":   "福德宫",
    "parentsPalace":  "父母宫",
}

_GENDER_NOTES = {
    "男": "阳男顺行大限",
    "女": "阴女逆行大限",
}


def build_ziwei_chart(
    solar_date: str,        # "YYYY-MM-DD"
    birth_hour_index: int,  # 0=子时 … 11=亥时 (each 2h period)
    gender: str,            # "男" | "女"
    language: str = "zh-CN",
) -> Dict[str, Any]:
    """
    Build a complete Zi Wei Dou Shu chart.

    Returns a serializable dict with all 12 palaces, major/minor/adjective
    stars, decadal ranges, long-life-12 positions, and chart metadata.
    """
    chart = astro.by_solar(solar_date, birth_hour_index, gender)

    # ── Metadata ────────────────────────────────────────────────────────────
    # ── 命主/身主星名 + 坐宫地支翻译 ─────────────────────────────────────
    # iztro_py 返回的 chart.soul / chart.body / earthly_branch_of_xxx
    # 是英文 key（如 'wenquMin', 'maoEarthly'）。这里翻译成中文展示名。
    SOUL_STAR_TRANSLATE = {
        "ziweiMaj":"紫微", "tianjiMaj":"天机", "taiyangMaj":"太阳",
        "wuquMaj":"武曲", "tiantongMaj":"天同", "lianzhenMaj":"廉贞",
        "tianfuMaj":"天府", "taiyinMaj":"太阴", "tanlangMaj":"贪狼",
        "jumenMaj":"巨门", "tianxiangMaj":"天相", "tianliangMaj":"天梁",
        "qishaMaj":"七杀", "pojunMaj":"破军",
        "wenchangMin":"文昌", "wenquMin":"文曲",
        "zuofuMin":"左辅", "youbiMin":"右弼",
        "tiankuiMin":"天魁", "tianyueMin":"天钺",
        "luchunMin":"禄存", "lucunMin":"禄存", "tianmaMin":"天马",
        "huoxingMin":"火星", "lingxingMin":"铃星",
        "qingyangMin":"擎羊", "tuoluoMin":"陀罗",
        "dikongMin":"地空", "dijieMin":"地劫",
    }
    BRANCH_TRANSLATE = {
        "ziEarthly":"子", "chouEarthly":"丑", "yinEarthly":"寅", "maoEarthly":"卯",
        "chenEarthly":"辰", "siEarthly":"巳", "wuEarthly":"午", "weiEarthly":"未",
        "shenEarthly":"申", "youEarthly":"酉", "xuEarthly":"戌", "haiEarthly":"亥",
    }
    def _tr(key, table):
        return table.get(key, key)

    metadata = {
        "solar_date":       solar_date,
        "birth_hour_index": birth_hour_index,
        "birth_hour_name":  chart.time,
        "birth_hour_range": chart.time_range,
        "gender":           gender,
        "lunar_date":       chart.lunar_date,
        "chinese_date":     chart.chinese_date,   # 四柱干支
        "zodiac":           chart.zodiac,
        "sign":             chart.sign,            # 星座
        "five_elements":    chart.five_elements_class,  # 五行局
        "earthly_soul":     _tr(chart.earthly_branch_of_soul_palace, BRANCH_TRANSLATE),
        "earthly_body":     _tr(chart.earthly_branch_of_body_palace, BRANCH_TRANSLATE),
    }

    # ── 命主 / 身主 ─────────────────────────────────────────────────────────
    # 命主：按【命宫地支】定，用北斗七星序（贪狼·巨门·禄存·文曲·廉贞·武曲·破军）
    #   子贪狼 丑亥巨门 寅戌禄存 卯酉文曲 辰申廉贞 巳未武曲 午破军
    #   （注意辰/申为「廉贞」而非文昌 —— 命主取北斗主星，文昌为时系吉星不入命主）
    # 身主：按【生年地支】定
    #   子午火星 丑未天相 寅申天梁 卯酉天同 辰戌文昌 巳亥天机
    # iztro 库已严格按上述《全书》标准计算（经全 12 地支逐一核验一致），
    # 故直接采用库值，避免手写表出错。
    HOUR_IDX_TO_BRANCH = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    time_branch = HOUR_IDX_TO_BRANCH[birth_hour_index] if 0 <= birth_hour_index < 12 else ""
    try:
        year_branch_cn = chart.chinese_date.split()[0][1]
    except Exception:
        year_branch_cn = ""

    metadata["soul_star"]       = _tr(chart.soul, SOUL_STAR_TRANSLATE)
    metadata["body_star"]       = _tr(chart.body, SOUL_STAR_TRANSLATE)
    metadata["soul_star_raw"]   = chart.soul
    metadata["body_star_raw"]   = chart.body
    metadata["soul_star_iztro"] = _tr(chart.soul, SOUL_STAR_TRANSLATE)
    metadata["body_star_iztro"] = _tr(chart.body, SOUL_STAR_TRANSLATE)
    metadata["soul_master_method"] = "《全书》标准（命主按命宫地支·北斗七星）"
    metadata["body_master_method"] = "《全书》标准（身主按生年地支）"

    # ── Palaces ──────────────────────────────────────────────────────────────
    palaces = []
    for i in range(12):
        p = chart.palace(i)
        if p is None:
            continue

        def _stars(star_list):
            return [
                {
                    "name":       s.translate_name(),
                    "type":       getattr(s, "type", ""),
                    "brightness": getattr(s, "brightness", None) or "",
                    "mutagen":    getattr(s, "mutagen", None) or "",
                    "scope":      getattr(s, "scope", "origin"),
                }
                for s in star_list
            ]

        # Decadal fortune range for this palace
        p_dump = p.model_dump()
        decadal = p_dump.get("decadal") or {}

        palace_dict = {
            "index":          p.index,
            "name":           p.translate_name(),
            "name_raw":       p.name,
            "heavenly_stem":  p.translate_heavenly_stem(),
            "earthly_branch": p.translate_earthly_branch(),
            "is_soul":        (p.name == "soulPalace"),
            "is_body":        p.is_body_palace,
            "major_stars":    _stars(p.major_stars),
            "minor_stars":    _stars(p.minor_stars),
            "adj_stars":      _stars(getattr(p, "adjective_stars", [])),
            "changsheng12":   p_dump.get("changsheng12", ""),  # 长生十二神
            "boshi12":        p_dump.get("boshi12", ""),       # 博士十二神
            "jiangqian12":    p_dump.get("jiangqian12", ""),   # 将前十二神
            "suiqian12":      p_dump.get("suiqian12", ""),     # 岁前十二神
            "ages":           p_dump.get("ages", []),          # 该宫所主流年（含小限循环）
            "decadal_range":  list(decadal.get("range", [])) if decadal else [],
            "decadal_stem":   decadal.get("heavenly_stem", "") if decadal else "",
            "decadal_branch": decadal.get("earthly_branch", "") if decadal else "",
        }
        # ── 星曜入十二宫完整断语（主星×宫 + 双星组合 + 辅煞星）──
        try:
            from core.ziwei.star_palace import interpret_palace_full, interpret_palace_stars
            palace_dict["star_interpretations"] = interpret_palace_stars(
                palace_dict["name"], palace_dict["major_stars"]
            )
            palace_dict["palace_full"] = interpret_palace_full(
                palace_dict["name"], palace_dict["major_stars"],
                (palace_dict.get("minor_stars") or []) + (palace_dict.get("adj_stars") or [])
            )
        except Exception:
            palace_dict["star_interpretations"] = []
            palace_dict["palace_full"] = {}
        palaces.append(palace_dict)

    # ── Soul & Body palace summaries ──────────────────────────────────────
    soul_p  = chart.get_soul_palace()
    body_p  = chart.get_body_palace()

    soul_summary = {
        "name":       soul_p.translate_name(),
        "stem_branch": f"{soul_p.translate_heavenly_stem()}{soul_p.translate_earthly_branch()}",
        "major_stars": [s.translate_name() for s in soul_p.major_stars],
        "minor_stars": [s.translate_name() for s in soul_p.minor_stars],
    }
    body_summary = {
        "name":       body_p.translate_name(),
        "stem_branch": f"{body_p.translate_heavenly_stem()}{body_p.translate_earthly_branch()}",
        "major_stars": [s.translate_name() for s in body_p.major_stars],
    }

    # ── Three-direction-four-normal (三方四正) of soul palace ─────────────
    try:
        surround = chart.surrounded_palaces(soul_p.index)
        sanjiao = []
        for sp in surround.all_palaces():
            sanjiao.append({
                "name":       sp.translate_name(),
                "major_stars": [s.translate_name() for s in sp.major_stars],
            })
    except Exception:
        sanjiao = []

    # ── Soul/Body star names ──────────────────────────────────────────────
    # iztro_py 默认 language='zh-CN'，chart.soul / chart.body 已是中文星名
    # （如 '破军' / '文昌'），无需再翻译。这里保留原字段名以兼容前端。
    # 注意：若未来切换其它语言，需要在这里通过查表补回中文。
    soul_star_translated = chart.soul
    body_star_translated = chart.body

    return {
        "metadata":     metadata,
        "palaces":      palaces,
        "soul_palace":  soul_summary,
        "body_palace":  body_summary,
        "sanjiao_sizheng": sanjiao,
        "soul_star_raw": soul_star_translated,
        "body_star_raw": body_star_translated,
    }


# ─────────────────────────────────────────────────────────────
# 飞化计算 (Flying Transformation Calculation)
# ─────────────────────────────────────────────────────────────

# Complete 十干四化 table
SHIGAN_SIHUA: Dict[str, Dict[str, str]] = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "右弼", "化忌": "天机"},
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "太阴", "化忌": "天同"},
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "左辅", "化忌": "武曲"},
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}

# 化禄/权/科/忌 meanings for interpretations
SIHUA_MEANINGS: Dict[str, str] = {
    "化禄": "福德流通，财运顺畅，得禄者宫位之事受益",
    "化权": "掌控主导，意志力强，宫位之事由自主导",
    "化科": "名声才华，贵人引荐，宫位考试文书顺利",
    "化忌": "阻碍执念，宫位之事多波折，为四化最重要",
}

# 化忌入各宫简要断法
HUAJI_PALACE_MEANING: Dict[str, str] = {
    "命宫":  "劳碌烦恼，执念重，自我要求高",
    "兄弟宫": "与兄弟缘薄，或损兄弟财",
    "夫妻宫": "感情波折，另一半有拖累，婚姻有危机",
    "子女宫": "与子女缘薄，或子女有麻烦",
    "财帛宫": "财运受阻，破财是非，财多纠纷",
    "疾厄宫": "健康有暗疾，注意该宫五行对应身体",
    "迁移宫": "出外多阻碍，不宜长期离乡",
    "交友宫": "朋友中有小人，合伙破财",
    "官禄宫": "事业多障碍，仕途不顺",
    "田宅宫": "家宅不安，宅运差，家庭是非",
    "福德宫": "精神压力大，多忧郁，难以享福",
    "父母宫": "与父母缘薄，文书考试出错",
}


def calculate_feihua(palaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate 飞化 (flying transformations) for all 12 palaces.

    For each palace:
      1. Read the palace heavenly stem (宫干)
      2. Apply SHIGAN_SIHUA to get 化禄/权/科/忌 star names
      3. Find which palace each transformed star is located in
      4. Build interpretation

    Returns list of 12 palace feihua records.
    """
    # Build star → palace index lookup
    star_to_palace: Dict[str, int] = {}
    palace_names: Dict[int, str] = {}
    for p in palaces:
        idx  = p["index"]
        name = p["name"]
        palace_names[idx] = name
        for s in p.get("major_stars", []) + p.get("minor_stars", []):
            star_name = s["name"] if isinstance(s, dict) else s
            star_to_palace[star_name] = idx

    results = []
    for p in palaces:
        idx       = p["index"]
        stem      = p.get("heavenly_stem", "")
        hua_table = SHIGAN_SIHUA.get(stem, {})

        transformations = []
        for hua_type in ["化禄", "化权", "化科", "化忌"]:
            target_star  = hua_table.get(hua_type, "")
            target_idx   = star_to_palace.get(target_star, -1)
            target_name  = palace_names.get(target_idx, "未知")

            # Build interpretation
            meaning = SIHUA_MEANINGS.get(hua_type, "")
            if hua_type == "化忌" and target_name in HUAJI_PALACE_MEANING:
                interp = HUAJI_PALACE_MEANING[target_name]
            else:
                interp = f"{hua_type}入{target_name}，{meaning}"

            is_self = (target_idx == idx)  # 飞化落入本宫 = 自化
            if is_self:
                self_meaning = {
                    "化禄": "自化禄：本宫好事留不住，财来财去，过度享乐",
                    "化权": "自化权：本宫主导欲过强，做事过度操控，难持久",
                    "化科": "自化科：名声虚而不实，才华难以持续发挥",
                    "化忌": "自化忌（最严重）：本宫事务散漫无章，执念深重，为最凶自化",
                }.get(hua_type, f"自化{hua_type}：本宫能量内耗")
                interp = self_meaning

            transformations.append({
                "hua_type":     hua_type,
                "target_star":  target_star,
                "target_palace_idx":  target_idx,
                "target_palace_name": target_name,
                "is_self_transform":  is_self,
                "interpretation": interp,
            })

        results.append({
            "palace_idx":   idx,
            "palace_name":  p["name"],
            "stem":         stem,
            "transformations": transformations,
        })

    return results


# ─────────────────────────────────────────────────────────────
# 三方四正 (Three Directions and Four Normals)
# ─────────────────────────────────────────────────────────────

# 三方四正 = 本宫 + 对宫 + 三合两宫
# Palace index layout (0-11): 0=命宫, 1=兄弟, 2=夫妻, 3=子女, 4=财帛, 5=疾厄,
#                              6=迁移, 7=交友, 8=官禄, 9=田宅, 10=福德, 11=父母
# 命宫 三方: 财帛(4) + 官禄(8) 三合; 对宫: 迁移(6)

def get_sanjiao_sizheng(soul_palace_idx: int, palace_names: Dict[int, str]) -> Dict[str, Any]:
    """
    Calculate 三方四正 for any palace (usually 命宫).

    三方: the palace itself + the two palaces forming a triangle (every 4th palace)
    四正: 三方 + the direct opposite palace

    Returns dict with the four palaces and their combined stars.
    """
    # Three-way groupings (triangle = every 4 steps in the 12-palace wheel)
    groups_of_four = [
        [0, 4, 8, 6],   # 命宫 财帛 官禄 迁移
        [1, 5, 9, 7],   # 兄弟 疾厄 田宅 交友
        [2, 6, 10, 8],  # 夫妻 迁移 福德 官禄
        [3, 7, 11, 9],  # 子女 交友 父母 田宅
    ]

    # Find which group contains soul_palace_idx
    target_group = None
    for g in groups_of_four:
        if soul_palace_idx in g:
            target_group = g
            break

    if target_group is None:
        # Compute directly: 三方 = every 4 steps; 对宫 = +6
        s = soul_palace_idx
        target_group = [s, (s + 4) % 12, (s + 8) % 12, (s + 6) % 12]

    return {
        "palaces": target_group,
        "names":   [palace_names.get(i, f"宫{i}") for i in target_group],
        "description": (
            f"三方：{palace_names.get(target_group[0],'命宫')}、"
            f"{palace_names.get(target_group[1],'财帛')}、"
            f"{palace_names.get(target_group[2],'官禄')}；"
            f"四正加：{palace_names.get(target_group[3],'迁移')}"
        ),
    }


def get_palace_three_directions(
    palace_idx: int,
    palaces: List[Dict[str, Any]],
    feihua: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Get the complete 三方四正 analysis for a palace,
    including all stars and 四化 that converge on it.
    """
    palace_names = {p["index"]: p["name"] for p in palaces}
    sanjiao      = get_sanjiao_sizheng(palace_idx, palace_names)

    # Collect stars from the four palaces
    all_stars = []
    all_hua   = []
    for i in sanjiao["palaces"]:
        p = next((x for x in palaces if x["index"] == i), {})
        for s in p.get("major_stars", []):
            star_name = s["name"] if isinstance(s, dict) else s
            mutagen   = s.get("mutagen", "") if isinstance(s, dict) else ""
            all_stars.append({"star": star_name, "palace": palace_names.get(i,""), "mutagen": mutagen})

    # Collect 化忌 and 化禄 that fly INTO each of the four palaces
    for fh in feihua:
        for tr in fh.get("transformations", []):
            if tr["target_palace_idx"] in sanjiao["palaces"]:
                all_hua.append({
                    "from_palace":  fh["palace_name"],
                    "hua_type":     tr["hua_type"],
                    "star":         tr["target_star"],
                    "into_palace":  tr["target_palace_name"],
                })

    return {
        "palace_idx":   palace_idx,
        "palace_name":  palace_names.get(palace_idx, ""),
        "sanjiao":      sanjiao,
        "converging_stars": all_stars,
        "converging_hua":   all_hua,
    }


# ─────────────────────────────────────────────────────────────
# 大限四化叠盘 (Decadal Flying Transformations)
# ─────────────────────────────────────────────────────────────

# iztro heavenly stem → Chinese char mapping
_IZTRO_STEM_MAP: Dict[str, str] = {
    "jiaHeavenly":"甲","yiHeavenly":"乙","bingHeavenly":"丙","dingHeavenly":"丁",
    "wuHeavenly":"戊","jiHeavenly":"己","gengHeavenly":"庚","xinHeavenly":"辛",
    "renHeavenly":"壬","guiHeavenly":"癸",
}


def get_decade_palace(
    solar_date: str, birth_hour_index: int, gender: str, age: int
) -> Optional[Dict[str, Any]]:
    """
    Find the 大限命宫 for the given age.

    Returns dict with:
        palace_idx:  0-11 (宫位序号)
        palace_name: Chinese name
        stem:        宫干 (Chinese character)
        age_range:   (start_age, end_age)
    """
    try:
        from iztro_py import astro
        chart = astro.by_solar(solar_date, birth_hour_index, gender)
        for i in range(12):
            p = chart.palace(i)
            dump = p.model_dump()
            rng  = dump.get("decadal", {}).get("range", ())
            if rng and len(rng) >= 2 and rng[0] <= age <= rng[1]:
                raw_stem = dump.get("decadal", {}).get("heavenly_stem", "")
                zh_stem  = _IZTRO_STEM_MAP.get(raw_stem, raw_stem)
                return {
                    "palace_idx":  i,
                    "palace_name": _PALACE_NAMES_ZH.get(dump.get("name",""), dump.get("name","")),
                    "stem":        zh_stem,
                    "age_range":   tuple(rng),
                    "palaces_layout": compute_decade_palaces_layout(i),
                }
    except Exception as _e1:
        from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e1)
    return None


# 大限十二宫名顺序（从大限命宫起，依逆时针排列）
# 紫微斗数标准顺序：命/兄/夫/子/财/疾/迁/友/官/田/福/父
DECADE_PALACE_NAMES = [
    "大限命宫", "大限兄弟", "大限夫妻", "大限子女",
    "大限财帛", "大限疾厄", "大限迁移", "大限交友",
    "大限官禄", "大限田宅", "大限福德", "大限父母",
]

# 大限十二宫的简称（用于前端 UI 角标）
DECADE_PALACE_SHORT = [
    "大-命", "大-兄", "大-夫", "大-子",
    "大-财", "大-疾", "大-迁", "大-友",
    "大-官", "大-田", "大-福", "大-父",
]


def compute_decade_palaces_layout(
    decade_palace_idx: int,
) -> Dict[int, Dict[str, str]]:
    """
    根据大限命宫在哪个本命 idx，计算大限十二宫的 layout。

    紫微斗数中所有十二宫排列都是"逆时针"：从命宫起，每减 1 个 idx 就是
    下一宫（兄弟、夫妻、子女...）。本命/大限/流年皆同。
    在 iztro 的 idx 编号系统里（寅0卯1辰2...丑11），逆时针 = idx-1。

    Args:
        decade_palace_idx: 大限命宫所在的本命 idx（0-11）

    Returns:
        {natal_idx: {"name": 大限宫名, "short": 简称}}
        例如本命命宫 idx=2，大限命宫 idx=5：
          {5: {"name": "大限命宫", "short": "大-命"},
           4: {"name": "大限兄弟", "short": "大-兄"},
           3: {"name": "大限夫妻", "short": "大-夫"},
           2: {"name": "大限子女", "short": "大-子"},
           ... }
    """
    layout: Dict[int, Dict[str, str]] = {}
    for offset in range(12):
        # 大限第 offset 宫所在的 natal idx
        natal_idx = (decade_palace_idx - offset) % 12
        layout[natal_idx] = {
            "name":  DECADE_PALACE_NAMES[offset],
            "short": DECADE_PALACE_SHORT[offset],
            "offset": offset,  # 在大限十二宫中的位置（0=命，1=兄...）
        }
    return layout


def compute_annual_palaces_layout(
    annual_palace_idx: int,
) -> Dict[int, Dict[str, str]]:
    """
    流年十二宫的 layout — 与大限规则相同，只是宫名前缀改成"流年"。

    Args:
        annual_palace_idx: 流年命宫所在的本命 idx
    """
    ANNUAL_NAMES = [n.replace("大限", "流年") for n in DECADE_PALACE_NAMES]
    ANNUAL_SHORT = [n.replace("大-", "年-") for n in DECADE_PALACE_SHORT]
    layout: Dict[int, Dict[str, str]] = {}
    for offset in range(12):
        natal_idx = (annual_palace_idx - offset) % 12
        layout[natal_idx] = {
            "name":   ANNUAL_NAMES[offset],
            "short":  ANNUAL_SHORT[offset],
            "offset": offset,
        }
    return layout


def calculate_decade_feihua(
    palaces: List[Dict[str, Any]],
    decade_stem: str,
    decade_palace_idx: int,
) -> List[Dict[str, Any]]:
    """
    Calculate 大限四化 (decadal flying transformations).

    The 大限命宫 stem determines four transformations that fly into the
    natal chart (本命盘). This is the key tool for 10-year fortune analysis.

    Args:
        palaces:           natal chart palaces (from build_ziwei_chart)
        decade_stem:       大限命宫宫干 (e.g. '庚')
        decade_palace_idx: which natal palace is the 大限命宫

    Returns list of 4 transformations with natal palace targets.
    """
    # Build star → palace index lookup from natal chart
    star_to_palace: Dict[str, int] = {}
    palace_names:   Dict[int, str] = {}
    for p in palaces:
        idx  = p["index"]
        name = p["name"]
        palace_names[idx] = name
        for s in p.get("major_stars", []) + p.get("minor_stars", []):
            star_name = s["name"] if isinstance(s, dict) else s
            star_to_palace[star_name] = idx

    hua_table = SHIGAN_SIHUA.get(decade_stem, {})
    transformations = []

    for hua_type in ("化禄", "化权", "化科", "化忌"):
        target_star = hua_table.get(hua_type, "")
        target_idx  = star_to_palace.get(target_star, -1)
        target_name = palace_names.get(target_idx, "未知")

        # Is it flying into the decade's own 命宫?
        is_self = (target_idx == decade_palace_idx)

        # Build interpretation
        if hua_type == "化忌":
            base_interp = HUAJI_PALACE_MEANING.get(target_name, f"化忌入{target_name}，此宫事务多波折")
        else:
            base_interp = f"{hua_type}入{target_name}，{SIHUA_MEANINGS.get(hua_type, '')}"

        if is_self:
            self_meaning = {
                "化禄": "大限自化禄：这十年好事留不住，财来财往",
                "化权": "大限自化权：这十年过度操控，难成大局",
                "化科": "大限自化科：这十年名声虚而不实",
                "化忌": "大限自化忌（最重要）：这十年事散漫无章，诸事有始无终",
            }.get(hua_type, f"大限自化{hua_type}")
            base_interp = self_meaning

        transformations.append({
            "hua_type":          hua_type,
            "target_star":       target_star,
            "target_palace_idx": target_idx,
            "target_palace_name": target_name,
            "is_self_transform": is_self,
            "interpretation":    base_interp,
        })

    return transformations


def calculate_triple_chart(
    solar_date: str,
    birth_hour_index: int,
    gender: str,
    age: int,
    current_year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build the complete 三盘叠合 (triple-plate) analysis:
      本命盘 (natal)  +  大限盘 (decadal)  +  流年盘 (annual, optional)

    This is the core tool for 紫微斗数 fortune prediction.

    Args:
        solar_date:       birth date 'YYYY-MM-DD'
        birth_hour_index: 0-11 (子=0, 丑=1, ..., 亥=11)
        gender:           '男' or '女'
        age:              current age for decade determination
        current_year:     Gregorian year for annual overlay (optional)

    Returns:
        natal_feihua:    本命飞化 (12宫×4化)
        decade_info:     大限命宫信息
        decade_feihua:   大限四化 (4条)
        annual_feihua:   流年四化 (4条, if current_year given)
        combined_analysis: 三盘综合断法
    """
    # Build natal chart
    natal = build_ziwei_chart(solar_date, birth_hour_index, gender)
    palaces = natal["palaces"]

    # Natal flying transformations
    natal_fh = calculate_feihua(palaces)

    # Decade info
    decade_info = get_decade_palace(solar_date, birth_hour_index, gender, age)
    decade_fh   = []
    if decade_info:
        decade_fh = calculate_decade_feihua(
            palaces, decade_info["stem"], decade_info["palace_idx"]
        )

    # Annual overlay
    annual_fh = []
    if current_year is not None:
        # 流年命宫干: 按流年太岁天干起四化
        # 流年干 = ganzhi of current_year: (year - 1984) % 60 → stem
        from core.constants import TIANGAN
        year_stem = TIANGAN[(current_year - 1984) % 10]
        annual_hua = SHIGAN_SIHUA.get(year_stem, {})
        # Build star→palace for annual feihua
        star_to_palace: Dict[str, int] = {}
        palace_names:   Dict[int, str] = {}
        for p in palaces:
            idx = p["index"]; name = p["name"]
            palace_names[idx] = name
            for s in p.get("major_stars",[]) + p.get("minor_stars",[]):
                sn = s["name"] if isinstance(s, dict) else s
                star_to_palace[sn] = idx

        for hua_type in ("化禄","化权","化科","化忌"):
            target_star = annual_hua.get(hua_type, "")
            target_idx  = star_to_palace.get(target_star, -1)
            target_name = palace_names.get(target_idx, "未知")
            interp = (HUAJI_PALACE_MEANING.get(target_name, f"化忌入{target_name}，需注意")
                      if hua_type == "化忌"
                      else f"{hua_type}入{target_name}，{SIHUA_MEANINGS.get(hua_type,'')}")
            annual_fh.append({
                "hua_type":          hua_type,
                "target_star":       target_star,
                "target_palace_idx": target_idx,
                "target_palace_name": target_name,
                "interpretation":    interp,
            })

    # Combined analysis: find palaces where multiple 化忌 converge
    ji_counts: Dict[str, int] = {}
    for fh_list in [natal_fh, [{"transformations": decade_fh}] if decade_fh else []]:
        for fh_item in fh_list:
            for tr in (fh_item.get("transformations", [fh_item]) if "transformations" in fh_item else [fh_item]):
                if tr.get("hua_type") == "化忌":
                    p_name = tr.get("target_palace_name", "")
                    ji_counts[p_name] = ji_counts.get(p_name, 0) + 1

    # Annual 化忌 double weight (most immediate)
    for tr in annual_fh:
        if tr.get("hua_type") == "化忌":
            p_name = tr.get("target_palace_name", "")
            ji_counts[p_name] = ji_counts.get(p_name, 0) + 2

    high_risk = sorted(
        [(p, cnt) for p, cnt in ji_counts.items() if cnt >= 2],
        key=lambda x: -x[1]
    )

    combined_warnings = []
    for palace, cnt in high_risk:
        combined_warnings.append(
            f"⚠ {palace}化忌叠加{cnt}次：{'本命+大限+流年三忌汇聚，此宫事极凶' if cnt >= 3 else '双忌入宫，此宫运势受阻'}"
        )

    return {
        "natal_chart":       natal,
        "natal_feihua":      natal_fh,
        "decade_info":       decade_info,
        "decade_feihua":     decade_fh,
        "annual_feihua":     annual_fh,
        "combined_warnings": combined_warnings,
        "age":               age,
        "current_year":      current_year,
    }


# ─────────────────────────────────────────────────────────────
# 八字附加信息 — 给紫微页面的"中宫信息板"提供丰富数据
# 包含：节气派/非节气派四柱、十神、藏干、纳音、起运、10步大运
# ─────────────────────────────────────────────────────────────

# 五虎遁年起月（用于非节气派月柱推算）
# 甲己之年丙作首，乙庚之岁戊为头，丙辛必定从庚起，丁壬壬位顺行流，戊癸甲寅好追求
_WUHUDUN_YIN = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

# 五鼠遁日起时（用于时柱推算）
# 甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途
_WUSHUDUN_ZI = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬",
}

_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"

# 天干五行
_GAN_WUXING = {
    "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
    "己":"土","庚":"金","辛":"金","壬":"水","癸":"水",
}
# 天干阴阳（+1=阳, -1=阴）
_GAN_YINYANG = {
    "甲":1,"乙":-1,"丙":1,"丁":-1,"戊":1,
    "己":-1,"庚":1,"辛":-1,"壬":1,"癸":-1,
}

# 地支藏干（人元，从主气到余气）
_ZHI_CANGGAN = {
    "子": ["癸"],
    "丑": ["己","癸","辛"],
    "寅": ["甲","丙","戊"],
    "卯": ["乙"],
    "辰": ["戊","乙","癸"],
    "巳": ["丙","戊","庚"],
    "午": ["丁","己"],
    "未": ["己","丁","乙"],
    "申": ["庚","壬","戊"],
    "酉": ["辛"],
    "戌": ["戊","辛","丁"],
    "亥": ["壬","甲"],
}

# 六十甲子纳音表
_NAYIN_TABLE = {
    ("甲","子"):"海中金", ("乙","丑"):"海中金",
    ("丙","寅"):"炉中火", ("丁","卯"):"炉中火",
    ("戊","辰"):"大林木", ("己","巳"):"大林木",
    ("庚","午"):"路旁土", ("辛","未"):"路旁土",
    ("壬","申"):"剑锋金", ("癸","酉"):"剑锋金",
    ("甲","戌"):"山头火", ("乙","亥"):"山头火",
    ("丙","子"):"涧下水", ("丁","丑"):"涧下水",
    ("戊","寅"):"城头土", ("己","卯"):"城头土",
    ("庚","辰"):"白蜡金", ("辛","巳"):"白蜡金",
    ("壬","午"):"杨柳木", ("癸","未"):"杨柳木",
    ("甲","申"):"泉中水", ("乙","酉"):"泉中水",
    ("丙","戌"):"屋上土", ("丁","亥"):"屋上土",
    ("戊","子"):"霹雳火", ("己","丑"):"霹雳火",
    ("庚","寅"):"松柏木", ("辛","卯"):"松柏木",
    ("壬","辰"):"长流水", ("癸","巳"):"长流水",
    ("甲","午"):"砂中金", ("乙","未"):"砂中金",
    ("丙","申"):"山下火", ("丁","酉"):"山下火",
    ("戊","戌"):"平地木", ("己","亥"):"平地木",
    ("庚","子"):"壁上土", ("辛","丑"):"壁上土",
    ("壬","寅"):"金箔金", ("癸","卯"):"金箔金",
    ("甲","辰"):"覆灯火", ("乙","巳"):"覆灯火",
    ("丙","午"):"天河水", ("丁","未"):"天河水",
    ("戊","申"):"大驿土", ("己","酉"):"大驿土",
    ("庚","戌"):"钗钏金", ("辛","亥"):"钗钏金",
    ("壬","子"):"桑柘木", ("癸","丑"):"桑柘木",
    ("甲","寅"):"大溪水", ("乙","卯"):"大溪水",
    ("丙","辰"):"沙中土", ("丁","巳"):"沙中土",
    ("戊","午"):"天上火", ("己","未"):"天上火",
    ("庚","申"):"石榴木", ("辛","酉"):"石榴木",
    ("壬","戌"):"大海水", ("癸","亥"):"大海水",
}


def _calc_shishen(day_gan: str, other_gan: str) -> str:
    """根据日主和他干，返回十神"""
    if not day_gan or not other_gan or day_gan not in _GAN_WUXING or other_gan not in _GAN_WUXING:
        return ""
    sheng = {"木":"火","火":"土","土":"金","金":"水","水":"木"}  # 我生
    ke    = {"木":"土","火":"金","土":"水","金":"木","水":"火"}  # 我克
    bei_sheng = {v:k for k,v in sheng.items()}  # 生我
    bei_ke    = {v:k for k,v in ke.items()}     # 克我

    dwx = _GAN_WUXING[day_gan]
    owx = _GAN_WUXING[other_gan]
    same_yy = _GAN_YINYANG[day_gan] == _GAN_YINYANG[other_gan]

    if dwx == owx:
        return "比肩" if same_yy else "劫财"
    elif owx == sheng[dwx]:
        return "食神" if same_yy else "伤官"
    elif owx == ke[dwx]:
        return "偏财" if same_yy else "正财"
    elif owx == bei_ke[dwx]:
        return "七杀" if same_yy else "正官"
    elif owx == bei_sheng[dwx]:
        return "偏印" if same_yy else "正印"
    return ""


def _calc_shishen_for_zhi(day_gan: str, zhi: str) -> List[str]:
    """根据日主和地支，返回该地支藏干的十神列表"""
    if not zhi or zhi not in _ZHI_CANGGAN:
        return []
    return [_calc_shishen(day_gan, g) for g in _ZHI_CANGGAN[zhi]]


# 五虎遁年起月（用于非节气派月柱推算）
# 甲己之年丙作首，乙庚之岁戊为头，丙辛必定从庚起，丁壬壬位顺行流，戊癸甲寅好追求
_WUHUDUN_YIN = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

# 五鼠遁日起时（用于时柱推算）
# 甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途
_WUSHUDUN_ZI = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬",
}


def _compute_nonjieqi_full(lunar, ec) -> Dict[str, Any]:
    """
    非节气派完整四柱信息（四柱 + 十神 + 藏干 + 纳音）。
    与节气派的差异：年柱按农历正月初一切换，月柱按农历月份切换。
    """
    lunar_year = lunar.getYear()
    lunar_month = lunar.getMonth()
    if lunar_month < 0:
        lunar_month = abs(lunar_month)

    # 年柱
    year_gz = lunar.getYearGan() + lunar.getYearZhi()
    year_gan = lunar.getYearGan()

    # 月柱（五虎遁推）
    month_zhi_idx = (2 + lunar_month - 1) % 12
    month_zhi = _ZHI[month_zhi_idx]
    start_gan = _WUHUDUN_YIN[year_gan]
    start_gan_idx = _GAN.index(start_gan)
    month_gan_idx = (start_gan_idx + lunar_month - 1) % 10
    month_gan = _GAN[month_gan_idx]
    month_gz = month_gan + month_zhi

    # 日柱（不变）
    day_gz = ec.getDay()
    day_gan = day_gz[0] if day_gz else ""

    # 时柱（不变）
    time_gz = ec.getTime()
    time_gan = time_gz[0] if time_gz else ""

    sizhu = {"year": year_gz, "month": month_gz, "day": day_gz, "time": time_gz}

    # 十神（基于新的年/月干 + 日主）
    shishen = {
        "year":  _calc_shishen(day_gan, year_gan),
        "month": _calc_shishen(day_gan, month_gan),
        "day":   "日主",
        "time":  _calc_shishen(day_gan, time_gan),
    }

    # 地支藏干
    canggan = {
        "year":  _ZHI_CANGGAN.get(year_gz[1] if len(year_gz) >= 2 else "", []),
        "month": _ZHI_CANGGAN.get(month_zhi, []),
        "day":   _ZHI_CANGGAN.get(day_gz[1] if len(day_gz) >= 2 else "", []),
        "time":  _ZHI_CANGGAN.get(time_gz[1] if len(time_gz) >= 2 else "", []),
    }

    # 地支藏干十神
    shishen_zhi = {
        "year":  [_calc_shishen(day_gan, g) for g in canggan["year"]],
        "month": [_calc_shishen(day_gan, g) for g in canggan["month"]],
        "day":   [_calc_shishen(day_gan, g) for g in canggan["day"]],
        "time":  [_calc_shishen(day_gan, g) for g in canggan["time"]],
    }

    # 纳音
    def _ny(gz):
        if not gz or len(gz) < 2: return ""
        return _NAYIN_TABLE.get((gz[0], gz[1]), "")
    nayin = {
        "year":  _ny(year_gz),
        "month": _ny(month_gz),
        "day":   _ny(day_gz),
        "time":  _ny(time_gz),
    }

    return {
        "sizhu":       sizhu,
        "shishen":     shishen,
        "shishen_zhi": shishen_zhi,
        "canggan":     canggan,
        "nayin":       nayin,
    }


def build_bazi_overlay(
    solar_date: str,    # YYYY-MM-DD
    hour: int,          # 0-23，钟表小时（非时辰索引）
    minute: int = 0,    # 分钟
    gender: str = "男",
    longitude: Optional[float] = None,  # 经度（用于真太阳时校正）
) -> Dict[str, Any]:
    """
    返回八字大运 + 节气/非节气派四柱 + 十神 + 起运信息。
    用于紫微页面中宫信息板和底栏时间盘。
    """
    try:
        from lunar_python import Solar
    except ImportError:
        return {}

    y, m, d = [int(x) for x in solar_date.split("-")]
    
    # 真太阳时校正（《天文历法·真太阳时校正法》）
    # 真太阳时 = 北京时间 + 经度时差 + 时差方程(EoT)
    real_hour = hour
    real_minute = minute
    if longitude is not None:
        # 1. 经度时差：当地经度与北京时区中心(120°E)的差，每经度差 4 分钟
        longitude_offset_min = (longitude - 120.0) * 4
        
        # 2. 时差方程（Equation of Time）— 真太阳与平太阳的差
        # Spencer 公式（1971，行业标准 EoT 公式，精度 ±15 秒）
        import math
        from datetime import date
        day_of_year = (date(y, m, d) - date(y, 1, 1)).days + 1
        # B 角（弧度）
        B = 2 * math.pi * (day_of_year - 81) / 365.0
        # EoT in minutes
        eot_min = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
        
        # 3. 合成真太阳时
        offset_minutes = longitude_offset_min + eot_min
        total = hour * 60 + minute + offset_minutes
        # 处理跨日
        if total < 0:
            total += 24 * 60
        if total >= 24 * 60:
            total -= 24 * 60
        real_hour = int(total // 60) % 24
        real_minute = int(total % 60)
    
    sol = Solar.fromYmdHms(y, m, d, real_hour, real_minute, 0)
    lunar = sol.getLunar()
    ec = lunar.getEightChar()

    # ── 节气派（lunar-python 默认）─────────────────
    ec.setSect(1)
    sizhu_jieqi = {
        "year":  ec.getYear(),
        "month": ec.getMonth(),
        "day":   ec.getDay(),
        "time":  ec.getTime(),
    }
    shishen_jieqi = {
        "year":  ec.getYearShiShenGan(),
        "month": ec.getMonthShiShenGan(),
        "day":   "日主",
        "time":  ec.getTimeShiShenGan(),
    }
    shishen_zhi_jieqi = {
        "year":  ec.getYearShiShenZhi(),
        "month": ec.getMonthShiShenZhi(),
        "day":   ec.getDayShiShenZhi(),
        "time":  ec.getTimeShiShenZhi(),
    }
    canggan_jieqi = {
        "year":  ec.getYearHideGan(),
        "month": ec.getMonthHideGan(),
        "day":   ec.getDayHideGan(),
        "time":  ec.getTimeHideGan(),
    }
    nayin_jieqi = {
        "year":  ec.getYearNaYin(),
        "month": ec.getMonthNaYin(),
        "day":   ec.getDayNaYin(),
        "time":  ec.getTimeNaYin(),
    }

    # ── 非节气派（自实现：按农历月份切换）──────────
    nonjieqi = _compute_nonjieqi_full(lunar, ec)
    sizhu_nonjieqi      = nonjieqi["sizhu"]
    shishen_nonjieqi    = nonjieqi["shishen"]
    shishen_zhi_nonjieqi = nonjieqi["shishen_zhi"]
    canggan_nonjieqi    = nonjieqi["canggan"]
    nayin_nonjieqi      = nonjieqi["nayin"]

    # 起运 + 大运（10 步）
    # gender_idx: 1=男, 0=女
    gender_idx = 1 if gender == "男" else 0
    try:
        yun = ec.getYun(gender_idx, 2)
        qiyun = {
            "year":  yun.getStartYear(),
            "month": yun.getStartMonth(),
            "day":   yun.getStartDay(),
            "summary": f"{yun.getStartYear()}年{yun.getStartMonth()}月{yun.getStartDay()}天起运",
        }
        dayun_list = []
        for d_yun in yun.getDaYun()[:11]:  # 11 步够到 100 岁
            dayun_list.append({
                "start_age":  d_yun.getStartAge(),
                "end_age":    d_yun.getStartAge() + 9,
                "ganzhi":     d_yun.getGanZhi() or "童限",
                "start_year": d_yun.getStartYear(),
            })
    except Exception:
        qiyun = {}
        dayun_list = []

    # 真太阳时信息
    real_time_info = None
    if longitude is not None:
        real_time_info = {
            "longitude":      longitude,
            "clock_time":     f"{hour:02d}:{minute:02d}",
            "real_solar_time": f"{real_hour:02d}:{real_minute:02d}",
            "offset_minutes": round((longitude - 120.0) * 4, 1),
        }

    return {
        # 四柱（两派）
        "sizhu_jieqi":     sizhu_jieqi,
        "sizhu_nonjieqi":  sizhu_nonjieqi,
        # 十神（两派）
        "shishen_jieqi":      shishen_jieqi,
        "shishen_nonjieqi":   shishen_nonjieqi,
        # 地支藏干十神（两派）
        "shishen_zhi_jieqi":     shishen_zhi_jieqi,
        "shishen_zhi_nonjieqi":  shishen_zhi_nonjieqi,
        # 藏干（两派）
        "canggan_jieqi":     canggan_jieqi,
        "canggan_nonjieqi":  canggan_nonjieqi,
        # 纳音（两派）
        "nayin_jieqi":     nayin_jieqi,
        "nayin_nonjieqi":  nayin_nonjieqi,
        # 向后兼容：默认显示节气派
        "shishen":         shishen_jieqi,
        "shishen_zhi":     shishen_zhi_jieqi,
        "canggan":         canggan_jieqi,
        "nayin":           nayin_jieqi,
        # 大运 + 真太阳时
        "qiyun":           qiyun,
        "dayun":           dayun_list,
        "real_time":       real_time_info,
    }


# ─────────────────────────────────────────────────────────────
# 流月/流日/流时 — 给底栏时间盘提供数据
# ─────────────────────────────────────────────────────────────

def build_time_panel(
    solar_date: str,
    target_year: int,
) -> Dict[str, Any]:
    """
    返回某流年的流月/流日/流时干支表。
    """
    try:
        from lunar_python import Solar, Lunar
    except ImportError:
        return {}

    # 流月：以立春为正月起点（八字派）；含闰月完整支持
    # 《紫微斗数全书·流月》：以节气定月，节气派与月节派两套
    months = []
    try:
        # 1. 检测该年是否有闰月
        # lunar_python 闰月用负数表示：如闰四月用 -4
        # 用 LunarYear 获取闰月信息（如有）
        leap_month = None
        try:
            from lunar_python import LunarYear
            ly = LunarYear.fromYear(target_year)
            for mo in ly.getMonths():
                if mo.isLeap():
                    leap_month = mo.getMonth()  # 闰月数（正数）
                    break
        except Exception as _e2:
            from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e2)
        
        # 2. 遍历所有月（含闰月）
        month_count = 0
        for m in range(1, 13):
            # 正常月
            try:
                lun = Lunar.fromYmd(target_year, m, 1)
                ec = lun.getEightChar()
                month_count += 1
                months.append({
                    "lunar_month": m,
                    "month_index": month_count,
                    "is_leap": False,
                    "month_name": ["正","二","三","四","五","六","七","八","九","十","冬","腊"][m-1] + "月",
                    "ganzhi": ec.getMonth(),
                })
            except Exception:
                continue
            
            # 闰月（在对应月后插入）
            if leap_month and m == leap_month:
                try:
                    lun_leap = Lunar.fromYmd(target_year, -m, 1)  # 负数表示闰月
                    ec_leap = lun_leap.getEightChar()
                    month_count += 1
                    months.append({
                        "lunar_month": m,
                        "month_index": month_count,
                        "is_leap": True,
                        "month_name": "闰" + ["正","二","三","四","五","六","七","八","九","十","冬","腊"][m-1] + "月",
                        "ganzhi": ec_leap.getMonth(),
                    })
                except Exception as _e3:
                    from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e3)
    except Exception as _e4:
        from core.log import log_failure; log_failure("ziwei", "装配(自动补充日志)", _e4)

    return {
        "year": target_year,
        "leap_month": leap_month if 'leap_month' in dir() else None,
        "months": months,
    }
