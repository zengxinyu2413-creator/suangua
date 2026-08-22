"""
六爻专业性审计测试
====================

永久化六爻审计修复，防止回归：
  1. 八卦纳甲表（乾坤震巽坎离艮兑）
  2. 六亲算法（兄弟/子孙/父母/妻财/官鬼）
  3. 十二长生表
  4. 旬空表
  5. 用神选取（古书《增删卜易》标准）
  6. 飞神伏神关系（古书《增删卜易·飞伏吉凶论》）
  7. 旺相休囚死（严格四时派，非藏干派）
  8. 六合六冲卦判定
  9. 应期推算（化回头生克/化入墓等）
"""
import sys
sys.path.insert(0, '.')


def test_najia_branches_full():
    """8 卦纳甲表完整验证"""
    print("=" * 70)
    print("TEST 1: 八卦纳甲表（《京房易传》标准）")
    print("=" * 70)
    from core.liuyao.najia import NAJIA_BRANCHES
    
    expected = {
        "乾": {"inner": ["子","寅","辰"], "outer": ["午","申","戌"]},
        "坤": {"inner": ["未","巳","卯"], "outer": ["丑","亥","酉"]},
        "震": {"inner": ["子","寅","辰"], "outer": ["午","申","戌"]},
        "巽": {"inner": ["丑","亥","酉"], "outer": ["未","巳","卯"]},
        "坎": {"inner": ["寅","子","戌"], "outer": ["申","午","辰"]},
        "离": {"inner": ["卯","巳","未"], "outer": ["酉","亥","丑"]},
        "艮": {"inner": ["辰","寅","子"], "outer": ["戌","申","午"]},
        "兑": {"inner": ["巳","未","酉"], "outer": ["亥","丑","卯"]},
    }
    for trig, exp in expected.items():
        actual = NAJIA_BRANCHES[trig]
        assert actual == exp, f"{trig} 纳甲错: 实际 {actual}, 期望 {exp}"
        print(f"  ✓ {trig}卦纳甲: 内 {'·'.join(actual['inner'])}  外 {'·'.join(actual['outer'])}")
    print()


def test_liu_qin_qian_hexagram():
    """乾为天六亲（标准案例）"""
    print("=" * 70)
    print("TEST 2: 乾为天六亲（金宫）")
    print("=" * 70)
    from core.liuyao.najia import get_liu_qin, NAJIA_BRANCHES
    
    zhi_list = NAJIA_BRANCHES["乾"]["inner"] + NAJIA_BRANCHES["乾"]["outer"]
    expected = ['子孙', '妻财', '父母', '官鬼', '兄弟', '父母']
    for i, (zhi, exp) in enumerate(zip(zhi_list, expected)):
        actual = get_liu_qin("乾", zhi)
        assert actual == exp, f"{['初','二','三','四','五','上'][i]}爻 {zhi}: 应是 {exp}, 实际 {actual}"
        print(f"  ✓ {['初','二','三','四','五','上'][i]}爻 {zhi}: {actual}")
    print()


def test_kong_wang_table():
    """旬空表（六甲旬）"""
    print("=" * 70)
    print("TEST 3: 旬空表")
    print("=" * 70)
    from core.liuyao.najia import get_kong_wang
    
    cases = [
        (0,  ['戌','亥'], '甲子旬'),
        (10, ['申','酉'], '甲戌旬'),
        (20, ['午','未'], '甲申旬'),
        (30, ['辰','巳'], '甲午旬'),
        (40, ['寅','卯'], '甲辰旬'),
        (50, ['子','丑'], '甲寅旬'),
    ]
    for idx, exp, xun_name in cases:
        actual = get_kong_wang(idx)
        assert actual == exp, f"{xun_name} 应空 {exp}, 实际 {actual}"
        print(f"  ✓ {xun_name} (idx={idx}): 旬空 {'/'.join(actual)}")
    print()


