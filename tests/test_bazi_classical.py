"""八字 — 传统断语汇集（古籍原文层，示于用户）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.bazi.classical import collect_classical_statements


def _chart():
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/bazi/chart", json={
        "year": 1990, "month": 5, "day": 22, "hour": 8,
        "gender": "male", "is_lunar": True}).json()["data"]


def test_collect_has_sources():
    d = _chart()
    cs = collect_classical_statements(d)
    assert cs["available"] and cs["count"] >= 3
    sources = {s["source"] for s in cs["statements"]}
    # 至少含调候 + 格局两类古籍
    assert any("穷通" in s for s in sources)
    assert any("子平真诠" in s for s in sources)


def test_statements_have_text_and_attribution():
    d = _chart()
    cs = collect_classical_statements(d)
    for s in cs["statements"]:
        assert s["source"] and s["title"] and s["text"]
        assert len(s["text"]) > 4


def test_in_chart_api():
    d = _chart()
    assert "classical_statements" in d
    assert d["classical_statements"]["available"]


def test_graceful_empty():
    cs = collect_classical_statements({})
    assert cs["available"] is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))


def test_deepened_content_is_substantial():
    """深化后传统断语须实质详解（非提要）：单条注解 ≥80 字、总量显著。"""
    d = _chart()
    cs = collect_classical_statements(d)
    texts = [s["text"] for s in cs["statements"]]
    # 至少有一条「滴天髓·体性详注」或「子平真诠·章旨」级别的长详解
    assert any(len(t) >= 80 for t in texts), "传统断语仍是提要，未达详解深度"
    assert sum(len(t) for t in texts) >= 400


def test_deep_module_full_coverage():
    from knowledge.bazi_classical_deep import DITIAN_SHIGAN_FULL, ZIPING_GE_FULL
    assert len(DITIAN_SHIGAN_FULL) == 10        # 十干全
    assert len(ZIPING_GE_FULL) == 10            # 十正格全
    for dm, e in DITIAN_SHIGAN_FULL.items():
        assert all(k in e for k in ("原文", "体性详注", "四时取用", "喜忌成器"))
        assert len(e["体性详注"]) >= 80
