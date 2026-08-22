/**
 * Frontend test: BaziInsightsBar (B-3)
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const BaziInsightsBar = require('/tmp/test_build/BaziInsightsBar.js').default

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}
function render(el) { return ReactDOMServer.renderToStaticMarkup(el) }

// 模拟真实命盘数据
const mockData = {
  yong_shen: {
    yong_shen_wx: '火',
    xi_shen_wx: '金',
    ji_shen_wx: '木',
    chou_shen_wx: '水',
    analysis: '庚金身弱，喜火炼金',
    tiao_hou: { desc: '丁壬为主，甲为佐' },
  },
  special_patterns: {
    total: 3, total_aus: 2, total_inaus: 1,
    matched: [
      { name: '财官印三全', auspicious: true, condition: '财、官、印同透',
        interpretation: '大富大贵之格' },
      { name: '魁罡格', auspicious: true, condition: '日柱庚辰',
        interpretation: '主聪明果断' },
      { name: '伤官见官', auspicious: false, condition: '伤官与正官同透',
        interpretation: '凶格' },
    ],
  },
  relations: {
    summary: {
      total_he: 2, total_chong: 0, total_xing: 0, total_hai: 1, total_po: 0,
      key_blessings: ['· 年柱午与月柱未六合化土'],
      key_warnings: ['· 日柱辰与时柱卯相害'],
    },
  },
  shensha: [
    { name: '天乙贵人', position: '月柱' },
    { name: '将星',     position: '年柱' },
    { name: '桃花',     position: '时柱' },
  ],
}

console.log('=' .repeat(70))
console.log('TEST 1: null data 不渲染')
console.log('='.repeat(70))
{
  const html = render(React.createElement(BaziInsightsBar, { data: null }))
  assert(html === '', 'null data 不渲染')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 完整数据渲染所有卡片')
console.log('='.repeat(70))
{
  const html = render(React.createElement(BaziInsightsBar, { data: mockData }))
  assert(html.includes('用神'), '用神卡片')
  assert(html.includes('特殊格局深度识别'), '特殊格局卡片')
  assert(html.includes('地支刑冲合害'), '刑冲合害卡片')
  assert(html.includes('神煞速览'), '神煞卡片')
  assert(html.includes('财官印三全'), '吉格名称')
  assert(html.includes('魁罡格'), '魁罡格名称')
  assert(html.includes('伤官见官'), '凶格名称')
  assert(html.includes('天乙贵人'), '神煞名称')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 用神五行颜色')
console.log('='.repeat(70))
{
  const html = render(React.createElement(BaziInsightsBar, { data: mockData }))
  // 用神是火 - 应该有红色
  assert(html.includes('#e74c3c') || html.includes('#E74C3C'), '火元素红色')
  // 喜神是金 - 灰色
  assert(html.includes('#95a5a6') || html.includes('#95A5A6'), '金元素灰色')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 特殊格局吉凶颜色区分')
console.log('='.repeat(70))
{
  const html = render(React.createElement(BaziInsightsBar, { data: mockData }))
  // 吉格 → 绿色 #27ae60
  assert(html.toLowerCase().includes('#27ae60'), '吉格绿色')
  // 凶格 → 红色 #e74c3c
  assert(html.toLowerCase().includes('#e74c3c'), '凶格红色')
  // 吉格符号
  assert(html.includes('✦'), '吉格符号 ✦')
  assert(html.includes('⚠'), '凶格符号 ⚠')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 刑冲合害计数')
console.log('='.repeat(70))
{
  const html = render(React.createElement(BaziInsightsBar, { data: mockData }))
  assert(html.includes('合×2'), '合×2 显示')
  assert(html.includes('害×1'), '害×1 显示')
  assert(!html.includes('冲×0'), '冲×0 不显示（隐藏空项）')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: 特殊格局 total=0 不渲染该卡')
console.log('='.repeat(70))
{
  const partialData = {
    yong_shen: mockData.yong_shen,
    special_patterns: { total: 0, total_aus: 0, total_inaus: 0, matched: [] },
    relations: mockData.relations,
  }
  const html = render(React.createElement(BaziInsightsBar, { data: partialData }))
  assert(!html.includes('特殊格局深度识别'), 'total=0 时不渲染')
  assert(html.includes('用神'), '其他卡片仍渲染')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 7: 调候信息')
console.log('='.repeat(70))
{
  const html = render(React.createElement(BaziInsightsBar, { data: mockData }))
  assert(html.includes('丁壬为主'), '调候内容')
  assert(html.includes('穷通宝鉴'), '调候出处')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
