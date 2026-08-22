/**
 * 紫微专业布局测试 — 全面验证 4 个新组件
 *   1. ZiweiCenterPanel — 中宫信息板（八字大运/十神/纳音/真太阳时）
 *   2. ZiweiTimePanel — 底栏时间盘（大运/流年/流月/流日/流时）
 *   3. ZiweiDirections — 8 方位边缘装饰
 *   4. PalaceCell 高密度宫位
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const fs = require('fs')
const path = require('path')

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}

// ──────────────────────────────────────────────────────
// TEST 1: 文件存在 + 语法
// ──────────────────────────────────────────────────────
console.log('='.repeat(70))
console.log('TEST 1: 新组件文件存在')
console.log('='.repeat(70))
const newComponents = [
  'ZiweiCenterPanel.jsx',
  'ZiweiTimePanel.jsx',
  'ZiweiDirections.jsx',
]
for (const f of newComponents) {
  const fp = path.join('/home/claude/bagua_project_build/frontend/src/pages/ZiWei', f)
  assert(fs.existsSync(fp), `文件存在: ${f}`)
}

// ──────────────────────────────────────────────────────
// TEST 2: ZiweiCenterPanel 关键字段
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 2: ZiweiCenterPanel — 中宫信息板字段')
console.log('='.repeat(70))
const centerSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiCenterPanel.jsx', 'utf8')

assert(centerSrc.includes('SHISHEN_COLOR'), '十神颜色定义')
assert(centerSrc.includes("'比肩'") && centerSrc.includes("'劫财'"), '十神 — 比劫')
assert(centerSrc.includes("'食神'") && centerSrc.includes("'伤官'"), '十神 — 食伤')
assert(centerSrc.includes("'七杀'") && centerSrc.includes("'正官'"), '十神 — 官杀')
assert(centerSrc.includes("'偏印'") && centerSrc.includes("'正印'"), '十神 — 印星')
assert(centerSrc.includes("showSect === 'jieqi'") || centerSrc.includes("'jieqi'"), '两派四柱切换 logic')
assert(centerSrc.includes('shishen_zhi'), '地支藏干十神')
assert(centerSrc.includes('canggan'), '藏干')
assert(centerSrc.includes('nayin'), '纳音')
assert(centerSrc.includes('qiyun'), '起运信息')
assert(centerSrc.includes('real_time'), '真太阳时')
assert(centerSrc.includes('钟表') && centerSrc.includes('真太阳时'), '真太阳时显示')
assert(centerSrc.includes('节气') && centerSrc.includes('非节气'), '派别切换 UI')
assert(centerSrc.includes('日↓') && centerSrc.includes('日↑'), '日切换按钮')
assert(centerSrc.includes('时↓') && centerSrc.includes('时↑'), '时切换按钮')

// ──────────────────────────────────────────────────────
// TEST 3: ZiweiTimePanel 5 行表格
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 3: ZiweiTimePanel — 5 行时间盘')
console.log('='.repeat(70))
const timeSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiTimePanel.jsx', 'utf8')

assert(timeSrc.includes('大限'), '大限行')
assert(timeSrc.includes('流年'), '流年行')
assert(timeSrc.includes('流月'), '流月行')
assert(timeSrc.includes('流日'), '流日行')
assert(timeSrc.includes('流时'), '流时行')
assert(timeSrc.includes("'子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'"), '12 时辰名')
assert(timeSrc.includes('正') && timeSrc.includes('腊'), '12 月名（含腊月）')
assert(timeSrc.includes('初一') || timeSrc.includes("初' + "), '农历日名')
assert(timeSrc.includes('onAgeChange'), '大限切换回调')
assert(timeSrc.includes('onYearChange'), '流年切换回调')
assert(timeSrc.includes('onMonthChange'), '流月切换回调')

// ──────────────────────────────────────────────────────
// TEST 4: ZiweiDirections 8 方位
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 4: ZiweiDirections — 8 方位边缘')
console.log('='.repeat(70))
const dirSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiweiDirections.jsx', 'utf8')

assert(dirSrc.includes('正南方'), '正南方')
assert(dirSrc.includes('正北方'), '正北方')
assert(dirSrc.includes('正东方'), '正东方')
assert(dirSrc.includes('正西方'), '正西方')
assert(dirSrc.includes('南偏西'), '南偏西')
assert(dirSrc.includes('北偏东'), '北偏东')
assert(dirSrc.includes('东偏北'), '东偏北')
assert(dirSrc.includes('西偏南'), '西偏南')

// ──────────────────────────────────────────────────────
// TEST 5: ZiWeiPage 集成
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 5: ZiWeiPage 集成 3 个新组件')
console.log('='.repeat(70))
const pageSrc = fs.readFileSync('/home/claude/bagua_project_build/frontend/src/pages/ZiWei/ZiWeiPage.jsx', 'utf8')

assert(pageSrc.includes("import ZiweiCenterPanel"), '导入 ZiweiCenterPanel')
assert(pageSrc.includes("import ZiweiTimePanel"), '导入 ZiweiTimePanel')
assert(pageSrc.includes("import ZiweiDirections"), '导入 ZiweiDirections')
assert(pageSrc.includes('<ZiweiCenterPanel'), '使用 ZiweiCenterPanel')
assert(pageSrc.includes('<ZiweiTimePanel'), '使用 ZiweiTimePanel')
assert(pageSrc.includes('<ZiweiDirections>'), '使用 ZiweiDirections 包裹')
assert(pageSrc.includes('baziOverlay={result.bazi_overlay}'), '传 bazi_overlay 给中宫')
assert(pageSrc.includes('timePanel={result.time_panel}'), '传 time_panel 给时间盘')

// ──────────────────────────────────────────────────────
// TEST 6: 渲染中宫面板
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 6: ZiweiCenterPanel 实际渲染')
console.log('='.repeat(70))
{
  // 用预编译路径（由 run_polish_frontend_tests.sh 转译）
  const ZiweiCenterPanel = require('/tmp/test_build/ZiweiCenterPanel.js').default
  
  const html = ReactDOMServer.renderToStaticMarkup(React.createElement(ZiweiCenterPanel, {
    meta: {
      solar_date: '1990-07-14',
      lunar_date: '庚午年五月廿二',
      birth_hour_name: '辰时',
      birth_hour_range: '07:00~09:00',
      five_elements: '土五局',
      gender: '男', zodiac: '马', sign: '双子座',
      soul_star: '禄存', body_star: '火星',
    },
    baziOverlay: {
      sizhu_jieqi:  { year:'庚午', month:'壬午', day:'庚戌', time:'己卯' },
      sizhu_nonjieqi: { year:'庚午', month:'癸未', day:'庚辰', time:'庚辰' },
      shishen:      { year:'比肩', month:'食神', day:'日主', time:'正印' },
      shishen_zhi:  { year:['正官','正印'], month:['正印','正官','正财'], day:['偏印','正财','伤官'], time:['偏印','正财','伤官'] },
      canggan:      { year:['丁','己'], month:['丁','己'], day:['戊','辛','丁'], time:['乙'] },
      nayin:        { year:'路旁土', month:'杨柳木', day:'钗钏金', time:'城头土' },
      qiyun:        { year:7, month:9, day:25, summary:'7年9月25天起运' },
      dayun:        [
        { start_age:1, end_age:10, ganzhi:'童限', start_year:1990 },
        { start_age:9, end_age:18, ganzhi:'癸未', start_year:1998 },
      ],
      real_time:    { longitude:104.06, clock_time:'07:00', real_solar_time:'05:56', offset_minutes:-63.8 },
    },
    layer: 'natal',
  }))
  
  assert(html.includes('紫微斗数'), '标题')
  assert(html.includes('土五局'), '五行局')
  assert(html.includes('1990-07-14'), '公历')
  assert(html.includes('庚午年五月廿二'), '农历')
  assert(html.includes('辰时'), '时辰')
  assert(html.includes('马'), '生肖')
  assert(html.includes('双子座'), '星座')
  assert(html.includes('禄存'), '命主')
  assert(html.includes('火星'), '身主')
  assert(html.includes('庚') && html.includes('午') && html.includes('壬'), '四柱字')
  assert(html.includes('比肩') && html.includes('食神'), '十神')
  assert(html.includes('丁') && html.includes('己'), '藏干')
  assert(html.includes('路旁土') || html.includes('杨柳木'), '纳音')
  assert(html.includes('7年9月25天起运'), '起运')
  assert(html.includes('钟表'), '真太阳时区')
  assert(html.includes('05:56'), '真太阳时值')
  assert(html.includes('节气'), '派别切换')
  // 日时切换需要传 onShiftDay/onShiftHour prop 才显示
}

// ──────────────────────────────────────────────────────
// TEST 7: 渲染时间盘
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 7: ZiweiTimePanel 实际渲染')
console.log('='.repeat(70))
{
  const ZiweiTimePanel = require('/tmp/test_build/ZiweiTimePanel.js').default
  
  const html = ReactDOMServer.renderToStaticMarkup(React.createElement(ZiweiTimePanel, {
    bazi: {
      dayun: [
        { start_age:1, end_age:10, ganzhi:'童限', start_year:1990 },
        { start_age:9, end_age:18, ganzhi:'癸未', start_year:1998 },
        { start_age:19, end_age:28, ganzhi:'甲申', start_year:2008 },
      ],
      qiyun: { summary:'7年9月25天起运' },
    },
    timePanel: {
      months: [
        { lunar_month:1, month_name:'正月', ganzhi:'庚寅' },
        { lunar_month:2, month_name:'二月', ganzhi:'辛卯' },
      ],
    },
    selectedAge: 30,
  }))
  
  assert(html.includes('时间盘'), '标题')
  assert(html.includes('大限'), '大限行')
  assert(html.includes('流年'), '流年行')
  assert(html.includes('流月'), '流月行')
  assert(html.includes('流日'), '流日行')
  assert(html.includes('流时'), '流时行')
  assert(html.includes('童限'), '童限显示')
  assert(html.includes('癸未'), '大运干支')
  assert(html.includes('正月'), '流月正月')
  assert(html.includes('初一'), '流日初一')
  assert(html.includes('子') && html.includes('亥'), '流时子+亥')
  assert(html.includes('7年9月25天起运'), '起运标题')
}

// ──────────────────────────────────────────────────────
// TEST 8: 渲染 8 方位
// ──────────────────────────────────────────────────────
console.log('\n' + '='.repeat(70))
console.log('TEST 8: ZiweiDirections 实际渲染')
console.log('='.repeat(70))
{
  const ZiweiDirections = require('/tmp/test_build/ZiweiDirections.js').default
  const html = ReactDOMServer.renderToStaticMarkup(
    React.createElement(ZiweiDirections, {},
      React.createElement('div', { className:'inner' }, 'children-content')
    )
  )
  
  for (const dir of ['正南方','正北方','正东方','正西方','南偏西','北偏东','东偏北','西偏南']) {
    assert(html.includes(dir), `8 方位 — ${dir}`)
  }
  assert(html.includes('children-content'), '子内容渲染')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
