"""紫微 — 大限流年并入主读盘（时间维度）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ziwei.current_fortune import build_ziwei_current_fortune


def _chart(year=1990):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/ziwei/chart",
                  json={"year": year, "month": 5, "day": 22, "hour": 8,
                        "gender": "male", "is_lunar": False}).json()["data"]


def test_daxian_varies_by_age():
    cf90 = build_ziwei_current_fortune(_chart(1990), 1990)
    cf76 = build_ziwei_current_fortune(_chart(1976), 1976)
    assert cf90["available"] and cf76["available"]
    # 不同年龄当前大限宫不同
    assert cf90["daxian"]["range"] != cf76["daxian"]["range"]


def test_daxian_covers_age():
    cf = build_ziwei_current_fortune(_chart(1990), 1990)
    rng = cf["daxian"]["range"]
    assert rng[0] <= cf["age"] <= rng[1]


def test_in_chart_and_overview():
    d = _chart(1990)
    assert d["current_fortune"]["available"]
    titles = [p["title"] for p in d["overview"]["paragraphs"]]
    assert "当前运限" in titles


def test_synthesis_separates_temporal():
    d = _chart(1990)
    assert "后天" in d["mingge_synthesis"]["chain_text"]
    assert d["mingge_synthesis"]["composite_label"].startswith("命格")


def test_perspectives_temporal_lens():
    d = _chart(1990)
    assert "yunxian" in {l["id"] for l in d["perspectives"]["lenses"]}
    assert "大限" in d["perspectives"]["coverage"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
