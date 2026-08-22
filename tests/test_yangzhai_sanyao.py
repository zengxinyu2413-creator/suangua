"""
tests/test_yangzhai_sanyao.py
《阳宅三要》门主灶断法测试
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.fengshui.yangzhai_sanyao import (
    analyze_yangzhai_sanyao, _younian_between, get_best_layout,
)

# 八宅游年标准对照（部分关键对）
_STD = {
    ("坎", "离"): "延年", ("坎", "震"): "天医", ("坎", "巽"): "生气",
    ("坎", "坤"): "绝命", ("坎", "艮"): "五鬼", ("坎", "乾"): "六煞", ("坎", "兑"): "祸害",
    ("乾", "坤"): "延年", ("乾", "艮"): "天医", ("乾", "兑"): "生气",
    ("乾", "离"): "绝命", ("乾", "震"): "五鬼", ("乾", "巽"): "祸害", ("乾", "坎"): "六煞",
    ("震", "兑"): "绝命", ("艮", "兑"): "延年", ("坤", "艮"): "生气",
}


def test_younian_table_correct_and_symmetric():
    """游年表与八宅经典一致，且 A→B == B→A（关系互见）。"""
    for (a, b), exp in _STD.items():
        assert _younian_between(a, b) == exp, f"{a}→{b} 应{exp}"
        assert _younian_between(b, a) == exp, f"{b}→{a} 应对称={exp}"


def test_younian_each_gua_complete():
    """每卦对八卦的游年八星齐全不重复（伏生天延绝五六祸各一）。"""
    EIGHT = {"伏位", "生气", "天医", "延年", "绝命", "五鬼", "六煞", "祸害"}
    for g in "坎离震巽乾坤艮兑":
        stars = {_younian_between(g, o) for o in "坎离震巽乾坤艮兑"}
        assert stars == EIGHT, f"{g} 八星不全: {stars}"


def test_supreme_house():
    """坎门·巽主·震灶：全东四，门主生气、主灶延年 → 上吉。"""
    r = analyze_yangzhai_sanyao("坎", "巽", "震")
    assert r["success"]
    assert r["house_type"].startswith("坎门")
    assert r["relations"]["men_zhu"]["younian"] == "生气"
    assert r["relations"]["zhu_zao"]["younian"] == "延年"
    assert r["purity"]["pure"] is True
    assert r["grade"] == "上吉之宅"
    assert r["score"] >= 80


def test_jue_ming_house():
    """坎门·坤主：门主犯绝命，东西驳杂 → 大凶。"""
    r = analyze_yangzhai_sanyao("坎", "坤", "艮")
    assert r["relations"]["men_zhu"]["younian"] == "绝命"
    assert r["purity"]["pure"] is False
    assert r["grade"] == "大凶之宅"
    assert any("主房宜移" in a for a in r["advice"])


def test_west_four_pure():
    """乾门·兑主·坤灶：全西四，门主生气、主灶天医 → 吉。"""
    r = analyze_yangzhai_sanyao("乾", "兑", "坤")
    assert r["relations"]["men_zhu"]["younian"] == "生气"
    assert r["relations"]["zhu_zao"]["younian"] == "天医"
    assert r["purity"]["pure"] is True
    assert r["grade"] in ("上吉之宅", "次吉之宅")


def test_input_alias():
    """方位名/洛书数等别名应能识别。"""
    r1 = analyze_yangzhai_sanyao("北", "东南", "东")    # = 坎巽震
    r2 = analyze_yangzhai_sanyao("坎", "巽", "震")
    assert r1["score"] == r2["score"]
    r3 = analyze_yangzhai_sanyao("1", "4", "3")          # 洛书数
    assert r3["score"] == r2["score"]


def test_zao_facing():
    """灶口向吉方应给出纳吉提示。"""
    r = analyze_yangzhai_sanyao("坎", "坤", "艮", zao_facing="巽")  # 坎→巽生气
    assert any("灶口向巽" in a for a in r["advice"])


def test_bad_input():
    r = analyze_yangzhai_sanyao("XYZ", "巽", "震")
    assert r["success"] is False


def test_layout_table():
    """门卦八方游年布局表：吉星排前、八卦齐全。"""
    r = get_best_layout("坎")
    assert r["success"]
    assert len(r["layout"]) == 8
    assert r["layout"][0]["younian"] == "生气"      # 排序后最吉在前
    assert r["layout"][0]["level"] == "上吉"


def test_menzhu_database_complete():
    """64 门主局断语库完整、游年自洽、五维齐全。"""
    from core.fengshui.yangzhai_data import MENZHU_JU
    guas = "坎震巽离乾坤艮兑"
    assert len(MENZHU_JU) == 64
    req = ["ming", "younian", "wuxing", "level", "zong", "ding", "cai", "gongjian", "yingren"]
    for m in guas:
        for z in guas:
            v = MENZHU_JU[(m, z)]
            assert v["younian"] == _younian_between(m, z), f"{m}{z} 游年不符"
            for f in req:
                assert v[f], f"{m}{z}.{f} 为空"
            # 每局断语须有实质字数（非占位）
            assert len(v["zong"]) >= 30


def test_analyze_includes_detail():
    """主分析输出须含 64 局详断与灶配断。"""
    r = analyze_yangzhai_sanyao("坎", "巽", "离")
    assert r["menzhu_ju"]["ming"] == "坎门巽主·生气一四同宫局"
    assert "一四同宫" in r["menzhu_ju"]["zong"]
    assert all(r["menzhu_ju"][k] for k in ("ding", "cai", "gongjian", "yingren"))
    assert r["zao_ju"]["desc"]


def test_house_overview():
    """八宅总论：八宅各有总论、坐向、三吉方。"""
    from core.fengshui.yangzhai_data import HOUSE_OVERVIEW
    assert len(HOUSE_OVERVIEW) == 8
    for g in "坎离震巽乾坤艮兑":
        ov = HOUSE_OVERVIEW[g]
        assert ov["name"] and ov["facing"] and len(ov["best"]) == 3 and len(ov["desc"]) >= 40
    r = analyze_yangzhai_sanyao("离", "震", "坎")
    assert r["house_overview"]["name"] == "离宅"
    assert r["house_overview"]["facing"] == "坐南朝北"


def test_24shan_door():
    """二十四山门向：识别山名、三元龙、地/人元给兼向提示。"""
    from core.fengshui.yangzhai_sanyao import parse_door
    assert parse_door("壬")["gua"] == "坎" and parse_door("壬")["yuan"] == "地"
    assert parse_door("午")["gua"] == "离" and parse_door("午")["yuan"] == "天"
    r = analyze_yangzhai_sanyao("壬", "巽", "离")
    assert r["house_type"].startswith("壬山")
    assert r["door_detail"]["shan"] == "壬"
    assert r["door_detail"]["jian_note"]   # 地元龙→兼向提示
    # 天元龙(子)正向，无兼向提示
    r2 = analyze_yangzhai_sanyao("子", "巽", "离")
    assert r2["door_detail"]["yuan"] == "天"
    assert not r2["door_detail"]["jian_note"]


def test_zao_seat_and_mouth():
    """灶座(主→灶)+灶口向(门→灶口)完整断，构成512局之灶环。"""
    from core.fengshui.yangzhai_data import ZAO_SEAT, ZAO_MOUTH
    assert len(ZAO_SEAT) == 8 and len(ZAO_MOUTH) == 8
    for s in ("生气", "天医", "延年", "伏位", "祸害", "六煞", "五鬼", "绝命"):
        assert len(ZAO_SEAT[s]["d"]) >= 30
    # 灶口向：门坎→震=天医（吉）
    r = analyze_yangzhai_sanyao("坎", "巽", "离", zao_facing="震")
    assert r["zao_ju"]["mouth_star"] == "天医"
    assert "灶口" in r["zao_ju"]["desc"]


def test_512_coverage():
    """64门主 × 8灶 = 512 组合，每组皆有具体门主局断+灶座断（无空）。"""
    guas = "坎震巽离乾坤艮兑"
    n = 0
    for men in guas:
        for zhu in guas:
            for zao in guas:
                r = analyze_yangzhai_sanyao(men, zhu, zao)
                assert r["success"]
                assert r["menzhu_ju"]["zong"]      # 门主局断非空
                assert r["zao_ju"]["desc"]         # 灶断非空
                assert r["grade"]
                n += 1
    assert n == 512


def test_star_full():
    """游年八星全解：人物/身体/应期/方位宜忌齐全。"""
    from core.fengshui.yangzhai_data import STAR_FULL
    assert len(STAR_FULL) == 8
    for s, v in STAR_FULL.items():
        assert v["jiuxing"] and v["duan"] and v["yi"] and v["ying"] and v["fang"]


def test_full_judgment_512():
    """512整局成文断：每组合皆有连贯成文 + 整局定名定级。"""
    from core.fengshui.yangzhai_sanyao import synthesize_full_judgment
    r = synthesize_full_judgment("坎", "巽", "震")
    assert r["full_ju"]["ju_name"] == "坎门巽主震灶局"
    assert r["full_ju"]["ju_grade"] in ("上上局", "上吉局", "次吉局", "平常局", "凶局", "大凶局")
    assert len(r["full_ju"]["full_text"]) >= 150   # 整局成文须有实质长度
    # 抽查多组皆成文
    for men in "坎乾":
        for zhu in "巽坤":
            for zao in "震兑":
                rr = synthesize_full_judgment(men, zhu, zao)
                assert rr["full_ju"]["full_text"] and rr["full_ju"]["ju_grade"]


def test_floor_wuxing():
    """论层数：坎宅(水)宜1/6水比和、4/9金生水；忌5/10土克水。"""
    from core.fengshui.yangzhai_floors import analyze_floor, best_floors
    assert analyze_floor("坎", 1)["quality"] == "吉"   # 水比和
    assert analyze_floor("坎", 6)["quality"] == "吉"
    assert analyze_floor("坎", 4)["quality"] == "吉"   # 金生水
    assert analyze_floor("坎", 5)["quality"] == "凶"   # 土克水
    bf = best_floors("坎")
    assert 1 in bf["best_floors"] and 5 in bf["worst_floors"]


def test_chuangong():
    """穿宫九星：自门起逐进排星，吉进宜高、凶进宜低。"""
    from core.fengshui.yangzhai_floors import chuangong_jiuxing
    cg = chuangong_jiuxing("坎", 5)
    assert len(cg["rows"]) == 5
    assert cg["rows"][0]["star"] == "伏位"
    assert cg["rows"][1]["star"] == "生气"
    assert all("高大" in r["advice"] or "低矮" in r["advice"] for r in cg["rows"])


def test_full_with_floor_jin():
    """整局可附楼层与穿宫。"""
    from core.fengshui.yangzhai_sanyao import synthesize_full_judgment
    r = synthesize_full_judgment("坎", "巽", "震", floor=6, jin=3)
    assert r["floor"]["quality"] == "吉"
    assert len(r["chuangong"]["rows"]) == 3
    assert r["floor_guide"]["best_floors"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
