"""奇门值符星回归守护 —— 防"找天蓬宫"简化法致值符星恒为天蓬。
此前 bug：calculate_qimen 以"天盘中天蓬所在宫"为值符宫 → 值符星永远天蓬（恒值），
        约 8/9 命盘值符分析全错。正法：旬首六仪所在地盘宫之本位九星 = 值符星。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_NATURAL = {1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅", 5: "天禽",
            6: "天心", 7: "天柱", 8: "天任", 9: "天英"}


def _zhifu_star(y, mo, d, h):
    from fastapi.testclient import TestClient
    from main import app
    r = TestClient(app).post("/api/v1/qimen/layout",
        json={"year": y, "month": mo, "day": d, "hour": h, "purpose": "求财"}).json()["data"]
    return r.get("zhifu_analysis", {}).get("zhifu", {}).get("star")


def test_zhifu_star_varies():
    """值符星随时辰遍历多种（修复前恒为天蓬1种）。"""
    seen = set()
    for mo in (2, 5, 8, 11):
        for d in (3, 15, 27):
            for h in range(0, 24, 2):
                s = _zhifu_star(2026, mo, d, h)
                if s:
                    seen.add(s)
    assert len(seen) >= 7, f"值符星种类过少（疑恒值）：{seen}"


def test_zhifu_star_matches_xunshou_liuyi():
    """独立核验：值符星 == 旬首六仪所在地盘宫之本位九星。"""
    from datetime import datetime
    from core.qimen.algorithm import _get_palace_stem, XUNSHOU_LIUYI, calculate_qimen
    from core.calendar.ganzhi import ganzhi_from_index, _REF_DATE, _REF_DAY_IDX
    from core.constants import get_hour_gan, hour_to_dizhi
    import random
    random.seed(7)
    bad = 0
    for _ in range(40):
        y, mo, d, h = random.randint(2020, 2027), random.randint(1, 12), random.randint(1, 28), random.randint(0, 23)
        layout = calculate_qimen(y, mo, d, h, 0)
        ju, yang = layout["ju_number"], layout["ju_type"] == "阳遁"
        zp = next((p for p in layout["palaces"] if p["is_zhifu"]), None)
        if not zp:
            continue
        dd = (datetime(y, mo, d, h).date() - _REF_DATE).days
        dgan, _ = ganzhi_from_index((_REF_DAY_IDX + dd) % 60)
        hgz = get_hour_gan(dgan, hour_to_dizhi(h)) + hour_to_dizhi(h)
        yi = XUNSHOU_LIUYI.get(hgz, "戊")
        dipan = next((p for p in range(1, 10) if _get_palace_stem(p, ju, yang) == yi), 1)
        if zp["star"] != _NATURAL[dipan]:
            bad += 1
    assert bad == 0, f"{bad} 例值符星与旬首六仪不符"


def test_zhifu_tianpeng_for_yang1_jiazi():
    """阳遁一局甲子旬：戊在1宫，值符当为天蓬（古法锚点）。"""
    from core.qimen.algorithm import _get_palace_stem
    dipan = next((p for p in range(1, 10) if _get_palace_stem(p, 1, True) == "戊"), None)
    assert dipan == 1 and _NATURAL[dipan] == "天蓬"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
