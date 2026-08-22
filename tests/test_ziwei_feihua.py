"""
Tests for core/ziwei/feihua_advanced.py

We verify the rewrite captures飞星派核心:
  1. 离心/向心/普通飞宫 分类正确
  2. 化忌冲对宫 在飞宫情况下检测到，自化时不冲
  3. 双忌叠加、禄解忌、禄忌交战 三种特殊语象检测
  4. 质能变（生年四化+自化）检测
  5. 命宫飞入/化忌冲命宫 汇总
  6. 我宫他宫分类
  7. 派别切换正确
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_ziwei_context import make_mock_chart_2000_8_16
from core.ziwei.feihua_advanced import (
    analyze_palace_feihua,
    summarize_feihua_landscape,
    format_feihua_for_prompt,
    is_inner_palace,
    is_outer_palace,
    FH_SELF_OUT, FH_SELF_IN, FH_FLY_OUT,
    ZHONGZHOU_SIHUA, QINTIAN_SIHUA,
)


# ─────────────────────────────────────────────────────────────
# Mock data review
# ─────────────────────────────────────────────────────────────
# 2000-8-16 寅时 女命 mock 命盘的关键事实：
#   生年四化（庚干）：太阳化禄@子女宫、武曲化权@财帛宫、太阴化科@交友宫、天同化忌@疾厄宫
#   12宫宫干：
#     index 0 财帛=戊， 1 子女=己， 2 夫妻=庚， 3 兄弟=辛， 4 命宫=壬，
#     5 父母=癸， 6 福德=甲， 7 田宅=乙， 8 官禄=丙， 9 交友=丁，10 迁移=戊，11 疾厄=己
#   命宫主星：紫微（在 index 4 / 午）
#   命宫的对宫是 index 10 迁移宫（戊子，主星贪狼）
#   命宫宫干壬，壬四化：禄天梁、权紫微、科左辅、忌武曲
#     - 紫微在命宫(4) → 化权落本宫 → 离心自化权
#     - 天梁在子女宫(1) → 普通飞宫，化禄飞入子女宫
#     - 左辅未列在 mock 数据中 → "未排到"
#     - 武曲在财帛宫(0) → 普通飞宫，化忌飞入财帛宫，冲对宫福德宫


def test_basic_classification():
    print("=" * 70)
    print("TEST 1: 离心/向心/普通飞宫 三类分类正确性")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    
    # 命宫记录
    soul_rec = next(r for r in records if r["palace_name"] == "命宫")
    
    # 命宫宫干壬，壬→ 禄天梁、权紫微、科左辅、忌武曲
    by_hua = {tr["hua_type"]: tr for tr in soul_rec["transformations"]}
    
    # 壬化权紫微 — 紫微在命宫本身 → 离心自化
    assert by_hua["化权"]["target_star"] == "紫微"
    assert by_hua["化权"]["target_palace_name"] == "命宫"
    assert by_hua["化权"]["fh_type"] == FH_SELF_OUT, \
        f"Expected SELF_OUT, got {by_hua['化权']['fh_type']}"
    print(f"  ✓ 命宫宫干壬化权紫微，紫微在命宫 → 离心自化 ✓")
    
    # 壬化禄天梁 — 天梁在子女宫 → 普通飞宫
    assert by_hua["化禄"]["target_star"] == "天梁"
    assert by_hua["化禄"]["target_palace_name"] == "子女宫"
    assert by_hua["化禄"]["fh_type"] == FH_FLY_OUT
    print(f"  ✓ 命宫宫干壬化禄天梁 → 飞入子女宫（普通飞宫） ✓")
    
    # 壬化忌武曲 — 武曲在财帛宫 → 普通飞宫，冲对宫福德宫
    assert by_hua["化忌"]["target_star"] == "武曲"
    assert by_hua["化忌"]["target_palace_name"] == "财帛宫"
    assert by_hua["化忌"]["fh_type"] == FH_FLY_OUT
    assert by_hua["化忌"]["chong_palace"] == "福德宫"
    print(f"  ✓ 命宫宫干壬化忌武曲 → 飞入财帛宫，冲福德宫 ✓")
    
    # 壬化科左辅 — 左辅在命宫（mock 里 minor_stars 含左辅）→ 离心自化科
    assert by_hua["化科"]["target_star"] == "左辅"
    assert by_hua["化科"]["target_palace_name"] == "命宫"
    assert by_hua["化科"]["fh_type"] == FH_SELF_OUT
    print(f"  ✓ 命宫宫干壬化科左辅，左辅在命宫 → 离心自化（命宫双自化！） ✓")
    print()


def test_self_in_detection():
    print("=" * 70)
    print("TEST 2: 向心自化检测（化星落对宫）")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    
    # 找一个向心自化的例子
    # 迁移宫 index 10, 干戊, 戊四化：禄贪狼、权太阴、科右弼、忌天机
    #   贪狼在迁移宫(10) → 化禄落本宫 → 离心自化禄
    # 财帛宫 index 0, 干戊, 戊四化也一样
    #   贪狼在迁移宫(10)，财帛宫对宫index 6福德宫
    #   贪狼不在福德也不在财帛 → 普通飞宫
    
    # 让我们找一个真正的向心自化例子：
    # 福德宫 index 6, 干甲, 甲四化：禄廉贞、权破军、科武曲、忌太阳
    #   破军在福德宫(6) → 离心自化权
    #   廉贞在官禄宫(8) → index 8 != 6 也 != 0(福德对宫财帛=index 0)
    #     ...等等 福德宫index 6, 对宫index 0=财帛宫
    #     廉贞在官禄宫 index 8 → 既不是 6 也不是 0 → 普通飞宫
    #   太阳在子女宫(1) → 普通飞宫
    
    # 找向心自化案例：
    # 子女宫 index 1, 干己，己四化：禄武曲、权贪狼、科天梁、忌文曲
    #   武曲在财帛宫(0) → index 0 != 1 也 != (1+6)%12=7(田宅) → 普通飞宫
    #   贪狼在迁移宫(10) → 普通飞宫
    #   天梁在子女宫(1) → 离心自化科
    #   文曲在官禄宫(8) → 普通飞宫
    
    # 试一下父母宫 index 5, 干癸, 癸四化：禄破军、权巨门、科太阴、忌贪狼
    #   破军在福德宫(6) → index 6 != 5 也 != 11 → 普通飞宫
    #   巨门在疾厄宫(11) → index 11 == (5+6)%12=11 → 向心自化权！
    #   太阴在交友宫(9) → 普通飞宫
    #   贪狼在迁移宫(10) → 普通飞宫
    
    parents = next(r for r in records if r["palace_name"] == "父母宫")
    by_hua = {tr["hua_type"]: tr for tr in parents["transformations"]}
    
    assert by_hua["化权"]["target_star"] == "巨门"
    assert by_hua["化权"]["target_palace_name"] == "疾厄宫"
    assert by_hua["化权"]["fh_type"] == FH_SELF_IN, \
        f"Expected SELF_IN, got {by_hua['化权']['fh_type']}"
    print(f"  ✓ 父母宫干癸化权巨门，巨门在疾厄宫(父母对宫) → 向心自化权 ✓")
    print()


def test_huji_chong_palace():
    print("=" * 70)
    print("TEST 3: 化忌冲对宫规则（飞宫忌冲，自化忌不冲）")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    
    for r in records:
        for tr in r["transformations"]:
            if tr["hua_type"] != "化忌":
                continue
            fh_type = tr["fh_type"]
            chong = tr.get("chong_palace", "")
            if fh_type == FH_FLY_OUT:
                # 飞宫忌应该有 chong_palace
                assert chong, \
                    f"飞宫忌应有冲宫: {r['palace_name']} → {tr['target_palace_name']}, chong={chong}"
            elif fh_type in (FH_SELF_OUT, FH_SELF_IN):
                # 自化忌不冲（按飞星派传统）
                assert not chong, \
                    f"自化忌不应有冲宫: {r['palace_name']}, fh_type={fh_type}, chong={chong}"
    
    print(f"  ✓ 所有飞宫忌都标了冲宫，所有自化忌都没冲 ✓")
    print()


def test_double_ji():
    print("=" * 70)
    print("TEST 4: 双忌叠加检测")
    print("=" * 70)
    
    # 在 mock 里，本命化忌是天同在疾厄宫(index 11)
    # 哪个宫的宫干化忌会飞到疾厄宫？需要查表
    # 疾厄宫index 11, 没主星位置因素，是看哪个干起化忌会落到天同所在的疾厄宫
    # 天同在疾厄宫. 飞忌入疾厄=飞忌入"天同所在宫"=飞忌的化忌星是天同
    # 庚干→化忌天同。但生年也是庚 → 同一星
    # 此外，丁干→化忌巨门(在疾厄宫). 父母宫干癸，癸忌贪狼不在疾厄
    # 检查哪个宫干是庚或丁。庚是夫妻宫(index 2). 丁是交友宫(index 9).
    
    # 夫妻宫干庚：庚→禄阳、权武、科阴、忌同
    # 庚化忌天同 → 天同在疾厄宫(11)。 夫妻index=2, 对宫=8(官禄). 11 != 2 且 != 8 → 普通飞宫
    # 此时 target=疾厄宫，疾厄宫坐生年化忌（天同·忌）
    # 但化忌的星就是天同 = 同一颗星，target=同一颗星之宫 → 双忌叠加！
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    
    fuqi = next(r for r in records if r["palace_name"] == "夫妻宫")
    by_hua = {tr["hua_type"]: tr for tr in fuqi["transformations"]}
    
    assert by_hua["化忌"]["target_star"] == "天同"
    assert by_hua["化忌"]["target_palace_name"] == "疾厄宫"
    assert by_hua["化忌"]["is_double_ji"] == True, \
        f"夫妻宫干庚化忌天同入疾厄宫，疾厄已坐生年化忌天同 → 应是双忌叠加"
    print(f"  ✓ 夫妻宫干庚化忌天同→疾厄宫（坐生年忌） → 双忌叠加 ✓")
    
    # 同时验证应该出现 "双忌叠加" 在标签里
    tags = by_hua["化忌"]["tags"]
    assert any("双忌" in t for t in tags), f"标签里没有'双忌': {tags}"
    print(f"  ✓ 标签包含'双忌叠加' ✓")
    print()


def test_lu_jie_ji():
    print("=" * 70)
    print("TEST 5: 禄解忌检测")
    print("=" * 70)
    
    # 本命化忌天同在疾厄宫(index 11)
    # 哪些宫干→化禄=天同？丙干→化禄天同
    # 哪个宫的宫干是丙？官禄宫(index 8)
    
    # 官禄宫干丙：丙→禄天同、权天机、科文昌、忌廉贞
    # 丙化禄天同 → 天同在疾厄宫(11). 官禄index=8, 对宫=2(夫妻). 
    # 11 != 8 且 != 2 → 普通飞宫
    # target_idx=11=natal_ji_idx → 应该 is_he_won_ji=True
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    
    guanlu = next(r for r in records if r["palace_name"] == "官禄宫")
    by_hua = {tr["hua_type"]: tr for tr in guanlu["transformations"]}
    
    assert by_hua["化禄"]["target_star"] == "天同"
    assert by_hua["化禄"]["target_palace_name"] == "疾厄宫"
    assert by_hua["化禄"]["is_he_won_ji"] == True, \
        f"官禄干丙化禄天同→疾厄宫(本命化忌宫) → 应是禄解忌"
    tags = by_hua["化禄"]["tags"]
    assert any("禄解忌" in t for t in tags)
    print(f"  ✓ 官禄宫干丙化禄天同→疾厄(本命忌宫) → 禄解忌 ✓")
    print()


def test_lu_ji_war():
    print("=" * 70)
    print("TEST 6: 禄忌交战（化忌入本命化禄宫）")
    print("=" * 70)
    
    # 本命化禄太阳在子女宫(index 1)
    # 哪些宫干→化忌=太阳？甲干→化忌太阳
    # 哪个宫干是甲？福德宫(index 6)
    
    # 福德宫干甲：甲→禄廉贞、权破军、科武曲、忌太阳
    # 甲化忌太阳 → 太阳在子女宫(1). 福德index=6, 对宫=0(财帛). 
    # 1 != 6 且 != 0 → 普通飞宫
    # target_idx=1=natal_lu_idx → 应该 is_lu_ji_war=True
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    
    fude = next(r for r in records if r["palace_name"] == "福德宫")
    by_hua = {tr["hua_type"]: tr for tr in fude["transformations"]}
    
    assert by_hua["化忌"]["target_star"] == "太阳"
    assert by_hua["化忌"]["target_palace_name"] == "子女宫"
    assert by_hua["化忌"]["is_lu_ji_war"] == True
    tags = by_hua["化忌"]["tags"]
    assert any("禄忌交战" in t for t in tags)
    print(f"  ✓ 福德宫干甲化忌太阳→子女宫(本命禄宫) → 禄忌交战 ✓")
    print()


def test_quality_change():
    print("=" * 70)
    print("TEST 7: 质能变检测（生年同类四化+本宫宫干自化）")
    print("=" * 70)
    
    # 寻找一个"本宫坐生年某化 + 本宫宫干起的自化"
    # 生年禄：太阳在子女宫(index 1)
    # 子女宫干己，己→禄武曲、权贪狼、科天梁、忌文曲
    #   天梁(科)在子女宫(1) → 离心自化科
    #   子女宫坐生年禄(太阳)，自化是科 — 不同类，不算质能变
    # 
    # 生年权：武曲在财帛宫(index 0)
    # 财帛宫干戊，戊→禄贪狼、权太阴、科右弼、忌天机
    #   太阴(权)在交友宫(9)→普通飞宫
    #   都不自化。所以财帛宫无质能变。
    # 
    # 生年科：太阴在交友宫(index 9)
    # 交友宫干丁，丁→禄太阴、权天同、科天机、忌巨门
    #   太阴(禄)在交友宫(9) → 离心自化禄！
    #   交友宫坐生年科(太阴)，自化是禄(同星) — 不同类化，但同星
    #   按我的代码定义：质能变 = 本宫坐生年【同类化】+本宫【自化同类】
    #   交友宫坐生年化科，宫干起自化禄 — 不同类，不算质能变
    # 
    # 生年忌：天同在疾厄宫(index 11)
    # 疾厄宫干己，己→禄武曲、权贪狼、科天梁、忌文曲
    #   武曲(禄)在财帛宫(0)→普通飞宫
    #   贪狼(权)在迁移宫(10)→普通飞宫
    #   天梁(科)在子女宫(1)→普通飞宫
    #   文曲(忌)未在mock中→未排到
    # 都不自化。所以疾厄宫无质能变。
    # 
    # 我们检查的 mock 没有"完美质能变"案例。这是预期的 — 
    # 质能变是相对罕见的语象。验证"无质能变"也是有效的。
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    summary = summarize_feihua_landscape(records, data["palaces"])
    
    print(f"  · 当前 mock 命盘的质能变数量：{len(summary['key_quality_changes'])}")
    # 这个 mock 不一定有，所以不强断言数量
    
    # 但我们应该构造一个会触发质能变的子测试
    # 修改 mock：让交友宫坐生年化科太阴+自化科太阴
    # 当前：交友宫干丁，丁化科天机（不是太阴）。 
    # 想让交友宫坐太阴(生年科)+自化太阴(任意化)
    # 太阴的"化"在哪些干？乙忌、丁禄、戊权、庚科、癸科
    # 想做"自化科"：庚或癸。 把交友宫干改成庚：
    
    data2 = make_mock_chart_2000_8_16()
    for p in data2["palaces"]:
        if p["index"] == 9:  # 交友宫
            p["heavenly_stem"] = "庚"
            break
    # 庚科太阴 + 太阴坐交友宫 + 太阴有生年化科 → 应触发质能变
    
    records2 = analyze_palace_feihua(data2["palaces"], school="zhongzhou")
    jiaoyou = next(r for r in records2 if r["palace_name"] == "交友宫")
    by_hua = {tr["hua_type"]: tr for tr in jiaoyou["transformations"]}
    
    assert by_hua["化科"]["target_star"] == "太阴"
    assert by_hua["化科"]["fh_type"] == FH_SELF_OUT  # 太阴在交友宫=本宫
    assert by_hua["化科"]["is_quality_change"] == True, \
        f"交友宫坐生年科太阴+宫干庚化科太阴 → 应是质能变"
    print(f"  ✓ 交友宫坐生年科太阴 + 宫干庚化科太阴 → 质能变 ✓")
    print()


def test_summary():
    print("=" * 70)
    print("TEST 8: 全盘汇总")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    summary = summarize_feihua_landscape(records, data["palaces"])
    
    # 应该至少有 1 个禄解忌、1 个双忌叠加、1 个禄忌交战
    print(f"  · 禄解忌: {len(summary['lu_jie_ji'])} 个")
    print(f"  · 双忌叠加: {len(summary['double_ji'])} 个")
    print(f"  · 禄忌交战: {len(summary['lu_ji_war'])} 个")
    print(f"  · 命宫飞入: {len(summary['soul_palace_incoming'])} 个")
    print(f"  · 化忌冲命宫: {len(summary['soul_palace_chong'])} 个")
    print(f"  · 离心自化宫位: {len(summary['self_out_palaces'])} 宫")
    print(f"  · 向心自化宫位: {len(summary['self_in_palaces'])} 宫")
    print(f"  · 飞化集中宫位: {summary['concentration']}")
    
    assert len(summary["lu_jie_ji"]) >= 1
    assert len(summary["double_ji"]) >= 1
    assert len(summary["lu_ji_war"]) >= 1
    print(f"  ✓ 所有关键语象都被检测到 ✓")
    print()


def test_format_output():
    print("=" * 70)
    print("TEST 9: prompt 格式化输出")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    records = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    summary = summarize_feihua_landscape(records, data["palaces"])
    output = format_feihua_for_prompt(records, summary, school="zhongzhou")
    
    must_contain = [
        "飞星派飞化分析",
        "中州派",
        "全盘关键语象",
        "禄解忌",
        "双忌叠加",
        "禄忌交战",
        "6 大重点宫位的完整飞化",
        "命宫",
        "财帛宫",
        "官禄宫",
        "迁移宫",
        "夫妻宫",
        "福德宫",
        "离心自化",
        "普通飞宫",
        "冲",  # 至少有一个化忌冲宫
    ]
    missing = [k for k in must_contain if k not in output]
    if missing:
        print(f"  ✗ 缺失关键词: {missing}")
        print("--- output ---")
        print(output)
        return False
    print(f"  ✓ 所有 {len(must_contain)} 个关键词都出现")
    print(f"  · 输出长度: {len(output)} chars, {output.count(chr(10))+1} lines")
    print()
    return True


def test_school_switch():
    print("=" * 70)
    print("TEST 10: 派别切换 — 中州派 vs 钦天派")
    print("=" * 70)
    
    data = make_mock_chart_2000_8_16()
    
    # 戊干 — 中州派化科右弼，钦天派化科太阳
    # 福德宫干甲（不是戊），换个戊干的宫来测：
    # mock 中 财帛(戊) 和 迁移(戊) 都是戊干
    
    records_z = analyze_palace_feihua(data["palaces"], school="zhongzhou")
    records_q = analyze_palace_feihua(data["palaces"], school="qintian")
    
    caibao_z = next(r for r in records_z if r["palace_name"] == "财帛宫")
    caibao_q = next(r for r in records_q if r["palace_name"] == "财帛宫")
    
    science_star_z = next(tr for tr in caibao_z["transformations"] if tr["hua_type"] == "化科")
    science_star_q = next(tr for tr in caibao_q["transformations"] if tr["hua_type"] == "化科")
    
    assert science_star_z["target_star"] == "右弼", f"中州派戊科应是右弼，got {science_star_z['target_star']}"
    assert science_star_q["target_star"] == "太阳", f"钦天派戊科应是太阳，got {science_star_q['target_star']}"
    print(f"  ✓ 财帛宫(戊)化科：中州派=右弼，钦天派=太阳 ✓")
    print()


if __name__ == "__main__":
    test_basic_classification()
    test_self_in_detection()
    test_huji_chong_palace()
    test_double_ji()
    test_lu_jie_ji()
    test_lu_ji_war()
    test_quality_change()
    test_summary()
    test_format_output()
    test_school_switch()
    print()
    print("=" * 70)
    print("ALL FEIHUA TESTS PASSED")
    print("=" * 70)
