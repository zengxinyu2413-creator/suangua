"""
tests/test_liuyao_yingqi.py
六爻应期精算专项测试（古法规则 + 公历日期映射）
"""
import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.yingqi_calculator import calculate_yingqi

DIVINE = datetime(2026, 6, 24, 14, 0, 0)   # 己巳日 · 固定便于复现
DAY_ZHI, MONTH_ZHI = "巳", "未"


def _yao(liu_qin, branch, label, **kw):
    base = {"liu_qin": liu_qin, "branch": branch, "element": "",
            "strength": {"label": label}, "kong_wang": False,
            "is_changing": False, "position": kw.get("position", 3)}
    base.update(kw)
    return base


def _primary_branch(yaos, ys, kong=None):
    r = calculate_yingqi(yaos, ys, day_zhi=DAY_ZHI, month_zhi=MONTH_ZHI,
                         kong_wang=kong or [], divine_date=DIVINE)
    assert r["available"], r
    return r["primary"]["branch"], r["primary"]["type"], r


def test_jing_wang_chong():
    """旺静用神 → 静者待冲：巳火逢亥冲。"""
    b, t, r = _primary_branch([_yao("妻财", "巳", "旺")], "妻财")
    assert b == "亥" and t == "逢冲应期"
    # 日期落点为真实干支
    assert r["primary"]["ganzhi"].endswith("亥")


def test_kong_chu_kong():
    """旬空用神 → 出空填实本支日。"""
    b, t, r = _primary_branch(
        [_yao("妻财", "申", "休", kong_wang=True)], "妻财", kong=["申", "酉"])
    assert b == "申" and t == "出空填实"
    assert r["primary"]["ganzhi"].endswith("申")


def test_ru_mu_chong_mu():
    """化入墓 → 冲墓开库：午化戌墓，待辰冲戌。"""
    b, t, _ = _primary_branch(
        [_yao("官鬼", "午", "旺", is_changing=True, changed_branch="戌")], "官鬼")
    assert b == "辰" and t == "冲墓开库"


def test_hua_jin_shen():
    """化进神 → 应于进神之支：寅化卯。"""
    b, t, _ = _primary_branch(
        [_yao("子孙", "寅", "相", is_changing=True, changed_branch="卯")], "子孙")
    assert b == "卯" and t == "化进神日"


def test_hui_tou_sheng():
    """化回头生 → 冲化神之日事成：戌化午，子冲午。"""
    b, t, _ = _primary_branch(
        [_yao("父母", "戌", "休", is_changing=True, changed_branch="午")], "父母")
    assert b == "子" and t == "冲化神日"


def test_dates_are_future_and_real():
    """所有候选落点应为占卦日之后、且日支与候选地支一致。"""
    r = calculate_yingqi([_yao("妻财", "巳", "旺")], "妻财",
                         day_zhi=DAY_ZHI, month_zhi=MONTH_ZHI, divine_date=DIVINE)
    for c in r["candidates"]:
        for d in c["dates"]:
            assert d["days_ahead"] >= 1
            if d["scope"] == "日":
                assert d["ganzhi"][-1] == c["branch"]


def test_no_yong_shen_graceful():
    """用神缺失时优雅降级，不抛异常。"""
    r = calculate_yingqi([_yao("兄弟", "丑", "旺")], "妻财",
                         day_zhi=DAY_ZHI, month_zhi=MONTH_ZHI, divine_date=DIVINE)
    assert r["available"] is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
