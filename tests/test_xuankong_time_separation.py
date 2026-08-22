"""玄空「建宅年 × 流年」分离参验
宅静时动：建宅年定运（本盘静态·不易），流年决定紫白/太岁动态叠加（辅参）。"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIBAI = {1: "一白", 2: "二黑", 3: "三碧", 4: "四绿", 5: "五黄", 6: "六白", 7: "七赤", 8: "八白", 9: "九紫"}


def _chart(year=2010, analysis_year=None, sitting="子"):
    from fastapi.testclient import TestClient
    from main import app
    body = {"sitting_mountain": sitting, "year": year}
    if analysis_year is not None:
        body["analysis_year"] = analysis_year
    return TestClient(app).post("/api/v1/fengshui/xuankong", json=body).json()["data"]


def test_static_plate_invariant_to_analysis_year():
    """运盘/山盘/向盘为本盘静态，不随分析流年变。"""
    a = _chart(2010, 2024)
    b = _chart(2010, 2026)
    assert a["yun_chart"] == b["yun_chart"]
    assert a["mountain_chart"] == b["mountain_chart"]
    assert a["direction_chart"] == b["direction_chart"]
    assert a["yun"]["yun"] == b["yun"]["yun"] == 8   # 建宅2010恒为八运


def test_annual_overlay_follows_analysis_year():
    """流年紫白入中随分析流年（年紫白逆飞：2024三碧/2025二黑/2026一白）。"""
    exp = {2024: 3, 2025: 2, 2026: 1}
    for ay, star in exp.items():
        ch = _chart(2010, ay)
        center = ch["overlaid_with_annual"]["5"]["annual"]
        assert center == star, f"{ay}: {center}!={star}"


def test_default_analysis_year_is_current():
    """缺省分析流年 = 当前年。"""
    ch = _chart(2010, None)
    assert ch["analysis_year"] == datetime.now().year


def test_annual_dimension_present():
    """master_synthesis 含流年辅参维度，含建宅年定运 + 流年紫白入中。"""
    ch = _chart(2010, 2026)
    ln = next((dv for dv in ch["master_synthesis"]["dimension_verdicts"] if dv.get("dim") == "流年"), None)
    assert ln is not None
    assert "2010" in ln["verdict"] and "一白" in ln["verdict"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
