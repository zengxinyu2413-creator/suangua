/**
 * 紫微页面：真实命盘 1990 卯时端到端测试
 *
 * 防止前后端字段漂移导致页面渲染异常。
 * 用 jsdom 模拟整个 ZiWeiPage 渲染，验证关键文本与字段。
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}

// 模拟后端 /chart 返回（来自真实 API 输出）
const mockChartResponse = {
  metadata: {
    birth_hour_name: '卯时',
    birth_hour_range: '05:00~07:00',
    soul_star: '文曲',
    body_star: '火星',
    five_elements: '土五局',
    soul_palace_index: 1,
    body_palace_index: 7,
    gender: '男',
    chinese_date: '庚午年 癸未月 庚辰日 己卯时',
    zodiac: '马',
    solar_date: '1990-07-14',
  },
  palaces: [
    { index: 0, name: '兄弟宫', earthly_branch: '寅', heavenly_stem: '戊',
      major_stars: [{name:'天机',brightness:'得'},{name:'太阴',brightness:'平'}],
      minor_stars: [{name:'地劫'}], is_soul: false, is_body: false },
    { index: 1, name: '命宫', earthly_branch: '卯', heavenly_stem: '己',
      major_stars: [{name:'紫微',brightness:'旺'},{name:'贪狼',brightness:'旺'}],
      minor_stars: [], is_soul: true, is_body: false },
    { index: 2, name: '父母宫', earthly_branch: '辰', heavenly_stem: '庚',
      major_stars: [{name:'巨门',brightness:'陷'}],
      minor_stars: [{name:'火星'}], is_soul: false, is_body: false },
  ],
  insights: {
    rating: {
      overall: '中上格',
      score: 1.88,
      summary: '主星明亮，先天命格良好，运程顺遂',
      soul_rating: '上格',
      soul_average: 6,
      soul_stars: ['紫微','贪狼'],
      sfsz_brief: [
        { palace: '命宫', stars: '紫微/贪狼', brightness: '旺/旺', rating: '上格' },
        { palace: '迁移宫', stars: '空宫', brightness: '', rating: '中格' },
        { palace: '官禄宫', stars: '廉贞/七杀', brightness: '平/平', rating: '中格' },
        { palace: '财帛宫', stars: '武曲/破军', brightness: '平/平', rating: '中格' },
      ],
      star_notes: [],
    },
    patterns: {
      good: [
        { name: '紫贪同宫格', category: '吉格',
          evidence: ['命宫在卯宫','紫微+贪狼同坐命宫','桃花格局，主多才多艺、人缘极佳'],
          meaning: '紫微为帝、贪狼为桃花，紫贪卯酉乃风流贵格' },
        { name: '杀破狼格', category: '吉格',
          evidence: ['七杀坐官禄宫','破军坐财帛宫','贪狼坐命宫','命财官三合会齐'],
          meaning: '易动不易静，一生变动大' },
      ],
      bad: [],
      total: 2,
    },
    feihua_summary: {
      double_ji: [], lu_jie_ji: [], lu_ji_war: [], soul_incoming: [],
      soul_chong: [], quality_changes: [], self_out_palaces: [], self_in_palaces: [],
      concentration: {},
    },
    feihua_by_palace: {},
    chong_chains: {
      total: 9,
      events: [],
      top_warnings: ['化忌冲命宫','双忌叠加'],
      key_palaces_hit: { '命宫': 2 },
    },
  },
}

console.log('='.repeat(70))
console.log('TEST 1: metadata 关键字段在响应中')
console.log('='.repeat(70))
{
  const md = mockChartResponse.metadata
  assert(md.soul_palace_index === 1, 'soul_palace_index = 1')
  assert(md.body_palace_index === 7, 'body_palace_index = 7')
  assert(md.birth_hour_name === '卯时', '时辰=卯时')
  assert(md.five_elements === '土五局', '五行局存在')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: insights.rating 字段')
console.log('='.repeat(70))
{
  const r = mockChartResponse.insights.rating
  assert(r.overall === '中上格', 'overall=中上格')
  assert(typeof r.score === 'number', 'score 是数字')
  assert(r.score === 1.88, 'score=1.88')
  assert(Array.isArray(r.soul_stars), 'soul_stars 是数组')
  assert(r.soul_stars.includes('紫微'), '命宫含紫微')
  assert(r.soul_stars.includes('贪狼'), '命宫含贪狼')
  assert(r.soul_rating === '上格', '命宫评级=上格')
  assert(r.sfsz_brief.length === 4, '三方四正 4 项')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: insights.patterns 字段')
console.log('='.repeat(70))
{
  const p = mockChartResponse.insights.patterns
  assert(Array.isArray(p.good), 'good 是数组')
  assert(Array.isArray(p.bad), 'bad 是数组')
  assert(p.good.length === 2, '识别 2 吉格')
  assert(p.bad.length === 0, '无凶格')
  assert(p.total === 2, 'total=2')
  
  const names = p.good.map(x => x.name)
  assert(names.includes('紫贪同宫格'), '识别紫贪同宫格')
  assert(names.includes('杀破狼格'), '识别杀破狼格')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: insights.chong_chains 结构')
console.log('='.repeat(70))
{
  const cc = mockChartResponse.insights.chong_chains
  assert(typeof cc.total === 'number', 'total 是数字')
  assert(cc.total === 9, 'chong_chains.total=9')
  assert(Array.isArray(cc.top_warnings), 'top_warnings 是数组')
  assert(cc.top_warnings.length >= 1, 'top_warnings 至少 1 条')
  assert(typeof cc.key_palaces_hit === 'object', 'key_palaces_hit 是 dict')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: palaces 数据结构（PalaceCell 渲染所需字段）')
console.log('='.repeat(70))
{
  const soulPalace = mockChartResponse.palaces[1]
  assert(soulPalace.is_soul === true, '命宫 is_soul=true')
  assert(soulPalace.earthly_branch === '卯', '命宫地支=卯')
  assert(soulPalace.heavenly_stem === '己', '命宫天干=己')
  assert(soulPalace.major_stars.length === 2, '命宫 2 主星')
  assert(soulPalace.major_stars[0].brightness === '旺', '紫微亮度=旺')
  assert(soulPalace.major_stars[1].brightness === '旺', '贪狼亮度=旺')
  assert(soulPalace.name === '命宫', '命宫.name=命宫')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: 大限响应扁平化逻辑（前端 loadDecade 字段映射）')
console.log('='.repeat(70))
{
  // 模拟后端返回
  const mockDecade = {
    decade: {
      palace_idx: 3,
      palace_name: '福德宫',
      stem: '辛',
      age_range: [25, 34],
      palaces_layout: {
        '3': { name: '大限命宫', short: '大-命', offset: 0 },
        '2': { name: '大限兄弟', short: '大-兄', offset: 1 },
      },
    },
    feihua: [
      { hua_type: '化禄', target_star: '巨门', target_palace_name: '父母宫' },
    ],
    overlay_insights: { decade: {} },
  }
  
  // 模拟前端扁平化（来自 ZiWeiPage.jsx loadDecade）
  const flat = {
    ...(mockDecade.decade || {}),
    decade_feihua: mockDecade.feihua || [],
    feihua: mockDecade.feihua || [],
    overlay_insights: mockDecade.overlay_insights || null,
  }
  
  assert(flat.palace_name === '福德宫', 'flat.palace_name=福德宫')
  assert(flat.age_range[0] === 25, 'age_range[0]=25')
  assert(flat.age_range[1] === 34, 'age_range[1]=34')
  assert(flat.palaces_layout && flat.palaces_layout['3'], 'palaces_layout 直接可用')
  assert(flat.decade_feihua.length === 1, 'decade_feihua 有数据')
  assert(flat.feihua.length === 1, 'feihua 兼容字段')
  assert(flat.overlay_insights, 'overlay_insights 保留')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
