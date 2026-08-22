"""
tests/test_liuyao_zhuang_gua.py
六爻·64卦装卦定式 / 世爻持世断 / 384爻六亲应事断
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.liuyao.zhuang_gua import (
    build_zhuang_gua, chi_shi_judgment, yao_yingshi, analyze_gua_static,
    all_64_table, _five_roles, LIU_QIN_SHENG, LIU_QIN_KE,
)
from core.liuyao.najia import get_liu_qin, PALACE_ELEMENT


def test_qian_zhuang_gua_classic():
    """乾为天装卦定式须与经典纳甲完全一致。"""
    zg = build_zhuang_gua(1)
    assert zg["success"]
    assert zg["palace"] == "乾" and zg["gua_type"] == "八纯卦"
    assert zg["world_line"] == 6 and zg["application_line"] == 3
    expect = [  # (地支, 六亲)
        ("子", "子孙"), ("寅", "妻财"), ("辰", "父母"),
        ("午", "官鬼"), ("申", "兄弟"), ("戌", "父母"),
    ]
    for row, (zhi, qin) in zip(zg["rows"], expect):
        assert row["zhi"] == zhi, f"{row['name']} 地支应{zhi}"
        assert row["liu_qin"] == qin, f"{row['name']} 六亲应{qin}"


def test_guihun_world_position():
    """归魂卦世在三爻（如火天大有/水地比）。"""
    for num in (14, 8):
        zg = build_zhuang_gua(num)
        assert zg["gua_type"] == "归魂卦"
        assert zg["world_line"] == 3 and zg["application_line"] == 6


def test_youhun_world_position():
    """游魂卦世在四爻（如火地晋 #35 / 雷山小过 #62）。"""
    for num in (35, 62):
        zg = build_zhuang_gua(num)
        assert zg["gua_type"] == "游魂卦"
        assert zg["world_line"] == 4


def test_all_64_zhuang_valid():
    """64 卦每卦六爻齐全、六亲皆五正、世应位合法且不同。"""
    valid_qin = {"父母", "兄弟", "子孙", "妻财", "官鬼"}
    for n in range(1, 65):
        zg = build_zhuang_gua(n)
        assert zg["success"], f"#{n} 失败"
        assert len(zg["rows"]) == 6
        for r in zg["rows"]:
            assert r["liu_qin"] in valid_qin
        w, a = zg["world_line"], zg["application_line"]
        assert 1 <= w <= 6 and 1 <= a <= 6 and w != a
        assert a == ((w - 1 + 3) % 6) + 1   # 应距世恒三位


def test_five_roles_bijection():
    """五神（用/元/忌/仇/制忌）对任一用神皆为六亲之满射双射。"""
    for yong in ("父母", "兄弟", "子孙", "妻财", "官鬼"):
        roles = _five_roles(yong)
        assert set(roles.keys()) == {"父母", "兄弟", "子孙", "妻财", "官鬼"}
        assert set(roles.values()) == {"用神", "元神", "忌神", "仇神", "制忌"}
        # 用神自身、元神生用、忌神克用
        assert roles[yong] == "用神"
        assert LIU_QIN_SHENG[[k for k,v in roles.items() if v=="元神"][0]] == yong
        assert LIU_QIN_KE[[k for k,v in roles.items() if v=="忌神"][0]] == yong


def test_qiucai_roles():
    """求财（用神妻财）：财=用、子孙=元、兄弟=忌、父母=仇、官鬼=制忌。"""
    r = _five_roles("妻财")
    assert r == {"妻财": "用神", "子孙": "元神", "兄弟": "忌神",
                 "父母": "仇神", "官鬼": "制忌"}


def test_chi_shi_lookup():
    """持世断：乾父母持世、坤兄弟? —— 世爻六亲须取自装卦，口诀非空。"""
    cs = chi_shi_judgment(1)
    assert cs["world_liu_qin"] == "父母"
    assert "父母持世" in cs["kou_jue"] or cs["kou_jue"]
    assert cs["jie_xi"] and cs["summary"]
    # 归魂卦 note 含"归魂"
    cs8 = chi_shi_judgment(8)
    assert "归魂" in cs8["pos_note"]


def test_chi_shi_all_64():
    """64 卦持世断皆有世爻六亲、口诀、解析。"""
    for n in range(1, 65):
        cs = chi_shi_judgment(n)
        assert cs["world_liu_qin"] in {"父母","兄弟","子孙","妻财","官鬼"}
        assert cs["kou_jue"] and cs["jie_xi"]


def test_yao_yingshi_gender_marriage():
    """婚姻用神随性别：男占以妻财为用、女占以官鬼为用。"""
    # 取一含妻财与官鬼的爻分别验证（乾：二爻妻财、四爻官鬼）
    ym = yao_yingshi(1, gender="male")
    cai_line = ym["lines"][1]   # 二爻妻财
    mh = next(t for t in cai_line["topics"] if t["topic"] == "婚姻")
    assert mh["role"] == "用神"      # 男占妻财为用
    yf = yao_yingshi(1, gender="female")
    cai_line_f = yf["lines"][1]
    mhf = next(t for t in cai_line_f["topics"] if t["topic"] == "婚姻")
    assert mhf["role"] != "用神"     # 女占妻财非用（官鬼才是）
    gui_line_f = yf["lines"][3]      # 四爻官鬼
    mhg = next(t for t in gui_line_f["topics"] if t["topic"] == "婚姻")
    assert mhg["role"] == "用神"


def test_disease_lawsuit_frames():
    """占病子孙=医药★、官鬼=病符✕；占讼子孙=解神★。"""
    ys = yao_yingshi(1)
    zisun = ys["lines"][0]   # 初爻子孙
    bing = next(t for t in zisun["topics"] if t["topic"] == "疾病")
    song = next(t for t in zisun["topics"] if t["topic"] == "官讼")
    assert "医药" in bing["quality"]
    assert "解神" in song["quality"]
    guigui = ys["lines"][3]  # 四爻官鬼
    bing2 = next(t for t in guigui["topics"] if t["topic"] == "疾病")
    assert "病符" in bing2["quality"]


def test_384_line_coverage():
    """64×6=384 爻全覆盖，每爻含求财/婚姻/疾病/官讼等分类应事。"""
    tbl = all_64_table()
    total = 0
    for n, v in tbl.items():
        lines = v["yao_yingshi"]["lines"]
        assert len(lines) == 6
        for ln in lines:
            total += 1
            topics = {t["topic"] for t in ln["topics"]}
            for must in ("求财", "婚姻", "疾病", "官讼", "求官", "考试", "求子"):
                assert must in topics, f"#{n} {ln['name']} 缺{must}"
            assert ln["summary"] and ln["liu_qin_meaning"]
    assert total == 384


def test_analyze_combined():
    """单卦综合：装卦+持世+应事 三件齐全。"""
    r = analyze_gua_static(1)
    assert r["zhuang_gua"]["success"]
    assert r["chi_shi"]["world_liu_qin"] == "父母"
    assert len(r["yao_yingshi"]["lines"]) == 6


def test_bad_input():
    assert build_zhuang_gua(0)["success"] is False
    assert build_zhuang_gua(65)["success"] is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
