"""阳宅三要流年方位辅参参验 — 门主灶静态、流年方位动态（年紫白飞星+年支）。"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _sanyao(analysis_year=None):
    from fastapi.testclient import TestClient
    from main import app
    body = {"men": "坎", "zhu": "巽", "zao": "震"}
    if analysis_year is not None:
        body["analysis_year"] = analysis_year
    return TestClient(app).post("/api/v1/fengshui/yangzhai_sanyao", json=body).json()["data"]


def test_annual_directions_helper():
    """流年方位 = 年紫白飞星 + 年支（2026：文昌东北/财位正东/五黄正南/太岁正南/三煞正北）。"""
    from core.fengshui.xuankong_advanced import get_annual_directions
    d = get_annual_directions(2026)
    assert d["wenchang"]["dir"] == "东北"   # 四绿@艮
    assert d["caiwei"]["dir"] == "正东"     # 八白@震
    assert d["wuhuang"]["dir"] == "正南"    # 五黄@离
    assert d["taisui"]["dir"] == "正南"     # 丙午年太岁
    assert d["sansha"]["dir"] == "正北"     # 寅午戌火局三煞在北


def test_mengzhuzao_static_across_years():
    """门主灶为静：宅型/品第不随分析流年变。"""
    a, b = _sanyao(2025), _sanyao(2026)
    assert a.get("grade") == b.get("grade")
    assert a.get("house_type") == b.get("house_type")


def test_annual_dimension_present_and_dynamic():
    """master_synthesis 含流年方位维度，且随分析流年变。"""
    a = _sanyao(2025); b = _sanyao(2026)
    da = next(dv for dv in a["master_synthesis"]["dimension_verdicts"] if dv["dim"] == "流年方位")
    db = next(dv for dv in b["master_synthesis"]["dimension_verdicts"] if dv["dim"] == "流年方位")
    assert "2025" in da["verdict"] and "2026" in db["verdict"]
    assert da["verdict"] != db["verdict"]     # 流年方位逐年不同


def test_default_analysis_year_current():
    """缺省分析流年 = 当前年。"""
    r = _sanyao(None)
    ln = next(dv for dv in r["master_synthesis"]["dimension_verdicts"] if dv["dim"] == "流年方位")
    assert str(datetime.now().year) in ln["verdict"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
