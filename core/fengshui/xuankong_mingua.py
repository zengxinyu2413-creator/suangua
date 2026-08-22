"""
core/fengshui/xuankong_mingua.py
================================
玄空·命卦人盘（理气 × 命卦 — 玄空纳人盘维度）。

玄空飞星定各方旺衰，本与住人无关；然同一旺方，于东四命之人为吉游年、于西四命
之人或为凶游年。本引擎补玄空之「人盘」：据主人命卦之八宅游年，交叉玄空当运
旺衰方——旺方又逢主人命卦吉方者为「双吉·最宜居用」，旺方却逢命卦凶方者为
「理气旺·于人不利」，俾因人而宜、不徒论理气。
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional

from core.fengshui.calculator import calculate_ming_gua, get_ming_gua_group
from core.fengshui.yangzhai_sanyao import _younian_between, YOUNIAN_STAR, JI_STARS, XIONG_STARS

_NUM_GUA = {1: "坎", 2: "坤", 3: "震", 4: "巽", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
_DIR_GUA = {"北": "坎", "西南": "坤", "东": "震", "东南": "巽",
            "西北": "乾", "西": "兑", "东北": "艮", "南": "离"}
_EAST4 = {"坎", "离", "震", "巽"}
_ALL_DIRS = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]


def analyze_xuankong_mingua(xk: Dict[str, Any], birth_year: Optional[int],
                            gender: Optional[str]) -> Dict[str, Any]:
    if not birth_year:
        return {"available": False}

    g = (gender or "male").lower()
    g = "male" if g in ("male", "男", "m", "1") else "female"
    num = calculate_ming_gua(birth_year, g)
    ming_gua = _NUM_GUA.get(num, "坤")
    ming_group = get_ming_gua_group(num)
    ming_dong = ming_gua in _EAST4

    lt = xk.get("luantou_summary", {}) or {}
    wang = set(lt.get("wang_directions", []) or [])
    shuai = set(lt.get("shuai_directions", []) or [])

    # 每方位：玄空旺衰 × 命卦游年
    dirs: List[Dict[str, Any]] = []
    best_dirs, avoid_dirs = [], []
    for d in _ALL_DIRS:
        dgua = _DIR_GUA.get(d, "")
        star = _younian_between(ming_gua, dgua) if dgua else ""
        info = YOUNIAN_STAR.get(star, {})
        ming_jx = "吉" if star in JI_STARS else ("凶" if star in XIONG_STARS else "平")
        liqi = "旺" if d in wang else ("衰" if d in shuai else "平")

        if liqi == "旺" and ming_jx == "吉":
            comb, cq = "双吉·最宜居用", "吉"
            best_dirs.append(d)
        elif liqi == "衰" and ming_jx == "凶":
            comb, cq = "双凶·切忌", "凶"
            avoid_dirs.append(d)
        elif liqi == "旺" and ming_jx == "凶":
            comb, cq = "理气旺·于人不利", "中"
        elif liqi == "衰" and ming_jx == "吉":
            comb, cq = "命吉·理气衰", "中"
        elif ming_jx == "吉":
            comb, cq = "命卦吉方", "吉"
        elif ming_jx == "凶":
            comb, cq = "命卦凶方", "凶"
        else:
            comb, cq = "平", "平"

        dirs.append({
            "direction": d, "ming_younian": star, "jiuxing": info.get("jiuxing", ""),
            "ming_jx": ming_jx, "liqi": liqi, "combine": comb, "combine_q": cq,
        })

    summary = (f"主人{ming_gua}命（{ming_group}）。"
               + (f"宜居用之方（玄空旺方又命卦吉方）：{('、'.join(best_dirs))}。" if best_dirs else "无玄空旺方与命卦吉方相叠之位，宜取命卦吉方为辅。")
               + (f"切忌之方（玄空衰方又命卦凶方）：{('、'.join(avoid_dirs))}。" if avoid_dirs else ""))

    return {
        "available": True,
        "ming_gua": ming_gua,
        "ming_group": ming_group,
        "directions": dirs,
        "best_dirs": best_dirs,
        "avoid_dirs": avoid_dirs,
        "summary": summary,
        "classical": "《八宅明镜》以命卦定人之四吉四凶方，玄空以三元九运定地之旺衰；二者相叠，旺方又命吉者方为此人之上吉位。",
    }
