"""
tests/test_liuyao_zonghe_duan.py
六爻 — 综合断卦（用神—原神—忌神—仇神 四位生克总断）
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.zonghe_duan import (
    analyze_zonghe_duan, _wangshuai, _locate_yong, _wx, _CHONG, _strong,
)
from core.liuyao.interpreter import _match_topic, get_yong_shen


def _mk_yaos():
    """构造一组带 najia 标注的爻（用于单元测试）。"""
    # branch/element/liu_qin/is_world/is_application/is_changing/changed_branch/kong_wang
    return [
        {"position": 1, "branch": "卯", "element": "木", "liu_qin": "子孙", "is_world": False, "is_application": False, "is_changing": False, "kong_wang": False},
        {"position": 2, "branch": "巳", "element": "火", "liu_qin": "妻财", "is_world": False, "is_application": True, "is_changing": False, "kong_wang": False},
        {"position": 3, "branch": "未", "element": "土", "liu_qin": "官鬼", "is_world": False, "is_application": False, "is_changing": True, "changed_branch": "辰", "kong_wang": False},
        {"position": 4, "branch": "午", "element": "火", "liu_qin": "妻财", "is_world": False, "is_application": False, "is_changing": False, "kong_wang": False},
        {"position": 5, "branch": "申", "element": "金", "liu_qin": "父母", "is_world": True, "is_application": False, "is_changing": False, "kong_wang": False},
        {"position": 6, "branch": "戌", "element": "土", "liu_qin": "官鬼", "is_world": False, "is_application": False, "is_changing": True, "changed_branch": "丑", "kong_wang": True},
    ]


# ── 旺衰 ──
def test_wangshuai_linri():
    """临日辰则旺。"""
    ws = _wangshuai("未", "未", "巳")   # 临月建未
    assert "临月建" in ws["notes"] and ws["force"] >= 2


def test_wangshuai_keke():
    """受月日克则休囚无气。"""
    ws = _wangshuai("申", "午", "午")   # 火克金
    assert ws["force"] < 0


def test_yuepo():
    """月破：地支冲月建。"""
    ws = _wangshuai("子", "午", "寅")   # 子午冲 → 月破
    assert ws["yuepo"] is True


# ── 用神定位 ──
def test_locate_yong_shiyao():
    """世爻用神定位到 is_world。"""
    loc = _locate_yong(_mk_yaos(), ["世爻"])
    assert loc["yao"] and loc["yao"]["is_world"]


def test_locate_yong_liuqin():
    """六亲用神：多现取持世/发动优先。"""
    loc = _locate_yong(_mk_yaos(), ["官鬼"])
    assert loc["yao"] and loc["yao"]["liu_qin"] == "官鬼"
    # 官鬼有两爻，应取发动者（位3 动）
    assert loc["yao"]["is_changing"]


def test_locate_yong_fushen():
    """用神不上卦 → 伏神标记。"""
    loc = _locate_yong(_mk_yaos(), ["兄弟"])   # 无兄弟爻
    assert loc["fu"] is True and loc["yao"] is None


# ── 四位综合断 ──
def test_zonghe_roles_complete():
    """综合断含用神/原神/忌神/仇神四位与五行。"""
    zd = analyze_zonghe_duan(_mk_yaos(), ["官鬼"], "未", "巳", kong=["戌", "亥"])
    assert zd["available"]
    assert zd["yong_wx"] == "土"
    assert zd["role_wx"]["原神"] == "火"   # 火生土
    assert zd["role_wx"]["忌神"] == "木"   # 木克土
    assert zd["role_wx"]["仇神"] == "水"   # 水生木
    assert set(zd["roles"].keys()) == {"用神", "原神", "忌神", "仇神"}


def test_zonghe_conclusion_and_chain():
    """综合断有结论、信心、断语链。"""
    zd = analyze_zonghe_duan(_mk_yaos(), ["官鬼"], "未", "巳", kong=["戌", "亥"])
    assert zd["conclusion"] in ("吉", "偏吉", "中（吉凶参半）", "偏凶", "凶")
    assert zd["confidence"] in ("高", "中", "低")
    assert zd["reasoning"] and zd["verdict"]


def test_zonghe_yong_wang_ji_xiu_is_ji():
    """用神旺相、忌神休囚静 → 偏吉以上。"""
    zd = analyze_zonghe_duan(_mk_yaos(), ["官鬼"], "未", "巳", kong=["戌", "亥"])
    # 官鬼未临月建旺、忌神木(子孙卯)受日辰巳泄 → 应偏吉/吉
    assert zd["score"] >= 1


def test_zonghe_jishen_dong_lowers():
    """忌神发动且旺 → 拉低吉凶分（构造忌神动旺之局）。"""
    yaos = _mk_yaos()
    # 让 忌神(木) 发动且旺：把位1子孙卯设为动，月建寅(木旺)
    yaos[0]["is_changing"] = True
    yaos[0]["changed_branch"] = "寅"
    zd_dong = analyze_zonghe_duan(yaos, ["官鬼"], "寅", "卯", kong=[])
    zd_jing = analyze_zonghe_duan(_mk_yaos(), ["官鬼"], "寅", "卯", kong=[])
    assert zd_dong["score"] <= zd_jing["score"]


def test_zonghe_fushen_verdict():
    """用神不上卦 → 待时结论。"""
    zd = analyze_zonghe_duan(_mk_yaos(), ["兄弟"], "未", "巳")
    assert zd["fu_shen"] is True and zd["conclusion"] == "待时"


def test_zonghe_shiying():
    """世应生克有断语。"""
    zd = analyze_zonghe_duan(_mk_yaos(), ["官鬼"], "未", "巳")
    assert zd["shiying"]   # 世申金 应巳火 → 应克世（火克金）
    assert "应克世" in zd["shiying"]


# ── topic 修复 ──
def test_topic_qiuzhi():
    """求职/升官/工作 → 求官仕途（官鬼为用）。"""
    for q in ("我能升官吗", "求职顺利吗", "这份工作能得到吗", "面试能过吗"):
        assert _match_topic(q) == "求官仕途"
    assert get_yong_shen("求官仕途", "male")[0] == "官鬼"


def test_topic_xingren():
    """他会回来吗 → 找人行人。"""
    assert _match_topic("他会回来吗") == "找人行人"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