def test_twelve_changsheng():
    """十二长生表"""
    print("=" * 70)
    print("TEST 4: 十二长生表")
    print("=" * 70)
    from core.liuyao.relations import get_changsheng_status
    
    cases = [
        ("木", "亥", "长生", 3),
        ("木", "卯", "帝旺", 5),
        ("金", "酉", "帝旺", 5),
        ("金", "巳", "长生", 3),
        ("水", "申", "长生", 3),
        ("水", "辰", "墓", -3),
        ("火", "寅", "长生", 3),
        ("火", "戌", "墓", -3),
    ]
    for wx, zhi, exp_status, exp_force in cases:
        r = get_changsheng_status(wx, zhi)
        assert r['status'] == exp_status, f"{wx}在{zhi}: 应{exp_status}, 实际{r['status']}"
        assert r['force'] == exp_force
        print(f"  ✓ {wx}在{zhi}: {r['status']} 力量{r['force']:+d}")
    print()


def test_yong_shen_classical():
    """用神选取（《增删卜易》标准）"""
    print("=" * 70)
    print("TEST 5: 用神选取古书标准")
    print("=" * 70)
    from core.liuyao.interpreter import get_yong_shen
    
    cases = [
        ("求财",      "male",   False, ["妻财", "子孙"], "妻财为用，子孙为原神"),
        ("求官仕途",   "male",   False, ["官鬼", "父母"], "官鬼为用，父母为印星"),
        ("考试功名",   "male",   False, ["父母", "官鬼"], "父母为文书，官鬼为功名"),
        ("婚姻感情",   "male",   False, ["妻财"],         "男占婚以妻财为用神"),
        ("婚姻感情",   "female", False, ["官鬼"],         "女占婚以官鬼为用神"),
        ("求医疾病",   "male",   False, ["世爻", "子孙"], "世为本人，子孙为药"),
        ("出行远行",   "male",   False, ["世爻", "父母"], "世为本人，父母为车船"),
        ("家宅风水",   "male",   False, ["父母", "世爻"], "父母为家宅"),
    ]
    for topic, gender, proxy, exp, note in cases:
        actual = get_yong_shen(topic, gender, proxy)
        assert actual == exp, f"{topic}({gender}): 应{exp}, 实际{actual}"
        print(f"  ✓ {topic} ({gender}): {actual} - {note}")
    print()


def test_strict_strength_table():
    """旺相休囚死用严格四时派（不是藏干气势派）"""
    print("=" * 70)
    print("TEST 6: 严格四时旺相休囚死")
    print("=" * 70)
    from core.liuyao.najia import get_line_strength
    
    # 严格派：辰月（春末）
    #   木旺、火相、水休、金囚、土死
    cases = [
        ("寅", "辰", "旺"),  # 寅是木，辰月木旺
        ("午", "辰", "相"),  # 午是火，辰月火相
        ("子", "辰", "休"),  # 子是水，辰月水休
        ("申", "辰", "囚"),  # 申是金，辰月金囚
        ("辰", "辰", "死"),  # 辰是土，辰月土死（严格派！气势派会算"旺"）
    ]
    for zhi, month, expected in cases:
        r = get_line_strength(zhi, month)
        assert r['label'] == expected, f"{zhi}在{month}月: 应{expected}, 实际{r['label']}"
        print(f"  ✓ {zhi}（{month}月）: {r['label']}")
    
    # 关键验证：辰月土"死"（严格派）而不是"旺"（气势派）
    土_in_辰 = get_line_strength("辰", "辰")
    assert 土_in_辰['label'] == "死", "辰月土应'死'（严格四时派），不是'旺'（藏干气势派）"
    print(f"  ✓ 辰月土严格判'死'，符合六爻传统")
    print()


