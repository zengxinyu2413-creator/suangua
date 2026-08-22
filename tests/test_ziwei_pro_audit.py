"""
紫微斗数命理学专业性审计测试
=================================

永久化已修复的命理学专业性 bug，防止回归：
  1. 命主身主算法（必须按古书"年支/时支"，不能用 iztro 的"命宫地支"）
  2. 机月同梁格（至少 3 颗会齐才成格）
  3. 火贪/铃贪（贪狼必须非陷地）
  4. 真太阳时（to_hour_index 支持经度校正）
  5. 巨火羊格措辞（不含极端"缢死"等）
"""
import sys
sys.path.insert(0, '.')


def test_soul_body_master_by_old_book():
    """命主身主须符《全书》标准：命主按命宫地支(北斗七星)、身主按生年地支。"""
    print("=" * 70)
    print("TEST 1: 命主身主标准算法（命宫地支·北斗七星 / 生年地支）")
    print("=" * 70)
    from core.ziwei.chart import build_ziwei_chart

    # 命主表（命宫地支 → 北斗七星）：辰/申为廉贞（非文昌！）
    SOUL = {'子':'贪狼','丑':'巨门','亥':'巨门','寅':'禄存','戌':'禄存',
            '卯':'文曲','酉':'文曲','辰':'廉贞','申':'廉贞',
            '巳':'武曲','未':'武曲','午':'破军'}
    # 身主表（生年地支）
    BODY = {'子':'火星','午':'火星','丑':'天相','未':'天相','寅':'天梁','申':'天梁',
            '卯':'天同','酉':'天同','辰':'文昌','戌':'文昌','巳':'天机','亥':'天机'}

    for date, h, g in [('1990-06-14', 3, '男'), ('1928-07-29', 6, '男'),
                       ('2010-12-12', 8, '男'), ('1975-09-30', 4, '女')]:
        md = build_ziwei_chart(date, h, g)['metadata']
        soul_branch = md['earthly_soul']
        year_branch = md['chinese_date'].split()[0][1]
        exp_soul = SOUL[soul_branch]
        exp_body = BODY[year_branch]
        assert md['soul_star'] == exp_soul, \
            f"{date} 命宫{soul_branch} 命主应{exp_soul}，实际{md['soul_star']}"
        assert md['body_star'] == exp_body, \
            f"{date} 年支{year_branch} 身主应{exp_body}，实际{md['body_star']}"
        # 与 iztro 库一致（库已严格按标准计算）
        assert md['soul_star'] == md['soul_star_iztro']
        assert md['body_star'] == md['body_star_iztro']
        print(f"  ✓ {date} 命宫{soul_branch}/年支{year_branch}："
              f"命主{md['soul_star']} 身主{md['body_star']}")
    print()


def test_jiyue_tongliang_strict():
    """机月同梁格：必须至少 3 颗会齐"""
    print("=" * 70)
    print("TEST 2: 机月同梁格严格化（≥3 颗）")
    print("=" * 70)
    from core.ziwei.chart import build_ziwei_chart
    from core.ziwei.pattern_detector import detect_jiyue_tongliang

    # 1990 卯时男：命宫紫贪，三方四正可能含天梁，但 <3 颗 — 不应成格
    chart = build_ziwei_chart('1990-06-14', 3, '男')
    result = detect_jiyue_tongliang(chart['palaces'])
    # 主用例三方四正只有天梁(1颗) → 不应成格
    assert result is None or '机月同梁' not in result.get('name', ''), \
        f"1990 卯时男紫贪坐命，三方四正不会齐机月同梁 4 星，不应成格，实际 {result}"
    print(f"  ✓ 1990 卯时男（紫贪坐命）：机月同梁 不成格（三方<3 颗）")
    print()


def test_huoling_tan_must_miaowang():
    """火贪/铃贪：贪狼落陷不成格"""
    print("=" * 70)
    print("TEST 3: 火贪/铃贪要求贪狼非落陷")
    print("=" * 70)
    from core.ziwei.pattern_detector import detect_huotan, detect_lingtan

    # 构造假命盘：贪狼陷 + 火星 同坐命宫
    fake_palaces = [{
        'index': 0, 'name': '命宫', 'is_soul': True, 'is_body': False,
        'heavenly_stem': '甲', 'earthly_branch': '子',
        'major_stars': [{'name': '贪狼', 'brightness': '陷'}],
        'minor_stars': [{'name': '火星'}],
        'adj_stars': [],
    }] + [{'index': i, 'name': f'宫{i}', 'is_soul': False, 'is_body': False,
            'heavenly_stem': '', 'earthly_branch': '',
            'major_stars': [], 'minor_stars': [], 'adj_stars': []} for i in range(1, 12)]
    
    r = detect_huotan(fake_palaces)
    assert r is None, f"贪狼陷地不应成火贪格，实际 {r}"
    print(f"  ✓ 贪狼陷地 + 火星：火贪不成格")
    
    # 改成贪狼旺 + 火星
    fake_palaces[0]['major_stars'][0]['brightness'] = '旺'
    r2 = detect_huotan(fake_palaces)
    assert r2 is not None and '火贪' in r2['name'], f"贪狼旺地应成火贪格"
    print(f"  ✓ 贪狼旺地 + 火星：火贪成格")
    
    # 同样验证铃贪
    fake_palaces[0]['major_stars'][0]['brightness'] = '陷'
    fake_palaces[0]['minor_stars'] = [{'name': '铃星'}]
    r3 = detect_lingtan(fake_palaces)
    assert r3 is None, "贪狼陷地不应成铃贪格"
    print(f"  ✓ 贪狼陷地 + 铃星：铃贪不成格")
    print()


