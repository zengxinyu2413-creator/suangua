"""奇门用神落宫断语合成器
————————————————————————————————————————————————————————————
将用神所落之宫的「门 × 星 × 神 × 旺衰 × 神煞」断料，按所测之事(topic)
合成多维具体断语（得地/门应/星助/神应/神煞/综合），使用神之断由泛论
（仅principle）深化到阳宅三要级之多维断语。

数据全部取自排盘已富集之宫层字段（door_yi/door_ji/door_detail/star_detail/
deity_detail/door_nature/star_nature/deity_nature/gong_wx/sd_rel），
不另造数据，只作组合与对口判断。
"""
from typing import Dict, Any, List, Optional

# 用神五行（门/星/神）——与 analyzer 同源
_MEN_WX = {"开门": "金", "惊门": "金", "休门": "水", "生门": "土",
           "死门": "土", "伤门": "木", "杜门": "木", "景门": "火"}
_XING_WX = {"天蓬": "水", "天芮": "土", "天冲": "木", "天辅": "木", "天禽": "土",
            "天心": "金", "天柱": "金", "天任": "土", "天英": "火"}
_WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 各用事所喜之门（对口则吉、相左则力减）
_TOPIC_FIT_DOOR = {
    "求财": ("生门", "开门"), "事业": ("开门", "生门"), "出行": ("开门", "生门", "休门"),
    "婚姻": ("休门", "生门"), "感情": ("休门", "生门"), "谋事": ("开门", "生门", "休门"),
    "学业": ("景门", "开门"), "健康": ("生门", "休门", "开门"),
}
# 各用事最忌之门
_TOPIC_BAD_DOOR = {
    "求财": ("死门", "伤门"), "事业": ("死门", "伤门"), "出行": ("死门", "惊门"),
    "婚姻": ("死门", "伤门", "绝"), "感情": ("死门", "伤门"), "谋事": ("死门",),
    "学业": ("死门", "伤门"), "健康": ("死门", "伤门", "惊门"),
}


def _wx_relation(a: str, b: str) -> str:
    """a 对 b 之五行关系（a 为用神、b 为宫）。"""
    if not a or not b:
        return ""
    if a == b:
        return "比和"
    if _WX_KE.get(b) == a:
        return "宫克用神"       # 用神受制
    if _WX_SHENG.get(b) == a:
        return "宫生用神"       # 用神得生
    if _WX_KE.get(a) == b:
        return "用神克宫"       # 用神耗力制宫
    if _WX_SHENG.get(a) == b:
        return "用神生宫"       # 用神泄气
    return ""


def synthesize_yongshen_judgment(yong_shen: Dict[str, Any],
                                 yong_palace: Optional[Dict[str, Any]],
                                 topic: str) -> Dict[str, Any]:
    """合成用神落宫多维断语。返回 {dimensions:[{dim,text}], paragraph}。"""
    if not yong_palace:
        return {"dimensions": [], "paragraph": ""}

    door = yong_palace.get("door", "") or ""
    star = yong_palace.get("star", "") or ""
    deity = yong_palace.get("deity", "") or ""
    # 宫五行：优先取字段；为空则由宫位序稳健推定（避「艮宫」vs「艮八宫」键不匹配致空）
    _POS_WX = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火"}
    gong_wx = yong_palace.get("gong_wx", "") or _POS_WX.get(yong_palace.get("position"), "")
    pname = yong_palace.get("palace_name", "")
    door_yi = yong_palace.get("door_yi", []) or []
    door_ji = yong_palace.get("door_ji", []) or []
    door_detail = yong_palace.get("door_detail", "") or ""
    deity_detail = yong_palace.get("deity_detail", "") or ""
    door_nature = yong_palace.get("door_nature", "") or ""
    star_nature = yong_palace.get("star_nature", "") or ""
    sd_rel = yong_palace.get("sd_rel", "") or ""

    dims: List[Dict[str, str]] = []

    # ① 得地（旺衰）：用神门五行 vs 宫五行
    men_wx = _MEN_WX.get(door, "")
    star_wx = _XING_WX.get(star, "")
    use_wx = men_wx or star_wx
    rel = _wx_relation(use_wx, gong_wx)
    if rel:
        _map = {
            "比和": f"用神（{use_wx}）与{pname}（{gong_wx}）比和，得地有气，用神得力。",
            "宫生用神": f"{pname}（{gong_wx}）生用神（{use_wx}），用神得生而旺，气势充盈、主有助力。",
            "用神克宫": f"用神（{use_wx}）克{pname}（{gong_wx}），用神当令制宫，主动可成、得掌主动。",
            "宫克用神": f"{pname}（{gong_wx}）克用神（{use_wx}），用神受制失地，力弱多阻，宜慎。",
            "用神生宫": f"用神（{use_wx}）生{pname}（{gong_wx}），用神泄气，徒耗其力、事倍功半。",
        }
        dims.append({"dim": "得地旺衰", "text": _map.get(rel, "")})

    # ② 门应：用神门是否对口所测之事
    fit = _TOPIC_FIT_DOOR.get(topic, ())
    bad = _TOPIC_BAD_DOOR.get(topic, ())
    if door:
        if any(d in door for d in fit):
            txt = f"用神临{door}（{door_nature or '吉'}），正应所测之{topic}，门户得宜、其事顺遂。"
        elif any(d in door for d in bad):
            txt = f"用神临{door}，于{topic}为忌门，门户相左、其事多阻，强求不利。"
        else:
            _yi = ('、'.join(door_yi[:3])) if door_yi else ""
            txt = f"用神临{door}，主{_yi or door_detail[:18]}，于{topic}非正用，吉凶参半、须察他象。"
        dims.append({"dim": "门户对口", "text": txt})

    # ③ 星助
    if star:
        s_good = "吉" in str(star_nature)
        txt = f"九星得{star}（{star_nature or ''}），" + (
            f"{star}主助，益其事之成。" if s_good else f"{star}非旺助，力有未逮、须借他吉。")
        # 借宫层既有星详
        sdetail = yong_palace.get("star_meaning", "")
        if sdetail:
            txt = f"九星得{star}，主「{sdetail}」，" + ("为吉助。" if s_good else "吉凶相参。")
        dims.append({"dim": "星辰助应", "text": txt})

    # ④ 神应
    if deity:
        dtxt = deity_detail or yong_palace.get("deity_meaning", "")
        dims.append({"dim": "八神临应", "text": f"八神临{deity}，{dtxt[:40] if dtxt else '主其事之机变'}。"})

    # ⑤ 神煞/天地盘关系（击刑·入墓·受制·主客）
    if sd_rel:
        dims.append({"dim": "奇仪神煞", "text": f"奇仪相临——{sd_rel[:60]}"})

    # ⑥ 综合断
    q = yong_shen.get("quality", "平")
    bad_door_hit = any(d in door for d in bad) if door else False
    if q in ("大吉", "吉") and not bad_door_hit:
        head = f"综断：用神落{pname}，门星神三盘相济、用神得力，所测之{topic}吉，宜趋此方此时进取。"
    elif q in ("大凶", "凶") or bad_door_hit:
        head = f"综断：用神落{pname}，门星神有制有阻、用神失地，所测之{topic}多舛，宜守、宜化解或另择吉时方。"
    else:
        head = f"综断：用神落{pname}，吉凶相参、成败在乎人事，所测之{topic}宜谋定后动、趋吉避凶。"

    paragraph = head + "　" + "；".join(d["text"] for d in dims if d.get("text"))
    return {"dimensions": dims, "paragraph": paragraph}