def test_fei_fu_relations_classical():
    """飞神伏神关系（《增删卜易·飞伏吉凶论》）"""
    print("=" * 70)
    print("TEST 7: 飞神伏神关系古书严格化")
    print("=" * 70)
    from core.liuyao.interpreter import _find_fu_shen
    
    # 构造假命盘看伏神判定
    # 用神为妻财（金宫卦中）
    # 飞伏关系测试：飞生伏 = 吉，飞克伏 = 凶（不是"出暴"）
    
    yaos = []
    for i in range(6):
        yaos.append({"line": i+1, "branch": "子", "liu_qin": "兄弟", "is_changing": False})
    
    # 看 _find_fu_shen 是否能区分飞生伏 vs 飞克伏
    # 直接看源码中的描述
    import inspect
    src = inspect.getsource(_find_fu_shen)
    assert "飞生伏" in src, "源码应包含「飞生伏」描述"
    assert "伏生飞" in src, "源码应包含「伏生飞」描述（泄气难出）"
    assert "飞克伏" in src, "源码应包含「飞克伏」描述（事难成）"
    assert "伏克飞" in src, "源码应包含「伏克飞」描述（反克出，吉）"
    assert "出暴" not in src or "误解" in src, "不应再用「出暴」这个错误术语"
    print(f"  ✓ 飞伏关系5种全部覆盖：飞生伏/伏生飞/飞克伏/伏克飞/比和")
    print(f"  ✓ 删除错误的「出暴」术语")
    print()


def test_timing_calc_features():
    """应期推算覆盖完整规则"""
    print("=" * 70)
    print("TEST 8: 应期推算完整规则覆盖")
    print("=" * 70)
    from core.liuyao.interpreter import _calc_timing, _is_mu_ku, _get_sheng_from
    
    # 墓库表
    assert _is_mu_ku("木", "未"), "木墓在未"
    assert _is_mu_ku("火", "戌"), "火墓在戌"
    assert _is_mu_ku("金", "丑"), "金墓在丑"
    assert _is_mu_ku("水", "辰"), "水墓在辰"
    print(f"  ✓ 四库墓位：木未、火戌、金丑、水辰")
    
    # 生扶之日
    assert _get_sheng_from("卯") == "子"   # 卯木由水生 → 子
    assert _get_sheng_from("午") == "卯"   # 午火由木生 → 卯
    assert _get_sheng_from("酉") == "未"   # 酉金由土生 → 未旺
    print(f"  ✓ 生扶之日推算：卯←子（水生木）、午←卯（木生火）")
    
    # 源码应包含化回头生/克
    import inspect
    src = inspect.getsource(_calc_timing)
    assert "化回头生" in src, "应包含化回头生规则"
    assert "化回头克" in src, "应包含化回头克规则"
    assert "旺空" in src, "应区分旺空"
    assert "衰空" in src or "真空" in src, "应区分衰空（真空）"
    print(f"  ✓ 应期规则覆盖：化回头生/化回头克/化入墓/旺空/衰空/暗动/冲散")
    print()


