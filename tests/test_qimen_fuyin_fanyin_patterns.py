"""奇门伏吟/反吟入格局列表回归守护 —— 防键错配致大凶格静默消失。
此前 bug：_detect_patterns 读 layout.get("fuyin")/("fanyin")（实际键为 fuyin_fanyin dict）→
        恒 None → 伏吟/反吟大凶格从不进 patterns。现以 detect_fuyin_fanyin 按局数判。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _layout(mo, d, h):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/qimen/layout",
        json={"year": 2026, "month": mo, "day": d, "hour": h, "purpose": "求财"}).json()["data"]


def test_fuyin_fanyin_appear_in_patterns():
    """扫多局，patterns 中应能出现伏吟与反吟（修复前恒无）。"""
    seen = set()
    for mo in range(1, 13):
        for d in range(1, 29, 3):
            for h in (0, 12):
                pats = [p["name"] for p in _layout(mo, d, h).get("patterns", [])]
                if "伏吟" in pats:
                    seen.add("伏吟")
                if "反吟" in pats:
                    seen.add("反吟")
    assert "伏吟" in seen, "伏吟大凶格仍未进 patterns"
    assert "反吟" in seen, "反吟大凶格仍未进 patterns"


def test_patterns_consistent_with_fuyin_fanyin_field():
    """patterns 中的伏吟/反吟须与 fuyin_fanyin 字段一致（不自相矛盾）。"""
    for mo in range(1, 13):
        for d in (5, 15, 25):
            for h in (0, 6, 18):
                d_ = _layout(mo, d, h)
                pats = [p["name"] for p in d_.get("patterns", [])]
                ff = (d_.get("fuyin_fanyin", {}) or {}).get("type")
                assert ("伏吟" in pats) == (ff == "伏吟")
                assert ("反吟" in pats) == (ff == "反吟")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