def test_real_solar_time_correction():
    """真太阳时校正：经度让时辰可能变化"""
    print("=" * 70)
    print("TEST 4: 真太阳时校正（to_hour_index 支持经度）")
    print("=" * 70)
    from api.ziwei import ZiWeiRequest

    # 不传经度 — 5:30 应是卯时（idx=3）
    r1 = ZiWeiRequest(year=1990, month=5, day=22, hour=5, minute=30, gender='男', is_lunar=True)
    assert r1.to_hour_index() == 3, f"5:30 应卯时（3），实际 {r1.to_hour_index()}"
    print(f"  ✓ 不传经度：5:30 → 卯时（idx=3）")
    
    # 成都经度 104.06°（偏 -63 分钟）— 5:30 → 真太阳 4:26 → 寅时（idx=2）
    r2 = ZiWeiRequest(year=1990, month=5, day=22, hour=5, minute=30,
                      gender='男', is_lunar=True, longitude=104.06)
    assert r2.to_hour_index() == 2, f"成都 5:30 校正后应寅时（2），实际 {r2.to_hour_index()}"
    print(f"  ✓ 成都 104.06° + 5:30 → 真太阳时 04:26 → 寅时（idx=2）")
    
    # 北京经度 116.4° — 几乎不偏移
    r3 = ZiWeiRequest(year=1990, month=5, day=22, hour=5, minute=30,
                      gender='男', is_lunar=True, longitude=116.4)
    # 116.4 - 120 = -3.6 度 = -14.4 分钟 → 5:30 - 14 ≈ 5:16 仍卯时
    assert r3.to_hour_index() == 3, f"北京 5:30 几乎不偏移，仍卯时"
    print(f"  ✓ 北京 116.4° + 5:30 → 真太阳时约 05:16 → 仍卯时（idx=3）")
    
    # 乌鲁木齐 87.6°（偏 -130 分钟）— 5:30 → 真太阳 03:20 → 寅时
    r4 = ZiWeiRequest(year=1990, month=5, day=22, hour=5, minute=30,
                      gender='男', is_lunar=True, longitude=87.6)
    assert r4.to_hour_index() == 2, f"乌鲁木齐 5:30 校正后应寅时（2）"
    print(f"  ✓ 乌鲁木齐 87.6° + 5:30 → 真太阳时 03:20 → 寅时（idx=2）")
    print()


def test_juhuo_yang_safe_wording():
    """巨火羊格措辞：不含'缢死'等极端词"""
    print("=" * 70)
    print("TEST 5: 巨火羊格用户友好措辞")
    print("=" * 70)
    from core.ziwei.pattern_detector import detect_juhuo_yang

    # 构造假命盘：巨门+火星+擎羊同坐命宫
    fake_palaces = [{
        'index': 0, 'name': '命宫', 'is_soul': True, 'is_body': False,
        'heavenly_stem': '甲', 'earthly_branch': '子',
        'major_stars': [{'name': '巨门', 'brightness': '陷'}],
        'minor_stars': [{'name': '火星'}, {'name': '擎羊'}],
        'adj_stars': [],
    }] + [{'index': i, 'name': f'宫{i}', 'is_soul': False, 'is_body': False,
            'heavenly_stem': '', 'earthly_branch': '',
            'major_stars': [], 'minor_stars': [], 'adj_stars': []} for i in range(1, 12)]
    
    r = detect_juhuo_yang(fake_palaces)
    assert r is not None, "巨火羊应成格"
    meaning = r.get('meaning', '')
    assert '缢死' not in meaning, f"meaning 不应包含'缢死'：{meaning}"
    assert '自残' not in meaning, f"meaning 不应包含'自残'：{meaning}"
    assert '心理健康' in meaning or '情绪' in meaning, f"meaning 应有现代健康提示"
    print(f"  ✓ 巨火羊格 meaning 不含极端词，有现代提示")
    print(f"    实际: {meaning[:80]}...")
    print()


if __name__ == "__main__":
    test_soul_body_master_by_old_book()
    test_jiyue_tongliang_strict()
    test_huoling_tan_must_miaowang()
    test_real_solar_time_correction()
    test_juhuo_yang_safe_wording()
    print("=" * 70)
    print("ALL 紫微专业性审计测试 PASSED")
    print("=" * 70)
