"""奇门 — 推理链 + 多视角 + 一致性审核"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.qimen.synthesis import synthesize_yongshen_force
from core.qimen.perspectives import build_perspectives
from core.qimen.consistency_audit import audit_consistency


def _layout(purpose="事业"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/qimen/layout", json={
        "year": 2026, "month": 6, "day": 24, "hour": 14, "minute": 0, "purpose": purpose}).json()["data"]


def test_synthesis_integrates_and_varies():
    shi = synthesize_yongshen_force(_layout("事业"))
    hun = synthesize_yongshen_force(_layout("婚姻"))
    assert shi["available"] and hun["available"]
    mods = {f["module"] for f in shi["factors"]}
    assert "门宫旺衰" in mods and "九星" in mods
    # 事业(吉宫)与婚姻(凶宫)综合力应不同
    assert shi["composite_score"] != hun["composite_score"]


def test_perspectives_no_orphans():
    p = build_perspectives(_layout())
    assert p["available"]
    ids = {l["id"] for l in p["lenses"]}
    assert ids == {"yongshen", "zhifu", "fangwei", "geju", "sanpan", "fuwen"}
    for needed in ["伏吟反吟", "烟波钓叟赋", "马星空亡", "击刑入墓"]:
        assert needed in p["coverage"], f"孤儿未纳入: {needed}"


def test_audit_detects_conflict_synthetic():
    """构造落宫吉但推理链凶的矛盾。"""
    fake = {
        "yong_shen": {"palace": "坎宫", "quality": "大吉", "topic": "求财"},
        "yongshen_synthesis": {"composite_label": "用神受制"},
        "best_palaces": ["坎宫"], "worst_palaces": [], "palaces": [{}],
        "layer_summary": {},
    }
    a = audit_consistency(fake)
    assert "yonggong_vs_force" in {f["id"] for f in a["findings"]}


def test_in_api():
    d = _layout()
    assert "yongshen_synthesis" in d and "perspectives" in d and "consistency_audit" in d


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
