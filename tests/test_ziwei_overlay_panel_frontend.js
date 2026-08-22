/**
 * Frontend test: ZiweiPalaceDetailPanel — layer-aware 渲染（Z-6 增强）
 *
 * 验证：
 *   1. layer='natal'：不显示运程层飞化
 *   2. layer='decade'：显示大限飞化分区（仅当本宫接收大限化象时）
 *   3. layer='triple'：同时显示大限+流年飞化分区
 *   4. 本宫未接收 overlay 化象时显示"未落入本宫"提示
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.HTMLElement = dom.window.HTMLElement

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const PalaceDetailPanel = require('/tmp/test_build/ZiweiPalaceDetailPanel.js').default

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}
function render(el) { return ReactDOMServer.renderToStaticMarkup(el) }

// 模拟命宫 idx=1
const mockPalace = {
  index: 1,
  name: '命宫',
  heavenly_stem: '己',
  earthly_branch: '卯',
  is_soul: true, is_body: false,
  major_stars: [
    { name: '紫微', brightness: '旺', mutagen: '' },
    { name: '贪狼', brightness: '旺', mutagen: '权' },
  ],
  minor_stars: [],
  adj_stars: [],
  decadal_range: [5, 14],
  changsheng12: '死',
}

const mockAllPalaces = []
for (let i = 0; i < 12; i++) {
  mockAllPalaces.push({
    index: i, name: `宫${i}`, earthly_branch: '子',
    heavenly_stem: '甲', major_stars: [],
  })
}

// 模拟 overlay：大限化象有飞入命宫(idx=1)，流年没有
const mockOverlayInsights = {
  decade: {
    stem: '壬',
    palace_name: '田宅宫',
    palace_idx: 4,
    key_warnings: ['✦ 大限化权紫微飞入命宫（大限吉象，本身受益）'],
    by_target_idx: {
      '1': [{
        hua_type: '化权', target_star: '紫微',
        target_palace_name: '命宫', fh_type: '普通飞宫',
        is_inner: true, chong_palace: '',
        is_he_won_ji: false, is_double_ji: false,
        is_lu_ji_war: false,
        interpretation: '大限化权紫微入命宫，主受益于运程',
      }],
      '4': [/* 落自己的大限宫，自化禄 */],
    },
    transformations: [],
  },
  annual: {
    stem: '丙',
    year: 2026,
    palace_name: '命宫',
    key_warnings: [],
    by_target_idx: {
      '6': [{
        hua_type: '化禄', target_star: '天同',
        target_palace_name: '官禄宫', fh_type: '普通飞宫',
        is_inner: false, chong_palace: '',
        is_he_won_ji: false, is_double_ji: false,
        is_lu_ji_war: false,
        interpretation: '流年化禄天同入官禄宫',
      }],
    },
    transformations: [],
  },
}

// 模拟流年也有飞入命宫的版本
const mockOverlayInsightsBothToSoul = {
  decade: mockOverlayInsights.decade,
  annual: {
    ...mockOverlayInsights.annual,
    by_target_idx: {
      '1': [{
        hua_type: '化忌', target_star: '廉贞',
        target_palace_name: '命宫', fh_type: '普通飞宫',
        is_inner: true, chong_palace: '迁移宫',
        is_he_won_ji: false, is_double_ji: false,
        is_lu_ji_war: false,
        interpretation: '流年化忌廉贞冲命宫',
      }],
    },
  },
}

console.log('='.repeat(70))
console.log('TEST 1: layer="natal" — 不显示运程层')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: null,
    layer: 'natal',
    overlayInsights: mockOverlayInsights,
  }))
  assert(!html.includes('运程层飞化'), 'natal 视图不显示运程层标题')
  assert(!html.includes('大限飞入本宫'), 'natal 视图不显示大限飞入')
  assert(!html.includes('流年'), 'natal 视图不显示流年')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: layer="decade" — 显示大限飞化（命宫接收大限化权）')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: null,
    layer: 'decade',
    overlayInsights: mockOverlayInsights,
  }))
  assert(html.includes('运程层飞化'), '运程层标题')
  assert(html.includes('大限层'), '大限层标记')
  assert(html.includes('大限飞入本宫'), '大限飞入分区')
  assert(html.includes('紫微'), '化象星紫微')
  assert(html.includes('化权'), '化象化权')
  assert(html.includes('田宅宫'), '大限命宫 meta')
  assert(html.includes('壬'), '大限干壬 meta')
  assert(!html.includes('流年飞入本宫'), 'decade 视图不显示流年分区')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: layer="triple" — 同时显示大限+流年（仅命宫接收大限）')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: null,
    layer: 'triple',
    overlayInsights: mockOverlayInsights,
  }))
  assert(html.includes('大限+流年层'), 'triple 视图标题')
  assert(html.includes('大限飞入本宫'), '大限飞入分区')
  assert(html.includes('紫微'), '大限化权星')
  // 流年没飞到命宫，所以不应有"流年飞入本宫"小节，但 renderHuaList 会跳过
  assert(!html.includes('流年2026 飞入本宫') && !html.includes('流年飞入本宫'),
    '流年没飞到命宫则不显示流年分区')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: layer="triple" — 大限+流年都飞到本宫')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: null,
    layer: 'triple',
    overlayInsights: mockOverlayInsightsBothToSoul,
  }))
  assert(html.includes('大限飞入本宫'), '大限分区')
  assert(html.includes('流年2026飞入本宫') || html.includes('流年2026 飞入本宫'), '流年分区')
  assert(html.includes('廉贞'), '流年化忌星')
  assert(html.includes('冲迁移宫'), '冲宫标记')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 本宫未接收 overlay 化象时显示提示')
console.log('='.repeat(70))
{
  // 用 idx=11（任何 by_target_idx 里没的 key）的宫位
  const otherPalace = { ...mockPalace, index: 11, name: '父母宫' }
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: otherPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: null,
    layer: 'decade',
    overlayInsights: mockOverlayInsights,
  }))
  assert(html.includes('大限') && html.includes('未落入本宫'), '显示"未落入本宫"提示')
  assert(html.includes('田宅宫'), '提示中显示大限命宫所在')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: overlayInsights=null 时不显示运程层')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: null,
    layer: 'triple',
    overlayInsights: null,
  }))
  assert(!html.includes('运程层飞化'), 'overlay=null 不显示运程层')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
