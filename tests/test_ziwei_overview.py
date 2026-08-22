"""紫微 — 命盘总论合成（综合总论层 + hero 字段）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ziwei.overview import synthesize_overview


def _chart(p=None):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"year": 1985, "month": 10, "day": 1, "hour": 14, "gender": "female", "is_lunar": False}
    if p:
        body.update(p)
    return c.post("/api/v1/ziwei/chart", json=body).json()["data"]


def test_overview_weaves_paragraphs():
    d = _chart()
    ov = synthesize_overview(d)
    assert ov["available"]
    titles = [p["title"] for p in ov["paragraphs"]]
    assert "立命主星" in titles and "命格评定" in titles and "命格总评" in titles


def test_hero_fields_present():
    ov = synthesize_overview(_chart())
    for k in ("quality", "rating", "ming_branch", "ming_stars", "soul_star", "verdict_line"):
        assert ov.get(k), f"hero 缺字段 {k}"
    assert ov["quality"] in ("吉", "中", "凶")


def test_in_api():
    d = _chart()
    assert "overview" in d and d["overview"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
