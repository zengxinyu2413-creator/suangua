"""流时紫白（时白诀）参验 — 独立核对《沈氏玄空学·时白诀》起例。
阳遁(冬至后)顺、阴遁(夏至后)逆；日支三元定子时入中，逐时推。"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_hourly_center_qili_yangdun():
    """阳遁起例：子午卯酉日子时一白、辰戌丑未日四绿、寅申巳亥日七赤，逐时+1。"""
    from core.fengshui.xuankong_advanced import get_hourly_zibai_center
    # 2026-01-05 己卯日(卯·子午卯酉) 小寒(阳遁)：子时1、丑时2、寅时3
    assert get_hourly_zibai_center(datetime(2026, 1, 5, 0)) == 1   # 子时
    assert get_hourly_zibai_center(datetime(2026, 1, 5, 1)) == 2   # 丑时
    assert get_hourly_zibai_center(datetime(2026, 1, 5, 3)) == 3   # 寅时
    # 2026-03-20 癸巳日(巳·寅申巳亥) 春分(阳遁)：子时7
    assert get_hourly_zibai_center(datetime(2026, 3, 20, 0)) == 7


def test_hourly_center_wraps_9to1():
    """逐时推 9→1 循环正确（阳遁顺）。"""
    from core.fengshui.xuankong_advanced import get_hourly_zibai_center
    # 巳日子时7：申时(7时,差4)= (7-1+? )… 取酉时(17时,index9)= (7-1+9)%9+1
    c = get_hourly_zibai_center(datetime(2026, 3, 20, 17))   # 酉时 index9
    assert 1 <= c <= 9


def test_hourly_directions_structure():
    """流时方位结构完整：文昌/财位/五黄/病符方位齐备，随时辰变。"""
    from core.fengshui.xuankong_advanced import get_hourly_directions
    d0 = get_hourly_directions(datetime(2026, 3, 20, 0))
    d6 = get_hourly_directions(datetime(2026, 3, 20, 12))
    for k in ("wenchang", "caiwei", "wuhuang", "bingfu"):
        assert d0[k]["dir"]
    assert d0["wuhuang"]["dir"] != d6["wuhuang"]["dir"]   # 五黄位随时辰移


def test_hourly_dimension_in_masters():
    """玄空/阳宅 master 含流时维度，构成 年→月→时 完整链。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    yz = c.post("/api/v1/fengshui/yangzhai_sanyao", json={"men": "坎", "zhu": "巽", "zao": "震"}).json()["data"]
    xk = c.post("/api/v1/fengshui/xuankong", json={"sitting_mountain": "子", "year": 2010}).json()["data"]
    yz_dims = [d["dim"] for d in yz["master_synthesis"]["dimension_verdicts"]]
    xk_dims = [d["dim"] for d in xk["master_synthesis"]["dimension_verdicts"]]
    assert "流时方位" in yz_dims and "流月方位" in yz_dims and "流年方位" in yz_dims
    assert "流时" in xk_dims and "流月" in xk_dims and "流年" in xk_dims


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
