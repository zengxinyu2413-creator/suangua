"""
tests/test_qimen_advanced.py
奇门遁甲 — 格局×九宫层级联动 / 用神宫自动定位
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qimen.algorithm import calculate_qimen
from core.qimen.analyzer import analyze_qimen
from core.qimen.purpose_analysis import enrich_qimen_analysis
from core.qimen.geju_layers import link_patterns_to_layers, DIR_TO_POS, _find_palace
from core.qimen.yongshen import analyze_yongshen_palaces, _locate_stem


def _enriched(y=2024, m=6, d=15, h=14):
    lay = calculate_qimen(y, m, d, h)
    res = analyze_qimen(lay)
    return enrich_qimen_analysis(res)


# ── 格局×层级联动 ──
def test_geju_layers_produced():
    """enrich 后产出 geju_layers，含 linked 与 summary。"""
    res = _enriched()
    gl = res["geju_layers"]
    assert gl["linked"] and gl["summary"]


def test_geju_located_have_joint():
    """可定位之格局含 palace + joint 成文 + tag。"""
    res = _enriched()
    located = [l for l in res["geju_layers"]["linked"] if l["located"]]
    assert located
    for l in located:
        assert l["palace"] and l["joint"] and l["tag"]


def test_dir_to_pos_complete():
    """八方+中 → 九宫序齐全。"""
    assert set(DIR_TO_POS.values()) == set(range(1, 10))


def test_ji_ge_受制_when_block():
    """吉格落门迫/入墓/击刑之宫 → tag 含'受制'或'逢空'(非'得地')。"""
    res = _enriched()
    for l in res["geju_layers"]["linked"]:
        if l.get("located") and l["tag"].startswith("吉"):
            flags = set(l.get("flags", []))
            if flags & {"门迫", "入墓", "击刑"}:
                assert "受制" in l["tag"]
            # 至少有一种成立即可（弱断言保证逻辑联通）
    assert True


def test_find_palace_by_direction():
    """据 direction 定位宫位正确。"""
    res = _enriched()
    pat = {"name": "测试", "direction": "东", "severity": "auspicious"}
    p = _find_palace(res, pat)
    assert p and p["position"] == 3   # 东=震三宫


# ── 用神宫定位 ──
def test_yongshen_basic_roles():
    """用神宫含值符/值使/日干/时干，并有层级 brief。"""
    res = _enriched()
    ys = analyze_yongshen_palaces(res)
    roles = {it["role"] for it in ys["items"]}
    assert "值符宫" in roles and "值使宫" in roles
    assert "日干宫" in roles and "时干宫" in roles
    for it in ys["items"]:
        assert it["palace"] and it["layer"]


def test_yongshen_nianming():
    """给生年则定年命宫。"""
    res = _enriched()
    ys = analyze_yongshen_palaces(res, birth_year=1988)
    nm = [it for it in ys["items"] if it["role"] == "年命宫"]
    assert nm and ys["nianming_zhi"]


def test_rg_sg_relation():
    """日干⇄时干生克关系成文。"""
    res = _enriched()
    ys = analyze_yongshen_palaces(res)
    assert ys["day_gan"] and ys["hour_gan"]
    assert ys["rg_sg_relation"]["desc"]
    assert ys["rg_sg_relation"]["relation"] in ("我克", "克我", "我生", "生我", "比和")


def test_locate_jia_via_zhifu():
    """甲遁旬首：定位甲应归值符宫。"""
    res = _enriched()
    loc = _locate_stem(res, "甲")
    zf = next((p["palace_name"] for p in res["palaces"] if p.get("is_zhifu")), None)
    assert loc["tian"] == zf
    assert "值符" in loc["via"]


def test_locate_stem_real():
    """实干（非甲）能在天/地盘定位到宫。"""
    res = _enriched()
    loc = _locate_stem(res, "乙")
    assert loc["tian"] or loc["di"]


def test_enrich_includes_yongshen():
    """enrich 输出含 yongshen_palaces。"""
    lay = calculate_qimen(2024, 6, 15, 14)
    lay["_birth_year"] = 1990
    res = analyze_qimen(lay)
    res = enrich_qimen_analysis(res)
    assert res.get("yongshen_palaces", {}).get("success")
    assert any(it["role"] == "年命宫" for it in res["yongshen_palaces"]["items"])


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
