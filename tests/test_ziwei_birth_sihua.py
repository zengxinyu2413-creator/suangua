"""
tests/test_ziwei_birth_sihua.py
紫微 — 生年四化盘 + 来因宫（飞星派论命起手）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ziwei.birth_sihua import (
    extract_birth_sihua, analyze_laiyin, interpret_birth_sihua,
    build_birth_sihua_panel, PALACE_THEME, HUA_MEANING,
)


def _chart(year=1985, month=3, day=15, hour=10, gender="male"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/ziwei/chart", json={
        "year": year, "month": month, "day": day, "hour": hour,
        "gender": gender, "is_lunar": False}).json()["data"]


def test_extract_four_hua():
    """生年四化齐全（禄权科忌各一）。"""
    d = _chart()
    bs = extract_birth_sihua(d)
    assert set(bs.keys()) == {"化禄", "化权", "化科", "化忌"}
    for hua, info in bs.items():
        assert info["star"] and info["palace"]


def test_yi_year_sihua_correct():
    """乙年四化：天机禄·天梁权·紫微科·太阴忌。"""
    d = _chart(1985)
    bs = extract_birth_sihua(d)
    assert bs["化禄"]["star"] == "天机"
    assert bs["化权"]["star"] == "天梁"
    assert bs["化科"]["star"] == "紫微"
    assert bs["化忌"]["star"] == "太阴"


def test_laiyin_is_stem_match():
    """来因宫 = 宫干同生年干之宫（梁派正解），非化忌宫。"""
    d = _chart(1985)
    bs = extract_birth_sihua(d)
    ly = analyze_laiyin(d, bs, "乙")
    assert ly["available"]
    # 来因宫之宫干应等于生年干
    pal = next((p for p in d["palaces"] if p["name"] == ly["palace"]), None)
    assert pal and pal["heavenly_stem"] == "乙"
    # 且单独记录生年忌入宫
    assert ly["ji_palace"]


def test_laiyin_distinct_from_jihua():
    """来因宫与生年化忌入宫为不同概念，分别记录。"""
    d = _chart(1985)
    panel = build_birth_sihua_panel(d)
    ly = panel["laiyin"]
    # 1985乙: 来因=命宫(宫干乙), 忌入=疾厄
    assert ly["palace"] != ly["ji_palace"]


def test_lu_ji_geju():
    """禄忌格局有断（同宫/对冲/分落）。"""
    d = _chart()
    panel = build_birth_sihua_panel(d)
    assert panel["lu_ji_geju"]
    assert any(k in panel["lu_ji_geju"] for k in ("同宫", "对冲", "福源", "成串"))


def test_interpret_rows():
    """四化解读逐条含 hua/star/palace/nature。"""
    d = _chart()
    bs = extract_birth_sihua(d)
    interp = interpret_birth_sihua(bs)
    assert len(interp["rows"]) == 4
    for r in interp["rows"]:
        assert r["hua"] and r["star"] and r["palace"] and r["nature"] in ("吉", "凶")


def test_panel_in_chart_api():
    """/chart 输出含 birth_sihua。"""
    d = _chart()
    assert "birth_sihua" in d
    assert d["birth_sihua"]["available"]
    assert d["birth_sihua"]["laiyin"]["palace"]


def test_different_year_stem():
    """不同生年干 → 不同四化与来因宫。"""
    d1 = _chart(1985)  # 乙
    d2 = _chart(1990, 7, 20, 14, "female")  # 庚
    p1 = build_birth_sihua_panel(d1)
    p2 = build_birth_sihua_panel(d2)
    assert p1["year_stem"] != p2["year_stem"]
    # 庚年化禄太阳、化忌天同
    assert p2["sihua"]["化禄"]["star"] == "太阳"
    assert p2["sihua"]["化忌"]["star"] == "天同"


def test_palace_theme_complete():
    """十二宫主题表覆盖主要宫名。"""
    for pal in ("命宫", "财帛宫", "官禄宫", "田宅宫", "疾厄宫", "夫妻宫"):
        assert pal in PALACE_THEME


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
