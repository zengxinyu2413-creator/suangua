/**
 * 紫微宫位高密度测试 — 验证 PalaceCell 显示文墨天机风格的所有元素
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

// 检查 ZiWeiPage.jsx 源码中是否已包含文墨天机风格的字段渲染
const src = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiWeiPage.jsx', 'utf8')

console.log('='.repeat(70))
console.log('TEST 1: 单星 StarChip 组件')
console.log('='.repeat(70))
assert(src.includes('function StarChip'), 'StarChip 组件存在')
assert(src.includes('MUTAGEN_BADGE'), '化禄/权/科/忌徽章定义')
assert(src.includes("'禄': { bg:"), '化禄徽章配置')
assert(src.includes("'权': { bg:"), '化权徽章配置')
assert(src.includes("'科': { bg:"), '化科徽章配置')
assert(src.includes("'忌': { bg:"), '化忌徽章配置')

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 星耀颜色分类')
console.log('='.repeat(70))
assert(src.includes('STAR_COLOR'), 'STAR_COLOR 定义')
assert(src.includes('左辅') && src.includes('右弼') && src.includes('文昌'), '六吉星识别')
assert(src.includes('火星') && src.includes('擎羊') && src.includes('陀罗'), '六煞星识别')
assert(src.includes('红鸾') && src.includes('天喜'), '桃花星识别')

console.log('\n' + '='.repeat(70))
console.log('TEST 3: PalaceCell 高密度元素')
console.log('='.repeat(70))
assert(src.includes('palace.adj_stars'), '杂曜字段渲染')
assert(src.includes('palace.major_stars'), '主星渲染')
assert(src.includes('palace.minor_stars'), '辅星渲染')
assert(src.includes('palace.boshi12'), '博士十二神')
assert(src.includes('palace.changsheng12'), '长生十二神')
assert(src.includes('palace.ages'), '流年小限数字')
assert(src.includes('palace.decadal_range'), '大限范围')
assert(src.includes("palace.name.replace('宫','')"), '宫名简化显示')
assert(src.match(/minHeight:\s*['"]160px/), '宫位高度 >= 160px（信息密度）')

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 中宫信息板（文墨风格）— 现已拆到 ZiweiCenterPanel.jsx')
console.log('='.repeat(70))
const centerSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiCenterPanel.jsx', 'utf8')
assert(centerSrc.includes('紫微斗数'), '中宫标题')
assert(centerSrc.includes('pillars') || centerSrc.includes('p.gz'), '中宫显示四柱')
assert(centerSrc.includes('命主') && centerSrc.includes('身主'), '命主身主显示')
assert(centerSrc.includes("meta?.solar_date") && centerSrc.includes("meta?.lunar_date"), '公历+农历都显示')
assert(centerSrc.includes('meta?.birth_hour_name') && centerSrc.includes('meta?.birth_hour_range'), '时辰名+范围')
assert(centerSrc.includes('meta?.zodiac') && centerSrc.includes('meta?.sign'), '生肖+星座')

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 命/身宫标记（文墨风格 + 内联避免重叠）')
console.log('='.repeat(70))
assert(src.includes("'命' : '身'"), '命/身 badge 单字（避免重叠主星）')
assert(src.includes('rgba(74,122,90,0.15)'), '命宫淡绿背景')
assert(src.includes('rgba(52,152,219,0.15)'), '身宫淡蓝背景')
// 确保 badge 在主星行内联，不再 absolute（防止字叠加）
const badgeBlock = src.match(/badge 内联在最前[\s\S]{0,500}/)?.[0] || ''
assert(badgeBlock.length > 0, 'badge 已改为内联（注释说明）')
assert(!badgeBlock.includes("position: 'absolute'"), 'badge 不再 absolute 定位')

console.log('\n' + '='.repeat(70))
console.log('TEST 6: InsightsBar 后移到 12 宫盘后')
console.log('='.repeat(70))
// InsightsBar 应该出现在 PalaceDetailPanel 之后
const insightsBarIdx = src.indexOf('<ZiweiInsightsBar')
const palaceGridIdx = src.indexOf('12-palace grid')
const palaceDetailIdx = src.indexOf('PalaceDetailPanel')
assert(insightsBarIdx > palaceGridIdx, 'InsightsBar 在 12 宫盘之后')
assert(insightsBarIdx > palaceDetailIdx, 'InsightsBar 在 PalaceDetailPanel 之后')

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
