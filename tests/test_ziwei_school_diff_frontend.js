/**
 * 紫微派别真实差异测试 — 验证三派各自呈现的命理学内容真的不同
 *
 * 这不是装饰性差异（颜色/排序），而是真实的命理学方法论差异：
 *   三合派：主星组合 + 三方四正 + 经典格局 + 煞星会照
 *   飞星派：自化 + 质能变 + 禄忌交战 + 命宫飞入
 *   四化派：生年四化落宫 + 来因宫 + 先天禀赋分析
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

const mockPalaces = [
  {index:0, name:'兄弟宫', heavenly_stem:'戊', earthly_branch:'寅',
    major_stars:[{name:'天机',brightness:'旺',mutagen:'权'},{name:'太阴',brightness:'得',mutagen:'科'}], minor_stars:[]},
  {index:1, name:'命宫', heavenly_stem:'己', earthly_branch:'卯',
    major_stars:[{name:'紫微',brightness:'旺'},{name:'贪狼',brightness:'旺'}], minor_stars:[]},
  {index:2, name:'父母宫', heavenly_stem:'庚', earthly_branch:'辰',
    major_stars:[{name:'巨门',brightness:'陷'}], minor_stars:[{name:'擎羊'}]},
  {index:3, name:'福德宫', heavenly_stem:'辛', earthly_branch:'巳',
    major_stars:[{name:'天相'}], minor_stars:[{name:'火星'}]},
  {index:4, name:'田宅宫', heavenly_stem:'壬', earthly_branch:'午',
    major_stars:[{name:'天梁'}], minor_stars:[]},
  {index:5, name:'官禄宫', heavenly_stem:'癸', earthly_branch:'未',
    major_stars:[{name:'廉贞'},{name:'七杀'}], minor_stars:[]},
  {index:6, name:'交友宫', heavenly_stem:'甲', earthly_branch:'申', major_stars:[], minor_stars:[]},
  {index:7, name:'迁移宫', heavenly_stem:'乙', earthly_branch:'酉', major_stars:[], minor_stars:[]},
  {index:8, name:'疾厄宫', heavenly_stem:'丙', earthly_branch:'戌',
    major_stars:[{name:'天同',mutagen:'忌'}], minor_stars:[]},
  {index:9, name:'财帛宫', heavenly_stem:'丁', earthly_branch:'亥',
    major_stars:[{name:'武曲',mutagen:'权'},{name:'破军'}], minor_stars:[]},
  {index:10,name:'子女宫', heavenly_stem:'戊', earthly_branch:'子',
    major_stars:[{name:'太阳',mutagen:'禄'}], minor_stars:[]},
  {index:11,name:'夫妻宫', heavenly_stem:'己', earthly_branch:'丑',
    major_stars:[{name:'天府'}], minor_stars:[]},
]
const mockInsights = {
  patterns: { good:[{name:'紫贪同宫格'},{name:'杀破狼格'}], bad:[] },
  feihua_summary: {
    self_out_palaces:['兄弟宫','父母宫'],
    self_in_palaces:['夫妻宫'],
    quality_changes:[{palace:'兄弟宫',star:'太阴',hua:'科',fh_type:'生年+离心'}],
    lu_ji_war:[],
    soul_incoming:[{from:'疾厄宫',hua:'化禄',star:'天机'}],
  }
}
const mockBazi = { sizhu_jieqi:{year:'庚午'} }

const Panel = require('/tmp/test_build/ZiweiSchoolPanel.js').default
const renderHTML = (school) => ReactDOMServer.renderToStaticMarkup(
  React.createElement(Panel, { school, palaces: mockPalaces, insights: mockInsights, soulIdx: 1, baziOverlay: mockBazi })
)

console.log('='.repeat(70))
console.log('TEST 1: 三合派面板 — 显示三方四正格局分析')
console.log('='.repeat(70))
const sanheHTML = renderHTML('sanhe')
assert(sanheHTML.length > 1000, '三合派面板内容充实（>1000 字符）')
assert(sanheHTML.includes('三合派解读'), '面板标题：三合派解读')
assert(sanheHTML.includes('主星组合'), '显示主星组合')
assert(sanheHTML.includes('紫微') && sanheHTML.includes('贪狼'), '显示具体命宫主星名')
assert(sanheHTML.includes('三方四正'), '显示三方四正')
assert(sanheHTML.includes('紫贪同宫格') && sanheHTML.includes('杀破狼格'), '显示经典格局')
assert(sanheHTML.includes('煞星会照'), '煞星会照分析')
assert(sanheHTML.includes('无煞星会照') || sanheHTML.includes('擎羊') || sanheHTML.includes('火星'), '识别煞星会照情况')
assert(!sanheHTML.includes('生年四化'), '不显示四化派专属内容')
assert(!sanheHTML.includes('质能变'), '不显示飞星派专属内容')
assert(!sanheHTML.includes('来因宫'), '不显示来因宫')

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 飞星派面板 — 显示宫干飞化与自化')
console.log('='.repeat(70))
const feixingHTML = renderHTML('feixing')
assert(feixingHTML.length > 800, '飞星派面板内容充实')
assert(feixingHTML.includes('飞星派解读'), '面板标题：飞星派解读')
assert(feixingHTML.includes('自化'), '显示自化分析')
assert(feixingHTML.includes('离心自化'), '识别离心自化')
assert(feixingHTML.includes('向心自化'), '识别向心自化')
assert(feixingHTML.includes('能量喷散') || feixingHTML.includes('能量内收'), '解释自化能量方向')
assert(feixingHTML.includes('质能变'), '显示质能变')
assert(feixingHTML.includes('事必发生') || feixingHTML.includes('生年四化 + 自化'), '解释质能变')
assert(feixingHTML.includes('命宫飞入') || feixingHTML.includes('一生格局'), '显示命宫飞入')
assert(!feixingHTML.includes('三方四正格局'), '不显示三合派专属')
assert(!feixingHTML.includes('来因宫'), '不显示来因宫')
assert(!feixingHTML.includes('先天禀赋'), '不显示四化派专属')

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 四化派面板 — 显示生年四化落宫')
console.log('='.repeat(70))
const sihuaHTML = renderHTML('sihua')
assert(sihuaHTML.length > 800, '四化派面板内容充实')
assert(sihuaHTML.includes('四化派解读'), '面板标题：四化派解读')
assert(sihuaHTML.includes('生年四化'), '显示生年四化')
assert(sihuaHTML.includes('先天禀赋'), '解释为先天禀赋')
assert(sihuaHTML.includes('化禄') && sihuaHTML.includes('化权') && sihuaHTML.includes('化科') && sihuaHTML.includes('化忌'), '4 化全显')
assert(sihuaHTML.includes('太阳') || sihuaHTML.includes('武曲') || sihuaHTML.includes('太阴') || sihuaHTML.includes('天同'),
  '识别 4 化所在的具体星')
assert(sihuaHTML.includes('入子女宫') || sihuaHTML.includes('入财帛宫') || sihuaHTML.includes('入兄弟宫') || sihuaHTML.includes('入疾厄宫'),
  '识别 4 化落宫')
assert(sihuaHTML.includes('来因宫'), '显示来因宫概念')
assert(!sihuaHTML.includes('三方四正格局'), '不显示三合派专属')
assert(!sihuaHTML.includes('质能变'), '不显示飞星派质能变')
assert(!sihuaHTML.includes('离心自化'), '不显示飞星派自化')

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 三派内容真实差异（核心要求 — 不是装饰性差异）')
console.log('='.repeat(70))
assert(sanheHTML !== feixingHTML, '三合 ≠ 飞星')
assert(sanheHTML !== sihuaHTML, '三合 ≠ 四化')
assert(feixingHTML !== sihuaHTML, '飞星 ≠ 四化')
console.log(`  长度对比: 三合=${sanheHTML.length}, 飞星=${feixingHTML.length}, 四化=${sihuaHTML.length}`)

console.log('\n' + '='.repeat(70))
console.log('TEST 5: ZiWeiPage 集成派别专属面板')
console.log('='.repeat(70))
const pageSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiWeiPage.jsx', 'utf8')
assert(pageSrc.includes("import ZiweiSchoolPanel"), '导入派别面板')
assert(pageSrc.includes('<ZiweiSchoolPanel'), '使用派别面板')
assert(pageSrc.includes("'飞星派解读'") || pageSrc.includes('feixing: \'飞星派解读\''), '飞星派标题')
assert(pageSrc.includes("'三合派解读'") || pageSrc.includes('sanhe: \'三合派解读\''), '三合派标题')
assert(pageSrc.includes("'四化派解读'") || pageSrc.includes('sihua: \'四化派解读\''), '四化派标题')

const schoolPanelSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiSchoolPanel.jsx', 'utf8')
assert(schoolPanelSrc.includes('SanhePanel') && schoolPanelSrc.includes('FeixingPanel') && schoolPanelSrc.includes('SihuaPanel'),
  '三个独立的派别函数定义')

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
