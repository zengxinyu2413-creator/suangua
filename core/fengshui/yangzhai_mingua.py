"""
core/fengshui/yangzhai_mingua.py
================================
阳宅·命卦匹配（人宅相配 — 八宅明镜之命根）。

原阳宅三要只断「门主灶」内部和谐与东西四纯度，却不问「此宅是否配主人命卦」。
然《八宅明镜》之核心正在「东四命住东四宅、西四命住西四宅」，及门、主、灶是否
落于主人之四吉方（生气·天医·延年·伏位）抑或四凶方（绝命·五鬼·六煞·祸害）。
本模块补此命根：据生年性别定主人命卦，配宅卦、并断门主灶各落主人游年之吉凶。
"""
from __future__ import annotations
from typing import Dict, Any, Optional

from core.fengshui.calculator import calculate_ming_gua, get_ming_gua_group
from core.fengshui.yangzhai_sanyao import _younian_between, YOUNIAN_STAR, JI_STARS, XIONG_STARS

# 命卦数字 → 卦名（5 寄坤/艮，依性别已在 calculate_ming_gua 处理，此处兜底寄坤）
_NUM_GUA = {1: "坎", 2: "坤", 3: "震", 4: "巽", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
_EAST4 = {"坎", "离", "震", "巽"}


def _pos_younian(ming_gua_name: str, pos_gua: str) -> Dict[str, str]:
    if not pos_gua or not ming_gua_name:
        return {}
    star = _younian_between(ming_gua_name, pos_gua)
    info = YOUNIAN_STAR.get(star, {})
    return {
        "younian": star,
        "jiuxing": info.get("jiuxing", ""),
        "level": info.get("level", ""),
        "ji_xiong": "吉" if star in JI_STARS else ("凶" if star in XIONG_STARS else "平"),
    }


def analyze_mingua_match(men: Dict[str, Any], zhu: Dict[str, Any], zao: Dict[str, Any],
                         birth_year: Optional[int], gender: Optional[str]) -> Dict[str, Any]:
    if not birth_year:
        return {"available": False}

    g = (gender or "male").lower()
    g = "male" if g in ("male", "男", "m", "1") else "female"
    num = calculate_ming_gua(birth_year, g)
    ming_gua = _NUM_GUA.get(num, "坤")
    ming_group = get_ming_gua_group(num)            # 东四命/西四命
    ming_dong = ming_gua in _EAST4

    house_group = men.get("group", "")              # 东四卦/西四卦（以门卦定宅）
    house_dong = "东四" in house_group

    compatible = (ming_dong == house_dong)

    men_yn = _pos_younian(ming_gua, men.get("gua", ""))
    zhu_yn = _pos_younian(ming_gua, zhu.get("gua", ""))
    zao_yn = _pos_younian(ming_gua, zao.get("gua", ""))

    n_ji = sum(1 for x in (men_yn, zhu_yn, zao_yn) if x.get("ji_xiong") == "吉")
    n_xiong = sum(1 for x in (men_yn, zhu_yn, zao_yn) if x.get("ji_xiong") == "凶")

    # 综合人宅契合
    if compatible and n_xiong == 0:
        match_level, match_q = "人宅大吉", "吉"
        summary = (f"主人{ming_gua}命（{ming_group}），此为{house_group.replace('卦','宅')}，"
                   f"命宅同类相得；门主灶皆不落凶方，乃人宅相配之上吉。")
    elif compatible:
        match_level, match_q = "人宅相配", "吉"
        summary = (f"主人{ming_gua}命（{ming_group}）配{house_group.replace('卦','宅')}，命宅相得；"
                   f"然门主灶中有 {n_xiong} 处落主人凶方，宜微调以避之。")
    elif n_ji >= 2:
        match_level, match_q = "宅不配命·门主尚可", "中"
        summary = (f"主人{ming_gua}命（{ming_group}）与{house_group.replace('卦','宅')}本不同类，"
                   f"然门主灶尚有 {n_ji} 处落主人吉方，可补不配之失，须重在吉方起居。")
    else:
        match_level, match_q = "人宅不配", "凶"
        summary = (f"主人{ming_gua}命（{ming_group}）住{house_group.replace('卦','宅')}，"
                   f"东西四命宅相违，又门主灶多落凶方；《八宅明镜》忌之，宜另择合命之宅或重调门主灶。")

    return {
        "available": True,
        "ming_gua": ming_gua,
        "ming_num": num,
        "ming_group": ming_group,
        "house_group": house_group,
        "compatible": compatible,
        "match_level": match_level,
        "match_quality": match_q,
        "men_younian": men_yn,
        "zhu_younian": zhu_yn,
        "zao_younian": zao_yn,
        "ji_count": n_ji,
        "xiong_count": n_xiong,
        "summary": summary,
        "classical": "《八宅明镜》：东四命住东四宅，西四命住西四宅，同类相得则吉；门、主、灶宜居本命四吉方（生气、天医、延年、伏位），忌居四凶方（绝命、五鬼、六煞、祸害）。",
    }
