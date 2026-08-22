/**
 * Frontend test: ZiweiInsightsBar → ChongChainsCard（Z-8）
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.HTMLElement = dom.window.HTMLElement

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const InsightsBar = require('/tmp/test_build/ZiweiInsightsBar.js').default

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}
function render(el) { return ReactDOMServer.renderToStaticMarkup(el) }

const mockChongChains = {
  total: 11,
  top_warnings: [
    "⚠ 【夫妻宫】被冲 4 次，配偶相关事项有多重风险，需重点关注",
    "⚠ 同一冲宫连锁：本命田宅宫/大限命宫/流年命宫 — 影响主题跨【家庭/命宫】，连锁效应明显",
  ],
  key_palaces_hit: { "夫妻宫": 4, "福德宫": 2 },
  events: [
    {
      from_palace: "疾厄宫",
      hua_type: "化忌",
      star: "巨门",
      chong_palace: "命宫",
      layer: "natal",
      multilayer: {
        natal:  { palace_name: "命宫",      theme: "本人" },
        decade: { palace_name: "大限子女宫", theme: "子女" },
        annual: { palace_name: "流年夫妻宫", theme: "配偶" },
      },
      interpretation: "本命疾厄宫 化忌巨门 → 迁移宫 冲【命宫】 — 本人受损",
    },
    {
      from_palace: "迁移宫",
      hua_type: "化忌",
      star: "廉贞",
      chong_palace: "田宅宫",
      layer: "natal",
      multilayer: {
        natal:  { palace_name: "田宅宫",   theme: "家庭" },
        decade: { palace_name: "大限命宫", theme: "本人" },
      },
    },
    {
      from_palace: "大限干起",
      hua_type: "化忌",
      star: "贪狼",
      chong_palace: "兄弟宫",
      layer: "decade",
      multilayer: {
        natal:  { palace_name: "兄弟宫", theme: "兄弟" },
      },
    },
    {
      from_palace: "流年干起",
      hua_type: "化忌",
      star: "廉贞",
      chong_palace: "夫妻宫",
      layer: "annual",
      multilayer: {
        natal:  { palace_name: "夫妻宫", theme: "配偶" },
      },
    },
  ],
}

console.log('='.repeat(70))
console.log('TEST 1: chongChains 为 null 不渲染该卡')
console.log('='.repeat(70))
{
  const html = render(React.createElement(InsightsBar, {
    insights: { rating: null, patterns: null, feihua_summary: null },
    chongChains: null,
  }))
  assert(!html.includes('冲宫连锁'), 'null chains 不显示卡片')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 有 chongChains 时渲染完整内容')
console.log('='.repeat(70))
{
  const html = render(React.createElement(InsightsBar, {
    insights: null,
    chongChains: mockChongChains,
  }))
  assert(html.includes('冲宫连锁警示'), '卡片标题')
  assert(html.includes('11 个化忌冲事件'), '事件总数')
  assert(html.includes('夫妻宫'), 'top_warning 内容')
  assert(html.includes('被冲 4 次'), '宫位被冲次数')
  assert(html.includes('本命层'), '本命层 section')
  assert(html.includes('大限层'), '大限层 section')
  assert(html.includes('流年层'), '流年层 section')
  assert(html.includes('疾厄宫'), '具体冲宫事件')
  assert(html.includes('化忌巨门'), '事件细节')
  assert(html.includes('冲【命宫】'), '冲哪宫')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 本命层事件显示多层语义链')
console.log('='.repeat(70))
{
  const html = render(React.createElement(InsightsBar, {
    insights: null,
    chongChains: mockChongChains,
  }))
  // 本命事件的 multilayer 应有 大限/流年 主题
  assert(html.includes('大限=子女') || html.includes('大限=本人'), '本命事件多层 → 大限主题')
  assert(html.includes('流年=配偶'), '本命事件多层 → 流年主题')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: chains.total=0 不渲染')
console.log('='.repeat(70))
{
  const empty = { total: 0, top_warnings: [], events: [], key_palaces_hit: {} }
  const html = render(React.createElement(InsightsBar, {
    insights: null,
    chongChains: empty,
  }))
  assert(!html.includes('冲宫连锁警示'), 'total=0 不渲染')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 自动回退到 insights.chong_chains')
console.log('='.repeat(70))
{
  // 不传 chongChains，但 insights.chong_chains 有
  const html = render(React.createElement(InsightsBar, {
    insights: { chong_chains: mockChongChains, rating: null, patterns: null, feihua_summary: null },
    chongChains: null,
  }))
  assert(html.includes('冲宫连锁警示'), '自动从 insights.chong_chains 取数据')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
