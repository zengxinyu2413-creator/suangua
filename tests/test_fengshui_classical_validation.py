"""玄空参验 — 运盘洛书顺飞 / 山向星入中 对古法独立校验"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LUOSHU = [5, 6, 7, 8, 9, 1, 2, 3, 4]


def _xk(sitting, year):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/fengshui/xuankong",
        json={"sitting_mountain": sitting, "year": year}).json()["data"]


def _g(chart, k):
    return chart.get(str(k), chart.get(k))


def test_yun_chart_luoshu_flight():
    """运盘 = 元运入中、洛书顺飞。八运/九运皆验。"""
    for year, center in [(2010, 8), (2025, 9)]:
        yc = _xk("子", year)["yun_chart"]
        assert _g(yc, 5) == center
        for i, gong in enumerate(LUOSHU):
            assert _g(yc, gong) == (center - 1 + i) % 9 + 1, f"{year} 宫{gong}"


def test_mountain_direction_center():
    """山星中宫=运盘坐山宫运星；向星中宫=运盘向首宫运星（子山午向：坐坎1向离9）。"""
    for year in (2010, 2025):
        r = _xk("子", year)
        yc, mc, dc = r["yun_chart"], r["mountain_chart"], r["direction_chart"]
        assert _g(mc, 5) == _g(yc, 1), f"{year} 山星入中"
        assert _g(dc, 5) == _g(yc, 9), f"{year} 向星入中"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
