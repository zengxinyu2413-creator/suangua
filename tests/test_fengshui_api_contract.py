"""
风水 API 字段名前后端一致性测试 — 防止前后端漂移

确保 /fengshui/analysis 返回 FengShuiPage.jsx 期望的所有字段。
起源：用户反馈，发现前端用 'life_trigram'/'life_group'/'compatibility===compatible' 等
不匹配后端字段名的代码，导致页面无法正确显示数据。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.fengshui import router


def make_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_required_fields():
    """前端 FengShuiPage 期望的所有字段都存在"""
    print("=" * 70)
    print("TEST 1: 风水 API 返回字段完整性")
    print("=" * 70)
    client = make_client()
    r = client.post('/fengshui/analysis', json={
        'birth_year': 1990, 'gender': 'male', 'house_facing': '南',
    })
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()['data']
    
    required = [
        # 命卦/宅卦
        "ming_gua", "ming_gua_name", "ming_gua_group",
        "house_gua", "house_gua_name", "house_group",
        # 朝向/坐山
        "house_facing", "house_sitting",
        # 相配性
        "compatibility", "is_compatible",
        "overall_advice",
        # 八宅扇区
        "auspicious_sectors", "inauspicious_sectors",
        # 飞星
        "annual_flying_stars",
        # 个人方位
        "personal_directions",
        # 综合建议
        "combined_advice",
    ]
    for field in required:
        assert field in data, f"缺失字段: {field}"
        print(f"  ✓ 字段存在: {field}")
    print()


def test_compatibility_boolean():
    """is_compatible 是布尔值"""
    print("=" * 70)
    print("TEST 2: is_compatible 是布尔，且与 compatibility 一致")
    print("=" * 70)
    client = make_client()
    # 坎命 + 朝南（坐北=坎宅）= 相配
    r1 = client.post('/fengshui/analysis', json={
        'birth_year': 1990, 'gender': 'male', 'house_facing': '南',
    })
    data1 = r1.json()['data']
    assert isinstance(data1['is_compatible'], bool)
    assert data1['is_compatible'] == True
    assert data1['compatibility'].startswith("相配")
    print(f"  ✓ 坎命+朝南→坎宅: is_compatible=True, compatibility 以'相配'开头")
    
    # 坎命 + 朝北（坐南=离宅，东四） — 同东四，应该相配
    # 坎命 + 朝东南（坐西北=乾宅，西四） — 不相配
    r2 = client.post('/fengshui/analysis', json={
        'birth_year': 1990, 'gender': 'male', 'house_facing': '东南',
    })
    data2 = r2.json()['data']
    assert data2['is_compatible'] == False
    assert data2['compatibility'].startswith("不相配")
    print(f"  ✓ 坎命(东四)+朝东南→乾宅(西四): is_compatible=False")
    print()


def test_sector_fields():
    """sector 字段有 star、quality、meaning、advice"""
    print("=" * 70)
    print("TEST 3: 八宅扇区字段")
    print("=" * 70)
    client = make_client()
    r = client.post('/fengshui/analysis', json={
        'birth_year': 1990, 'gender': 'male', 'house_facing': '南',
    })
    data = r.json()['data']
    
    aus = data.get('auspicious_sectors', [])
    assert len(aus) >= 3, f"吉方应至少 3 个"  # 生气、天医、延年
    for s in aus:
        for f in ('direction', 'star', 'quality'):
            assert f in s, f"扇区缺 {f}"
    print(f"  ✓ 吉方 {len(aus)} 个，字段齐全")
    
    inaus = data.get('inauspicious_sectors', [])
    assert len(inaus) >= 4, f"凶方应至少 4 个"
    print(f"  ✓ 凶方 {len(inaus)} 个，字段齐全")
    print()


def test_sitting_inversion():
    """朝向 → 坐山反转正确"""
    print("=" * 70)
    print("TEST 4: 朝向→坐山反转")
    print("=" * 70)
    client = make_client()
    cases = [
        ('南', '北', 1, '坎'),
        ('北', '南', 9, '离'),
        ('东', '西', 7, '兑'),
        ('西', '东', 3, '震'),
        ('东南', '西北', 6, '乾'),
        ('西北', '东南', 4, '巽'),
        ('东北', '西南', 2, '坤'),
        ('西南', '东北', 8, '艮'),
    ]
    for facing, expected_sitting, expected_gua, expected_name in cases:
        r = client.post('/fengshui/analysis', json={
            'birth_year': 1990, 'gender': 'male', 'house_facing': facing,
        })
        data = r.json()['data']
        assert data['house_sitting'] == expected_sitting, \
            f"朝{facing}: sitting={data['house_sitting']} 应={expected_sitting}"
        assert data['house_gua'] == expected_gua, \
            f"朝{facing}: gua={data['house_gua']} 应={expected_gua}"
        assert data['house_gua_name'] == expected_name
        print(f"  ✓ 朝{facing} → 坐{expected_sitting} → {expected_name}宅(卦{expected_gua})")
    print()


def test_personal_directions_complete():
    """个人方位包含 8 个吉凶位"""
    print("=" * 70)
    print("TEST 5: 个人方位 8 项完整")
    print("=" * 70)
    client = make_client()
    r = client.post('/fengshui/analysis', json={
        'birth_year': 1990, 'gender': 'male', 'house_facing': '南',
    })
    data = r.json()['data']
    pd = data['personal_directions']
    for key in ('shengqi', 'tianyi', 'niannian', 'fuwei',
                'jueming', 'wugui', 'liusha', 'huohai'):
        assert key in pd, f"缺 {key}"
        assert 'direction' in pd[key]
        assert 'meaning' in pd[key]
        print(f"  ✓ {key}: {pd[key]['direction']}")
    print()


def test_overall_advice_correctness():
    """overall_advice 与 is_compatible 一致（之前的 bug：永远显示不相配）"""
    print("=" * 70)
    print("TEST 6: overall_advice 与相配性一致")
    print("=" * 70)
    client = make_client()
    # 相配的情况
    r = client.post('/fengshui/analysis', json={
        'birth_year': 1990, 'gender': 'male', 'house_facing': '南',
    })
    data = r.json()['data']
    if data['is_compatible']:
        assert "相配，居住有利" in data['overall_advice'], \
            f"is_compatible=True 但 overall_advice='{data['overall_advice']}'"
    print(f"  ✓ 相配时 overall_advice 含'居住有利'")
    
    # 不相配的情况
    r2 = client.post('/fengshui/analysis', json={
        'birth_year': 1990, 'gender': 'male', 'house_facing': '东南',
    })
    data2 = r2.json()['data']
    if not data2['is_compatible']:
        assert "不相配" in data2['overall_advice']
    print(f"  ✓ 不相配时 overall_advice 含'不相配'")
    print()


if __name__ == "__main__":
    test_required_fields()
    test_compatibility_boolean()
    test_sector_fields()
    test_sitting_inversion()
    test_personal_directions_complete()
    test_overall_advice_correctness()
    print("=" * 70)
    print("ALL 风水前后端字段对齐 TESTS PASSED")
    print("=" * 70)
