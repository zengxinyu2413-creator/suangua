/**
 * 紫微布局修复测试 — 验证三个用户反馈的问题：
 *   1. 导出 PNG 按钮不再 absolute 定位（导致字叠加）
 *   2. ZiweiDirections padding 加大避免方位标注盖到宫位
 *   3. 冲宫连锁警示可展开/收起
 */
const fs = require('fs')
let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}

const pageSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiWeiPage.jsx', 'utf8')
const insightsSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiInsightsBar.jsx', 'utf8')
const dirsSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiDirections.jsx', 'utf8')

console.log('='.repeat(70))
console.log('TEST 1: 导出 PNG 按钮不再绝对定位（避免字叠加）')
console.log('='.repeat(70))

// 导出按钮所在区域不再有 position:absolute
const exportBtnArea = pageSrc.match(/12-palace grid 工具栏[\s\S]{0,800}exportChart[\s\S]{0,400}/)?.[0] || ''
assert(!exportBtnArea.includes("position: 'absolute'"), '导出按钮区域不再绝对定位')
assert(pageSrc.includes('12-palace grid 工具栏') || pageSrc.includes('独立行'), '工具栏改为独立行（注释说明）')
assert(pageSrc.includes("justifyContent: 'space-between'"), '工具栏左右两栏布局')

console.log('\n' + '='.repeat(70))
console.log('TEST 2: ZiweiDirections padding 加大')
console.log('='.repeat(70))

assert(dirsSrc.includes("padding: '26px 30px'") || dirsSrc.match(/padding:\s*['"]2[5-9]px/), '边距 ≥ 25px')
assert(dirsSrc.includes('pointerEvents'), '方位标注 pointer-events: none（避免阻挡点击）')

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 冲宫连锁警示 — 可展开/收起')
console.log('='.repeat(70))

assert(insightsSrc.includes('expandedLayers'), '展开状态 state')
assert(insightsSrc.includes('toggleLayer'), '切换函数')
assert(insightsSrc.includes('展开全部'), '展开按钮文案')
assert(insightsSrc.includes('收起'), '收起按钮')
assert(!insightsSrc.match(/top_warnings\?.length > 0 \&\& \(\s*<div.*\{chains\.top_warnings\.slice\(0, 5\)/),
  'top_warnings 不再 slice(0,5)（全显）')

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 飞星派关键语象 — 质能变可展开')
console.log('='.repeat(70))

assert(insightsSrc.includes('showAllQuality'), '质能变展开 state')
assert(insightsSrc.includes('qcDisplay'), '质能变显示列表')
assert(insightsSrc.includes('展开质能变') || insightsSrc.includes('收起质能变'), '展开/收起按钮')

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 三方四正断语 — 可展开')
console.log('='.repeat(70))

assert(insightsSrc.includes('showAllNotes'), '断语展开 state')
assert(insightsSrc.includes('displayNotes'), '断语显示列表')
assert(insightsSrc.includes('收起断语'), '收起断语按钮')

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
