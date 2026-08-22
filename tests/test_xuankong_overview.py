"""玄空 — 宅运总论合成（综合总论层 + hero）+ 坐山差异验证"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.fengshui.xuankong_overview import synthesize_overview


def _chart(sm="子"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/fengshui/xuankong", json={"sitting_mountain": sm, "year": 2026}).json()["data"]


def test_overview_weaves():
    ov = synthesize_overview(_chart("子"))
    assert ov["available"]
    titles = [p["title"] for p in ov["paragraphs"]]
    assert "山向格局" in titles and "宅运总评" in titles
    assert ov["quality"] in ("吉", "中", "凶")


def test_auspicious_vs_inauspicious():
    """坐子(旺山旺向吉) 与 坐艮(上山下水凶) 须评不同。"""
    zi = synthesize_overview(_chart("子"))
    gen = synthesize_overview(_chart("艮"))
    assert zi["quality"] == "吉" and zi["verdict"] == "旺山旺向"
    assert gen["quality"] == "凶" and gen["verdict"] == "上山下水"


def test_in_api():
    d = _chart("子")
    assert "overview" in d and d["overview"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
