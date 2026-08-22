"""六爻总断与用神七维断一致性参验 — 总断 overall_quality == 七维 verdict_level。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_LV = {"auspicious": "吉", "inauspicious": "凶", "neutral": "中"}
_CASES = [
    ([7, 9, 8, 7, 8, 6], "求财", "2026-09-10"), ([7, 9, 8, 7, 8, 6], "官司", "2026-06-10"),
    ([8, 7, 6, 9, 7, 8], "求财", "2026-03-15"), ([9, 8, 7, 6, 8, 7], "婚姻", "2026-11-20"),
    ([6, 7, 8, 9, 8, 7], "事业", "2026-01-08"), ([7, 8, 9, 6, 7, 8], "求财", "2026-07-22"),
    ([8, 9, 7, 8, 6, 7], "官司", "2026-04-18"), ([7, 6, 9, 8, 7, 8], "求医", "2026-10-05"),
]


def _div(yv, topic, qt):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/liuyao/divine",
        json={"method": "manual", "yao_values": yv, "gender": "male",
              "topic": topic, "query_time": qt + "T10:00:00"}).json()["data"]


def test_master_overall_matches_seven_dim():
    """总断 overall_quality 与七维 verdict_level 映射一致（总断=用神断）。"""
    checked = 0
    for yv, topic, qt in _CASES:
        d = _div(yv, topic, qt)
        yj = d.get("yongshen_judgment", {})
        ms = d.get("master_synthesis", {})
        if not yj.get("available"):
            continue
        checked += 1
        assert ms["overall_quality"] == _LV.get(yj["verdict_level"]), (topic, qt)
    assert checked >= 6


def test_master_headline_is_seven_dim_verdict():
    """总断 headline 即七维断之 verdict（同一断语，不相违）。"""
    d = _div(*_CASES[4])    # 事业·吉
    yj = d["yongshen_judgment"]; ms = d["master_synthesis"]
    assert ms["headline"] == yj["verdict"]


def test_seven_dim_dimension_present():
    """master 维度含「用神七维断」，呈成败之据。"""
    d = _div(*_CASES[0])
    ms = d["master_synthesis"]
    sd = next((x for x in ms["dimension_verdicts"] if x["dim"] == "用神七维断"), None)
    assert sd and "七维合参" in sd["verdict"]


def test_consistency_holds_across_yuelin():
    """同卦异月令，总断随七维断同步变化（一致联动）。"""
    sep = _div([7, 9, 8, 7, 8, 6], "官司", "2026-09-10")
    jun = _div([7, 9, 8, 7, 8, 6], "官司", "2026-06-10")
    for d in (sep, jun):
        assert d["master_synthesis"]["overall_quality"] == _LV.get(d["yongshen_judgment"]["verdict_level"])
    # 月令不同→七维不同→总断亦不同
    assert sep["master_synthesis"]["overall_quality"] != jun["master_synthesis"]["overall_quality"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
