"""
tests/test_yangzhai_liushi.py
《阳宅六事》（路·井·灶·厕·碓磨·畜栏）安置断测试
总则：净者居吉方，秽者镇凶方。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.fengshui.yangzhai_liushi import (
    analyze_one_item, analyze_liushi, liushi_best_positions,
    LIUSHI_META, LIUSHI_GENERAL,
)
from core.fengshui.yangzhai_sanyao import (
    _younian_between, JI_STARS, XIONG_STARS, GUA_NAME_NUM,
)


def test_meta_complete():
    """六事元数据齐全：每事有性质、宜向、专则。"""
    for name in ("门", "路", "井", "灶", "厕", "碓磨", "畜栏"):
        m = LIUSHI_META[name]
        assert m["nature"] and m["principle"]
        assert m["prefers"] in ("吉", "凶")
    # 净物宜吉、秽物宜凶
    assert LIUSHI_META["井"]["prefers"] == "吉"
    assert LIUSHI_META["路"]["prefers"] == "吉"
    assert LIUSHI_META["厕"]["prefers"] == "凶"
    assert LIUSHI_META["碓磨"]["prefers"] == "凶"
    assert LIUSHI_META["畜栏"]["prefers"] == "凶"


def test_clean_item_prefers_lucky():
    """净物（井）置吉方为吉、置凶方为凶。"""
    # 坎门→巽=生气(吉)，井宜
    r = analyze_one_item("坎", "井", "巽")
    assert r["younian"] == "生气" and r["quality"] == "吉"
    # 坎门→坤=绝命(凶)，净物失位
    r = analyze_one_item("坎", "井", "坤")
    assert r["younian"] == "绝命" and r["quality"] == "凶"


def test_dirty_item_prefers_unlucky():
    """秽物（厕）压凶方为吉（合用）、占吉方为凶。"""
    # 坎门→艮=五鬼(凶)，厕压煞为用
    r = analyze_one_item("坎", "厕", "艮")
    assert r["younian"] == "五鬼" and r["quality"] == "吉"
    assert "压" in r["judgment"] or "镇" in r["judgment"]
    # 坎门→震=天医(吉)，秽占吉方为凶
    r = analyze_one_item("坎", "厕", "震")
    assert r["younian"] == "天医" and r["quality"] == "凶"


def test_center_taboo():
    """井/厕/碓磨/畜栏居中宫皆大忌。"""
    for it in ("井", "厕", "碓磨", "畜栏"):
        r = analyze_one_item("坎", it, "中宫")
        assert r["place"] == "中宫" and r["quality"] == "凶"
        assert "中宫" in r["judgment"]


def test_well_wuxing_note():
    """井属水：居火方(离)有水火相激提示，居金水方井泉清旺。"""
    r = analyze_one_item("坎", "水井", "离")   # 离=火方
    assert any("水火" in e for e in r["extra"])
    r2 = analyze_one_item("坎", "井", "兑")     # 兑=金方
    assert any("清旺" in e for e in r2["extra"])


def test_item_aliases():
    """别名归一：厕所/卫生间→厕，石磨→碓磨，水井→井。"""
    assert analyze_one_item("坎", "厕所", "艮")["item"] == "厕"
    assert analyze_one_item("坎", "卫生间", "艮")["item"] == "厕"
    assert analyze_one_item("坎", "石磨", "坤")["item"] == "碓磨"
    assert analyze_one_item("坎", "水井", "巽")["item"] == "井"
    assert analyze_one_item("坎", "猪圈", "坤")["item"] == "畜栏"


def test_position_alias():
    """安置方位支持八方位/洛书数/二十四山。"""
    r1 = analyze_one_item("坎", "井", "东南")    # = 巽
    r2 = analyze_one_item("坎", "井", "4")        # 巽=4
    r3 = analyze_one_item("坎", "井", "巽")
    assert r1["quality"] == r2["quality"] == r3["quality"] == "吉"


def test_analyze_liushi_all_good():
    """坎门：井@巽(生气)、厕@艮(五鬼)、碓磨@坤(绝命)、路@震(天医) → 六事俱合。"""
    r = analyze_liushi("坎", {"井": "巽", "厕": "艮", "碓磨": "坤", "路": "震"})
    assert r["success"]
    assert r["good_count"] == 4 and r["bad_count"] == 0
    assert r["grade"] == "六事俱合"


def test_analyze_liushi_misplaced():
    """净秽倒置：井@坤(绝命)、厕@巽(生气) → 多有失位。"""
    r = analyze_liushi("坎", {"井": "坤", "厕": "巽"})
    assert r["bad_count"] == 2
    assert "失位" in r["grade"] or r["bad_count"] > r["good_count"]


def test_interaction_dangmen():
    """当门冲：厕与门同方 → 开门见厕警示。"""
    r = analyze_liushi("坎", {"厕": "坎"})   # 门在坎，厕亦坎
    assert any("当门" in w for w in r["interaction_warnings"])


def test_interaction_well_stove():
    """井灶同方 → 水火相射警示。"""
    r = analyze_liushi("坎", {"井": "震", "灶": "震"})
    assert any("水火相射" in w for w in r["interaction_warnings"])


def test_best_positions():
    """六事宜方表：净物列吉方、秽物列凶方，且与门游年自洽。"""
    bp = liushi_best_positions("坎")
    assert bp["success"]
    # 井（净）推荐方全为吉星
    for x in bp["items"]["井"]["recommend"]:
        assert _younian_between("坎", x["gua"]) in JI_STARS
    # 厕（秽）推荐方全为凶星
    for x in bp["items"]["厕"]["recommend"]:
        assert _younian_between("坎", x["gua"]) in XIONG_STARS
    assert bp["items"]["厕"]["center_taboo"] is True


def test_general_principle():
    """六事总则文案完整。"""
    assert "净者居吉方" in LIUSHI_GENERAL["principle"]
    assert len(LIUSHI_GENERAL["detail"]) >= 60


def test_full_judgment_with_liushi():
    """整局成文可附六事断 + 六事宜方表。"""
    from core.fengshui.yangzhai_sanyao import synthesize_full_judgment
    r = synthesize_full_judgment("坎", "巽", "震",
                                 liushi={"井": "巽", "厕": "艮"})
    assert r["liushi"]["success"]
    assert r["liushi"]["good_count"] == 2
    assert r["liushi_guide"]["items"]["井"]["recommend"]


def test_all_eight_doors_have_guide():
    """八门皆能生成六事宜方表，净物吉方/秽物凶方各四。"""
    for men in "坎离震巽乾坤艮兑":
        bp = liushi_best_positions(men)
        assert bp["success"]
        # 净物恒有 4 吉方（含伏位），秽物恒有 4 凶方
        assert len(bp["items"]["井"]["recommend"]) == 4
        assert len(bp["items"]["厕"]["recommend"]) == 4


def test_bad_input():
    assert analyze_one_item("XYZ", "井", "巽")["success"] is False
    assert analyze_one_item("坎", "未知物", "巽")["success"] is False
    assert analyze_liushi("坎", {})["success"] is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
