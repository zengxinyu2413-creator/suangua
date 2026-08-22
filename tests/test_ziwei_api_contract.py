"""
紫微 /chart API 字段契约测试 — 防止前后端漂移

关键字段：
- metadata.soul_palace_index / body_palace_index (前端 InsightsBar / vis 依赖)
- insights.patterns.good/bad/total (PatternsCard 渲染)
- insights.rating.overall/score/soul_stars/soul_rating/sfsz_brief
- insights.feihua_by_palace
- insights.feihua_summary.{double_ji,soul_chong,lu_ji_war,lu_jie_ji,soul_incoming,quality_changes}
- insights.chong_chains.{total,events,top_warnings}
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.ziwei import router


def make_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_required_fields():
    """前端依赖的所有字段都存在"""
    print("=" * 70)
    print("TEST 1: 紫微 /chart 返回字段完整")
    print("=" * 70)
    client = make_client()
    r = client.post('/ziwei/chart', json={
        'year': 1990, 'month': 5, 'day': 22, 'hour': 5,
        'gender': '男', 'is_lunar': True,
    })
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()['data']
    
    # 顶层
    for f in ('metadata', 'palaces', 'feihua', 'sanjiao_analysis', 'insights'):
        assert f in data, f"缺顶层字段: {f}"
        print(f"  ✓ 顶层: {f}")
    
    # palaces 12 个
    assert len(data['palaces']) == 12
    print(f"  ✓ palaces = 12")
    
    # metadata 关键
    md = data['metadata']
    for f in ('birth_hour_name', 'soul_star', 'body_star', 'five_elements',
              'soul_palace_index', 'body_palace_index'):
        assert f in md, f"缺 metadata.{f}"
        print(f"  ✓ metadata.{f}: {md[f]}")
    
    # soul_palace_index 必须 ≥0（不是 -1）
    assert md['soul_palace_index'] >= 0, "soul_palace_index 应 ≥0"
    assert md['body_palace_index'] >= 0
    print()


def test_insights_structure():
    """insights 字段结构完整"""
    print("=" * 70)
    print("TEST 2: insights 结构")
    print("=" * 70)
    client = make_client()
    r = client.post('/ziwei/chart', json={
        'year': 1990, 'month': 5, 'day': 22, 'hour': 5,
        'gender': '男', 'is_lunar': True,
    })
    data = r.json()['data']
    ins = data['insights']
    
    # rating
    rating = ins.get('rating', {})
    for f in ('overall', 'score', 'soul_stars', 'sfsz_brief'):
        assert f in rating, f"缺 insights.rating.{f}"
    print(f"  ✓ rating: overall={rating['overall']}, score={rating['score']}")
    assert isinstance(rating['score'], (int, float))
    assert isinstance(rating['soul_stars'], list)
    assert len(rating['sfsz_brief']) >= 1, "sfsz_brief 应至少 1 项（三方四正）"
    print(f"  ✓ sfsz_brief 项数: {len(rating['sfsz_brief'])}")
    
    # patterns
    patterns = ins.get('patterns', {})
    for f in ('good', 'bad', 'total'):
        assert f in patterns, f"缺 insights.patterns.{f}"
    assert isinstance(patterns['good'], list)
    assert isinstance(patterns['bad'], list)
    print(f"  ✓ patterns: 吉{len(patterns['good'])}/凶{len(patterns['bad'])}/total={patterns['total']}")
    
    # feihua_summary
    fs = ins.get('feihua_summary', {})
    for f in ('double_ji', 'lu_jie_ji', 'lu_ji_war', 'soul_incoming', 'soul_chong',
              'quality_changes', 'self_out_palaces', 'self_in_palaces'):
        assert f in fs, f"缺 insights.feihua_summary.{f}"
    print(f"  ✓ feihua_summary 8 个子字段齐全")
    
    # feihua_by_palace
    fbp = ins.get('feihua_by_palace', {})
    assert isinstance(fbp, dict), "feihua_by_palace 应为 dict"
    assert len(fbp) == 12, f"feihua_by_palace 应有 12 宫，实际 {len(fbp)}"
    print(f"  ✓ feihua_by_palace 12 宫齐全")
    
    # chong_chains
    cc = ins.get('chong_chains', {})
    for f in ('total', 'events', 'top_warnings', 'key_palaces_hit'):
        assert f in cc, f"缺 insights.chong_chains.{f}"
    print(f"  ✓ chong_chains: total={cc['total']}, warnings={len(cc['top_warnings'])}")
    print()


def test_real_chart_zitan():
    """真实命盘 1990 卯时：紫贪同宫格 + 杀破狼格"""
    print("=" * 70)
    print("TEST 3: 1990 卯时男 — 紫贪同宫 + 杀破狼")
    print("=" * 70)
    client = make_client()
    r = client.post('/ziwei/chart', json={
        'year': 1990, 'month': 5, 'day': 22, 'hour': 5,
        'gender': '男', 'is_lunar': True,
    })
    data = r.json()['data']
    
    # 时辰应是卯时
    assert data['metadata']['birth_hour_name'] == '卯时', \
        f"hour=5 应为卯时，实际 {data['metadata']['birth_hour_name']}"
    print(f"  ✓ hour=5 = 卯时")
    
    # 命宫主星
    soul_idx = data['metadata']['soul_palace_index']
    soul_p = data['palaces'][soul_idx]
    soul_stars = {s['name'] for s in soul_p.get('major_stars', [])}
    assert '紫微' in soul_stars and '贪狼' in soul_stars, \
        f"命宫应紫微+贪狼，实际 {soul_stars}"
    print(f"  ✓ 命宫紫微+贪狼")
    
    # 命宫在卯
    assert soul_p['earthly_branch'] == '卯'
    print(f"  ✓ 命宫在卯位")
    
    # 格局应识别紫贪同宫格 + 杀破狼格
    pattern_names = [p['name'] for p in data['insights']['patterns']['good']]
    assert '紫贪同宫格' in pattern_names, f"应识别紫贪同宫格，实际 {pattern_names}"
    assert '杀破狼格' in pattern_names, f"应识别杀破狼格，实际 {pattern_names}"
    print(f"  ✓ 识别格局: {pattern_names}")
    print()


def test_decade_endpoint():
    """大限端点字段"""
    print("=" * 70)
    print("TEST 4: /ziwei/decade 端点")
    print("=" * 70)
    client = make_client()
    r = client.post('/ziwei/decade', json={
        'year': 1990, 'month': 5, 'day': 22, 'hour': 5,
        'gender': '男', 'is_lunar': True, 'age': 30,
    })
    assert r.status_code == 200, f"HTTP {r.status_code}"
    data = r.json()['data']
    
    # decade 嵌套在 data.decade
    assert 'decade' in data, f"缺 decade 嵌套"
    decade = data['decade']
    for f in ('palace_name', 'age_range', 'stem', 'palaces_layout'):
        assert f in decade, f"缺 decade.{f}"
    print(f"  ✓ 大限{decade.get('palace_name')} ({decade.get('age_range')})")
    
    # feihua + overlay_insights 在顶层
    assert 'feihua' in data
    assert isinstance(data['feihua'], list) and len(data['feihua']) >= 3
    print(f"  ✓ 大限四化 {len(data['feihua'])} 条")
    
    assert 'overlay_insights' in data
    print(f"  ✓ overlay_insights 存在")
    print()


def test_triple_endpoint():
    """三盘叠合端点"""
    print("=" * 70)
    print("TEST 5: /ziwei/triple 端点")
    print("=" * 70)
    client = make_client()
    r = client.post('/ziwei/triple', json={
        'year': 1990, 'month': 5, 'day': 22, 'hour': 5,
        'gender': '男', 'is_lunar': True, 'age': 30,
    })
    assert r.status_code == 200
    data = r.json()['data']
    print(f"  ✓ /triple 返回 200，字段: {list(data.keys())[:6]}")
    print()


def test_bazi_overlay():
    """bazi_overlay 字段：八字大运、十神、纳音、真太阳时"""
    print("=" * 70)
    print("TEST 6: bazi_overlay 八字大运字段")
    print("=" * 70)
    client = make_client()
    r = client.post('/ziwei/chart', json={
        'year': 1990, 'month': 5, 'day': 22, 'hour': 7, 'minute': 30,
        'gender': '男', 'is_lunar': True,
        'longitude': 104.06,
    })
    data = r.json()['data']
    ovr = data.get('bazi_overlay', {})
    assert ovr, "缺 bazi_overlay 字段"
    
    for k in ('sizhu_jieqi', 'sizhu_nonjieqi', 'shishen', 'shishen_zhi',
              'canggan', 'nayin', 'qiyun', 'dayun', 'real_time'):
        assert k in ovr, f"缺 bazi_overlay.{k}"
    print(f"  ✓ 9 个子字段齐全")
    
    sj = ovr['sizhu_jieqi']
    for k in ('year', 'month', 'day', 'time'):
        assert k in sj
    print(f"  ✓ 节气四柱: {sj}")
    
    ss = ovr['shishen']
    assert ss.get('year') and ss.get('month') and ss.get('time')
    assert ss.get('day') == '日主'
    print(f"  ✓ 十神: 年{ss['year']}/月{ss['month']}/日{ss['day']}/时{ss['time']}")
    
    dy = ovr['dayun']
    assert isinstance(dy, list) and len(dy) >= 8
    assert all('start_age' in d and 'ganzhi' in d for d in dy)
    print(f"  ✓ 大运 {len(dy)} 步：首步 {dy[0]['start_age']}-{dy[0]['end_age']}岁 {dy[0]['ganzhi']}")
    
    rt = ovr['real_time']
    assert rt and 'real_solar_time' in rt
    print(f"  ✓ 真太阳时: {rt['clock_time']} → {rt['real_solar_time']} (经度 {rt['longitude']}°)")
    print()


def test_time_panel():
    """time_panel 字段：流月"""
    print("=" * 70)
    print("TEST 7: time_panel 流月")
    print("=" * 70)
    client = make_client()
    r = client.post('/ziwei/chart', json={
        'year': 1990, 'month': 5, 'day': 22, 'hour': 7,
        'gender': '男', 'is_lunar': True,
    })
    data = r.json()['data']
    tp = data.get('time_panel', {})
    assert tp, "缺 time_panel"
    
    months = tp.get('months', [])
    assert len(months) == 12, f"流月应 12 个，实际 {len(months)}"
    for m in months:
        for k in ('lunar_month', 'month_name', 'ganzhi'):
            assert k in m
    print(f"  ✓ 流月 12 个，首月: {months[0]['month_name']}({months[0]['ganzhi']})")
    print()


def test_jieqi_vs_nonjieqi_differ():
    """节气派/非节气派在节气交界日应该真的不同"""
    print("=" * 70)
    print("TEST 8: 节气派/非节气派差异（节气交界日）")
    print("=" * 70)
    client = make_client()
    
    # 1990-02-04 立春日 (公历)
    # 节气派：年柱已切到庚午
    # 非节气派：年柱还是己巳（农历未到正月初一）
    r = client.post('/ziwei/chart', json={
        'year': 1990, 'month': 2, 'day': 4, 'hour': 5,
        'gender': '男', 'is_lunar': False,
    })
    data = r.json()['data']
    ovr = data['bazi_overlay']
    
    sjq = ovr['sizhu_jieqi']
    snj = ovr['sizhu_nonjieqi']
    assert sjq != snj, f"节气交界日两派应该不同，实际相同: {sjq}"
    print(f"  ✓ 节气派:   {sjq}")
    print(f"  ✓ 非节气派: {snj}")
    
    # 十神也应该不同
    ssj = ovr['shishen_jieqi']
    ssn = ovr['shishen_nonjieqi']
    assert ssj != ssn, "节气交界日十神应该不同"
    print(f"  ✓ 节气派十神:   {ssj}")
    print(f"  ✓ 非节气派十神: {ssn}")
    
    # 纳音也应该不同（年柱不同）
    nyj = ovr['nayin_jieqi']
    nyn = ovr['nayin_nonjieqi']
    assert nyj['year'] != nyn['year'], "节气交界日年柱纳音应该不同"
    print(f"  ✓ 节气派年纳音:   {nyj['year']}")
    print(f"  ✓ 非节气派年纳音: {nyn['year']}")
    print()


def test_layer_difference():
    """本命/大限/三盘 — 三层数据应有显著差异"""
    print("=" * 70)
    print("TEST 9: 本命/大限/三盘 三层差异")
    print("=" * 70)
    client = make_client()
    
    base = {'year':1990,'month':5,'day':22,'hour':5,
            'gender':'男','is_lunar':True}
    
    # 1. /chart 本命
    r1 = client.post('/ziwei/chart', json=base)
    natal = r1.json()['data']
    
    # 2. /decade 大限
    r2 = client.post('/ziwei/decade', json={**base, 'age': 35})
    decade = r2.json()['data']
    
    # 3. /triple 三盘
    r3 = client.post('/ziwei/triple', json={**base, 'age': 35})
    triple = r3.json()['data']
    
    # 验证 1: 大限有 palaces_layout
    decade_layout = (decade.get('overlay_insights',{}) or {}).get('decade',{}).get('palaces_layout') \
                    or decade.get('palaces_layout')
    assert decade_layout, f"大限缺 palaces_layout，data keys={list(decade.keys())}"
    assert len(decade_layout) == 12
    print(f"  ✓ /decade 返回 12 宫大限名称（如 '大限命宫'）")
    
    # 验证 2: 三盘的 overlay_insights.annual 不再是 None（默认 current_year 当年）
    triple_annual = triple.get('overlay_insights',{}).get('annual')
    assert triple_annual is not None, "三盘 annual 不应该为 None（已默认当前年）"
    annual_layout = triple_annual.get('palaces_layout')
    assert annual_layout and len(annual_layout) == 12, "annual.palaces_layout 应有 12 宫"
    print(f"  ✓ /triple 返回 annual.palaces_layout（流年 12 宫名称）")
    print(f"    流年: {triple_annual['year']}年（{triple_annual['stem']}干）")
    
    # 验证 3: 大限/流年命宫名应符合预期
    soul_decade = [k for k, v in decade_layout.items() if v.get('name') == '大限命宫']
    soul_annual = [k for k, v in annual_layout.items() if v.get('name') == '流年命宫']
    assert len(soul_decade) == 1
    assert len(soul_annual) == 1
    print(f"  ✓ 大限命宫位于本命第 {soul_decade[0]} 宫")
    print(f"  ✓ 流年命宫位于本命第 {soul_annual[0]} 宫")
    print()


if __name__ == "__main__":
    test_required_fields()
    test_insights_structure()
    test_real_chart_zitan()
    test_decade_endpoint()
    test_triple_endpoint()
    test_bazi_overlay()
    test_time_panel()
    test_jieqi_vs_nonjieqi_differ()
    test_layer_difference()
    print("=" * 70)
    print("ALL 紫微 API 契约测试 PASSED")
    print("=" * 70)