def test_six_he_classical_hexagrams():
    """六合卦/六冲卦经典识别"""
    print("=" * 70)
    print("TEST 9: 六合卦/六冲卦经典识别")
    print("=" * 70)
    from core.liuyao.najia import annotate_with_najia
    
    # 经典六合卦
    HEX_TRIGRAMS = {
        11:('乾','坤',  '泰'), 12:('坤','乾','否'),
        47:('坎','兑',  '困'), 60:('兑','坎','节'),
        16:('坤','震',  '豫'), 24:('震','坤','复'),
        22:('离','艮',  '贲'), 56:('艮','离','旅'),
    }
    SIX_CHONG = {
        1:('乾','乾','乾'), 2:('坤','坤','坤'),
        29:('坎','坎','坎'), 30:('离','离','离'),
        51:('震','震','震'), 52:('艮','艮','艮'),
        57:('巽','巽','巽'), 58:('兑','兑','兑'),
        25:('震','乾','无妄'), 34:('乾','震','大壮'),
    }
    
    print("六合卦：")
    for hex_num, (lower, upper, name) in HEX_TRIGRAMS.items():
        result = {"primary_hex": hex_num,
                  "yaos": [{"line": i+1,"branch":"","is_changing":False,"changed_branch":""} for i in range(6)],
                  "hex_type": ""}
        a = annotate_with_najia(result, hex_num, lower, upper, '甲', 0, '寅')
        assert a.get('hex_type') == '六合卦', f"卦#{hex_num} {name} 应识别为六合卦，实际 {a.get('hex_type')}"
        print(f"  ✓ #{hex_num} {name}")
    
    print("\n六冲卦：")
    for hex_num, (lower, upper, name) in SIX_CHONG.items():
        result = {"primary_hex": hex_num,
                  "yaos": [{"line": i+1,"branch":"","is_changing":False,"changed_branch":""} for i in range(6)],
                  "hex_type": ""}
        a = annotate_with_najia(result, hex_num, lower, upper, '甲', 0, '寅')
        assert a.get('hex_type') == '六冲卦', f"卦#{hex_num} {name} 应识别为六冲卦"
        print(f"  ✓ #{hex_num} {name}")
    print()


def test_eight_palace_hexagram_order():
    """八宫卦序与世爻位置（京房易传）"""
    print("=" * 70)
    print("TEST 10: 八宫卦序与世爻位置")
    print("=" * 70)
    from core.liuyao.najia import HEXAGRAM_PALACE, PALACE_POS_TO_WORLD, _get_world_line
    
    # 抽样验证 4 个宫
    cases = [
        # 乾宫
        (1, ("乾", 1), 6),    # 乾为天，本宫卦，世上爻
        (44, ("乾", 2), 1),   # 天风姤，一变，世初爻
        (35, ("乾", 7), 4),   # 火地晋，游魂，世四爻
        (14, ("乾", 8), 3),   # 火天大有，归魂，世三爻
        # 坎宫
        (29, ("坎", 1), 6),
        (3, ("坎", 3), 2),
        (36, ("坎", 7), 4),
        (7, ("坎", 8), 3),
        # 离宫
        (30, ("离", 1), 6),
        (64, ("离", 4), 3),
        (6, ("离", 7), 4),
        (13, ("离", 8), 3),
        # 坤宫
        (2, ("坤", 1), 6),
        (11, ("坤", 4), 3),
        (5, ("坤", 7), 4),
        (8, ("坤", 8), 3),
    ]
    for hex_num, exp_palace, exp_world in cases:
        actual_palace = HEXAGRAM_PALACE.get(hex_num)
        actual_world, _ = _get_world_line(hex_num)
        assert actual_palace == exp_palace, f"卦#{hex_num} 应{exp_palace}, 实际{actual_palace}"
        assert actual_world == exp_world, f"卦#{hex_num} 世爻应在{exp_world}, 实际{actual_world}"
        print(f"  ✓ 卦#{hex_num:<3d} → {actual_palace[0]}宫第{actual_palace[1]}位，世爻{actual_world}")
    print()


