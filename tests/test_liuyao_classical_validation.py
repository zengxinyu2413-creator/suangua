"""六爻参验 — 纳甲地支 / 六亲 / 世应 对京房标准独立校验"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _div(vals):
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app).post("/api/v1/liuyao/divine",
        json={"question": "测", "method": "manual", "query_time": "2026-01-02T10:00:00", "yao_values": vals}).json()["data"]


def test_qian_najia():
    """乾为天：纳甲干支甲子甲寅甲辰壬午壬申壬戌、六亲、世6应3。"""
    d = _div([7, 7, 7, 7, 7, 7])
    yaos = d["yaos"]
    assert [y["branch"] for y in yaos] == ["子", "寅", "辰", "午", "申", "戌"]
    assert [y["ganzhi"] for y in yaos] == ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"]
    assert [y["liu_qin"] for y in yaos] == ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"]
    assert next(i + 1 for i, y in enumerate(yaos) if y["is_world"]) == 6
    assert next(i + 1 for i, y in enumerate(yaos) if y["is_application"]) == 3


def test_najia_stems_by_trigram():
    """纳甲天干：乾甲壬·坤乙癸·离己·坎戊（京房）。"""
    assert [y["ganzhi"] for y in _div([8, 8, 8, 8, 8, 8])["yaos"]] == \
        ["乙未", "乙巳", "乙卯", "癸丑", "癸亥", "癸酉"]            # 坤乙癸
    jiji = _div([7, 8, 7, 8, 7, 8])["yaos"]                      # 既济 离下坎上
    assert [y["stem"] for y in jiji] == ["己", "己", "己", "戊", "戊", "戊"]


def test_kun_najia():
    """坤为地：地支未巳卯丑亥酉、世6应3。"""
    d = _div([8, 8, 8, 8, 8, 8])
    assert [y["branch"] for y in d["yaos"]] == ["未", "巳", "卯", "丑", "亥", "酉"]
    assert next(i + 1 for i, y in enumerate(d["yaos"]) if y["is_world"]) == 6


def test_world_app_by_palace_rank():
    """世应随八宫卦序：一世卦世1应4、五世卦世5应2。"""
    gou = _div([8, 7, 7, 7, 7, 7])   # 天风姤·乾宫一世
    assert next(i + 1 for i, y in enumerate(gou["yaos"]) if y["is_world"]) == 1
    assert next(i + 1 for i, y in enumerate(gou["yaos"]) if y["is_application"]) == 4
    bo = _div([8, 8, 8, 8, 8, 7])    # 山地剥·乾宫五世
    assert next(i + 1 for i, y in enumerate(bo["yaos"]) if y["is_world"]) == 5
    assert next(i + 1 for i, y in enumerate(bo["yaos"]) if y["is_application"]) == 2


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
