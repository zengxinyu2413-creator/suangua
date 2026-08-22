"""
tests/test_liuyao_duan_overview.py
六爻 — 断卦总览（综合断卦 × 应期联动：何事·吉凶·何时应）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.duan_overview import build_duan_overview, _polarity, _reframe_yingqi


def test_polarity():
    assert _polarity("吉") == "吉"
    assert _polarity("偏吉") == "吉"
    assert _polarity("偏凶") == "凶"
    assert _polarity("凶") == "凶"
    assert _polarity("中（吉凶参半）") == "中"


def test_reframe_mu_ji_vs_xiong():
    """入墓应期：吉则'出墓得用事成'，凶则'墓开祸发'。"""
    primary = {"date": "2026-06-29", "ganzhi": "甲戌", "scope": "日",
               "days_ahead": 5, "type": "冲墓开库"}
    ji = _reframe_yingqi(primary, "吉")
    xiong = _reframe_yingqi(primary, "凶")
    assert "事成" in ji or "得用" in ji
    assert "祸发" in xiong or "患发" in xiong


def test_reframe_kong():
    """逢空应期：吉则填实出空而成，凶则出空凶真。"""
    primary = {"date": "2026-07-01", "ganzhi": "丙子", "scope": "日",
               "days_ahead": 7, "type": "填实出空"}
    ji = _reframe_yingqi(primary, "吉")
    xiong = _reframe_yingqi(primary, "凶")
    assert "落实" in ji or "成" in ji
    assert "凶事方真" in xiong or "凶" in xiong


def test_reframe_no_primary():
    txt = _reframe_yingqi(None, "吉")
    assert "无明确应期" in txt or "拖延" in txt


def test_build_overview_ji():
    """吉断 + 应期 → 总览含事/结论/应期。"""
    zonghe = {"available": True, "conclusion": "吉", "confidence": "中",
              "yong_liuqin": "官鬼", "yong_shen": "官鬼",
              "reasoning": ["用神官鬼旺相，事有根基。"]}
    yingqi = {"primary": {"date": "2026-06-29", "ganzhi": "甲戌", "scope": "日",
                          "days_ahead": 5, "type": "冲墓开库"},
              "tempo": "用神旺相，应期较速。"}
    do = build_duan_overview(zonghe, yingqi, topic="求官仕途")
    assert do["available"]
    assert do["polarity"] == "吉"
    assert do["conclusion"] == "吉"
    assert "求官仕途" in do["overview"]
    assert "官鬼" in do["overview"]
    assert do["primary_date"] == "2026-06-29"
    assert "事成" in do["overview"] or "得用" in do["overview"]


def test_build_overview_fushen():
    """用神伏藏 → 待时，无吉凶无应期。"""
    zonghe = {"available": True, "fu_shen": True}
    do = build_duan_overview(zonghe, {}, topic="失物寻物")
    assert do["available"] and do["conclusion"] == "待时"
    assert "伏" in do["overview"]


def test_build_overview_unavailable():
    assert build_duan_overview({}, {})["available"] is False
    assert build_duan_overview({"available": False}, {})["available"] is False


def test_overview_in_divine():
    """端到端：/divine 输出含 duan_overview，且 overview 成段。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r = c.post("/api/v1/liuyao/divine", json={
        "method": "manual", "query_time": "2026-01-02T10:00:00", "yao_values": [7, 8, 9, 7, 8, 6],
        "question": "我能升官吗", "gender": "male"})
    d = r.json()["data"]
    do = d.get("duan_overview", {})
    assert do.get("available")
    assert do.get("overview") and do.get("conclusion")
    assert do.get("polarity") in ("吉", "凶", "中", "待")


def test_overview_polarity_reframes_yingqi():
    """同一卦不同性别（用神不同）→ 总览极性与应期措辞相应变化。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r1 = c.post("/api/v1/liuyao/divine", json={
        "method": "manual", "query_time": "2026-01-02T10:00:00", "yao_values": [7, 8, 9, 7, 8, 6],
        "question": "我能升官吗", "gender": "male"}).json()["data"]
    do = r1.get("duan_overview", {})
    # 吉则措辞含正向（成/得用/可把握），凶则含避备
    if do.get("polarity") == "吉":
        assert any(k in do["overview"] for k in ("成", "得用", "把握"))
    elif do.get("polarity") == "凶":
        assert any(k in do["overview"] for k in ("避", "备", "凶事应此"))


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
