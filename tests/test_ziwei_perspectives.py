"""紫微 — 多视角整合 + 一致性审核"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ziwei.perspectives import build_perspectives
from core.ziwei.consistency_audit import audit_consistency


def _chart(p=None):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"year": 1985, "month": 10, "day": 1, "hour": 14, "gender": "female", "is_lunar": False}
    if p:
        body.update(p)
    return c.post("/api/v1/ziwei/chart", json=body).json()["data"]


def test_six_lenses_no_orphans():
    p = build_perspectives(_chart())
    assert p["available"]
    ids = {l["id"] for l in p["lenses"]}
    assert ids == {"mingshen", "sanfang", "sihua", "shiergong", "shayao", "jiaodian", "yunxian"}
    covered = set(p["coverage"].keys())
    for needed in ["生年四化", "飞入命宫", "双忌", "飞化聚焦", "冲链", "长生十二神"]:
        assert needed in covered, f"孤儿未纳入: {needed}"


def test_audit_structured():
    a = audit_consistency(_chart())
    assert a["available"]
    for f in a["findings"]:
        assert f["severity"] in ("矛盾", "注意", "提示")
        assert f["modules"] and f["detail"] and f["suggestion"]


def test_audit_rating_vs_synthesis():
    """评等与推理链分歧须被检出（紫府女 上格 vs 命格中平）。"""
    a = audit_consistency(_chart())
    ids = {f["id"] for f in a["findings"]}
    assert "rating_vs_synthesis_soft" in ids or "rating_vs_synthesis_hard" in ids


def test_in_api():
    d = _chart()
    assert "perspectives" in d and d["perspectives"]["available"]
    assert "consistency_audit" in d


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))


def test_classical_deepened():
    from core.ziwei.classical import collect_classical_statements
    from knowledge.ziwei_classical_deep import ZIWEI_14_FULL
    assert len(ZIWEI_14_FULL) == 14
    for star, e in ZIWEI_14_FULL.items():
        assert len(e["星性总论"]) >= 80
    cs = collect_classical_statements(_chart())
    assert cs["available"] and cs["count"] >= 4
    assert any(len(s["text"]) >= 80 for s in cs["statements"])
