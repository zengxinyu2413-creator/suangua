"""玄空 — 推理链 + 多视角 + 一致性审核 + 五黄吉凶 bug 回归"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.fengshui.xuankong_synthesis import synthesize_zhaiyun
from core.fengshui.xuankong_perspectives import build_perspectives
from core.fengshui.xuankong_audit import audit_consistency


def _chart(sm="子"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    return c.post("/api/v1/fengshui/xuankong", json={"sitting_mountain": sm, "year": 2026}).json()["data"]


def test_synthesis_varies_and_integrates():
    zi = synthesize_zhaiyun(_chart("子"))
    gen = synthesize_zhaiyun(_chart("艮"))
    assert zi["available"] and gen["available"]
    mods = {f["module"] for f in zi["factors"]}
    assert "山向格局" in mods


def test_wuhuang_not_both_good_and_bad():
    """五黄入向/山 只可记为凶象，不可同时记吉格（startswith 修复）。"""
    s = synthesize_zhaiyun(_chart("子"))
    facs = [f["factor"] for f in s["factors"]]
    assert not any("吉格·五黄" in f for f in facs), "五黄误记为吉格"
    assert any("凶象·五黄" in f for f in facs), "五黄应记为凶象"


def test_shangshan_rescued_by_sanban():
    """艮山上山下水，逢父母三般卦救应，推理链应含救应因子。"""
    s = synthesize_zhaiyun(_chart("艮"))
    assert any("救" in f["factor"] or "三般卦" in f["factor"] for f in s["factors"])


def test_perspectives_no_orphans():
    p = build_perspectives(_chart())
    ids = {l["id"] for l in p["lenses"]}
    assert ids == {"geju", "tege", "zhengling", "jiugong", "luantou", "huajie"}
    for needed in ["各宫飞星判断", "化解法", "流年警示"]:
        assert needed in p["coverage"]


def test_audit_detects_verdict_force_divergence():
    """艮山(verdict上山下水凶)推理链救为向上(吉) → 审核应捕捉分歧。"""
    a = audit_consistency(_chart("艮"))
    ids = {f["id"] for f in a["findings"]}
    assert "verdict_vs_force" in ids or "shangshan_saved" in ids


def test_in_api():
    d = _chart()
    assert all(k in d for k in ("zhaiyun_synthesis", "perspectives", "consistency_audit"))


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
