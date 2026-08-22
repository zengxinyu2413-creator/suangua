/**
 * test_compendium_panel.js
 * 验证 ClassicalCompendiumPanel 静态渲染（无数据状态）
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.localStorage = dom.window.localStorage
global.fetch = () => Promise.reject(new Error('no network in test'))

const React = require('react')
const { renderToStaticMarkup } = require('react-dom/server')
const Panel = require('/tmp/test_build/ClassicalCompendiumPanel.js').default

let pass = 0, fail = 0
function assert(cond, msg) {
  if (cond) { console.log('  ✓ ' + msg); pass++ }
  else { console.log('  ✗ ' + msg); fail++ }
}

console.log('=' .repeat(70))
console.log('TEST: ClassicalCompendiumPanel 静态渲染')
console.log('='.repeat(70))
{
  const html = renderToStaticMarkup(React.createElement(Panel, {}))
  assert(html.includes('典籍精读'), '标题')
  assert(html.includes('十大命理学典籍'), '介绍文字')
  assert(html.includes('历史背景') || html.includes('章节') || html.length > 500, '基本结构渲染')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${pass} 通过 / ${fail} 失败`)
console.log('='.repeat(70))
if (fail > 0) process.exit(1)
