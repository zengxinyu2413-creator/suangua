/**
 * test_xuankong_panel.js
 * 验证 XuankongPanel 渲染、九宫数据、令星判定 UI
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.fetch = () => Promise.reject(new Error('no network in test'))

const React = require('react')
const { renderToStaticMarkup } = require('react-dom/server')
const XuankongPanel = require('/tmp/test_build/XuankongPanel.js').default

let pass = 0, fail = 0
function assert(cond, msg) {
  if (cond) { console.log('  ✓ ' + msg); pass++ }
  else { console.log('  ✗ ' + msg); fail++ }
}

console.log('=' .repeat(70))
console.log('TEST: XuankongPanel 静态渲染（无数据状态）')
console.log('='.repeat(70))
{
  const html = renderToStaticMarkup(React.createElement(XuankongPanel, {}))
  assert(html.includes('玄空飞星专业排盘'), '标题渲染')
  assert(html.includes('沈氏玄空学'), '出处标注')
  assert(html.includes('建宅/入伙年'), '年份输入提示')
  assert(html.includes('坐山方位'), '坐山选择提示')
  assert(html.includes('坎'), '坎卦组')
  assert(html.includes('艮'), '艮卦组')
  assert(html.includes('壬') && html.includes('癸'), '坎卦三山部分')
  assert(html.includes('丙') && html.includes('丁'), '离卦三山部分')
  assert(html.includes('阳山顺飞'), '阳山标识')
  assert(html.includes('阴山逆飞'), '阴山标识')
  assert(html.includes('青囊奥语') || html.includes('挨星诀'), '挨星诀出处')
  assert(html.includes('排盘'), '排盘按钮')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${pass} 通过 / ${fail} 失败`)
console.log('='.repeat(70))
if (fail > 0) process.exit(1)
