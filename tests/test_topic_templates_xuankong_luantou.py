"""
tests/test_topic_templates_xuankong_luantou.py
六爻 14类专用断语 + 玄空峦头形理多层级
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.topic_templates import build_topic_verdict, _TEMPLATES
from core.fengshui.xuankong import calculate_xuankong_chart
from core.fengshui.xuankong_luantou import (
    enrich_xuankong_luantou, analyze_palace_luantou, _wangshuai, STAR_NAME, STAR_NATURE,
)


# ════════ 六爻 14类专用断语 ════════
def test_templates_cover_topics():
    """模板覆盖各主要占事类型。"""
    for t in ("求财", "求官仕途", "考试功名", "婚姻感情", "求医疾病",
              "出行远行", "官司诉讼", "求子嗣", "找人行人", "失物寻物",
              "家宅风水", "天气占候", "综合"):
        assert t in _TEMPLATES
        v = _TEMPLATES[t]
        assert all(k in v for k in ("yong", "ji", "xiong", "zhong", "watch"))


def test_topic_verdict_ji():
    """吉断采用吉模板，含用神说明与看点。"""
    zonghe = {"available": True, "conclusion": "吉", "yong_liuqin": "官鬼",
              "roles": {}}
    yaos = [{"liu_qin": "官鬼", "branch": "未", "strength": {"label": "旺"}, "is_changing": True},
            {"liu_qin": "父母", "branch": "申", "strength": {"label": "相"}}]
    tv = build_topic_verdict("求官仕途", zonghe, yaos)
    assert tv["available"] and tv["polarity"] == "吉"
    assert "官星旺相" in tv["verdict"] or "功名" in tv["verdict"]
    assert any("官星" in w for w in tv["watch_points"])


def test_topic_verdict_xiong():
    zonghe = {"available": True, "conclusion": "偏凶", "yong_liuqin": "妻财", "roles": {}}
    tv = build_topic_verdict("求财", zonghe, [{"liu_qin": "妻财", "branch": "巳"}])
    assert tv["polarity"] == "凶"
    assert "阻" in tv["verdict"] or "破耗" in tv["verdict"]


def test_topic_verdict_zhong():
    zonghe = {"available": True, "conclusion": "中（吉凶参半）", "yong_liuqin": "妻财", "roles": {}}
    tv = build_topic_verdict("求财", zonghe, [{"liu_qin": "妻财", "branch": "巳"}])
    assert tv["polarity"] == "中"


def test_topic_verdict_fushen():
    zonghe = {"available": True, "fu_shen": True}
    tv = build_topic_verdict("婚姻感情", zonghe, [])
    assert "伏" in tv["verdict"]


def test_topic_verdict_watch_state():
    """看点反映六亲实际状态（发动/空亡）。"""
    zonghe = {"available": True, "conclusion": "吉", "yong_liuqin": "妻财", "roles": {}}
    yaos = [{"liu_qin": "妻财", "branch": "巳", "is_changing": True, "kong_wang": True,
             "strength": {"label": "相"}}]
    tv = build_topic_verdict("求财", zonghe, yaos)
    fin = next((w for w in tv["watch_points"] if "财爻" in w), "")
    assert "发动" in fin and "空亡" in fin


# ════════ 玄空峦头形理 ════════
def test_wangshuai_九运():
    """九运旺衰：9旺、1生、8退、5煞、3死。"""
    assert _wangshuai(9, 9)["level"] == "旺"
    assert _wangshuai(1, 9)["level"] == "生"
    assert _wangshuai(8, 9)["level"] == "退"
    assert _wangshuai(5, 9)["level"] == "煞"
    assert _wangshuai(3, 9)["level"] == "死"


def test_star_tables():
    assert len(STAR_NAME) == 9 and len(STAR_NATURE) == 9
    assert STAR_NAME[5] == "五黄廉贞"


def test_palace_luantou_facing_water():
    """向星当令 → 宜见水旺财。"""
    pal = {"mountain": 8, "facing": 9, "direction": "北", "annual": 8}
    lt = analyze_palace_luantou(pal, 9)
    assert any("宜见水" in a for a in lt["advice"])
    assert lt["quality"] in ("旺方", "进气方")


def test_palace_luantou_wuhuang_flag():
    """五黄到方 → 大凶 flag、忌动土。"""
    pal = {"mountain": 5, "facing": 4, "direction": "中", "annual": 3}
    lt = analyze_palace_luantou(pal, 9)
    assert any(f["type"] == "五黄到方" for f in lt["flags"])
    assert lt["quality"] == "煞方"


def test_palace_luantou_annual_wuhuang():
    """流年五黄入方 → 流年五黄 flag。"""
    pal = {"mountain": 8, "facing": 1, "direction": "南", "annual": 5}
    lt = analyze_palace_luantou(pal, 9)
    assert any(f["type"] == "流年五黄" for f in lt["flags"])


def test_enrich_full_chart():
    """整盘 enrich：每宫有 luantou，summary 分旺/衰/煞方。"""
    chart = calculate_xuankong_chart(2024, sitting_degree=180)
    enrich_xuankong_luantou(chart)
    assert chart["luantou"] and chart["luantou_summary"]
    s = chart["luantou_summary"]
    assert "wang_directions" in s and "sha_directions" in s
    # 九运
    assert s["yun"] == 9
    for ls, lt in chart["luantou"].items():
        assert lt["advice"] and lt["quality"]


def test_enrich_api():
    """/xuankong 端点带 luantou。"""
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r = c.post("/api/v1/fengshui/xuankong", json={"sitting_mountain": "子", "year": 2024})
    d = r.json()["data"]
    assert "luantou" in d and "luantou_summary" in d


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
