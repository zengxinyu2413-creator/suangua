"""八字 — 命局一致性审核（确定性矛盾检测）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.bazi.consistency_audit import audit_consistency, _fu_yi_sets


def _chart(p=None):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    body = {"year": 1988, "month": 2, "day": 15, "hour": 10, "gender": "male", "is_lunar": False}
    if p:
        body.update(p)
    return c.post("/api/v1/bazi/chart", json=body).json()["data"]


def test_fu_yi_sets_correct():
    fu, xie = _fu_yi_sets("金")
    assert fu == {"金", "土"}          # 同我金 + 生我土
    assert xie == {"水", "木", "火"}    # 我生水 + 我克木 + 克我火


def test_audit_runs_and_structured():
    a = audit_consistency(_chart())
    assert a["available"]
    for f in a["findings"]:
        assert f["severity"] in ("矛盾", "注意", "提示")
        assert f["modules"] and f["detail"] and f["suggestion"]


def test_severity_sorted():
    a = audit_consistency(_chart({"year": 2000, "month": 8, "day": 8, "hour": 6, "is_lunar": False}))
    rank = {"矛盾": 3, "注意": 2, "提示": 1}
    sevs = [rank[f["severity"]] for f in a["findings"]]
    assert sevs == sorted(sevs, reverse=True)


def test_yong_ji_overlap_detection():
    """构造用神=忌神的矛盾，须被检出。"""
    fake = {"day_master": "庚", "day_master_wuxing": "金", "strength": "中和",
            "yong_shen": {"yong_shen_wx": "水", "ji_shen_wx": "水"}}
    a = audit_consistency(fake)
    assert "yong_ji_overlap" in {f["id"] for f in a["findings"]}


def test_weak_drain_contradiction():
    """身弱却取克泄为用 → 矛盾。"""
    fake = {"day_master": "庚", "day_master_wuxing": "金", "strength": "身弱",
            "yong_shen": {"yong_shen_wx": "火", "ji_shen_wx": "木"}}  # 火克金=克泄
    a = audit_consistency(fake)
    assert "weak_but_drain_yong" in {f["id"] for f in a["findings"]}


def test_in_api():
    d = _chart()
    assert "consistency_audit" in d


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
