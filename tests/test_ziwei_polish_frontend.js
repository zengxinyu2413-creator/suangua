/**
 * Frontend test: ZiweiInsightsBar 渲染测试
 *
 * 前置：测试运行前已用 babel CLI 转译 .jsx → /tmp/test_build/*.js
 */
const { JSDOM } = require('jsdom')

// 模拟 DOM
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
})
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.HTMLElement = dom.window.HTMLElement

const React = require('react')
const ReactDOMServer = require('react-dom/server')

const ZiweiInsightsBar = require('/tmp/test_build/ZiweiInsightsBar.js').default

// ── 测试用数据 ──
const fullInsights = {
  rating: {
    overall: '上格',
    score: 2.14,
    summary: '命宫与三方四正主星普遍庙旺，先天命格优异',
    soul_rating: '上格',
    soul_average: 3.0,
    soul_stars: ['紫微'],
    sfsz_brief: [
      { palace: '命宫', branch: '午', stars: ['紫微'], rating: '上格', score: 3.0 },
      { palace: '官禄宫', branch: '戌', stars: ['廉贞', '天府'], rating: '中上格', score: 1.5 },
      { palace: '财帛宫', branch: '寅', stars: ['武曲', '天相'], rating: '上格', score: 2.0 },
      { palace: '迁移宫', branch: '子', stars: ['贪狼'], rating: '上格', score: 2.0 },
    ],
    star_notes: [
      '紫微午宫入庙：帝座之地，权威最盛',
      '天府戌宫入庙：库星归位，主稳重而富',
      '太阴亥宫入庙：月朗天门格，富贵之命',
      '太阳卯宫入庙：日照雷门格，富贵声扬',
    ],
  },
  patterns: {
    good: [
      {
        name: '君臣庆会格',
        category: '吉格',
        evidence: ['命宫坐紫微（午宫）', '三方四正会齐 5 颗辅佐星'],
        meaning: '紫微为君，府相昌曲为臣；不大贵即当大富',
        break_conditions: ['见四煞空劫忌则反为奴欺主'],
        is_partial: false,
      },
      {
        name: '日月并明格',
        category: '吉格',
        evidence: ['太阳卯庙', '太阴亥庙'],
        meaning: '富贵双全，女命旺夫益子',
        break_conditions: ['若两星都化忌则减格'],
        is_partial: false,
      },
    ],
    bad: [],
    total: 2,
  },
  feihua_summary: {
    quality_changes: [],
    double_ji: [
      { from: '夫妻宫', star: '天同', to: '疾厄宫' },
    ],
    lu_jie_ji: [
      { from: '官禄宫', star: '天同', to: '疾厄宫' },
    ],
    lu_ji_war: [],
    soul_incoming: [
      { from: '田宅宫', hua: '化科', star: '紫微' },
    ],
    soul_chong: [
      { from: '父母宫', star: '贪狼' },
    ],
    self_out_palaces: [],
    self_in_palaces: [],
    concentration: {},
  },
}

// ─────────────────────────────────────────────────────────
// 测试集
// ─────────────────────────────────────────────────────────
let passed = 0
let failed = 0
function assert(cond, msg) {
  if (cond) {
    passed++
    console.log('  ✓ ' + msg)
  } else {
    failed++
    console.log('  ✗ ' + msg)
  }
}

function renderHTML(component) {
  return ReactDOMServer.renderToStaticMarkup(component)
}

