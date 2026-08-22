"""紫微 — 命格力量综合推理链"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ziwei.synthesis import synthesize_mingge


def _chart(p=None):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"year": 1985, "month": 10, "day": 1, "hour": 14, "gender": "female", "is_lunar": False}
    if p:
        body.update(p)
    return c.post("/api/v1/ziwei/chart", json=body).json()["data"]


def test_chain_integrates_submodules():
    s = synthesize_mingge(_chart())
    assert s["available"]
    mods = {f["module"] for f in s["factors"]}
    assert "命宫主星" in mods
    assert "三方四正" in mods or "格局成破" in mods


def test_factors_attributed():
    s = synthesize_mingge(_chart())
    for f in s["factors"]:
        assert f["module"] and f["polarity"] in ("利", "害", "中") and f["note"]


def test_composite():
    s = synthesize_mingge(_chart())
    assert s["composite_label"] in (
        "命格上乘", "命格中上", "命格中平", "命格偏弱", "命格受损")
    assert "→" in s["chain_text"] and "⟹" in s["chain_text"]


def test_in_api():
    d = _chart()
    assert "mingge_synthesis" in d and d["mingge_synthesis"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
