/**
 * Frontend test: LiuyaoDeepRelations (L-1 深度关系展示)
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const LiuyaoDeepRelations = require('/tmp/test_build/LiuyaoDeepRelations.js').default

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}
function render(el) { return ReactDOMServer.renderToStaticMarkup(el) }

const mockDeepRelations = {
  deep_relations: {
    yong_yuan_ji_chou: {
      '用神_wx': '金', '原神_wx': '土',
      '忌神_wx': '火', '仇神_wx': '木',
    },
    key_lines: {
      '用神_lines': [{ position: 4, liu_qin: '妻财', branch: '酉' }],
      '原神_lines': [
        { position: 3, liu_qin: '子孙', branch: '未' },
        { position: 6, liu_qin: '子孙', branch: '丑' },
      ],
      '忌神_lines': [{ position: 2, liu_qin: '兄弟', branch: '巳' }],
      '仇神_lines': [{ position: 1, liu_qin: '父母', branch: '卯' }],
    },
    changing_relations: [
      {
        position: 3, liu_qin: '子孙',
        relation: '回头生',
        interpretation: '未动化亥，水生土，回头生',
        orig_branch: '未', changed_branch: '亥',
        orig_wx: '土', changed_wx: '水',
      },
    ],
    line_details: [
      { liu_qin: '父母', branch: '卯', wuxing: '木',
        month_chs: { status: '病' }, day_chs: { status: '绝' },
        is_yuepo: false, is_ripo: false, overall: '无气' },
      { liu_qin: '兄弟', branch: '巳', wuxing: '火',
        month_chs: { status: '帝旺' }, day_chs: { status: '绝' },
        is_yuepo: false, is_ripo: true, overall: '中和' },
    ],
    summary: [
      '用神金、原神土（生用神）、忌神火（克用神）、仇神木（生忌神）',
      '⚠ 忌神出现于：第2爻(兄弟巳) — 需重点关注其状态',
    ],
  },
}

console.log('=' .repeat(70))
console.log('TEST 1: 无 deep_relations 显示提示')
console.log('='.repeat(70))
{
  const html = render(React.createElement(LiuyaoDeepRelations, { data: {} }))
  assert(html.includes('未启用深度关系分析'), '空数据提示')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 四神五行卡片')
console.log('='.repeat(70))
{
  const html = render(React.createElement(LiuyaoDeepRelations, { data: mockDeepRelations }))
  assert(html.includes('用神'), '用神标签')
  assert(html.includes('原神'), '原神标签')
  assert(html.includes('忌神'), '忌神标签')
  assert(html.includes('仇神'), '仇神标签')
  assert(html.includes('生用神（护神）'), '原神角色描述')
  assert(html.includes('克用神'), '忌神角色描述')
  // 五行颜色
  assert(html.includes('#95a5a6') || html.toLowerCase().includes('#95a5a6'), '金元素灰色')
  assert(html.includes('#e74c3c') || html.toLowerCase().includes('#e74c3c'), '火元素红色')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 四神爻位定位')
console.log('='.repeat(70))
{
  const html = render(React.createElement(LiuyaoDeepRelations, { data: mockDeepRelations }))
  assert(html.includes('四神爻位详查'), '四神爻位标题')
  assert(html.includes('第4爻') || html.includes('四爻'), '第4爻位置')
  assert(html.includes('妻财') && html.includes('酉'), '妻财酉爻信息')
  assert(html.includes('第3爻') || html.includes('三爻'), '第3爻位置')
  assert(html.includes('子孙') && html.includes('未'), '子孙未爻信息')
  assert(html.includes('兄弟') && html.includes('巳'), '兄弟巳爻信息')
  assert(html.includes('生用神（护神）'), '原神描述')
  assert(html.includes('克用神（敌）'), '忌神描述')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 动爻变化分析')
console.log('='.repeat(70))
{
  const html = render(React.createElement(LiuyaoDeepRelations, { data: mockDeepRelations }))
  assert(html.includes('动爻变化'), '动爻变化标题')
  assert(html.includes('共 1 处'), '动爻数量')
  assert(html.includes('回头生'), '回头生关系')
  assert(html.includes('未动化亥'), '动爻具体描述')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 六爻力量评估')
console.log('='.repeat(70))
{
  const html = render(React.createElement(LiuyaoDeepRelations, { data: mockDeepRelations }))
  assert(html.includes('十二长生'), '十二长生说明')
  assert(html.includes('初'), '初爻位置')
  assert(html.includes('无气'), '力量评估')
  assert(html.includes('[日破]'), '日破标记')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: 关键提示')
console.log('='.repeat(70))
{
  const html = render(React.createElement(LiuyaoDeepRelations, { data: mockDeepRelations }))
  assert(html.includes('关键提示'), '关键提示标题')
  assert(html.includes('忌神出现于'), '警示内容')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 7: 引文')
console.log('='.repeat(70))
{
  const html = render(React.createElement(LiuyaoDeepRelations, { data: mockDeepRelations }))
  assert(html.includes('《增删卜易》'), '引古书')
  assert(html.includes('用神旺相又有原神生扶'), '论卦要诀')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
