"""
core/fengshui/yangzhai_floors.py
================================
阳宅·论层数（楼层五行）与穿宫九星（进深），补全《阳宅三要》《阳宅十书》
"门主灶"之外的层数、进深细节。

一、论层数（楼层五行 · 河图）
   一六共宗水、二七同道火、三八为朋木、四九为友金、五十同途土。
   楼层（取个位）配五行，与宅卦（门卦）五行论生克：
     层生宅 / 层比宅  → 吉（旺宅气）
     宅克层           → 小吉（宅旺克层，可用而略耗层气）
     宅生层           → 平（宅气泄于层，退气）
     层克宅           → 凶（层克宅气，最忌）

二、穿宫九星（进深 · 翻卦穿宫法）
   《阳宅十书·论穿宫九星》："大游年既主方位，又主层数。"
   以大门所在卦起，逐进（重）翻卦排九星：
     进1=伏位，进2起按翻爻顺序 生→祸→五→天→六→延→绝 周流。
   吉星之进（生气/天医/延年/伏位）宜高大宽敞；
   凶星之进（祸害/六煞/五鬼/绝命）宜低矮窄小，以低压凶。
"""
from __future__ import annotations
from typing import Dict, Any, List

from core.fengshui.calculator import EIGHT_MANSION, SECTOR_QUALITY
from core.fengshui.yangzhai_sanyao import (
    GUA_NAME_NUM, GUA_NUM_DIR, GUA_WUXING, _group, _younian_between,
)
from core.constants import WUXING_SHENG, WUXING_KE

# 楼层个位 → 五行（河图）
FLOOR_WUXING: Dict[int, str] = {
    1: "水", 6: "水", 2: "火", 7: "火",
    3: "木", 8: "木", 4: "金", 9: "金",
    5: "土", 0: "土",  # 10/20… 取 0
}


def _wx_relation(layer_wx: str, house_wx: str) -> Dict[str, str]:
    """层五行 vs 宅五行 生克关系。"""
    if layer_wx == house_wx:
        return {"rel": "比和", "q": "吉", "desc": "层宅同气，比和助旺，吉"}
    if WUXING_SHENG.get(layer_wx) == house_wx:
        return {"rel": "层生宅", "q": "吉", "desc": "楼层之气生助宅卦，旺宅，大吉"}
    if WUXING_KE.get(house_wx) == layer_wx:
        return {"rel": "宅克层", "q": "小吉", "desc": "宅旺克层，可用而略耗层气，小吉"}
    if WUXING_SHENG.get(house_wx) == layer_wx:
        return {"rel": "宅生层", "q": "平", "desc": "宅气泄于层，退气，平平"}
    if WUXING_KE.get(layer_wx) == house_wx:
        return {"rel": "层克宅", "q": "凶", "desc": "楼层之气克制宅卦，损宅气，凶"}
    return {"rel": "无", "q": "平", "desc": "无明显生克"}


def analyze_floor(men_gua: str, floor: int) -> Dict[str, Any]:
    """
    论某楼层对此宅（门卦）之吉凶（楼层五行生克）。
    floor: 楼层数（1,2,3…）。
    """
    house_wx = GUA_WUXING.get(men_gua, "")
    if not house_wx or floor < 1:
        return {"success": False, "error": "门卦或楼层无效"}
    unit = floor % 10
    layer_wx = FLOOR_WUXING.get(unit, "")
    rel = _wx_relation(layer_wx, house_wx)
    return {
        "success": True,
        "floor": floor,
        "floor_wuxing": layer_wx,
        "house_gua": men_gua,
        "house_wuxing": house_wx,
        "relation": rel["rel"],
        "quality": rel["q"],
        "desc": f"第{floor}层属{layer_wx}（{'一六水二七火三八木四九金五十土'}），"
                f"{men_gua}宅属{house_wx}：{rel['desc']}。",
    }


def best_floors(men_gua: str, max_floor: int = 33) -> Dict[str, Any]:
    """列出对此宅最吉/最凶的楼层（1..max_floor）。"""
    house_wx = GUA_WUXING.get(men_gua, "")
    if not house_wx:
        return {"success": False, "error": "门卦无效"}
    ji, xiong = [], []
    for f in range(1, max_floor + 1):
        r = analyze_floor(men_gua, f)
        if r["quality"] == "吉":
            ji.append(f)
        elif r["quality"] == "凶":
            xiong.append(f)
    return {
        "success": True, "house_gua": men_gua, "house_wuxing": house_wx,
        "best_floors": ji, "worst_floors": xiong,
        "desc": f"{men_gua}宅属{house_wx}，宜居{'/'.join(map(str, ji[:6]))}…层（旺宅），"
                f"忌居{'/'.join(map(str, xiong[:6]))}…层（克宅）。",
    }


# 穿宫九星：以门卦起，逐进翻卦的九星顺序
# 翻爻穿宫序（自门伏位起，依次往内进）：伏→生→祸→五→天→六→延→绝
# 该序对应门卦在八方的游年，按"进深"周流取用。
_CHUANGONG_ORDER = ["伏位", "生气", "祸害", "五鬼", "天医", "六煞", "延年", "绝命"]
_JI_STARS = {"生气", "天医", "延年", "伏位"}


def chuangong_jiuxing(men_gua: str, jin_count: int = 5) -> Dict[str, Any]:
    """
    穿宫九星：自大门起，逐进（重/层）排九星，论高低进深。
    jin_count: 房屋进数（前后几重）。
    """
    if men_gua not in GUA_NAME_NUM or jin_count < 1:
        return {"success": False, "error": "门卦或进数无效"}
    rows: List[Dict[str, Any]] = []
    for i in range(jin_count):
        star = _CHUANGONG_ORDER[i % 8]
        is_ji = star in _JI_STARS
        q = SECTOR_QUALITY.get(star, {})
        rows.append({
            "jin": i + 1,
            "star": star,
            "is_auspicious": is_ji,
            "quality": q.get("quality", "吉" if is_ji else "凶"),
            "advice": (f"第{i+1}进属【{star}】（{q.get('quality', '')}）："
                       + ("此进宜高大宽敞、为厅堂正房，主受旺气。"
                          if is_ji else
                          "此进宜低矮窄小、作偏房杂用，以低压凶气，忌高大。")),
        })
    return {
        "success": True, "men": men_gua, "jin_count": jin_count,
        "method": "《阳宅十书·论穿宫九星》翻卦穿宫法",
        "rows": rows,
        "note": "吉星之进宜高大（受旺）、凶星之进宜低矮（压煞）；"
                "若宜高者反低、宜低者反高，则吉变凶。",
    }
