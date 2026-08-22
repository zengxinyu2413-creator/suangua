"""六爻 — 断卦一致性审核（确定性矛盾检测）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.liuyao.consistency_audit import audit_consistency, _polarity_dir


def _divine(vals, q="求测"):
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    # 固定 query_time —— 入墓检测依赖日辰，不可用 wall-clock（否则随真实时间漂移成 flaky）
    return c.post("/api/v1/liuyao/divine", json={
        "method": "manual", "yao_values": vals, "question": q, "gender": "male",
        "query_time": "2026-01-02T10:00:00"}).json()["data"]


def test_detects_real_contradiction():
    """升职案应检出用神入墓的跨模块矛盾 + 用神两现提示。"""
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    a = audit_consistency(d)
    assert a["available"]
    ids = {f["id"] for f in a["findings"]}
    assert "mu_conflict" in ids          # 入墓矛盾
    assert "yong_duplication" in ids     # 用神两现
    assert a["summary"]["矛盾"] >= 1


def test_findings_have_attribution():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    a = audit_consistency(d)
    for f in a["findings"]:
        assert f["severity"] in ("矛盾", "注意", "提示")
        assert f["modules"] and f["detail"] and f["suggestion"]


def test_severity_sorted():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    a = audit_consistency(d)
    rank = {"矛盾": 3, "注意": 2, "提示": 1}
    sevs = [rank[f["severity"]] for f in a["findings"]]
    assert sevs == sorted(sevs, reverse=True)   # 矛盾在前


def test_clean_case_reports_coherent():
    d = _divine([7, 7, 7, 7, 7, 7], "财运")    # 乾求财
    a = audit_consistency(d)
    assert a["summary"]["矛盾"] == 0


def test_polarity_dir():
    assert _polarity_dir("吉") == "吉向"
    assert _polarity_dir("偏吉") == "吉向"
    assert _polarity_dir("凶") == "凶向"
    assert _polarity_dir("难成") == "凶向"


def test_in_api():
    d = _divine([9, 8, 7, 8, 9, 6], "升职")
    assert "consistency_audit" in d


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
