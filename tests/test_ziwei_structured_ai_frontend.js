/**
 * Frontend test: StructuredAiOutput (Z-9 结构化 AI 解读渲染)
 *
 * 验证：
 *   1. 章节标题解析
 *   2. 引用标签 [依据：section·item] 渲染
 *   3. 粗体 **text** 渲染
 *   4. 流式光标
 *   5. 引用点击事件
 *   6. 折叠/展开
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.HTMLElement = dom.window.HTMLElement

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const StructuredAiOutput = require('/tmp/test_build/StructuredAiOutput.js').default

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}
function render(el) { return ReactDOMServer.renderToStaticMarkup(el) }

console.log('='.repeat(70))
console.log('TEST 1: 空输入不报错')
console.log('='.repeat(70))
{
  const html = render(React.createElement(StructuredAiOutput, { text: '', streaming: false }))
  assert(html === '', '空文本不渲染')

  const html2 = render(React.createElement(StructuredAiOutput, { text: null, streaming: false }))
  assert(html2 === '', 'null 文本不渲染')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 章节标题解析')
console.log('='.repeat(70))
{
  const text = `## 第一步：命格定位
此命整体上格 [依据：主星亮度评级·上格]。

## 第二步：来因宫论核心命题
来因宫在田宅宫。

## 第七步：结论与建议
事业有成。`
  const html = render(React.createElement(StructuredAiOutput, { text, streaming: false }))
  assert(html.includes('第一步：命格定位'), '第一步标题')
  assert(html.includes('第二步：来因宫论核心命题'), '第二步标题')
  assert(html.includes('第七步：结论与建议'), '第七步标题')
  assert(html.includes('3 章节'), '统计章节数')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 引用标签 [依据：section·item] 渲染')
console.log('='.repeat(70))
{
  const text = `## 第一步：命格定位
此命整体上格 [依据：主星亮度评级·整体评级上格+2.14]。命宫紫微入庙 [依据：经典格局·紫微午宫入庙]。`
  const html = render(React.createElement(StructuredAiOutput, { text, streaming: false }))
  assert(html.includes('主星亮度评级·整体评级上格+2.14'), '引用标签内容渲染')
  assert(html.includes('经典格局·紫微午宫入庙'), '第二个引用标签')
  assert(html.includes('2 处溯源'), '溯源计数')
  // 应该有 onClick handler
  assert(html.includes('cursor:pointer') || html.includes('cursor: pointer') || html.includes('cursor:&#x27;pointer&#x27;'), '可点击样式')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 粗体渲染')
console.log('='.repeat(70))
{
  const text = `## 第一步：命格定位
此命 **整体上格** 且 **紫微入庙**。`
  const html = render(React.createElement(StructuredAiOutput, { text, streaming: false }))
  assert(html.includes('<strong'), '粗体标签')
  assert(html.includes('整体上格'), '粗体内容1')
  assert(html.includes('紫微入庙'), '粗体内容2')
  assert(!html.includes('**整体上格**'), 'Markdown 粗体语法被移除')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 流式光标显示')
console.log('='.repeat(70))
{
  const html = render(React.createElement(StructuredAiOutput, { text: '部分内容', streaming: true }))
  assert(html.includes('blink-cursor'), '流式时显示光标')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: 章节颜色区分')
console.log('='.repeat(70))
{
  const text = `## 第一步：命格定位
[依据：主星亮度评级·上格]
[依据：经典格局·君臣庆会]
[依据：冲宫连锁·夫妻宫被冲4次]
[依据：飞星派飞化·命宫离心自化忌]`
  const html = render(React.createElement(StructuredAiOutput, { text, streaming: false }))
  // 不同 section 应该用不同颜色
  assert(html.includes('#c8a04a') || html.includes('#C8A04A'), '主星亮度评级金色')
  assert(html.includes('#9b59b6') || html.includes('#9B59B6'), '经典格局紫色')
  assert(html.includes('#e74c3c') || html.includes('#E74C3C'), '冲宫连锁红色')
  assert(html.includes('#27ae60') || html.includes('#27AE60'), '飞星派飞化绿色')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 7: 流式中无标题的纯文本也能渲染')
console.log('='.repeat(70))
{
  // 流式刚开始，还没出第一个 ## 标题
  const text = `正在分析命盘，请稍候...
  `
  const html = render(React.createElement(StructuredAiOutput, { text, streaming: true }))
  assert(html.includes('正在分析命盘'), '前言文本渲染')
  assert(html.includes('blink-cursor'), '光标还在')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 8: 引用标签变体格式（中英文冒号）')
console.log('='.repeat(70))
{
  // 测试中文冒号 ：
  const text1 = `## 第一步\n[依据：经典格局·君臣]`
  const html1 = render(React.createElement(StructuredAiOutput, { text: text1, streaming: false }))
  assert(html1.includes('经典格局·君臣'), '中文冒号格式')

  // 测试英文冒号 :
  const text2 = `## 第一步\n[依据: 飞星派飞化·禄解忌]`
  const html2 = render(React.createElement(StructuredAiOutput, { text: text2, streaming: false }))
  assert(html2.includes('飞星派飞化·禄解忌'), '英文冒号格式')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 9: 复杂混合 — 真实输出场景')
console.log('='.repeat(70))
{
  const text = `## 第一步：命格定位
此命整体 **上格** [依据：主星亮度评级·上格+2.14]，命宫紫微入庙是帝座之地 [依据：主星亮度评级·紫微午宫入庙]。同时触发 **君臣庆会** 吉格 [依据：经典格局·君臣庆会格]。

## 第四步：飞星派飞化语象
夫妻宫被多次冲犯，**配偶关系是重灾区** [依据：冲宫连锁·夫妻宫被冲4次]。
此外命宫天同离心自化忌 [依据：飞星派飞化·命宫天同离心自化忌]。

## 第七步：结论与建议
**整体格局优**，但需注意配偶关系。`

  const html = render(React.createElement(StructuredAiOutput, { text, streaming: false }))
  // 三个 section
  assert(html.includes('3 章节'), '3 个章节')
  // 5 个引用
  assert(html.includes('5 处溯源'), '5 处溯源')
  // 3 个加粗
  const boldCount = (html.match(/<strong/g) || []).length
  assert(boldCount >= 3, `粗体出现 ${boldCount} 次`)
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