console.log('='.repeat(70))
console.log('TEST 1: 无 insights 不渲染')
console.log('='.repeat(70))
{
  const html = renderHTML(React.createElement(ZiweiInsightsBar, { insights: null }))
  assert(html === '', '传入 null 返回空字符串（不渲染）')
  const html2 = renderHTML(React.createElement(ZiweiInsightsBar, { insights: undefined }))
  assert(html2 === '', '传入 undefined 返回空字符串')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 完整 insights 渲染 4 个卡片')
console.log('='.repeat(70))
{
  const html = renderHTML(React.createElement(ZiweiInsightsBar, { insights: fullInsights }))
  assert(html.includes('上格'), '渲染评级徽章"上格"')
  assert(html.includes('+2.14'), '渲染分数 +2.14')
  assert(html.includes('紫微'), '命宫主星显示')
  assert(html.includes('帝座之地'), '主星断语显示')
  assert(html.includes('君臣庆会格'), '吉格徽章')
  assert(html.includes('日月并明格'), '日月并明格徽章')
  assert(html.includes('双忌叠加'), '飞化警示双忌叠加')
  assert(html.includes('禄解忌'), '飞化警示禄解忌')
  assert(html.includes('飞入命宫') || html.includes('→ 命宫'), '命宫飞入提示')
  assert(html.includes('冲命宫'), '化忌冲命提示')
  assert(html.includes('官禄宫'), '三方四正表显示官禄宫')
  assert(html.includes('财帛宫'), '三方四正表显示财帛宫')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 凶格警示颜色（红色）')
console.log('='.repeat(70))
{
  const insightsWithBad = {
    ...fullInsights,
    patterns: {
      good: [],
      bad: [{
        name: '羊陀夹忌格',
        category: '凶格',
        evidence: ['禄存坐命宫', '命宫坐生年化忌'],
        meaning: '败局，多灾多难',
        break_conditions: ['三奇嘉会可解'],
      }],
      total: 1,
    },
  }
  const html = renderHTML(React.createElement(ZiweiInsightsBar, { insights: insightsWithBad }))
  assert(html.includes('羊陀夹忌格'), '凶格名显示')
  assert(html.includes('#e74c3c'), '凶格红色样式')
  assert(html.includes('⚠'), '凶格警示图标')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 评级颜色映射')
console.log('='.repeat(70))
{
  // 测试每个评级的颜色
  const tests = [
    { rating: '上格', score: 2.5, color: '#c8a04a' },
    { rating: '中上格', score: 1.0, color: '#7fb069' },
    { rating: '中格', score: -0.3, color: '#7f8c8d' },
    { rating: '中下格', score: -1.5, color: '#e67e22' },
    { rating: '下格', score: -2.5, color: '#e74c3c' },
  ]
  for (const t of tests) {
    const insights = {
      rating: {
        overall: t.rating,
        score: t.score,
        summary: 'test',
        soul_stars: [],
        sfsz_brief: [],
        star_notes: [],
      },
    }
    const html = renderHTML(React.createElement(ZiweiInsightsBar, { insights }))
    assert(html.includes(t.color), `${t.rating} → ${t.color}`)
  }
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 仅 rating 无 patterns 时不报错')
console.log('='.repeat(70))
{
  const partial = {
    rating: {
      overall: '中格',
      score: 0.0,
      summary: 'test',
      soul_stars: ['紫微'],
      sfsz_brief: [
        { palace: '命宫', branch: '午', stars: ['紫微'], rating: '中格', score: 0.0 },
      ],
      star_notes: [],
    },
  }
  let ok = true
  try {
    renderHTML(React.createElement(ZiweiInsightsBar, { insights: partial }))
  } catch (e) {
    ok = false
    console.log('  ✗ 异常:', e.message)
  }
  assert(ok, '只有 rating 时仍能正常渲染')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: 仅 patterns 无 rating 也能渲染')
console.log('='.repeat(70))
{
  const partial = {
    patterns: {
      good: [{
        name: '紫府同宫格',
        evidence: ['命宫寅'],
        meaning: '终身福厚',
        break_conditions: [],
        is_partial: false,
      }],
      bad: [],
      total: 1,
    },
  }
  let ok = true
  let html = ''
  try {
    html = renderHTML(React.createElement(ZiweiInsightsBar, { insights: partial }))
  } catch (e) {
    ok = false
  }
  assert(ok, '只有 patterns 时仍能渲染')
  assert(html.includes('紫府同宫格'), '紫府同宫格徽章显示')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) {
  process.exit(1)
}
