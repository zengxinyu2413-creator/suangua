"""八字参验 — 四柱引擎对公认命例 + 独立差分校验"""
import os, sys, random
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GAN = "甲乙丙丁戊己庚辛壬癸"; ZHI = "子丑寅卯辰巳午未申酉戌亥"
_A = date(1900, 1, 1); _AIDX = 10   # 1900-01-01=甲戌（命理界公认锚点）


def _indep_day(d):
    i = (_AIDX + (d - _A).days) % 60
    return GAN[i % 10] + ZHI[i % 12]


def test_famous_case_mao():
    """毛泽东 1893-12-26：公认八字年癸巳·月甲子·日丁酉。"""
    from lunar_python import Solar
    lun = Solar.fromYmd(1893, 12, 26).getLunar()
    assert lun.getYearInGanZhiByLiChun() == "癸巳"
    assert lun.getMonthInGanZhi() == "甲子"
    assert lun.getDayInGanZhi() == "丁酉"


def test_year_pillar_switches_at_lichun():
    """年柱以立春换，非元旦。"""
    from lunar_python import Solar
    assert Solar.fromYmd(2024, 2, 3).getLunar().getYearInGanZhiByLiChun() == "癸卯"  # 立春前
    assert Solar.fromYmd(2024, 2, 5).getLunar().getYearInGanZhiByLiChun() == "甲辰"  # 立春后


def test_day_pillar_differential():
    """引擎日柱 vs 独立六十甲子推算，跨多日全一致。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    random.seed(7)
    for _ in range(25):
        y = random.randint(1900, 2025); m = random.randint(1, 12); dd = random.randint(1, 28)
        exp = _indep_day(date(y, m, dd))
        r = c.post("/api/v1/bazi/chart",
                   json={"year": y, "month": m, "day": dd, "hour": 12,
                         "gender": "male", "is_lunar": False}).json()["data"]
        dp = r["day_pillar"]
        assert f"{dp['tiangan']}{dp['dizhi']}" == exp, f"{y}-{m}-{dd}"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
