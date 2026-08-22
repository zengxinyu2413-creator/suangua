"""
Quick smoke test for core/ziwei/context_builder.py

Uses mocked iztro_py-shaped data (since the library isn't installed in
this environment). Verifies:
  1. Soul palace correctly identified (not always index 0)
  2. Natal sihua extracted from mutagen fields
  3. Laiyin palace found from 化忌 star
  4. Ming/Shen Zhu resolved from branches when metadata is raw/empty
  5. Empty palaces (空宫) get borrowing hint
  6. Output is well-formed Chinese text
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ziwei.context_builder import (
    build_ziwei_context,
    find_soul_palace,
    find_body_palace,
    collect_natal_sihua,
    find_laiyin_palace,
    resolve_ming_zhu,
    resolve_shen_zhu,
    detect_borrowed_palace,
    get_san_fang_si_zheng,
)


# ─────────────────────────────────────────────────────────────
# Mock data: 2000-8-16 寅时 女命 (based on py-iztro docs)
# This is the canonical iztro example, fully populated.
# Key features:
#   - 命宫在午（soul palace index 6）, 主星: 紫微·七杀 (per typical setup)
#     Note: actual iztro output may differ slightly; we use plausible
#     values to test format_palace_detail and downstream functions.
#   - 庚辰年生，庚干生年四化: 太阳化禄、武曲化权、太阴化科、天同化忌
# ─────────────────────────────────────────────────────────────

def make_mock_chart_2000_8_16():
    """Build a mock chart data matching iztro_py output shape."""
    metadata = {
        "solar_date": "2000-8-16",
        "birth_hour_index": 2,
        "birth_hour_name": "寅时",
        "birth_hour_range": "03:00~05:00",
        "gender": "女",
        "lunar_date": "二〇〇〇年七月十七",
        "chinese_date": "庚辰 甲申 丙午 庚寅",   # 庚辰年
        "zodiac": "龙",
        "sign": "狮子座",
        "five_elements": "木三局",
        "soul_star": "破军",   # iztro_py returns Chinese by default
        "body_star": "文昌",
        "earthly_soul": "午",
        "earthly_body": "戌",
    }

    # 12 palaces — order: index 0..11
    # We construct so that 命宫 is at index 6 (地支午)
    # Standard iztro layout: 寅卯辰巳午未申酉戌亥子丑 → 0..11
    palaces = [
        # 0 寅: 财帛宫
        {
            "index": 0, "name": "财帛宫", "name_raw": "wealthPalace",
            "heavenly_stem": "戊", "earthly_branch": "寅",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "武曲", "type": "major", "scope": "origin",
                 "brightness": "得", "mutagen": "权"},   # 庚干武曲化权
                {"name": "天相", "type": "major", "scope": "origin",
                 "brightness": "庙", "mutagen": ""},
            ],
            "minor_stars": [
                {"name": "天马", "type": "tianma", "scope": "origin", "brightness": "", "mutagen": ""},
                {"name": "文昌", "type": "soft", "scope": "origin", "brightness": "得", "mutagen": ""},
            ],
            "adj_stars": [
                {"name": "三台", "type": "adjective", "scope": "origin"},
            ],
            "changsheng12": "病", "boshi12": "博士",
            "decadal_range": [114, 123],
        },
        # 1 卯: 子女宫
        {
            "index": 1, "name": "子女宫", "name_raw": "childrenPalace",
            "heavenly_stem": "己", "earthly_branch": "卯",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "太阳", "type": "major", "scope": "origin",
                 "brightness": "庙", "mutagen": "禄"},   # 庚干太阳化禄
                {"name": "天梁", "type": "major", "scope": "origin",
                 "brightness": "庙", "mutagen": ""},
            ],
            "minor_stars": [],
            "adj_stars": [],
            "changsheng12": "衰", "boshi12": "力士",
            "decadal_range": [104, 113],
        },
        # 2 辰: 夫妻宫
        {
            "index": 2, "name": "夫妻宫", "name_raw": "spousePalace",
            "heavenly_stem": "庚", "earthly_branch": "辰",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "七杀", "type": "major", "scope": "origin",
                 "brightness": "庙", "mutagen": ""},
            ],
            "minor_stars": [
                {"name": "擎羊", "type": "tough", "scope": "origin",
                 "brightness": "陷", "mutagen": ""},
            ],
            "adj_stars": [],
            "changsheng12": "帝旺", "boshi12": "青龙",
            "decadal_range": [94, 103],
        },
        # 3 巳: 兄弟宫
        {
            "index": 3, "name": "兄弟宫", "name_raw": "siblingsPalace",
            "heavenly_stem": "辛", "earthly_branch": "巳",
            "is_soul": False, "is_body": False,
            "major_stars": [],  # 空宫
            "minor_stars": [],
            "adj_stars": [],
            "changsheng12": "临官", "boshi12": "小耗",
            "decadal_range": [84, 93],
        },
        # 4 午: 命宫 ★
        {
            "index": 4, "name": "命宫", "name_raw": "soulPalace",
            "heavenly_stem": "壬", "earthly_branch": "午",
            "is_soul": True, "is_body": False,
            "major_stars": [
                {"name": "紫微", "type": "major", "scope": "origin",
                 "brightness": "庙", "mutagen": ""},
            ],
            "minor_stars": [
                {"name": "左辅", "type": "soft", "scope": "origin", "brightness": "", "mutagen": ""},
                {"name": "天魁", "type": "soft", "scope": "origin", "brightness": "", "mutagen": ""},
            ],
            "adj_stars": [
                {"name": "红鸾", "type": "flower", "scope": "origin"},
            ],
            "changsheng12": "冠带", "boshi12": "将军",
            "decadal_range": [4, 13],
        },
        # 5 未: 父母宫
        {
            "index": 5, "name": "父母宫", "name_raw": "parentsPalace",
            "heavenly_stem": "癸", "earthly_branch": "未",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "天机", "type": "major", "scope": "origin",
                 "brightness": "陷", "mutagen": ""},
            ],
            "minor_stars": [
                {"name": "陀罗", "type": "tough", "scope": "origin", "brightness": "", "mutagen": ""},
            ],
            "adj_stars": [],
            "changsheng12": "沐浴", "boshi12": "奏书",
            "decadal_range": [14, 23],
        },
        # 6 申: 福德宫
        {
            "index": 6, "name": "福德宫", "name_raw": "spiritPalace",
            "heavenly_stem": "甲", "earthly_branch": "申",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "破军", "type": "major", "scope": "origin",
                 "brightness": "得", "mutagen": ""},
            ],
            "minor_stars": [],
            "adj_stars": [],
            "changsheng12": "长生", "boshi12": "飞廉",
            "decadal_range": [24, 33],
        },
        # 7 酉: 田宅宫
        {
            "index": 7, "name": "田宅宫", "name_raw": "propertyPalace",
            "heavenly_stem": "乙", "earthly_branch": "酉",
            "is_soul": False, "is_body": False,
            "major_stars": [],  # 空宫
            "minor_stars": [
                {"name": "禄存", "type": "lucun", "scope": "origin", "brightness": "庙", "mutagen": ""},
            ],
            "adj_stars": [],
            "changsheng12": "养", "boshi12": "喜神",
            "decadal_range": [34, 43],
        },
        # 8 戌: 官禄宫 (身宫所在)
        {
            "index": 8, "name": "官禄宫", "name_raw": "careerPalace",
            "heavenly_stem": "丙", "earthly_branch": "戌",
            "is_soul": False, "is_body": True,    # 身宫
            "major_stars": [
                {"name": "廉贞", "type": "major", "scope": "origin",
                 "brightness": "利", "mutagen": ""},
                {"name": "天府", "type": "major", "scope": "origin",
                 "brightness": "庙", "mutagen": ""},
            ],
            "minor_stars": [
                {"name": "文曲", "type": "soft", "scope": "origin", "brightness": "得", "mutagen": ""},
            ],
            "adj_stars": [],
            "changsheng12": "胎", "boshi12": "病符",
            "decadal_range": [44, 53],
        },
        # 9 亥: 仆役宫 / 交友宫
        {
            "index": 9, "name": "交友宫", "name_raw": "friendsPalace",
            "heavenly_stem": "丁", "earthly_branch": "亥",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "太阴", "type": "major", "scope": "origin",
                 "brightness": "庙", "mutagen": "科"},   # 庚干太阴化科
            ],
            "minor_stars": [
                {"name": "火星", "type": "tough", "scope": "origin", "brightness": "庙", "mutagen": ""},
            ],
            "adj_stars": [],
            "changsheng12": "绝", "boshi12": "大耗",
            "decadal_range": [54, 63],
        },
        # 10 子: 迁移宫
        {
            "index": 10, "name": "迁移宫", "name_raw": "surfacePalace",
            "heavenly_stem": "戊", "earthly_branch": "子",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "贪狼", "type": "major", "scope": "origin",
                 "brightness": "旺", "mutagen": ""},
            ],
            "minor_stars": [],
            "adj_stars": [],
            "changsheng12": "墓", "boshi12": "伏兵",
            "decadal_range": [64, 73],
        },
        # 11 丑: 疾厄宫
        {
            "index": 11, "name": "疾厄宫", "name_raw": "healthPalace",
            "heavenly_stem": "己", "earthly_branch": "丑",
            "is_soul": False, "is_body": False,
            "major_stars": [
                {"name": "天同", "type": "major", "scope": "origin",
                 "brightness": "不", "mutagen": "忌"},   # 庚干天同化忌 → 来因宫
                {"name": "巨门", "type": "major", "scope": "origin",
                 "brightness": "陷", "mutagen": ""},
            ],
            "minor_stars": [
                {"name": "地空", "type": "tough", "scope": "origin", "brightness": "", "mutagen": ""},
                {"name": "地劫", "type": "tough", "scope": "origin", "brightness": "", "mutagen": ""},
            ],
            "adj_stars": [],
            "changsheng12": "死", "boshi12": "官府",
            "decadal_range": [74, 83],
        },
    ]

    return {
        "metadata": metadata,
        "palaces": palaces,
        "soul_palace": {
            "name": "命宫", "stem_branch": "壬午",
            "major_stars": ["紫微"], "minor_stars": ["左辅", "天魁"],
        },
        "body_palace": {
            "name": "官禄宫", "stem_branch": "丙戌",
            "major_stars": ["廉贞", "天府"],
        },
        "sanjiao_sizheng": [],
        "soul_star_raw": "破军",
        "body_star_raw": "文昌",
    }


def test_individual_helpers():
    print("=" * 70)
    print("TEST 1: Individual helper functions")
    print("=" * 70)

    data = make_mock_chart_2000_8_16()
    palaces = data["palaces"]
    metadata = data["metadata"]

    # 1. find_soul_palace
    soul = find_soul_palace(palaces)
    assert soul is not None
    assert soul["name"] == "命宫"
    assert soul["index"] == 4
    assert soul["earthly_branch"] == "午"
    print(f"✓ find_soul_palace → {soul['name']}@{soul['earthly_branch']} (index={soul['index']})")

    # 2. find_body_palace
    body = find_body_palace(palaces)
    assert body is not None
    assert body["name"] == "官禄宫"
    assert body["index"] == 8
    print(f"✓ find_body_palace → {body['name']}@{body['earthly_branch']} (index={body['index']})")

    # 3. collect_natal_sihua
    natal_sihua = collect_natal_sihua(palaces)
    assert len(natal_sihua) == 4, f"Expected 4 sihua, got {len(natal_sihua)}: {natal_sihua}"
    sihua_dict = {x["hua_type"]: x for x in natal_sihua}
    assert sihua_dict["化禄"]["star"] == "太阳"
    assert sihua_dict["化权"]["star"] == "武曲"
    assert sihua_dict["化科"]["star"] == "太阴"
    assert sihua_dict["化忌"]["star"] == "天同"
    print(f"✓ collect_natal_sihua → 禄=太阳, 权=武曲, 科=太阴, 忌=天同 (all 4 found)")

    # 4. find_laiyin_palace (生年化忌天同在疾厄宫)
    laiyin = find_laiyin_palace(natal_sihua)
    assert laiyin is not None
    assert laiyin["palace"] == "疾厄宫"
    assert laiyin["ji_star"] == "天同"
    print(f"✓ find_laiyin_palace → 疾厄宫（天同化忌坐守）")

    # 5. resolve_ming_zhu (metadata 有中文 raw → 直接用)
    ming = resolve_ming_zhu(metadata, soul)
    assert ming == "破军", f"Expected 破军 got {ming}"
    print(f"✓ resolve_ming_zhu (metadata 中文) → {ming}")

    # 5b. resolve_ming_zhu (metadata 给英文 raw key → 走 fallback 按地支取)
    bad_meta = dict(metadata); bad_meta["soul_star"] = "poJunMaj"   # 模拟 iztro 英文 key
    ming2 = resolve_ming_zhu(bad_meta, soul)
    # 命宫地支午 → 破军（按 MING_ZHU_BY_BRANCH）
    assert ming2 == "破军", f"Expected fallback 破军 got {ming2}"
    print(f"✓ resolve_ming_zhu (英文 raw key fallback) → {ming2}")

    # 6. resolve_shen_zhu (metadata 中文)
    shen = resolve_shen_zhu(metadata)
    assert shen == "文昌"
    print(f"✓ resolve_shen_zhu (metadata 中文) → {shen}")

    # 6b. resolve_shen_zhu (metadata 缺失 → 从 chinese_date 年支辰推 → 文昌)
    bad_meta2 = dict(metadata); bad_meta2["body_star"] = ""
    shen2 = resolve_shen_zhu(bad_meta2)
    # 庚辰年生 → 辰 → 文昌
    assert shen2 == "文昌", f"Expected fallback 文昌 got {shen2}"
    print(f"✓ resolve_shen_zhu (从年支推) → {shen2}")

    # 7. detect_borrowed_palace (命宫紫微独坐，不空，应返回 None)
    borrowed = detect_borrowed_palace(soul, palaces)
    assert borrowed is None
    print(f"✓ detect_borrowed_palace (命宫有主星) → None")

    # 7b. 测试一个空宫情况：兄弟宫(index 3)空宫，对宫(index 9)交友宫有太阴
    siblings = next(p for p in palaces if p["index"] == 3)
    borrowed2 = detect_borrowed_palace(siblings, palaces)
    assert borrowed2 is not None
    assert borrowed2["opposite_palace"] == "交友宫"
    assert any("太阴" in s for s in borrowed2["opposite_stars"])
    print(f"✓ detect_borrowed_palace (兄弟宫空宫→借交友宫太阴) → {borrowed2}")

    # 8. get_san_fang_si_zheng (命宫 index=4 → 4, 8(+4 官禄), 0(+8 财帛), 10(+6 迁移))
    sfsz = get_san_fang_si_zheng(palaces, 4)
    sfsz_names = [p["name"] for p in sfsz]
    assert sfsz_names == ["命宫", "官禄宫", "财帛宫", "迁移宫"], f"Got {sfsz_names}"
    print(f"✓ get_san_fang_si_zheng (命宫) → {' → '.join(sfsz_names)}")

    print()


def test_full_build():
    print("=" * 70)
    print("TEST 2: Full build_ziwei_context output")
    print("=" * 70)

    data = make_mock_chart_2000_8_16()
    output = build_ziwei_context(data)

    # 基本字段都要出现
    must_contain = [
        "派别声明",
        "中州派",
        "基础信息",
        "2000-8-16",
        "庚辰 甲申 丙午 庚寅",
        "木三局",
        "破军",                # 命主
        "文昌",                # 身主
        "命宫详情",
        "紫微(庙)",            # 命宫主星格式
        "身宫详情",
        "命宫三方四正",
        "财帛宫",
        "官禄宫",
        "迁移宫",
        "生年四化",
        "太阳",                # 化禄星
        "化禄",
        "武曲",                # 化权星
        "化权",
        "天同",                # 化忌星
        "化忌",
        "来因宫",
        "疾厄宫",              # 来因宫所在
        "十二宫概览",
        "兄弟宫",
        "数据范围",
    ]
    missing = [k for k in must_contain if k not in output]
    if missing:
        print(f"✗ Missing keywords: {missing}")
        print("Output was:")
        print(output)
        return False
    print(f"✓ All {len(must_contain)} required keywords present")

    # 检查空宫信息
    # 兄弟宫和田宅宫都是空宫，应在十二宫概览出现"空宫"标记
    if "兄弟宫(辛巳)：空宫" not in output:
        print(f"✗ Empty palace 兄弟宫 not marked as 空宫")
        return False
    if "田宅宫(乙酉)：空宫" not in output:
        print(f"✗ Empty palace 田宅宫 not marked as 空宫")
        return False
    print(f"✓ Empty palaces correctly marked")

    # 检查煞星标记 — 擎羊在夫妻宫（不在三方四正中，但应在十二宫概览出现"煞：擎羊"）
    if "煞：擎羊" not in output and "六煞：擎羊" not in output:
        print(f"✗ 擎羊 not marked in any 煞 context")
        return False
    # 地空地劫在疾厄宫（也不在三方四正），同理走单行格式
    if "煞：地空" not in output and "煞：地劫" not in output and "六煞：地" not in output:
        print(f"✗ 地空地劫 not marked in any 煞 context")
        return False
    print(f"✓ Sha stars correctly marked in 煞 channel")

    # 检查桃花星
    if "红鸾" not in output:
        print(f"✗ 红鸾 not present in output")
        return False
    print(f"✓ Taohua stars present")

    print()
    print("=" * 70)
    print("FULL OUTPUT PREVIEW:")
    print("=" * 70)
    print(output)
    print()
    print(f"Total output length: {len(output)} chars")
    print(f"Total lines: {output.count(chr(10))+1}")
    return True


def test_edge_cases():
    print("=" * 70)
    print("TEST 3: Edge cases")
    print("=" * 70)

    # Case 1: empty data
    out = build_ziwei_context({})
    assert "命盘数据不完整" in out
    print(f"✓ Empty data → graceful warning")

    # Case 2: missing metadata fields
    minimal = {
        "palaces": make_mock_chart_2000_8_16()["palaces"],
        "metadata": {},
    }
    out2 = build_ziwei_context(minimal)
    assert "派别声明" in out2
    assert "命宫" in out2
    # 命主应该被 fallback 按地支推出来 (命宫午 → 破军)
    assert "破军" in out2
    print(f"✓ Minimal metadata → fallbacks work")

    # Case 3: 命宫空宫 — 临时改 mock 让命宫主星清空
    data3 = make_mock_chart_2000_8_16()
    # 把命宫(index 4)主星清空
    for p in data3["palaces"]:
        if p["index"] == 4:
            p["major_stars"] = []
            break
    out3 = build_ziwei_context(data3)
    assert "借宫提示" in out3
    assert "迁移宫" in out3   # 对宫
    print(f"✓ Empty soul palace → borrowing hint")

    # Case 4: no natal sihua
    data4 = make_mock_chart_2000_8_16()
    for p in data4["palaces"]:
        for s_list_key in ("major_stars", "minor_stars", "adj_stars"):
            for s in p.get(s_list_key, []):
                if isinstance(s, dict):
                    s["mutagen"] = ""
    out4 = build_ziwei_context(data4)
    assert "未在命盘数据中检测到 mutagen" in out4
    print(f"✓ No mutagen field → graceful warning")

    print()


if __name__ == "__main__":
    test_individual_helpers()
    ok = test_full_build()
    test_edge_cases()
    print()
    print("=" * 70)
    print("ALL TESTS PASSED" if ok else "SOME TESTS FAILED")
    print("=" * 70)
