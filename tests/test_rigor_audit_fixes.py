"""严谨性审计修复回归守护：六爻月令、奇门节气/元。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


def test_liuyao_month_zhi_uses_solar_term():
    """六爻月令须按节气月支，非公历月。2026-06-24 在夏至后→午月（旧法误为未）。"""
    c = _client()
    cases = {"2026-06-24T14:00:00": "午", "2026-06-03T14:00:00": "巳",
             "2026-01-15T10:00:00": "丑", "2026-08-10T10:00:00": "申"}
    for qt, exp in cases.items():
        d = c.post("/api/v1/liuyao/divine",
                   json={"question": "测", "method": "time", "query_time": qt}).json()["data"]
        assert d["month_zhi"] == exp, f"{qt}: 月支 {d['month_zhi']} != {exp}"


def test_liuyao_query_time_no_crash():
    """time 法显式传 query_time 不应崩溃（datetime 作用域 bug 回归）。"""
    c = _client()
    r = c.post("/api/v1/liuyao/divine",
               json={"question": "测", "method": "time", "query_time": "2026-06-24T14:00:00"})
    assert r.json()["success"]


def test_qimen_yuan_from_day_position_not_ju():
    """奇门元由日在节气内位置定，非由局数反推。夏至后3日=上元（旧法误为下元）。"""
    c = _client()
    d = c.post("/api/v1/qimen/layout",
               json={"year": 2026, "month": 6, "day": 24, "hour": 14, "minute": 0, "purpose": "求财"}).json()["data"]
    assert d["jieqi"] == "夏至"
    assert d["yuan"] == "上元"      # 旧法 _get_yuan(9)=下元 为误
    assert d["ju_number"] == 9


def test_qimen_jieqi_surfaced():
    """奇门节气名须 surface。"""
    c = _client()
    for m, dd in [(7, 10), (12, 25), (3, 25)]:
        d = c.post("/api/v1/qimen/layout",
                   json={"year": 2026, "month": m, "day": dd, "hour": 14, "minute": 0, "purpose": "求财"}).json()["data"]
        assert d.get("jieqi"), f"{m}-{dd} 节气未surface"
        assert d.get("yuan") in ("上元", "中元", "下元")


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
