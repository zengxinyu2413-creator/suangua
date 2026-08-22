"""流月方位辅参参验 — 流月紫白飞星 + 流月叠流年凶星检测。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_monthly_directions_positions():
    """流月方位由流月紫白飞星定，逐月不同。"""
    from core.fengshui.xuankong_advanced import get_monthly_directions
    dirs = {m: get_monthly_directions(2026, m)["wuhuang"]["dir"] for m in range(1, 13)}
    assert len(set(dirs.values())) >= 6   # 五黄位逐月移，方位多样


def test_monthly_annual_overlap_detected():
    """流月凶星叠流年凶星之方被检出（2026年8月：流月一白入中==流年一白入中，全盘叠合）。"""
    from core.fengshui.xuankong_advanced import get_monthly_directions
    d8 = get_monthly_directions(2026, 8)
    assert d8["overlaps"], "8月应有双五黄叠临"
    assert any("双五黄" in o for o in d8["overlaps"])
    # 非叠合月无 overlap
    d5 = get_monthly_directions(2026, 5)
    assert not d5["overlaps"]


def test_monthly_dimension_in_yangzhai():
    """阳宅三要 master 含流月方位维度，叠加月示大凶方。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r = c.post("/api/v1/fengshui/yangzhai_sanyao",
               json={"men": "坎", "zhu": "巽", "zao": "震", "analysis_year": 2026, "analysis_month": 8}).json()["data"]
    lm = next(dv for dv in r["master_synthesis"]["dimension_verdicts"] if dv["dim"] == "流月方位")
    assert "双五黄" in lm["verdict"]


def test_monthly_dimension_in_xuankong():
    """玄空 master 含流月维度。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r = c.post("/api/v1/fengshui/xuankong",
               json={"sitting_mountain": "子", "year": 2010, "analysis_year": 2026, "analysis_month": 8}).json()["data"]
    dims = [dv["dim"] for dv in r["master_synthesis"]["dimension_verdicts"]]
    assert "流月" in dims and "流年" in dims


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