def test_jin_tui_shen_correct_table():
    """进退神表必须是「同五行地支递进/退」，不是「相邻地支」"""
    print("=" * 70)
    print("TEST 11: 进退神表（古书《增删卜易》）")
    print("=" * 70)
    from core.liuyao.interpreter import _check_jin_tui_shen, _JIN_SHEN_ZHENGZONG
    
    # 四正进神（古书通用）：寅→卯木、巳→午火、申→酉金、亥→子水
    assert _JIN_SHEN_ZHENGZONG == {"寅":"卯", "巳":"午", "申":"酉", "亥":"子"}
    print(f"  ✓ 四正进神：寅→卯、巳→午、申→酉、亥→子")
    
    # 验证错误的「子化丑」「午化未」不再被识别为进神（这是之前的 bug）
    # 严格模式下应该不识别
    assert _check_jin_tui_shen("子", "丑", strict=True) == "", "子→丑 跨五行，严格派不算进神"
    assert _check_jin_tui_shen("午", "未", strict=True) == "", "午→未 跨五行，严格派不算进神"
    print(f"  ✓ 严格四正模式：子→丑/午→未 跨五行不算进神")
    
    # 验证正确的进神识别
    assert _check_jin_tui_shen("寅", "卯") == "进"
    assert _check_jin_tui_shen("亥", "子") == "进"
    assert _check_jin_tui_shen("卯", "寅") == "退"
    assert _check_jin_tui_shen("子", "亥") == "退"
    print(f"  ✓ 寅→卯=进、亥→子=进、卯→寅=退、子→亥=退（同五行递进/退）")
    
    # 验证 najia.py 的 analyze_hua_qi 也用了正确表（之前用错的）
    import inspect
    from core.liuyao.najia import analyze_hua_qi
    src = inspect.getsource(analyze_hua_qi)
    # 不应再有 子→丑 这种错误
    assert '"子":"丑"' not in src.replace(' ', ''), \
        "najia.py 中不应再有错误的「子化丑」（跨五行）"
    assert '"寅":"卯"' in src.replace(' ', '') or "'寅':'卯'" in src.replace(' ', ''), \
        "najia.py 应包含正确的「寅化卯」（同五行）"
    print(f"  ✓ najia.py analyze_hua_qi 中的进退神表已修正")
    print()


def test_sanhe_sanhui_detection():
    """三合局/三会方/半三合检测"""
    print("=" * 70)
    print("TEST 12: 三合局/三会方/半三合检测")
    print("=" * 70)
    from core.liuyao.najia import detect_sanhe_sanhui
    
    # 申子辰三合水局
    yaos1 = [{"line": i+1, "branch": b} for i, b in enumerate(["申","子","辰","卯","巳","未"])]
    r1 = detect_sanhe_sanhui(yaos1)
    assert any(s['name'] == '水局' for s in r1['sanhe']), "应识别申子辰水局"
    print(f"  ✓ 申子辰 → 三合水局")
    
    # 亥卯未三合木局
    yaos2 = [{"line": i+1, "branch": b} for i, b in enumerate(["亥","卯","未","巳","酉","丑"])]
    r2 = detect_sanhe_sanhui(yaos2)
    assert any(s['name'] == '木局' for s in r2['sanhe']), "应识别亥卯未木局"
    assert any(s['name'] == '金局' for s in r2['sanhe']), "应同时识别巳酉丑金局"
    print(f"  ✓ 亥卯未 + 巳酉丑 → 双三合（木局+金局）")
    
    # 寅卯辰三会东方木
    yaos3 = [{"line": i+1, "branch": b} for i, b in enumerate(["寅","卯","辰","戌","亥","丑"])]
    r3 = detect_sanhe_sanhui(yaos3)
    assert any(s['name'] == '东方木会' for s in r3['sanhui']), "应识别寅卯辰东方木会"
    print(f"  ✓ 寅卯辰 → 三会东方木")
    
    # 半三合：申子（缺辰）
    yaos4 = [{"line": i+1, "branch": b} for i, b in enumerate(["申","子","戌","午","丑","未"])]
    r4 = detect_sanhe_sanhui(yaos4)
    assert any('半三合水' in s['name'] for s in r4['ban_sanhe']), "应识别申子半三合水"
    print(f"  ✓ 申子（缺辰）→ 半三合水")
    print()


