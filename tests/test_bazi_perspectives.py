"""八字 — 多视角整合解读（子模块尽其用·无孤儿）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.bazi.perspectives import build_perspectives


def _chart(p=None):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"year": 1988, "month": 2, "day": 15, "hour": 10, "gender": "male", "is_lunar": False}
    if p:
        body.update(p)
    return c.post("/api/v1/bazi/chart", json=body).json()["data"]


def test_six_lenses():
    p = build_perspectives(_chart())
    assert p["available"]
    ids = {l["id"] for l in p["lenses"]}
    assert ids == {"geju", "qiangruo", "shishen", "xingchong", "shensha", "gongwei", "yuncheng"}


def test_no_orphans_previously_isolated_covered():
    """此前孤立的子模块（成破/十神/神煞/命宫/人元司令）现都须被某视角消费。"""
    p = build_perspectives(_chart())
    covered = set(p["coverage"].keys())
    for needed in ["成破救应", "十神统计", "神煞", "命宫", "身宫", "胎元", "人元司令", "特殊格局"]:
        assert needed in covered, f"孤儿未纳入视角: {needed}"


def test_lenses_weave_content():
    p = build_perspectives(_chart())
    for l in p["lenses"]:
        assert l["modules"] and len(l["text"]) > 30


def test_in_api():
    d = _chart()
    assert "perspectives" in d and d["perspectives"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
