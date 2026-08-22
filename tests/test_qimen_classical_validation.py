"""奇门参验 — 局数(节气三元) / 地盘三奇六仪 对《烟波钓叟赋》标准独立校验"""
import os, sys
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _layout(y, m, d, h=12):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/qimen/layout",
        json={"year": y, "month": m, "day": d, "hour": h, "minute": 0, "purpose": "求财"}).json()["data"]


def test_ju_number_by_jieqi_yuan():
    """局数 = 节气三元局数表。"""
    TABLE = {("冬至", "上元"): 1, ("冬至", "中元"): 7, ("冬至", "下元"): 4,
             ("小寒", "上元"): 2, ("夏至", "上元"): 9, ("春分", "上元"): 3}
    samples = [(2025, 12, 22), (2025, 12, 26), (2025, 12, 31),
               (2026, 1, 6), (2026, 6, 22), (2026, 3, 21)]
    checked = 0
    for y, m, d in samples:
        r = _layout(y, m, d)
        key = (r.get("jieqi"), r.get("yuan"))
        if key in TABLE:
            assert r["ju_number"] == TABLE[key], f"{y}-{m}-{d} {key}"
            checked += 1
    assert checked >= 5


def test_dipan_yangdun_ju1():
    """阳遁一局地盘：戊1己2庚3辛4壬5癸6丁7丙8乙9。"""
    r = _layout(2025, 12, 22)
    exp = {1: "戊", 2: "己", 3: "庚", 4: "辛", 5: "壬", 6: "癸", 7: "丁", 8: "丙", 9: "乙"}
    got = {p["position"]: p.get("di_pan") for p in r["palaces"]}
    for pos in range(1, 10):
        assert got[pos] == exp[pos], f"{pos}宫"


def test_yin_yang_dun():
    """冬至后阳遁、夏至后阴遁。"""
    assert _layout(2025, 12, 22)["ju_type"] == "阳遁"
    assert _layout(2026, 6, 22)["ju_type"] == "阴遁"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
