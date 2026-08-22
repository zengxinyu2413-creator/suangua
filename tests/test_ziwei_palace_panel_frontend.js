/**
 * Frontend test: ZiweiPalaceDetailPanel 完整宫位详情面板
 *
 * 前置：先用 babel 把 jsx 转译到 /tmp/test_build/
 */
const { JSDOM } = require('jsdom')
const dom = new JSDOM('<!DOCTYPE html>', { url: 'http://localhost' })
global.window = dom.window
global.document = dom.window.document
global.navigator = dom.window.navigator
global.HTMLElement = dom.window.HTMLElement

const React = require('react')
const ReactDOMServer = require('react-dom/server')
const PalaceDetailPanel = require('/tmp/test_build/ZiweiPalaceDetailPanel.js').default

let passed = 0, failed = 0
function assert(cond, msg) {
  if (cond) { passed++; console.log('  ✓ ' + msg) }
  else      { failed++; console.log('  ✗ ' + msg) }
}
function render(el) { return ReactDOMServer.renderToStaticMarkup(el) }

// 模拟一个完整宫位数据（命宫天同陷+化忌、火星煞、左辅吉）
const mockPalace = {
  index: 2,
  name: '命宫',
  heavenly_stem: '庚',
  earthly_branch: '辰',
  is_soul: true,
  is_body: false,
  major_stars: [
    { name: '天同', brightness: '陷', mutagen: '忌' },
  ],
  minor_stars: [
    { name: '火星', brightness: '', mutagen: '' },
    { name: '左辅', brightness: '', mutagen: '' },
    { name: '禄存', brightness: '', mutagen: '' },
  ],
  adj_stars: [
    { name: '凤阁', brightness: '', mutagen: '' },
    { name: '寡宿', brightness: '', mutagen: '' },
  ],
  decadal_range: [5, 14],
  changsheng12: '养',
  boshi12: '病符',
}

// 模拟全 12 宫（极简）
const mockAllPalaces = []
for (let i = 0; i < 12; i++) {
  const branches = ['寅','卯','辰','巳','午','未','申','酉','戌','亥','子','丑']
  const names = ['兄弟宫','夫妻宫','命宫','父母宫','福德宫','田宅宫',
                 '官禄宫','交友宫','迁移宫','疾厄宫','财帛宫','子女宫']
  mockAllPalaces.push({
    index: i,
    name: i === 2 ? '命宫' : names[i],
    earthly_branch: branches[i],
    heavenly_stem: '甲',
    major_stars: i === 8 ? [{ name: '太阴', brightness: '旺' }]
                : i === 6 ? [{ name: '太阳', brightness: '庙' }]
                : i === 10 ? [{ name: '武曲', brightness: '庙' }, { name: '天府', brightness: '庙' }]
                : [],
  })
}
mockAllPalaces[2] = mockPalace

// 模拟 feihua_by_palace（命宫的飞化）
const mockFeihuaByPalace = {
  '2': {
    palace_idx: 2,
    palace_name: '命宫',
    stem: '庚',
    branch: '辰',
    opp_palace_name: '迁移宫',
    transformations: [
      {
        hua_type: '化禄', target_star: '太阳',
        target_palace_name: '官禄宫', target_palace_idx: 6,
        fh_type: '普通飞宫', is_inner: true,
        chong_palace: '',
        is_he_won_ji: false, is_double_ji: false,
        is_lu_ji_war: false, is_quality_change: false,
        interpretation: '太阳化禄入【官禄宫】（我宫）：在此领域有获益',
      },
      {
        hua_type: '化忌', target_star: '天同',
        target_palace_name: '命宫', target_palace_idx: 2,
        fh_type: '离心自化', is_inner: true,
        chong_palace: '',
        is_he_won_ji: false, is_double_ji: false,
        is_lu_ji_war: false, is_quality_change: true,
        interpretation: '天同离心自化忌：本宫执念深重；⚠ 质能变',
      },
      {
        hua_type: '化权', target_star: '武曲',
        target_palace_name: '财帛宫', target_palace_idx: 10,
        fh_type: '普通飞宫', is_inner: true,
        chong_palace: '',
        is_he_won_ji: false, is_double_ji: false,
        is_lu_ji_war: false, is_quality_change: false,
        interpretation: '武曲化权入【财帛宫】（我宫）：在此领域有主导力',
      },
      {
        hua_type: '化科', target_star: '太阴',
        target_palace_name: '迁移宫', target_palace_idx: 8,
        fh_type: '向心自化', is_inner: false,
        chong_palace: '',
        is_he_won_ji: false, is_double_ji: false,
        is_lu_ji_war: false, is_quality_change: false,
        interpretation: '太阴向心自化科：能量射向对宫迁移宫',
      },
    ],
    self_out_count: 1,
    self_in_count: 1,
    fly_out_count: 2,
    incoming_count: 2,
    incoming_list: [
      { from_palace: '迁移宫', hua_type: '化禄', star: '天同', fh_type: '向心自化', chong_palace: '' },
      { from_palace: '父母宫', hua_type: '化忌', star: '天同', fh_type: '普通飞宫', chong_palace: '命宫' },
    ],
  },
}

