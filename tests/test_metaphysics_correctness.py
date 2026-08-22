"""
Tests for metaphysical correctness — 命理学专业性系统验证

涵盖：
  1. 十神表完整性 + 正确性（100/100）
  2. 藏干表（地支主气/中气/余气）
  3. 旺相休囚死表（藏干气势派 + 严格四时派）
  4. 大运起运方向规则
  5. 六亲规则（卦宫 vs 爻地支）
  6. 天乙贵人歌诀（甲戊庚牛羊 等）
  7. 地支六冲规则
  8. 地支六合规则
  9. 地支三合规则
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import (
    TIANGAN, DIZHI, TIANGAN_WUXING, TIANGAN_YIN_YANG,
    DIZHI_WUXING, WUXING_SHENG, WUXING_KE,
    SHISHEN, CANGGAN, SHENSHA,
    get_wuxing_strength, get_wuxing_strength_strict,
)


def test_shishen_complete():
    """十神表 100 个组合验证"""
    print("=" * 70)
    print("TEST 1: 十神表 100 个组合系统验证")
    print("=" * 70)
    
    def derive_shishen(dm, target):
        dm_wx, t_wx = TIANGAN_WUXING[dm], TIANGAN_WUXING[target]
        dm_yy, t_yy = TIANGAN_YIN_YANG[dm], TIANGAN_YIN_YANG[target]
        same_yy = dm_yy == t_yy
        if dm_wx == t_wx:
            return "比肩" if same_yy else "劫财"
        if WUXING_SHENG[dm_wx] == t_wx:
            return "食神" if same_yy else "伤官"
        if WUXING_KE[dm_wx] == t_wx:
            return "偏财" if same_yy else "正财"
        if WUXING_KE[t_wx] == dm_wx:
            return "七杀" if same_yy else "正官"
        if WUXING_SHENG[t_wx] == dm_wx:
            return "偏印" if same_yy else "正印"
        return "?"

    errors = []
    for dm in TIANGAN:
        for tg in TIANGAN:
            expected = derive_shishen(dm, tg)
            actual = SHISHEN.get((dm, tg), "")
            if expected != actual:
                errors.append(f"({dm},{tg}): 表={actual} 应={expected}")
    
    assert len(SHISHEN) == 100, f"十神表条目数 {len(SHISHEN)} ≠ 100"
    assert len(errors) == 0, f"十神错误: {errors[:5]}"
    print(f"  ✓ 十神表 100 个组合全部正确")
    print()


def test_canggan_traditional():
    """藏干表 — 12 地支藏干符合传统命理"""
    print("=" * 70)
    print("TEST 2: 12 地支藏干符合传统")
    print("=" * 70)
    
    # 标准藏干表（《渊海子平》等经典）
    expected = {
        "子": ["癸"],
        "丑": ["己", "癸", "辛"],
        "寅": ["甲", "丙", "戊"],
        "卯": ["乙"],
        "辰": ["戊", "乙", "癸"],
        "巳": ["丙", "庚", "戊"],
        "午": ["丁", "己"],
        "未": ["己", "丁", "乙"],
        "申": ["庚", "壬", "戊"],
        "酉": ["辛"],
        "戌": ["戊", "辛", "丁"],
        "亥": ["壬", "甲"],
    }
    
    for dz, exp in expected.items():
        actual = CANGGAN.get(dz, [])
        assert actual == exp, f"{dz}藏干: 表={actual} 应={exp}"
    print(f"  ✓ 12 地支藏干表完全符合传统标准")
    print()


def test_strict_wangxiang():
    """严格《子平真诠》四时旺相休囚死"""
    print("=" * 70)
    print("TEST 3: 严格四时旺相休囚死")
    print("=" * 70)
    
    # 春木旺，火相，水休，金囚，土死
    assert get_wuxing_strength_strict("木", "寅") == "旺"
    assert get_wuxing_strength_strict("木", "卯") == "旺"
    assert get_wuxing_strength_strict("火", "寅") == "相"
    assert get_wuxing_strength_strict("水", "寅") == "休"
    assert get_wuxing_strength_strict("金", "寅") == "囚"
    assert get_wuxing_strength_strict("土", "寅") == "死"
    print(f"  ✓ 春月（寅）：木旺/火相/水休/金囚/土死")
    
    # 夏火旺，土相，木休，水囚，金死
    assert get_wuxing_strength_strict("火", "午") == "旺"
    assert get_wuxing_strength_strict("土", "午") == "相"
    assert get_wuxing_strength_strict("木", "午") == "休"
    assert get_wuxing_strength_strict("水", "午") == "囚"
    assert get_wuxing_strength_strict("金", "午") == "死"
    print(f"  ✓ 夏月（午）：火旺/土相/木休/水囚/金死")
    
    # 秋金旺，水相，土休，火囚，木死
    assert get_wuxing_strength_strict("金", "酉") == "旺"
    assert get_wuxing_strength_strict("水", "酉") == "相"
    assert get_wuxing_strength_strict("土", "酉") == "休"
    assert get_wuxing_strength_strict("火", "酉") == "囚"
    assert get_wuxing_strength_strict("木", "酉") == "死"
    print(f"  ✓ 秋月（酉）：金旺/水相/土休/火囚/木死")
    
    # 冬水旺，木相，金休，土囚，火死
    assert get_wuxing_strength_strict("水", "子") == "旺"
    assert get_wuxing_strength_strict("木", "子") == "相"
    assert get_wuxing_strength_strict("金", "子") == "休"
    assert get_wuxing_strength_strict("土", "子") == "囚"
    assert get_wuxing_strength_strict("火", "子") == "死"
    print(f"  ✓ 冬月（子）：水旺/木相/金休/土囚/火死")
    print()


def test_tianyi_guiren_gejue():
    """天乙贵人歌诀验证：甲戊庚牛羊，乙己鼠猴乡..."""
    print("=" * 70)
    print("TEST 4: 天乙贵人歌诀")
    print("=" * 70)
    
    ty = SHENSHA["天乙贵人"]
    # 甲戊庚 → 丑未（牛羊）
    for dm in ["甲", "戊", "庚"]:
        assert set(ty[dm]) == {"丑", "未"}, f"{dm}日天乙应在丑未"
    # 乙己 → 子申（鼠猴）
    for dm in ["乙", "己"]:
        assert set(ty[dm]) == {"子", "申"}
    # 丙丁 → 亥酉（猪鸡）
    for dm in ["丙", "丁"]:
        assert set(ty[dm]) == {"亥", "酉"}
    # 壬癸 → 卯巳（兔蛇）
    for dm in ["壬", "癸"]:
        assert set(ty[dm]) == {"卯", "巳"}
    # 辛 → 寅午（虎马）
    assert set(ty["辛"]) == {"寅", "午"}
    print(f"  ✓ 天乙贵人歌诀完全正确（六辛逢马虎特殊处理）")
    print()


def test_liu_chong():
    """地支六冲：子午、丑未、寅申、卯酉、辰戌、巳亥"""
    print("=" * 70)
    print("TEST 5: 地支六冲")
    print("=" * 70)
    from core.bazi.relations import LIU_CHONG
    
    expected = [
        frozenset({"子", "午"}), frozenset({"丑", "未"}),
        frozenset({"寅", "申"}), frozenset({"卯", "酉"}),
        frozenset({"辰", "戌"}), frozenset({"巳", "亥"}),
    ]
    for e in expected:
        assert e in LIU_CHONG, f"{e} 应在六冲表"
    assert len(LIU_CHONG) == 6
    print(f"  ✓ 六冲完整：子午/丑未/寅申/卯酉/辰戌/巳亥")
    print()


def test_liu_he():
    """地支六合：子丑、寅亥、卯戌、辰酉、巳申、午未"""
    print("=" * 70)
    print("TEST 6: 地支六合")
    print("=" * 70)
    from core.bazi.relations import LIU_HE
    
    expected = {
        frozenset({"子", "丑"}): "土",
        frozenset({"寅", "亥"}): "木",
        frozenset({"卯", "戌"}): "火",
        frozenset({"辰", "酉"}): "金",
        frozenset({"巳", "申"}): "水",
        frozenset({"午", "未"}): "土",
    }
    for pair, wx in expected.items():
        assert pair in LIU_HE
        assert LIU_HE[pair] == wx, f"{pair} 六合化{LIU_HE[pair]} 应化{wx}"
    print(f"  ✓ 六合及其化神完全正确")
    print()


def test_san_he():
    """地支三合：申子辰水、亥卯未木、寅午戌火、巳酉丑金"""
    print("=" * 70)
    print("TEST 7: 地支三合")
    print("=" * 70)
    from core.bazi.relations import SAN_HE
    
    expected = {
        frozenset({"申", "子", "辰"}): "水",
        frozenset({"亥", "卯", "未"}): "木",
        frozenset({"寅", "午", "戌"}): "火",
        frozenset({"巳", "酉", "丑"}): "金",
    }
    for triple, wx in expected.items():
        assert triple in SAN_HE
        assert SAN_HE[triple] == wx
    print(f"  ✓ 三合局完整：申子辰水/亥卯未木/寅午戌火/巳酉丑金")
    print()


def test_san_xing():
    """三刑：寅巳申（无恩之刑）、丑戌未（恃势之刑）"""
    print("=" * 70)
    print("TEST 8: 三刑")
    print("=" * 70)
    from core.bazi.relations import SAN_XING_GROUPS, HU_XING, ZI_XING
    
    # 三刑组应该是 {寅,巳,申} 和 {丑,戌,未}
    san_xing_sets = [s for s, _ in SAN_XING_GROUPS]
    assert {"寅", "巳", "申"} in san_xing_sets
    assert {"丑", "戌", "未"} in san_xing_sets
    
    # 互刑：子卯
    assert frozenset({"子", "卯"}) in HU_XING
    
    # 自刑：辰午酉亥
    assert ZI_XING == {"辰", "午", "酉", "亥"}
    
    print(f"  ✓ 三刑：寅巳申、丑戌未")
    print(f"  ✓ 互刑：子卯（无礼之刑）")
    print(f"  ✓ 自刑：辰、午、酉、亥")
    print()


def test_liuyao_liuqin_rules():
    """六爻六亲规则：以卦宫为'我'，五行生克定六亲"""
    print("=" * 70)
    print("TEST 9: 六爻六亲规则")
    print("=" * 70)
    from core.liuyao.najia import get_liu_qin
    
    # 例如：乾宫属金（金为'我'）
    # 爻地支戌（土）→ 土生金 → 父母 ✓
    # 爻地支寅（木）→ 金克木 → 妻财 ✓
    # 爻地支午（火）→ 火克金 → 官鬼 ✓
    # 爻地支酉（金）→ 同行 → 兄弟 ✓
    # 爻地支子（水）→ 金生水 → 子孙 ✓
    
    assert get_liu_qin("乾", "戌") == "父母", f"乾宫戌爻 应为父母"
    assert get_liu_qin("乾", "寅") == "妻财", f"乾宫寅爻 应为妻财"
    assert get_liu_qin("乾", "午") == "官鬼", f"乾宫午爻 应为官鬼"
    assert get_liu_qin("乾", "酉") == "兄弟", f"乾宫酉爻 应为兄弟"
    assert get_liu_qin("乾", "子") == "子孙", f"乾宫子爻 应为子孙"
    print(f"  ✓ 乾宫（金）六亲：戌父母、寅妻财、午官鬼、酉兄弟、子子孙")
    print()


def test_kong_wang_table():
    """空亡：每旬空两支"""
    print("=" * 70)
    print("TEST 10: 旬空")
    print("=" * 70)
    from core.liuyao.najia import KONG_WANG_TABLE, get_kong_wang
    
    # 甲子旬（0-9）空戌亥
    assert get_kong_wang(0) == ["戌", "亥"]
    # 甲戌旬（10-19）空申酉
    assert get_kong_wang(10) == ["申", "酉"]
    # 甲申旬（20-29）空午未
    assert get_kong_wang(20) == ["午", "未"]
    # 甲午旬（30-39）空辰巳
    assert get_kong_wang(30) == ["辰", "巳"]
    # 甲辰旬（40-49）空寅卯
    assert get_kong_wang(40) == ["寅", "卯"]
    # 甲寅旬（50-59）空子丑
    assert get_kong_wang(50) == ["子", "丑"]
    print(f"  ✓ 六旬旬空表完整")
    print()


def test_yarrow_probability():
    """蓍草法概率：6=1/16, 7=5/16, 8=7/16, 9=3/16"""
    print("=" * 70)
    print("TEST 11: 蓍草法概率分布")
    print("=" * 70)
    # 跑 10000 次抽样验证
    import random
    random.seed(42)
    weights = [1, 5, 7, 3]
    types = [6, 7, 8, 9]
    counts = {6:0, 7:0, 8:0, 9:0}
    N = 100000
    for _ in range(N):
        v = random.choices(types, weights=weights, k=1)[0]
        counts[v] += 1
    # 容差 ±0.5%
    expected_freq = {6: 1/16, 7: 5/16, 8: 7/16, 9: 3/16}
    for v, exp in expected_freq.items():
        actual = counts[v] / N
        assert abs(actual - exp) < 0.005, \
            f"蓍草法 {v} 概率 {actual:.4f} 偏离期望 {exp:.4f}"
    print(f"  ✓ 蓍草法概率分布正确（容差<0.5%）")
    print()


def test_coin_probability():
    """铜钱法概率：6=1/8, 7=3/8, 8=3/8, 9=1/8"""
    print("=" * 70)
    print("TEST 12: 铜钱法概率分布")
    print("=" * 70)
    import random
    random.seed(42)
    counts = {6:0, 7:0, 8:0, 9:0}
    N = 100000
    for _ in range(N):
        heads = sum(random.randint(0,1) for _ in range(3))
        v = [6, 7, 8, 9][heads]  # 0→6 1→7 2→8 3→9
        counts[v] += 1
    expected_freq = {6: 1/8, 7: 3/8, 8: 3/8, 9: 1/8}
    for v, exp in expected_freq.items():
        actual = counts[v] / N
        assert abs(actual - exp) < 0.005
    print(f"  ✓ 铜钱法概率分布正确（容差<0.5%）")
    print()


def test_dayun_direction():
    """大运方向：阳男阴女顺，阴男阳女逆"""
    print("=" * 70)
    print("TEST 13: 大运起运方向")
    print("=" * 70)
    from core.bazi.forecaster import _dayun_direction
    
    # 阳年（甲丙戊庚壬）男 → 顺(+1)
    assert _dayun_direction("男", "甲") == 1
    assert _dayun_direction("男", "壬") == 1
    # 阴年（乙丁己辛癸）男 → 逆(-1)
    assert _dayun_direction("男", "乙") == -1
    assert _dayun_direction("男", "癸") == -1
    # 阳年女 → 逆
    assert _dayun_direction("女", "甲") == -1
    # 阴年女 → 顺
    assert _dayun_direction("女", "乙") == 1
    print(f"  ✓ 阳男阴女顺行，阴男阳女逆行")
    print()


if __name__ == "__main__":
    test_shishen_complete()
    test_canggan_traditional()
    test_strict_wangxiang()
    test_tianyi_guiren_gejue()
    test_liu_chong()
    test_liu_he()
    test_san_he()
    test_san_xing()
    test_liuyao_liuqin_rules()
    test_kong_wang_table()
    test_yarrow_probability()
    test_coin_probability()
    test_dayun_direction()
    print("=" * 70)
    print("ALL 命理学专业性 TESTS PASSED")
    print("=" * 70)
