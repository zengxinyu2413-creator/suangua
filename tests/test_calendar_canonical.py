"""历法底座 — 权威 helper 回归守护（防止月支/节气类 bug 复发）"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.calendar.solar_terms import (
    day_ganzhi_at, month_ganzhi_at, month_dizhi_at,
    solar_term_on, current_solar_term, get_month_dizhi_at,
)


def test_day_ganzhi():
    assert day_ganzhi_at(datetime(2026, 6, 24, 14, 0)) == "己巳"


def test_month_ganzhi_and_dizhi():
    assert month_ganzhi_at(datetime(2026, 6, 24)) == "甲午"
    assert month_dizhi_at(datetime(2026, 6, 24)) == "午"


def test_month_dizhi_by_solar_term():
    """月支按节气，非日历月号。"""
    cases = [
        (datetime(2026, 1, 15), "丑"), (datetime(2026, 6, 3), "巳"),
        (datetime(2026, 7, 15), "未"), (datetime(2026, 8, 10), "申"),
        (datetime(2026, 12, 20), "子"),
    ]
    for dt, exp in cases:
        assert month_dizhi_at(dt) == exp, f"{dt.date()} 应 {exp}"


def test_solar_term_on():
    assert solar_term_on(datetime(2026, 6, 21)) == "夏至"
    assert solar_term_on(datetime(2026, 6, 24)) is None  # 非交节日


def test_current_solar_term():
    assert current_solar_term(datetime(2026, 6, 24)) == "夏至"


def test_alias_consistency():
    """month_dizhi_at 与 get_month_dizhi_at 一致。"""
    dt = datetime(2026, 7, 15)
    assert month_dizhi_at(dt) == get_month_dizhi_at(dt)


def test_modules_use_base():
    """六爻与择日端到端：月支/节气经底座后仍正确。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    ly = c.post("/api/v1/liuyao/divine",
                json={"question": "测", "method": "time",
                      "query_time": "2026-06-24T14:00:00"}).json()["data"]
    assert ly["month_zhi"] == "午" and ly["day_zhi"] == "巳"
    zr = c.post("/api/v1/date-selection/select",
                json={"purpose": "结婚", "year": 2026, "month": 7}).json()["data"]
    assert zr["month_zhi"] == "未"
    assert "小暑" in " ".join(zr.get("month_jieqi", []))


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
