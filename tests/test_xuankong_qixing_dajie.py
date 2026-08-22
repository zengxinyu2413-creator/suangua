"""玄空七星打劫回归守护 —— 防"艮坤假打劫"恒报致每盘虚加吉分。
此前 bug：艮坤(2-5-8)向星恒成三般卦（飞星中宫线必差3之数学必然），旧版 OTHER_TRIPLETS
        检测使每盘皆误报「艮坤假打劫·吉」并 +1 分。真打劫专论离-坎线，不成则「无」。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _qixing(s, y):
    from fastapi.testclient import TestClient
    from main import app
    r = TestClient(app).post("/api/v1/fengshui/xuankong",
        json={"sitting_mountain": s, "year": y}).json()["data"]
    return r.get("qixing_dajie_precise", {})


def test_not_always_jiakaijie():
    """七星打劫不可每盘恒报「艮坤假打劫」（修复前 96/96 恒报）。"""
    types = set()
    for s in ["子", "午", "卯", "酉", "乾", "巽", "艮", "坤", "甲", "丙", "庚", "壬"]:
        for y in (2010, 2024, 1984, 2004):
            types.add(_qixing(s, y).get("type"))
    # 不可恒为「艮坤假打劫」
    assert types != {"艮坤假打劫"}, "七星打劫仍恒报艮坤假打劫"
    # 平凡的艮坤假打劫不应出现
    assert "艮坤假打劫" not in types, types


def test_no_spurious_auspicious_level():
    """非真打劫之盘 level 不应恒为 auspicious（旧版恒 auspicious 虚加吉分）。"""
    levels = set()
    for s in ["子", "午", "卯", "酉", "乾", "巽"]:
        for y in (2010, 2024):
            levels.add(_qixing(s, y).get("level"))
    assert levels != {"auspicious"}, "level 仍恒 auspicious"


def test_unit_jiakaijie_math_property():
    """单元锚点：艮坤(2-5-8)向星恒成三般卦是数学必然，不得据此报吉格。"""
    # 构造任一中宫向星 V，顺飞下 坤2=V+6、艮8=V+3、中5=V 必成三般卦
    THREE = [{1, 4, 7}, {2, 5, 8}, {3, 6, 9}]
    for V in range(1, 10):
        trip = {((V - 1) % 9) + 1, ((V + 3 - 1) % 9) + 1, ((V + 6 - 1) % 9) + 1}
        assert trip in THREE, V  # 恒成三般 → 不可作判别性格局


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
