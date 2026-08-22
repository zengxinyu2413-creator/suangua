"""玄空纳命卦 — 理气×命卦人盘"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.fengshui.xuankong import calculate_xuankong_chart
from core.fengshui.xuankong_luantou import enrich_xuankong_luantou
from core.fengshui.xuankong_mingua import analyze_xuankong_mingua


def _xk():
    xk = calculate_xuankong_chart(2026, sitting_mountain="子")
    enrich_xuankong_luantou(xk)
    return xk


def test_mingua_cross_liqi():
    m = analyze_xuankong_mingua(_xk(), 1990, "male")
    assert m["available"]
    assert m["ming_gua"] and len(m["directions"]) == 8


def test_best_dirs_differ_by_occupant():
    """同宅，坎命与乾命宜居方不同（人盘维度）。"""
    xk = _xk()
    dong = analyze_xuankong_mingua(xk, 1990, "male")   # 坎命东四
    xi = analyze_xuankong_mingua(xk, 1976, "male")     # 乾命西四
    assert set(dong["best_dirs"]) != set(xi["best_dirs"])


def test_double_lucky_is_wang_and_ming_ji():
    """宜居用方须既是玄空旺方、又是命卦吉方。"""
    xk = _xk()
    wang = set(xk["luantou_summary"]["wang_directions"])
    m = analyze_xuankong_mingua(xk, 1990, "male")
    for d in m["best_dirs"]:
        rec = next(x for x in m["directions"] if x["direction"] == d)
        assert rec["liqi"] == "旺" and rec["ming_jx"] == "吉"


def test_in_api():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    d = c.post("/api/v1/fengshui/xuankong",
               json={"sitting_mountain": "子", "year": 2026, "birth_year": 1990, "gender": "male"}).json()["data"]
    assert "mingua_renpan" in d and d["mingua_renpan"]["available"]
    assert any(p["title"] == "命卦宜居" for p in d["overview"]["paragraphs"])


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
