"""
tests/test_ziwei_star_palace.py
紫微·十四主星入十二宫断语库测试
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ziwei.star_palace import (
    STAR_INFO, STAR_PALACE, PALACES_12,
    get_star_palace, interpret_palace_stars, BRIGHTNESS_MODIFIER,
)

STARS_14 = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
            "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"]


def test_14_stars_info():
    assert len(STAR_INFO) == 14
    for s in STARS_14:
        info = STAR_INFO[s]
        assert info["wuxing"] and info["dou"] and info["zhu"] and len(info["nature"]) >= 20


def test_168_complete():
    """14主星 × 12宫 = 168 条，无缺失，每条有实质内容。"""
    assert len(STAR_PALACE) == 168
    for s in STARS_14:
        for p in PALACES_12:
            duan = get_star_palace(s, p)
            assert duan, f"{s}入{p} 断语缺失"
            assert len(duan) >= 20, f"{s}入{p} 断语过短"


def test_no_ascii_contamination():
    """断语不应混入英文单词。"""
    import re
    for (s, p), v in STAR_PALACE.items():
        assert not re.search(r"[A-Za-z]{3,}", v), f"{s}入{p} 含英文: {v}"


def test_brightness_modifier():
    assert set(BRIGHTNESS_MODIFIER) >= {"庙", "旺", "得", "利", "平", "陷"}


def test_interpret_palace():
    """解读某宫主星（含庙旺）。"""
    stars = [{"name": "武曲", "brightness": "得"}, {"name": "天府", "brightness": "庙"}]
    out = interpret_palace_stars("命宫", stars)
    assert len(out) == 2
    assert out[0]["star"] == "武曲" and out[0]["duan"]
    assert out[1]["star"] == "天府" and out[1]["brightness_tone"] == "吉性大显"
    # 非主星忽略
    out2 = interpret_palace_stars("命宫", [{"name": "文昌", "brightness": "庙"}])
    assert out2 == []


def test_chart_integration():
    """排盘每宫附 star_interpretations。"""
    from core.ziwei.chart import build_ziwei_chart
    r = build_ziwei_chart("1990-06-15", 6, "男")
    soul = next(p for p in r["palaces"] if p["is_soul"])
    assert "star_interpretations" in soul
    if soul["major_stars"]:
        assert len(soul["star_interpretations"]) >= 1
        assert soul["star_interpretations"][0]["duan"]


def test_double_stars():
    """24 双星组合：皆为主星对、断语充实、对称可取。"""
    from core.ziwei.star_palace import DOUBLE_STARS, get_double_star, STAR_INFO
    assert len(DOUBLE_STARS) == 24
    maj = set(STAR_INFO)
    for k, v in DOUBLE_STARS.items():
        assert set(k) <= maj and len(set(k)) == 2
        assert v["ming"] and len(v["duan"]) >= 40
    # 对称
    assert get_double_star("武曲", "天府")["ming"] == get_double_star("天府", "武曲")["ming"]
    assert get_double_star("紫微", "七杀")["ming"] == "紫微七杀·化杀为权"


def test_aux_stars_168():
    """辅煞星 + 杂曜 × 12 宫落宫断，每星每宫无缺失。"""
    from core.ziwei.star_palace import AUX_STAR_INFO, AUX_STAR_PALACE, PALACES_12, get_aux_star
    # 六吉六煞禄存天马（14）+ 杂曜（红鸾天喜天姚天刑孤辰寡宿华盖龙池凤阁…）
    assert len(AUX_STAR_INFO) >= 48
    assert len(AUX_STAR_PALACE) == len(AUX_STAR_INFO) * 12
    core14 = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "天马",
              "火星", "铃星", "擎羊", "陀罗", "地空", "地劫"}
    zayao = {"红鸾", "天喜", "天姚", "天刑", "孤辰", "寡宿", "华盖", "龙池", "凤阁"}
    assert core14.issubset(AUX_STAR_INFO.keys())
    assert zayao.issubset(AUX_STAR_INFO.keys())
    for s in AUX_STAR_INFO:
        for p in PALACES_12:
            assert get_aux_star(s, p), f"{s}入{p}缺"


def test_zayao_palace_differential():
    """杂曜落宫断真随宫变（同星不同宫断语不同），非通用占位。"""
    from core.ziwei.star_palace import get_aux_star
    for star in ("红鸾", "天刑", "孤辰", "华盖", "天姚"):
        duans = {get_aux_star(star, p) for p in ("命宫", "夫妻", "疾厄", "官禄", "田宅")}
        assert len(duans) >= 4, f"{star} 落宫断雷同"


def test_zayao_surfaces_in_chart():
    """杂曜落宫断接入命盘 palace_full.aux（adj_stars 亦纳入）。"""
    from core.ziwei.chart import build_ziwei_chart
    from core.ziwei.star_palace import AUX_STAR_INFO
    core14 = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "天马",
              "火星", "铃星", "擎羊", "陀罗", "地空", "地劫"}
    found_zayao = False
    for hi in range(0, 12, 2):
        ch = build_ziwei_chart("1988-08-08", hi, "男")
        for p in ch["palaces"]:
            for a in (p.get("palace_full", {}) or {}).get("aux", []):
                if a["star"] in AUX_STAR_INFO and a["star"] not in core14 and a.get("effect"):
                    found_zayao = True
    assert found_zayao


def test_palace_full():
    """统一宫位解读：主星断 + 双星 + 辅煞。"""
    from core.ziwei.star_palace import interpret_palace_full
    full = interpret_palace_full(
        "财帛",
        [{"name": "武曲", "brightness": "庙"}, {"name": "天府", "brightness": "得"}],
        [{"name": "禄存"}, {"name": "擎羊"}],
    )
    assert full["double_star"]["ming"] == "武曲天府·财库双美"
    assert len(full["majors"]) == 2
    aux_names = [a["star"] for a in full["aux"]]
    assert "禄存" in aux_names and "擎羊" in aux_names


def test_chart_double_aux():
    """排盘宫位含 palace_full（双星/辅煞）。"""
    from core.ziwei.chart import build_ziwei_chart
    r = build_ziwei_chart("1990-06-15", 6, "男")
    soul = next(p for p in r["palaces"] if p["is_soul"])
    assert "palace_full" in soul
    # 命宫武曲天府 → 双星组合
    if len([s for s in soul["major_stars"] if s["name"] in ("武曲", "天府")]) == 2:
        assert soul["palace_full"]["double_star"]["ming"] == "武曲天府·财库双美"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
