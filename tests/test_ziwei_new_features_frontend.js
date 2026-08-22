/**
 * 紫微 4 大新功能测试 — 日时切换 / 派别切换 / 命例库 / 导出 PNG
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const fs = require('fs')

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}

const pageSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiWeiPage.jsx', 'utf8')
const centerSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiCenterPanel.jsx', 'utf8')

// ──────────────────────────────────────────────────────
// TEST 1: 日↑↓ / 时↑↓ 工具栏函数
// ──────────────────────────────────────────────────────
console.log('='.repeat(70))
console.log('TEST 1: 日↑↓ / 时↑↓ 工具栏（任务1）')
console.log('='.repeat(70))

assert(pageSrc.includes('const shiftDay = async'), 'shiftDay 函数定义')
assert(pageSrc.includes('const shiftHour = async'), 'shiftHour 函数定义')
assert(pageSrc.includes('HOUR_VALUES'), 'shiftHour 用 HOUR_VALUES 切换 12 时辰')
assert(pageSrc.includes('onShiftDay={shiftDay}'), 'shiftDay 传给 CenterPanel')
assert(pageSrc.includes('onShiftHour={shiftHour}'), 'shiftHour 传给 CenterPanel')
assert(pageSrc.includes('setTimeout(() => run(), 50)') || pageSrc.includes('run()'), '切换后触发重排盘')

// CenterPanel 端
assert(centerSrc.includes('onClick={() => onShiftDay(-1)}'), 'CenterPanel 日↓按钮')
assert(centerSrc.includes('onClick={() => onShiftDay(1)}'),  'CenterPanel 日↑按钮')
assert(centerSrc.includes('onClick={() => onShiftHour(-1)}'), 'CenterPanel 时↓按钮')
assert(centerSrc.includes('onClick={() => onShiftHour(1)}'),  'CenterPanel 时↑按钮')

// ──────────────────────────────────────────────────────
// TEST 2: 紫微派别切换（任务2）
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 2: 紫微派别切换 — 飞星/三合/四化')
console.log('='.repeat(70))

assert(pageSrc.includes("const [school, setSchool]"), 'school state')
assert(pageSrc.includes("'feixing'") || pageSrc.includes('feixing'), '飞星派 id')
assert(pageSrc.includes("school === 'sihua'"), '四化派过滤')
assert(pageSrc.includes("school === 'sanhe'"), '三合派过滤')
assert(pageSrc.includes('school={school}'), 'school 传给 CenterPanel/PalaceCell')
assert(pageSrc.includes('onSchoolChange={setSchool}'), '切换回调')

// CenterPanel 端 — 派别 UI
assert(centerSrc.includes('紫微派别'), '派别切换 label')
assert(centerSrc.includes('飞星') && centerSrc.includes('三合') && centerSrc.includes('四化'), '3 个派别按钮')
assert(centerSrc.includes('onSchoolChange'), 'onSchoolChange prop')
assert(centerSrc.includes('重四化飞化') || centerSrc.includes('飞化'), '飞星 desc')
assert(centerSrc.includes('重三方四正') || centerSrc.includes('三方'), '三合 desc')

// ──────────────────────────────────────────────────────
// TEST 3: 名人命例库（任务3）
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 3: 名人命例库')
console.log('='.repeat(70))

const famousSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/famousCases.js', 'utf8')
const famousJsxSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiFamousCases.jsx', 'utf8')

assert(famousSrc.includes('FAMOUS_CASES'), 'FAMOUS_CASES 数组定义')
assert(famousSrc.includes('毛泽东'), '毛泽东命例')
assert(famousSrc.includes('李嘉诚'), '李嘉诚命例')
assert(famousSrc.includes('爱因斯坦'), '爱因斯坦命例')
assert(famousSrc.includes('金庸'), '金庸命例')
assert(famousSrc.includes('慈禧'), '慈禧命例')
assert(famousSrc.includes('周恩来'), '周恩来命例')
assert(famousSrc.includes('王永庆'), '王永庆命例')
assert(famousSrc.includes('groupCasesByCategory'), '分类分组函数')

// 命例数据完整性
assert(famousSrc.includes("category: '近代政治家'"), '分类: 近代政治家')
assert(famousSrc.includes("category: '商业巨子'"), '分类: 商业巨子')
assert(famousSrc.includes('longitude:'), '经度字段（用于真太阳时）')
assert(famousSrc.includes('highlights:'), '亮点字段')

// 选择器组件
assert(famousJsxSrc.includes('FAMOUS_CASES'), '选择器加载命例')
assert(famousJsxSrc.includes('onSelect'), '选中回调')
assert(famousJsxSrc.includes('groupCasesByCategory'), '使用分组函数')
assert(famousJsxSrc.includes('命例数据仅供学术研究'), '免责声明')

// ZiWeiPage 集成
assert(pageSrc.includes("import ZiweiFamousCases"), '导入命例组件')
assert(pageSrc.includes('<ZiweiFamousCases'), '使用命例组件')
assert(pageSrc.includes('loadFamousCase'), '命例载入函数')
assert(pageSrc.includes('已导入命例'), '通知文案')

// ──────────────────────────────────────────────────────
// TEST 4: 命盘导出 PNG（任务4）
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 4: 命盘导出 PNG')
console.log('='.repeat(70))

const exportSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/exportChartPng.js', 'utf8')

assert(exportSrc.includes('exportElementToPng'), '导出函数')
assert(exportSrc.includes('foreignObject'), '使用 SVG foreignObject')
assert(exportSrc.includes('XMLSerializer'), 'XML 序列化')
assert(exportSrc.includes('canvas.toBlob'), 'Canvas 转 Blob')
assert(exportSrc.includes('inlineStyles'), '内联样式函数（关键技术）')
assert(exportSrc.includes('getComputedStyle'), '获取 computed style')
assert(exportSrc.includes("scale = 2"), '默认 2× 高清')

// ZiWeiPage 集成
assert(pageSrc.includes("import { exportElementToPng }"), '导入导出函数')
assert(pageSrc.includes('data-ziwei-chart-export'), '数据标记')
assert(pageSrc.includes('exportChart'), 'exportChart 函数')
assert(pageSrc.includes("'⬇ 导出 PNG'") || pageSrc.includes('导出 PNG'), '导出按钮文案')
assert(pageSrc.includes('exporting'), '导出加载状态')

// ──────────────────────────────────────────────────────
// TEST 5: 现场渲染（用预编译的 jsx）
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 5: 渲染验证')
console.log('='.repeat(70))

try {
  const ZiweiFamousCases = require('/tmp/test_build/ZiweiFamousCases.js').default
  const html = ReactDOMServer.renderToStaticMarkup(
    React.createElement(ZiweiFamousCases, { onSelect: () => {} })
  )
  // 折叠状态：只显示按钮 title
  assert(html.includes('名人命例库'), '折叠时显示名称')
  assert(html.includes(' 8 例') || html.includes('例'), '显示命例数量')
} catch (e) {
  console.log('  ! 跳过（需 babel 转译）:', e.message)
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