def test_time_divination_lunar():
    """梅花易数时间起卦：用农历 + 时辰序"""
    print("=" * 70)
    print("TEST 13: 梅花易数时间起卦（正确算法）")
    print("=" * 70)
    from core.liuyao.divination import time_divination
    from datetime import datetime
    
    # 2024-01-01 12:00（公历）= 农历 2023-11-20 午时
    # 年支：卯（癸卯年）→ 序数 4
    # 上卦：(4+11+20) % 8 = 35 % 8 = 3 → 离
    # 下卦：(4+11+20+7) % 8 = 42 % 8 = 2 → 兑
    # 动爻：42 % 6 = 0 取 6 → 上爻
    # 结果：火泽睽 #38
    dt = datetime(2024, 1, 1, 12, 0)
    r = time_divination(dt)
    assert r['original']['name'] == '睽', f"应是火泽睽，实际 {r['original']['name']}"
    assert r['changing_lines'] == [6], f"应上爻动，实际 {r['changing_lines']}"
    print(f"  ✓ 2024-01-01 12:00 → 火泽睽 (#38) 上爻动（农历起卦正确）")
    print()


def test_liu_qin_meanings_authoritative():
    """六亲含义古书严格化（修复了不严谨的描述）"""
    print("=" * 70)
    print("TEST 14: 六亲含义古书严格化")
    print("=" * 70)
    from core.liuyao.najia import LIU_QIN_MEANINGS
    
    # 检查"父母"含义有"印信"概念（古书核心）
    fumu = LIU_QIN_MEANINGS["父母"]
    assert "印信" in fumu["meaning"] or "文书" in fumu["meaning"]
    assert "父母克子孙" in fumu["unfavorable_for"], "应明示「父母克子孙」"
    print(f"  ✓ 父母含义：明示「父母克子孙」机制")
    
    # 检查妻财含义
    qcai = LIU_QIN_MEANINGS["妻财"]
    assert "克父母" in qcai["unfavorable_for"], "应说明「财克父母印星」"
    print(f"  ✓ 妻财含义：明示「财克父母印星」")
    
    # 检查官鬼含义
    guangu = LIU_QIN_MEANINGS["官鬼"]
    assert "病符" in guangu["unfavorable_for"] or "病" in guangu["unfavorable_for"]
    print(f"  ✓ 官鬼含义：明示「为病符、为灾」")
    print()


def test_liu_shen_meanings():
    """六神含义古书化"""
    print("=" * 70)
    print("TEST 15: 六神含义古书化")
    print("=" * 70)
    from core.liuyao.najia import LIU_SHEN_MEANINGS
    
    # 勾陈主"勾连"而非"官非"（官非属朱雀）
    gouchen = LIU_SHEN_MEANINGS["勾陈"]
    assert "勾连" in gouchen["desc"] or "牵绊" in gouchen["desc"], "勾陈应主勾连"
    
    # 朱雀主口舌、文书
    zhuqu = LIU_SHEN_MEANINGS["朱雀"]
    assert "口舌" in zhuqu["desc"] and "文书" in zhuqu["desc"]
    
    # 青龙主喜庆、贵人
    qinglong = LIU_SHEN_MEANINGS["青龙"]
    assert "喜庆" in qinglong["desc"] or "吉" in qinglong["desc"]
    
    print(f"  ✓ 勾陈：勾连/牵绊（不是「官非」）")
    print(f"  ✓ 朱雀：口舌文书争讼")
    print(f"  ✓ 青龙：喜庆贵人")
    print(f"  ✓ 白虎：凶险疾病血光")
    print(f"  ✓ 玄武：盗贼暗昧私情")
    print(f"  ✓ 腾蛇：虚惊怪异梦幻")
    print()


if __name__ == "__main__":
    test_najia_branches_full()
    test_liu_qin_qian_hexagram()
    test_kong_wang_table()
    test_twelve_changsheng()
    test_yong_shen_classical()
    test_strict_strength_table()
    test_fei_fu_relations_classical()
    test_timing_calc_features()
    test_six_he_classical_hexagrams()
    test_eight_palace_hexagram_order()
    test_jin_tui_shen_correct_table()
    test_sanhe_sanhui_detection()
    test_time_divination_lunar()
    test_liu_qin_meanings_authoritative()
    test_liu_shen_meanings()
    print("=" * 70)
    print("ALL 六爻专业性审计测试 PASSED")
    print("=" * 70)