console.log('='.repeat(70))
console.log('TEST 1: 无 palace 时不渲染')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, { palace: null }))
  assert(html === '', '传入 null 不渲染')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 2: 完整宫位面板 — Header 信息')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: mockFeihuaByPalace,
  }))
  assert(html.includes('命宫'), '宫名显示')
  assert(html.includes('庚辰'), '干支显示')
  assert(html.includes('对宫'), '对宫标识')
  assert(html.includes('迁移宫'), '对宫名称')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 3: 星耀分区')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: mockFeihuaByPalace,
  }))
  assert(html.includes('天同'), '主星天同显示')
  assert(html.includes('陷'), '亮度陷')
  assert(html.includes('化忌'), '生年化忌标记')
  assert(html.includes('火星'), '煞星火星')
  assert(html.includes('左辅'), '吉星左辅')
  assert(html.includes('禄存'), '禄存')
  assert(html.includes('凤阁') || html.includes('寡宿'), '调候星显示')
  assert(html.includes('大限'), '大限信息')
  assert(html.includes('5') && html.includes('14'), '大限年龄段 5-14')
  assert(html.includes('长生'), '长生十二')
  assert(html.includes('养'), '长生：养')
  assert(html.includes('博士'), '博士十二')
  assert(html.includes('病符'), '博士：病符')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 4: 飞化区 — 4 化象 + 类型 + 语象')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: mockFeihuaByPalace,
  }))
  // 4 化象都显示
  assert(html.includes('化禄'), '化禄')
  assert(html.includes('化权'), '化权')
  assert(html.includes('化科'), '化科')
  assert((html.match(/化忌/g) || []).length >= 2, '化忌（生年+宫干）')
  // 化星目标
  assert(html.includes('太阳'), '化禄星：太阳')
  assert(html.includes('武曲'), '化权星：武曲')
  assert(html.includes('太阴'), '化科星：太阴')
  // 飞化类型
  assert(html.includes('普通飞宫'), '普通飞宫类型')
  assert(html.includes('离心自化'), '离心自化类型')
  assert(html.includes('向心自化'), '向心自化类型')
  // 语象标签
  assert(html.includes('质能变'), '质能变标签')
  // 我宫/他宫
  assert(html.includes('我宫'), '我宫标记')
  assert(html.includes('他宫'), '他宫标记')
  // 统计
  assert(html.includes('离心自化 1') && html.includes('普通飞宫 2'), '飞化数量统计')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 5: 他宫飞入')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: mockFeihuaByPalace,
  }))
  assert(html.includes('他宫飞入本宫'), '他宫飞入标题')
  assert(html.includes('迁移宫'), '飞入来源：迁移宫')
  assert(html.includes('父母宫'), '飞入来源：父母宫')
  assert(html.includes('冲命宫'), '冲宫标记')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 6: 三方四正')
console.log('='.repeat(70))
{
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: mockPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: mockFeihuaByPalace,
  }))
  assert(html.includes('本宫三方四正'), '三方四正标题')
  assert(html.includes('财帛位') || html.includes('财帛'), '财帛位')
  assert(html.includes('官禄位') || html.includes('官禄'), '官禄位')
  assert(html.includes('迁移位') || html.includes('迁移'), '迁移位（对宫）')
  // mock 命宫 idx=2，三方四正 = 2,6,10,8
  // index 6 = 官禄宫, 主星太阳(庙)
  // index 10 = 财帛宫, 主星武曲(庙)+天府(庙)
  // index 8 = 迁移宫, 主星太阴(旺)
  assert(html.includes('太阳'), '官禄位主星太阳')
  assert(html.includes('武曲') && html.includes('天府'), '财帛位主星武曲+天府')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 7: 无 feihuaByPalace 时优雅降级')
console.log('='.repeat(70))
{
  let ok = true
  let html = ''
  try {
    html = render(React.createElement(PalaceDetailPanel, {
      palace: mockPalace,
      allPalaces: mockAllPalaces,
      feihuaByPalace: null,
    }))
  } catch (e) {
    ok = false
    console.log('  ✗ 异常:', e.message)
  }
  assert(ok, '无 feihuaByPalace 不报错')
  assert(html.includes('命宫'), '其他区域仍然渲染')
  assert(html.includes('未生成') || html.includes('insights'), '提示飞化数据未生成')
}

console.log('\n' + '='.repeat(70))
console.log('TEST 8: 空宫场景')
console.log('='.repeat(70))
{
  const emptyPalace = {
    ...mockPalace,
    name: '兄弟宫', is_soul: false, is_body: false,
    major_stars: [],
  }
  const html = render(React.createElement(PalaceDetailPanel, {
    palace: emptyPalace,
    allPalaces: mockAllPalaces,
    feihuaByPalace: mockFeihuaByPalace,
  }))
  assert(html.includes('兄弟宫'), '宫名显示')
  assert(html.includes('空宫'), '空宫提示')
}

console.log('\n' + '='.repeat(70))
console.log(`总计: ${passed} 通过 / ${failed} 失败`)
console.log('='.repeat(70))
if (failed > 0) process.exit(1)
