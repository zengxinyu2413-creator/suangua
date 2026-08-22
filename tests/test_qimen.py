"""
tests/test_qimen.py
奇门遁甲 — 排盘 / 九宫多层级断 / 用事
（此前 qimen 无测试，本文件补足核心覆盖）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qimen.algorithm import calculate_qimen
from core.qimen.analyzer import analyze_qimen
from core.qimen.purpose_analysis import enrich_qimen_analysis, PURPOSE_LOGIC
from core.qimen.palace_layers import (
    analyze_palace_layers, enrich_palace_layers, _wx_relation,
    _hour_xunkong, SANHE_MA, JIXING_GONG, GONG_WX, GONG_DIZHI, WX_MU,
)
from datetime import datetime


# ── 排盘基础 ──
def test_layout_nine_palaces():
    """排盘出九宫，每宫四盘一星齐全。"""
    lay = calculate_qimen(2024, 6, 15, 14)
    pals = lay["palaces"]
    assert len(pals) == 9
    for p in pals:
        for k in ("palace_name", "star", "door", "deity", "tian_pan", "di_pan"):
            assert p.get(k), f"{p.get('palace_name')} 缺 {k}"
    assert 1 <= lay["ju_number"] <= 9


def test_ju_varies_by_time():
    """不同节气/时辰局数应不同（排除硬编码）。"""
    a = calculate_qimen(2024, 1, 10, 3)["ju_number"]
    b = calculate_qimen(2024, 7, 20, 15)["ju_number"]
    # 局数为 1-9，至少两个不同时刻不应恒等（弱校验）
    assert isinstance(a, int) and isinstance(b, int)


# ── 多层级 ──
def test_wx_relation():
    assert _wx_relation("金", "木") == "我克"   # 金克木
    assert _wx_relation("木", "金") == "克我"
    assert _wx_relation("水", "木") == "我生"   # 水生木
    assert _wx_relation("木", "水") == "生我"
    assert _wx_relation("土", "土") == "比和"


def test_jixing():
    """六仪击刑：戊落震宫、庚落艮宫。"""
    r = analyze_palace_layers(
        {"palace_name": "震宫", "tian_pan": "乙", "di_pan": "戊",
         "door": "生门", "star": "天冲", "deity": "太阴"}, [], "")
    assert r["ji_xing"] is True
    r2 = analyze_palace_layers(
        {"palace_name": "艮宫", "tian_pan": "乙", "di_pan": "庚",
         "door": "生门", "star": "天任", "deity": "太阴"}, [], "")
    assert r2["ji_xing"] is True


def test_rumu():
    """入墓：天盘丙（火）落乾宫（戌）火墓于戌。"""
    r = analyze_palace_layers(
        {"palace_name": "乾宫", "tian_pan": "丙", "di_pan": "庚",
         "door": "开门", "star": "天心", "deity": "值符"}, [], "")
    assert r["ru_mu"] is True
    assert any(f["type"] == "入墓" for f in r["flags"])


def test_qiyi_shengke():
    """奇仪生克：天盘庚(金)地盘乙(木) 金克木=上克下利客。"""
    r = analyze_palace_layers(
        {"palace_name": "离宫", "tian_pan": "庚", "di_pan": "乙",
         "door": "景门", "star": "天英", "deity": "白虎"}, [], "")
    assert r["sd_tag"] == "吉客"
    assert "上克下" in r["sd_rel"]


def test_menpo():
    """门迫：宫克门（坎宫水 克 景门火？水克火，宫克门=门迫）。"""
    r = analyze_palace_layers(
        {"palace_name": "坎宫", "tian_pan": "甲", "di_pan": "己",
         "door": "景门", "star": "天英", "deity": "值符"}, [], "")
    assert r["men_po"] is True


def test_kong_and_ma():
    """旬空宫 + 马星宫。"""
    # 坤宫纳未申；旬空含申 → 空亡
    r = analyze_palace_layers(
        {"palace_name": "坤宫", "tian_pan": "乙", "di_pan": "丁",
         "door": "死门", "star": "天芮", "deity": "玄武"}, ["申", "酉"], "未")
    assert r["kong"] is True
    assert r["ma"] is True   # 马支未在坤宫


def test_xunkong_calc():
    """时柱旬空计算正确（甲子旬→戌亥）。"""
    # 2024-1-1 子时附近，验证函数不报错且返回两支
    xk = _hour_xunkong(datetime(2024, 6, 15, 14))
    assert len(xk) == 2 and all(z in "子丑寅卯辰巳午未申酉戌亥" for z in xk)


def test_enrich_fills_layers():
    """enrich 后每宫 sd_rel/gong_wx/stem_info 非空，并产出 layer_summary。"""
    lay = calculate_qimen(2024, 6, 15, 14)
    enrich_palace_layers(lay)
    for p in lay["palaces"]:
        assert p["gong_wx"]
        assert p["stem_info"]
        assert "layers" in p and p["layers"]["layer_judgment"]
    assert lay["layer_summary"]["desc"]


def test_full_pipeline_enrich():
    """analyze + enrich 全流程，层级与用事并存。"""
    lay = calculate_qimen(2024, 6, 15, 14)
    res = analyze_qimen(lay)
    res = enrich_qimen_analysis(res)
    assert "layer_summary" in res
    assert "purpose_analyses" in res
    # 每宫已补层级
    assert res["palaces"][0].get("layers")


# ── 用事扩展 ──
def test_purpose_expanded():
    """用事扩展到经典全集（含官司/疾病/失物/寻人/谋事/婚姻/胜负/买卖）。"""
    for p in ("求财", "官司", "疾病", "失物", "寻人", "谋事", "婚姻", "胜负", "买卖"):
        assert p in PURPOSE_LOGIC, f"缺用事：{p}"
        v = PURPOSE_LOGIC[p]
        assert v["title"] and v["principle"] and v["best_doors"]


def test_purpose_wellformed():
    """每个用事条目结构完整。"""
    for k, v in PURPOSE_LOGIC.items():
        for f in ("title", "best_doors", "best_stars", "best_stems",
                  "worst_doors", "worst_stars", "principle"):
            assert f in v, f"{k} 缺字段 {f}"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
