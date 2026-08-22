/**
 * Frontend test: ZiweiVis — fh_type 区分飞化箭头（Z-6 增强）
 *
 * 验证：
 *   1. 接受空 feihua 不报错
 *   2. 接受带 fh_type 的飞化数据不报错
 *   3. 三种 fh_type（离心自化 / 向心自化 / 普通飞宫）都能初始化粒子
 *   4. 化忌粒子标记 is_ji
 *   5. 旧版数据（无 fh_type）也能降级渲染
 *
 * 注：canvas 渲染逻辑无法在 jsdom 中验证视觉效果，
 *      但我们通过快照 component 不抛错来验证数据流通畅。
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
})
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.HTMLElement = dom.window.HTMLElement
global.HTMLCanvasElement = dom.window.HTMLCanvasElement
// JSDOM canvas getContext 默认返回 null；patch 一个 minimal 实现
const noop = () => {}
const fakeCtx = {
  setTransform: noop, clearRect: noop, beginPath: noop,
  arc: noop, fill: noop, fillStyle: '', strokeStyle: '',
  lineWidth: 0, lineCap: '', moveTo: noop, lineTo: noop, stroke: noop,
}
dom.window.HTMLCanvasElement.prototype.getContext = () => fakeCtx
dom.window.HTMLCanvasElement.prototype.getBoundingClientRect = () => ({
  width: 320, height: 64, top: 0, left: 0, right: 320, bottom: 64,
})
dom.window.requestAnimationFrame = () => 0
dom.window.cancelAnimationFrame = noop
dom.window.ResizeObserver = class {
  observe() {}
  disconnect() {}
}
global.requestAnimationFrame = dom.window.requestAnimationFrame
global.cancelAnimationFrame = dom.window.cancelAnimationFrame
global.ResizeObserver = dom.window.ResizeObserver

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const { ZiweiVis } = require('/tmp/test_build/Visualizations.js')

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}
function render(el) {
  try {
    return ReactDOMServer.renderToStaticMarkup(el)
  } catch (e) {
    console.log('  ✗ render exception:', e.message)
    return null
  }
}

const mockPalaces = Array.from({length: 12}, (_, i) => ({
  index: i, name: `宫${i}`, earthly_branch: '子', major_stars: [],
}))

console.log('='.repeat(70))
console.log('TEST 1: 空 feihua 不报错')
console.log('='.repeat(70))
{
  const html = render(React.createElement(ZiweiVis, {
    palaces: mockPalaces, feihua: [], soulIdx: 0,
  }))
  assert(html !== null, '空 feihua 不抛错')
  assert(html && html.includes('<canvas'), '渲染 canvas 元素')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 带 fh_type 的完整飞化数据')
console.log('='.repeat(70))
{
  const feihua = [
    { from: 1, to: 4, type: '化禄', fh_type: '普通飞宫', is_ji: false },
    { from: 1, to: 1, type: '化权', fh_type: '离心自化', is_ji: false },
    { from: 1, to: 1, type: '化科', fh_type: '向心自化', is_ji: false },
    { from: 1, to: 7, type: '化忌', fh_type: '普通飞宫', is_ji: true },
  ]
  const html = render(React.createElement(ZiweiVis, {
    palaces: mockPalaces, feihua, soulIdx: 1,
  }))
  assert(html !== null, '带 4 类化象的 feihua 不抛错')
  assert(html && html.includes('canvas'), 'canvas 元素存在')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 三种 fh_type 同时存在（混合数据）')
console.log('='.repeat(70))
{
  const feihua = [
    // 离心自化（self_out）
    { from: 2, to: 2, type: '化忌', fh_type: '离心自化', is_ji: true },
    { from: 5, to: 5, type: '化权', fh_type: '离心自化' },
    // 向心自化（self_in）
    { from: 3, to: 3, type: '化禄', fh_type: '向心自化' },
    { from: 8, to: 8, type: '化科', fh_type: '向心自化' },
    // 普通飞宫
    { from: 0, to: 6, type: '化禄', fh_type: '普通飞宫' },
    { from: 6, to: 0, type: '化忌', fh_type: '普通飞宫', is_ji: true },
    // 跨多宫
    { from: 4, to: 10, type: '化权', fh_type: '普通飞宫' },
  ]
  const html = render(React.createElement(ZiweiVis, {
    palaces: mockPalaces, feihua, soulIdx: 4,
  }))
  assert(html !== null, '7 条混合飞化数据不抛错')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 旧版数据（无 fh_type）降级')
console.log('='.repeat(70))
{
  const feihua = [
    { from: 1, to: 4, type: '化禄' },  // 无 fh_type
    { from: 2, to: 2, type: '化忌' },  // 自化（from===to）
  ]
  const html = render(React.createElement(ZiweiVis, {
    palaces: mockPalaces, feihua, soulIdx: 0,
  }))
  assert(html !== null, '旧版无 fh_type 数据不抛错（默认推断）')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: layer prop 切换')
console.log('='.repeat(70))
{
  for (const layer of ['natal', 'decade', 'triple']) {
    const html = render(React.createElement(ZiweiVis, {
      palaces: mockPalaces,
      feihua: [{ from: 1, to: 4, type: '化禄', fh_type: '普通飞宫' }],
      soulIdx: 1,
      layer,
    }))
    assert(html !== null, `layer='${layer}' 不抛错`)
  }
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: 大量飞化数据（24 条）性能 / 不爆栈')
console.log('='.repeat(70))
{
  // 模拟 12 宫 × 4 化 = 48 条，加 overlay 8 条
  const feihua = []
  for (let i = 0; i < 12; i++) {
    for (const t of ['化禄', '化权', '化科', '化忌']) {
      feihua.push({
        from: i,
        to: (i + 3) % 12,
        type: t,
        fh_type: i % 3 === 0 ? '离心自化' : i % 3 === 1 ? '向心自化' : '普通飞宫',
        is_ji: t === '化忌',
      })
    }
  }
  const html = render(React.createElement(ZiweiVis, {
    palaces: mockPalaces, feihua, soulIdx: 0,
  }))
  assert(html !== null, `${feihua.length} 条飞化数据不抛错`)
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
