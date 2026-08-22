"""八字 — 命局力量综合推理链（子模块互助集成）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.bazi.synthesis import synthesize_mingju


def _chart(p=None):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"year": 1990, "month": 5, "day": 22, "hour": 8, "gender": "male", "is_lunar": True}
    if p:
        body.update(p)
    return c.post("/api/v1/bazi/chart", json=body).json()["data"]


def test_chain_integrates_submodules():
    d = _chart()
    s = synthesize_mingju(d)
    assert s["available"]
    mods = {f["module"] for f in s["factors"]}
    # 日主旺衰 + 格局成破 至少都参与
    assert "日主旺衰" in mods
    assert "格局成破" in mods


def test_factors_attributed():
    d = _chart()
    s = synthesize_mingju(d)
    for f in s["factors"]:
        assert f["module"] and "polarity" in f and "factor" in f and "note" in f
        assert f["polarity"] in ("利", "害", "中")


def test_composite_reflects_score():
    d = _chart()
    s = synthesize_mingju(d)
    assert s["composite_label"] in (
        "命局上佳", "命局中平偏上", "命局中平", "命局偏弱", "命局受损")
    assert "→" in s["chain_text"] and "⟹" in s["chain_text"]


def test_in_api():
    d = _chart()
    assert "mingju_synthesis" in d and d["mingju_synthesis"]["available"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
