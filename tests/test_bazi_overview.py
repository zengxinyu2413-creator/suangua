"""八字 — 命局总论合成器（连贯叙述，非词条罗列）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.bazi.overview import synthesize_overview


def _chart():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/bazi/chart", json={
        "year": 1990, "month": 5, "day": 22, "hour": 8,
        "gender": "male", "is_lunar": True}).json()["data"]


def test_overview_available_and_structured():
    d = _chart()
    ov = synthesize_overview(d)
    assert ov["available"]
    assert ov["headline"]
    titles = [p["title"] for p in ov["paragraphs"]]
    # 必含日主立命 + 用神趋避 + 一生大局
    assert "日主立命" in titles
    assert "用神趋避" in titles
    assert "一生大局" in titles


def test_overview_weaves_facts():
    """总论须串入日主/格局/用神等具体事实，而非空泛。"""
    d = _chart()
    ov = synthesize_overview(d)
    blob = " ".join(p["text"] for p in ov["paragraphs"])
    assert d["day_master"] in blob          # 日主入文
    assert d["pattern"] in blob             # 格局入文
    assert len(blob) > 150                  # 成篇非词条


def test_overview_in_chart_api():
    d = _chart()
    assert "overview" in d and d["overview"]["available"]


def test_overview_headline_compact():
    d = _chart()
    ov = synthesize_overview(d)
    # 摘要含日主与格局
    assert d["day_master"] in ov["headline"]


def test_overview_graceful_empty():
    """缺字段不崩。"""
    ov = synthesize_overview({})
    assert ov["available"] is False or ov["paragraphs"] is not None


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
