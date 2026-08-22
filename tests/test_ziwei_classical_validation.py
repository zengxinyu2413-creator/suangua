"""紫微参验 — 命宫定位 / 紫微星定位 / 十四主星排布 对古法独立校验"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZHI = "子丑寅卯辰巳午未申酉戌亥"
CASES = [("1990-05-22", 8), ("1985-11-03", 14), ("2000-01-15", 2), ("1976-08-20", 22), ("1995-07-07", 10)]
JU = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}


def _hidx(h): return ((h + 1) // 2) % 12
def _qi_ziwei(day, ju):
    n = day
    while n % ju: n += 1
    q = n // ju; borrow = n - day
    pos = 2 + (q - 1) + (-borrow if borrow % 2 else borrow)
    return pos % 12


def _chart(sd, h):
    from fastapi.testclient import TestClient
    from main import app
    y, m, d = map(int, sd.split("-"))
    return TestClient(app).post("/api/v1/ziwei/chart",
        json={"year": y, "month": m, "day": d, "hour": h, "gender": "male", "is_lunar": False}).json()["data"]


def test_life_palace_position():
    """命宫=寅起正月顺数生月、起子时逆数生时。"""
    from lunar_python import Solar
    for sd, h in CASES:
        y, m, d = map(int, sd.split("-"))
        lm = abs(Solar.fromYmd(y, m, d).getLunar().getMonth())
        exp = ZHI[(2 + (lm - 1) - _hidx(h)) % 12]
        r = _chart(sd, h)
        soul = next(p for p in r["palaces"] if p.get("is_soul"))
        assert soul["earthly_branch"] == exp, f"{sd} 命宫"


def test_ziwei_star_position():
    """紫微星定位 = 起紫微诀（五行局 + 生日）。"""
    from lunar_python import Solar
    for sd, h in CASES:
        y, m, d = map(int, sd.split("-"))
        lday = abs(Solar.fromYmd(y, m, d).getLunar().getDay())
        r = _chart(sd, h)
        ju = JU[r["metadata"]["five_elements"]]
        zw = next(ZHI.index(p["earthly_branch"]) for p in r["palaces"]
                  for s in p.get("major_stars", []) if s["name"] == "紫微")
        assert zw == _qi_ziwei(lday, ju), f"{sd} 紫微位"


def test_fourteen_stars_arrangement():
    """十四主星按紫微系/天府系固定偏移排布。"""
    r = _chart("1990-05-22", 8)
    pos = {s["name"]: ZHI.index(p["earthly_branch"]) for p in r["palaces"] for s in p.get("major_stars", [])}
    zw, tf = pos["紫微"], pos["天府"]
    for s, off in {"天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": -8}.items():
        if s in pos: assert pos[s] == (zw + off) % 12, f"紫微系 {s}"
    for s, off in {"太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4, "天梁": 5, "七杀": 6, "破军": 10}.items():
        if s in pos: assert pos[s] == (tf + off) % 12, f"天府系 {s}"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
