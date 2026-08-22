import BirthFillBar from '../../components/UI/BirthFillBar'
import React, { useState, useMemo, useEffect } from 'react'
import { useNotifyStore } from '../../store/settingsStore'
import { useSettingsStore } from '../../store/settingsStore'
import AiInterpretPanel from '../../components/UI/AiInterpretPanel'
import ShareImage from '../../components/UI/ShareImage'
import { ZiweiVis } from '../../components/particles/Visualizations'
import ZiweiInsightsBar from './ZiweiInsightsBar'
import ZiweiOverview from './ZiweiOverview'
import ZiweiMinggeSynthesis from './ZiweiMinggeSynthesis'
import ZiweiPerspectives from './ZiweiPerspectives'
import ZiweiConsistencyAudit from './ZiweiConsistencyAudit'
import ZiweiClassical from './ZiweiClassical'
import ZiweiPalaceDetailPanel from './ZiweiPalaceDetailPanel'
import ZiweiCenterPanel from './ZiweiCenterPanel'
import ZiweiTimePanel from './ZiweiTimePanel'
import ZiweiDirections from './ZiweiDirections'
import ZiweiFamousCases from './ZiweiFamousCases'
import ZiweiSanheOverlay from './ZiweiSanheOverlay'
import ZiweiSchoolPanel from './ZiweiSchoolPanel'
import { exportElementToPng } from './exportChartPng'
import NarrationPanel from '../../components/NarrationPanel'
import { baziApi } from '../../api/client'

const HOUR_OPTIONS = [
  { label: '子时 23:00–01:00', value: 23 },
  { label: '丑时 01:00–03:00', value: 1  },
  { label: '寅时 03:00–05:00', value: 3  },
  { label: '卯时 05:00–07:00', value: 5  },
  { label: '辰时 07:00–09:00', value: 7  },
  { label: '巳时 09:00–11:00', value: 9  },
  { label: '午时 11:00–13:00', value: 11 },
  { label: '未时 13:00–15:00', value: 13 },
  { label: '申时 15:00–17:00', value: 15 },
  { label: '酉时 17:00–19:00', value: 17 },
  { label: '戌时 19:00–21:00', value: 19 },
  { label: '亥时 21:00–23:00', value: 21 },
]

// Brightness color
const BRIGHT_COLOR = { '庙': '#c8a04a', '旺': '#f39c12', '得地': '#3498db', '利': '#27ae60', '平和': '#7f8c8d', '不得地': '#e67e22', '落陷': '#e74c3c', '陷': '#e74c3c' }

// Palace display order (clockwise from top-right, traditional layout)
// 标准紫微命盘 4×4 布局（文墨天机式）：寅在左下角，地支顺时针排布
//   巳 午 未 申        idx: 3  4  5  6
//   辰      酉    →    idx: 2  _  _  7
//   卯      戌         idx: 1  _  _  8
//   寅 丑 子 亥        idx: 0 11 10  9
// （库的 palace.index 固定：0=寅 1=卯 … 9=亥 10=子 11=丑）
const PALACE_LAYOUT = [
  // row 0: top (left→right)  巳午未申
  [3, 4, 5, 6],
  // row 1: sides             辰 _ _ 酉
  [2, null, null, 7],
  // row 2: sides             卯 _ _ 戌
  [1, null, null, 8],
  // row 3: bottom (left→right) 寅丑子亥
  [0, 11, 10, 9],
]

// 星耀分类颜色（模仿文墨天机）
const STAR_COLOR = {
  // 14 主星 — 红色系
  major: '#c0392b',
  // 六吉星（左辅/右弼/文昌/文曲/天魁/天钺）— 蓝色
  soft:  '#2980b9',
  // 六煞星（火星/铃星/擎羊/陀罗/地空/地劫）— 紫红
  tough: '#8e44ad',
  // 桃花星（红鸾/天喜/咸池）— 粉
  flower:'#e91e63',
  // 杂曜/神煞 — 灰
  adj:   '#7f8c8d',
  // 化禄/化权/化科 — 绿/橙/蓝/红
  lu:    '#27ae60',
  quan:  '#f39c12',
  ke:    '#2980b9',
  ji:    '#e74c3c',
}

const MUTAGEN_BADGE = {
  '禄': { bg: '#e8f5e9', color: '#27ae60', text: '禄' },
  '权': { bg: '#fff3e0', color: '#f39c12', text: '权' },
  '科': { bg: '#e3f2fd', color: '#2980b9', text: '科' },
  '忌': { bg: '#ffebee', color: '#e74c3c', text: '忌' },
}

// 单颗星的小渲染
function StarChip({ star, sizeClass = 'major' }) {
  const isMajor = sizeClass === 'major'
  const isMinor = sizeClass === 'minor'
  const fontSize = isMajor ? '0.74rem' : isMinor ? '0.66rem' : '0.58rem'
  const fontWeight = isMajor ? 700 : isMinor ? 600 : 400
  let color = STAR_COLOR.adj
  if (isMajor) color = STAR_COLOR.major
  else if (isMinor) {
    if (['左辅','右弼','文昌','文曲','天魁','天钺','禄存','天马'].includes(star.name)) color = STAR_COLOR.soft
    else if (['火星','铃星','擎羊','陀罗','地空','地劫'].includes(star.name)) color = STAR_COLOR.tough
    else if (['红鸾','天喜','咸池'].includes(star.name)) color = STAR_COLOR.flower
    else color = STAR_COLOR.adj
  }

  return (
    <span style={{ display:'inline-flex', alignItems:'baseline', gap:'1px', whiteSpace:'nowrap' }}>
      <span style={{ fontSize, fontWeight, color, lineHeight: 1.15 }}>
        {star.name}
      </span>
      {star.brightness && (
        <span style={{ fontSize:'var(--text-2xs)', color: BRIGHT_COLOR[star.brightness] || color }}>
          ({star.brightness})
        </span>
      )}
      {star.mutagen && MUTAGEN_BADGE[star.mutagen] && (
        <span style={{
          marginLeft:'1px', padding:'0 2px',
          fontSize:'var(--text-2xs)', fontWeight: 700,
          background: MUTAGEN_BADGE[star.mutagen].bg,
          color: MUTAGEN_BADGE[star.mutagen].color,
          border: `1px solid ${MUTAGEN_BADGE[star.mutagen].color}66`,
        }}>{star.mutagen}</span>
      )}
    </span>
  )
}

function PalaceCell({ palace, isSoul, isBody, onSelect, selected, decadeLabel, annualLabel, school = 'feixing' }) {
  if (!palace) {
    return (
      <div style={{
        gridColumn: 'span 2', gridRow: 'span 2',
        border: '1px solid var(--border)',
        background: 'var(--bg-subtle)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        gap: '0.3rem',
      }}>
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontFamily: 'var(--font-serif)' }}>命盘中宫</div>
      </div>
    )
  }

  const isDecadeSoul = decadeLabel && decadeLabel.name === '大限命宫'
  const isAnnualSoul = annualLabel && annualLabel.name === '流年命宫'

  // 边框 / 背景：选中 > 流年命宫 > 大限命宫 > 本命命宫/身宫 > 默认
  let borderColor, bgColor
  if (selected) {
    borderColor = 'var(--accent)'
    bgColor = 'var(--accent-bg)'
  } else if (isAnnualSoul) {
    borderColor = '#d35400'
    bgColor = 'rgba(211,84,0,0.08)'
  } else if (isDecadeSoul) {
    borderColor = '#9b59b6'
    bgColor = 'rgba(155,89,182,0.06)'
  } else if (isSoul) {
    borderColor = 'var(--jade)'
    bgColor = 'rgba(74,122,90,0.05)'
  } else if (isBody) {
    borderColor = 'var(--cyan-b, #3498db)'
    bgColor = 'var(--bg-card)'
  } else {
    borderColor = 'var(--border)'
    bgColor = 'var(--bg-card)'
  }

  // 将杂曜与神煞分开
  const adjStars = palace.adj_stars || []
  
  // 整理流年与小限数字（每 12 年循环）
  const ages = palace.ages || []
  const annualYears = ages.slice(0, 5)  // 取前 5 个

  return (
    <div
      onClick={() => onSelect(palace)}
      style={{
        border: `1.5px solid ${borderColor}`,
        background: bgColor,
        padding: '4px 5px 4px 5px',
        cursor: 'pointer',
        display: 'flex', flexDirection: 'column', gap: '2px',
        minHeight: '160px',
        transition: 'all 0.12s',
        position: 'relative',
        fontFamily: 'var(--font-serif)',
      }}
    >
      {/* 顶部：主星行（命/身/大-命/年-命 badge 内联在最前，永不重叠） */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '3px', minHeight: '20px' }}>
        {(isSoul || isBody) && (
          <span style={{
            fontSize:'var(--text-2xs)', fontWeight: 700,
            padding: '1px 4px',
            background: isSoul ? 'rgba(74,122,90,0.15)' : 'rgba(52,152,219,0.15)',
            color: isSoul ? 'var(--jade)' : 'var(--cyan-b, #3498db)',
            border: `1px solid ${isSoul ? 'var(--jade)' : 'var(--cyan-b, #3498db)'}`,
            lineHeight: 1,
            flexShrink: 0,
          }}>{isSoul ? '命' : '身'}</span>
        )}
        {/* 大限命宫高亮 badge */}
        {isDecadeSoul && (
          <span style={{
            fontSize:'var(--text-2xs)', fontWeight: 700,
            padding: '1px 4px',
            background: 'rgba(155,89,182,0.15)',
            color: '#9b59b6',
            border: '1px solid #9b59b6',
            lineHeight: 1,
            flexShrink: 0,
          }}>大命</span>
        )}
        {/* 流年命宫高亮 badge */}
        {isAnnualSoul && (
          <span style={{
            fontSize:'var(--text-2xs)', fontWeight: 700,
            padding: '1px 4px',
            background: 'rgba(211,84,0,0.15)',
            color: '#d35400',
            border: '1px solid #d35400',
            lineHeight: 1,
            flexShrink: 0,
          }}>年命</span>
        )}
        {(palace.major_stars || []).map((s, i) => (
          <StarChip key={`mj-${i}`} star={s} sizeClass="major" />
        ))}
        {(palace.major_stars || []).length === 0 && (
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontStyle: 'italic' }}>无主星</span>
        )}
      </div>
      
      {/* 辅星行 */}
      {(palace.minor_stars || []).length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
          {palace.minor_stars.map((s, i) => (
            <StarChip key={`mn-${i}`} star={s} sizeClass="minor" />
          ))}
        </div>
      )}
      
      {/* 杂曜（小字灰色）— 自动换行 */}
      {adjStars.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px', marginTop: '1px' }}>
          {adjStars.slice(0, 8).map((s, i) => (
            <StarChip key={`adj-${i}`} star={s} sizeClass="adj" />
          ))}
        </div>
      )}

      {/* 流年/小限数字 */}
      {annualYears.length > 0 && (
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', lineHeight: 1.3, marginTop: '2px',
          fontFamily: 'var(--font-mono)' }}>
          流年: {annualYears.join(',')}
        </div>
      )}

      {/* 大限/流年角标（Z-7） */}
      {(decadeLabel || annualLabel) && (
        <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap', marginTop:'1px' }}>
          {decadeLabel && (
            <span style={{
              fontSize: '0.52rem', fontWeight: 600,
              color: isDecadeSoul ? '#9b59b6' : '#9b59b6cc',
              background: isDecadeSoul ? 'rgba(155,89,182,0.15)' : 'rgba(155,89,182,0.05)',
              border: isDecadeSoul ? '1px solid #9b59b6' : '1px solid rgba(155,89,182,0.3)',
              padding: '0 3px',
            }}>{decadeLabel.short}</span>
          )}
          {annualLabel && (
            <span style={{
              fontSize: '0.52rem', fontWeight: 600,
              color: isAnnualSoul ? '#d35400' : '#d3540099',
              background: isAnnualSoul ? 'rgba(211,84,0,0.15)' : 'rgba(211,84,0,0.04)',
              border: isAnnualSoul ? '1px solid #d35400' : '1px solid rgba(211,84,0,0.3)',
              padding: '0 3px',
            }}>{annualLabel.short}</span>
          )}
        </div>
      )}

      {/* 中下部空白 */}
      <div style={{ flex: 1 }} />

      {/* 博士十二神（左下，绿色 — 论吉凶） */}
      {palace.boshi12 && (
        <div style={{ position:'absolute', left: 4, bottom: 18,
          fontSize:'0.52rem', color: '#16a085' }}
          title="博士12神（论吉凶）">
          {palace.boshi12}
        </div>
      )}

      {/* 将前十二神（中下偏左，紫色 — 论煞气） */}
      {palace.jiangqian12 && (
        <div style={{ position:'absolute', left: 32, bottom: 18,
          fontSize:'0.52rem', color: '#8e44ad' }}
          title="将前12神（论煞气）">
          {palace.jiangqian12}
        </div>
      )}

      {/* 岁前十二神（中下偏右，棕色 — 论流年凶吉） */}
      {palace.suiqian12 && (
        <div style={{ position:'absolute', right: 32, bottom: 18,
          fontSize:'0.52rem', color: '#a0522d' }}
          title="岁前12神（论流年凶吉）">
          {palace.suiqian12}
        </div>
      )}
      
      {/* 大限范围 */}
      {palace.decadal_range && palace.decadal_range.length === 2 && (
        <div style={{
          position: 'absolute', left: 4, bottom: 4,
          fontSize:'var(--text-2xs)', color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
        }}>{palace.decadal_range[0]}~{palace.decadal_range[1]}</div>
      )}

      {/* 长生十二（右下） */}
      {palace.changsheng12 && (
        <div style={{
          position: 'absolute', right: 4, bottom: 4,
          fontSize:'var(--text-2xs)', color: 'var(--text-muted)',
        }}
          title="长生12神（论气场强弱）">{palace.changsheng12}</div>
      )}

      {/* 宫名（底部居中，红色突出） */}
      <div style={{
        position: 'absolute', bottom: 4, left: '50%', transform: 'translateX(-50%)',
        fontSize:'var(--text-xs)', fontWeight: 700,
        color: isSoul ? 'var(--jade)' : isBody ? 'var(--cyan-b, #3498db)' : '#c0392b',
        whiteSpace: 'nowrap',
      }}>
        {palace.name.replace('宫','')}
      </div>

      {/* 干支（右上角） */}
      <span style={{
        position: 'absolute', top: 3, right: 5,
        fontSize:'var(--text-2xs)', color: 'var(--text-muted)',
        fontFamily: 'var(--font-serif)',
      }}>
        {palace.heavenly_stem}{palace.earthly_branch}
      </span>
    </div>
  )
}

export default function ZiWeiPage() {
  const { apiBaseUrl } = useSettingsStore()
  const { notify } = useNotifyStore()
  const now = new Date()

  const [form, setForm] = useState({
    year: 1990, month: 5, day: 22, hour: 7, minute: 0, gender: '男', name: '',
    is_lunar: true, is_leap_month: false,
    longitude: null,  // 可选；如填则启用真太阳时校正
  })
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(null)
  const [showShare, setShowShare] = useState(false)
  const [layer, setLayer]     = useState('natal')  // natal | decade | triple
  const [decadeData, setDecadeData] = useState(null)
  const [tripleData, setTripleData] = useState(null)
  const [decadeAge, setDecadeAge]   = useState(35)
  const [school, setSchool] = useState('feixing')  // 派别: feixing(飞星) / sanhe(三合) / sihua(四化)
  // Z-9: 溯源点击 — 记录当前高亮的 section，传给 InsightsBar 让对应卡片闪一下
  const [highlightedSection, setHighlightedSection] = useState(null)

  // Z-9: 监听 StructuredAiOutput 派发的 ziwei:citation-click 事件
  useEffect(() => {
    const onCite = (ev) => {
      const { section, item } = ev.detail || {}
      if (!section) return
      // 1. 滚动到 InsightsBar
      const insightsEl = document.querySelector('[data-ziwei-insights-bar]')
      if (insightsEl) insightsEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
      // 2. 高亮对应卡片 2 秒
      setHighlightedSection(section)
      setTimeout(() => setHighlightedSection(null), 2200)
    }
    window.addEventListener('ziwei:citation-click', onCite)
    return () => window.removeEventListener('ziwei:citation-click', onCite)
  }, [])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  // 日↑↓ / 时↑↓ — 改变出生日期/时辰并重新排盘
  const shiftDay = async (delta) => {
    // 用 lunar-python 风格的算法在前端简单处理农历日期变化
    // 但简单方式：直接调后端，让后端处理（农历闰月等边界）
    const newDay = form.day + delta
    // 简单处理：不超过 1-30 区间，超过则不变（农历月最多 30 天）
    if (newDay < 1 || newDay > 30) {
      notify(`已到${delta > 0 ? '月末' : '月初'}，请手动改月份`, 'warning')
      return
    }
    setForm(f => ({ ...f, day: newDay }))
    setTimeout(() => run(), 50)  // 异步触发重排
  }

  const shiftHour = async (delta) => {
    // 时辰索引 0-11；hour 字段是钟表小时（23/1/3/5/.../21）
    const HOUR_VALUES = [23, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
    const currIdx = HOUR_VALUES.indexOf(form.hour)
    let newIdx = currIdx >= 0 ? currIdx + delta : 0
    // 跨日处理
    if (newIdx < 0) newIdx = 11
    if (newIdx > 11) newIdx = 0
    const newHour = HOUR_VALUES[newIdx]
    setForm(f => ({ ...f, hour: newHour }))
    setTimeout(() => run(), 50)
  }

  // 从命例库导入
  const loadFamousCase = async (caseData) => {
    setForm({
      year: caseData.year,
      month: caseData.month,
      day: caseData.day,
      hour: caseData.hour,
      gender: caseData.gender,
      name: caseData.name,
      is_lunar: caseData.is_lunar !== false,
      is_leap_month: !!caseData.is_leap_month,
      longitude: caseData.longitude,
    })
    notify(`已导入命例：${caseData.name}`, 'success')
    setTimeout(() => run(), 50)
  }

  // 导出命盘 PNG
  const [exporting, setExporting] = useState(false)
  const exportChart = async () => {
    if (!result) {
      notify('请先排盘', 'warning')
      return
    }
    setExporting(true)
    try {
      const el = document.querySelector('[data-ziwei-chart-export]')
      if (!el) throw new Error('找不到命盘元素')
      const filename = `紫微-${form.name || form.year + '_' + form.month + '_' + form.day}-${form.gender}`
      await exportElementToPng(el, filename, { scale: 2, background: '#ffffff' })
      notify('命盘 PNG 已下载', 'success')
    } catch (e) {
      notify('导出失败：' + e.message, 'error')
    } finally {
      setExporting(false)
    }
  }

  const run = async () => {
    setLoading(true)
    setSelected(null); setLayer('natal'); setDecadeData(null); setTripleData(null)
    try {
      const res  = await fetch(`${apiBaseUrl}/api/v1/ziwei/chart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          year: +form.year, month: +form.month, day: +form.day, hour: +form.hour,
          is_lunar: form.is_lunar !== false,
          is_leap_month: form.is_leap_month === true,
        }),
      })
      const json = await res.json()
      if (!json.success) throw new Error(json.message || '排盘失败')
      setResult(json.data)
      notify('紫微排盘完成', 'success')
    } catch (e) {
      notify(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  // Layer 2.4: 大限四化
  const loadDecade = async (age) => {
    if (!result) return
    setDecadeAge(age)
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/ziwei/decade`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, year:+form.year, month:+form.month, day:+form.day, hour:+form.hour, age }),
      })
      const json = await res.json()
      if (json.success) {
        // 后端返回 { decade: {...}, feihua: [...], overlay_insights: {...} }
        // 扁平化让前端用 decadeData.palace_name 而非 decadeData.decade.palace_name
        const d = json.data || {}
        const flat = {
          ...(d.decade || {}),                // palace_name / palace_idx / stem / age_range / palaces_layout
          decade_feihua: d.feihua || [],
          feihua: d.feihua || [],             // 兼容旧字段
          overlay_insights: d.overlay_insights || null,
        }
        setDecadeData(flat); setLayer('decade')
      }
    } catch (e) { notify(e.message, 'error') }
  }

  // Layer 2.4: 三盘叠合
  const loadTriple = async () => {
    if (!result) return
    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/ziwei/triple`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, year:+form.year, month:+form.month, day:+form.day, hour:+form.hour, age: decadeAge, current_year: new Date().getFullYear() }),
      })
      const json = await res.json()
      if (json.success) { setTripleData(json.data); setLayer('triple') }
    } catch (e) { notify(e.message, 'error') }
  }

  const palaces = result?.palaces || []
  const meta    = result?.metadata || {}
  const soul    = result?.soul_palace
  const body    = result?.body_palace

  // Build index map for grid
  const palaceByIndex = {}
  palaces.forEach(p => { palaceByIndex[p.index] = p })

  // —— 任务 3：把 decadeData/tripleData 合并进 result.\_overlay
  // 这样后端 context_builder 能识别 overlay 并用 Z-2 飞化引擎计算大限/流年飞化
  const enrichedResult = useMemo(() => {
    if (!result) return null
    if (!decadeData && !tripleData) return result
    return {
      ...result,
      _overlay: {
        layer,                  // 用户当前选择的视图（natal/decade/triple）
        decade: decadeData,     // /ziwei/decade 端点返回的原始 data
        triple: tripleData,     // /ziwei/triple 端点返回的原始 data
      }
    }
  }, [result, decadeData, tripleData, layer])

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">紫微斗数</div>
          <div className="page-subtitle">十四主星 · 十二宫位 · 三方四正 · 大小限流年</div>
        </div>
      </div>

      <div className="page-body">
        <div className="page-cols">
          {/* ── LEFT ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="card">
              <div className="card-title">出生信息</div>
              <BirthFillBar currentValues={{...form, gender:form.gender==='男'?'male':'female'}} onFill={b=>setForm(f=>({...f, year:b.year, month:b.month, day:b.day, hour:b.hour, gender:b.gender==='male'?'男':'女', is_lunar:b.is_lunar!==false, is_leap_month:!!b.is_leap_month}))} />
              {/* ── 农历/公历切换 ── */}
              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:'0.65rem' }}>
                <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', letterSpacing:'0.06em', textTransform:'uppercase', fontWeight:600 }}>历法</span>
                <div style={{ display:'flex', gap:'3px', background:'var(--bg-subtle)', borderRadius:'var(--r-sm)', padding:'3px' }}>
                  {[{v:true,l:'农历'},{v:false,l:'公历'}].map(({v,l}) => (
                    <button key={String(v)} onClick={() => set('is_lunar', v)} style={{
                      padding:'3px 9px', borderRadius:0, border:'none',
                      background: form.is_lunar===v ? 'var(--surface)' : 'transparent',
                      color:      form.is_lunar===v ? 'var(--accent)'  : 'var(--text-muted)',
                      fontWeight: form.is_lunar===v ? 600 : 400,
                      fontSize:'var(--text-xs)', cursor:'pointer',
                      boxShadow: form.is_lunar===v ? 'var(--shadow-xs)' : 'none',
                      transition:'all var(--t-fast)',
                    }}>{l}</button>
                  ))}
                </div>
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label>{form.is_lunar ? '农历年' : '公历年'}</label>
                  <input type="number" min="1800" max="2100" value={form.year} onChange={e => set('year', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>{form.is_lunar ? '农历月' : '公历月'}</label>
                  {form.is_lunar ? (
                    <select value={form.month} onChange={e => set('month', +e.target.value)}>
                      {[['正月',1],['二月',2],['三月',3],['四月',4],['五月',5],['六月',6],
                        ['七月',7],['八月',8],['九月',9],['十月',10],['十一月',11],['腊月',12]
                      ].map(([l,v]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  ) : (
                    <select value={form.month} onChange={e => set('month', +e.target.value)}>
                      {Array.from({length:12},(_,i) => <option key={i+1} value={i+1}>{i+1}月</option>)}
                    </select>
                  )}
                </div>
              </div>
              <div className="form-row-2">
                <div className="form-group">
                  <label>{form.is_lunar ? '农历日' : '公历日'}</label>
                  <input type="number" min="1" max={form.is_lunar ? 30 : 31} value={form.day} onChange={e => set('day', e.target.value)} />
                </div>
                <div className="form-group"><label>性别</label>
                  <select value={form.gender} onChange={e => set('gender', e.target.value)}>
                    <option value="男">男</option>
                    <option value="女">女</option>
                  </select>
                </div>
              </div>
              {form.is_lunar && (
                <label style={{ display:'flex', alignItems:'center', gap:'0.4rem', fontSize:'var(--text-xs)', color:'var(--text-muted)', cursor:'pointer', marginBottom:'0.35rem' }}>
                  <input type="checkbox" checked={form.is_leap_month||false}
                    onChange={e => set('is_leap_month', e.target.checked)}
                    style={{ accentColor:'var(--accent)', cursor:'pointer' }} />
                  <span>闰月</span>
                </label>
              )}
              <div className="form-group">
                <label>出生时辰</label>
                <select value={form.hour} onChange={e => set('hour', +e.target.value)}>
                  {HOUR_OPTIONS.map(h => (
                    <option key={h.value} value={h.value}>{h.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>出生地经度（可选，启用真太阳时）
                  <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginLeft: '4px' }}>
                    北京 116.4 / 上海 121.5 / 成都 104.0 / 乌鲁木齐 87.6
                  </span>
                </label>
                <input type="number" step="0.1" placeholder="如 104.0" value={form.longitude ?? ''}
                  onChange={e => set('longitude', e.target.value === '' ? null : parseFloat(e.target.value))} />
                <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {form.longitude
                    ? `校正：钟表与真太阳时差 ${((form.longitude - 120) * 4).toFixed(1)} 分钟，可能改变时辰`
                    : '未启用 — 使用北京时区钟表时间（民国后俗法）'}
                </div>
              </div>
              <div className="form-group">
                <label>姓名（可选）</label>
                <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="仅作标注" />
              </div>
            </div>

            <button className="btn btn-primary btn-full btn-lg" onClick={run} disabled={loading}>
              {loading ? '起盘中…' : '起紫微斗数盘 ▶'}
            </button>

            {/* 名人命例库 */}
            <ZiweiFamousCases onSelect={loadFamousCase} />

            {/* Metadata card */}
            {meta.five_elements && (
              <div className="card card-glow">
                <div className="card-title">命盘基本信息</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.35rem 0.75rem', fontSize: 'var(--text-sm)' }}>
                  {[
                    ['四柱', meta.chinese_date],
                    ['五行局', meta.five_elements],
                    ['农历', meta.lunar_date],
                    ['生肖', meta.zodiac],
                    ['时辰', meta.birth_hour_name + ' ' + meta.birth_hour_range],
                    ['星座', meta.sign],
                  ].map(([k, v]) => (
                    <React.Fragment key={k}>
                      <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                      <span style={{ fontFamily: 'var(--font-serif)' }}>{v}</span>
                    </React.Fragment>
                  ))}
                </div>
                {soul && (
                  <div style={{ marginTop: '0.6rem', borderTop: '1px solid var(--border)', paddingTop: '0.5rem' }}>
                    <div style={{ display: 'flex', gap: '1.5rem', fontSize: 'var(--text-sm)' }}>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>命宫 </span>
                        <span style={{ color: 'var(--jade)', fontWeight: 700 }}>
                          {soul.stem_branch} {soul.major_stars.join('·') || '无主星'}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>身宫 </span>
                        <span style={{ color: 'var(--cyan-b, #3498db)', fontWeight: 700 }}>
                          {body?.name} {body?.major_stars?.join('·') || ''}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 三方四正评级已由右栏 ZiweiInsightsBar 完整展示（含亮度评级/分数），此处不再重复 */}
          </div>

          {/* ── RIGHT ── */}
          <div>
            {loading && (
              <div className="loading"><div className="spinner"/><p>排盘中…</p></div>
            )}

            {!loading && !result && (
              <div className="card" style={{ textAlign: 'center', padding: '3.5rem 2rem' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.15 }}>☆</div>
                <p style={{ fontFamily: 'var(--font-serif)', color: 'var(--text-muted)', lineHeight: 1.9 }}>
                  紫微斗数，以北斗紫微星为主，<br/>统御十四主星布十二宫，<br/>论命运起伏，知人生格局
                </p>
              </div>
            )}

            {!loading && result && (
              <>
                {/* ── Particle visualization（layer-aware 飞化箭头） ── */}
                {result.palaces && (() => {
                  // 命宫所在宫位 — 用于识别"生年四化"
                  const soulPalaceIdx = result.metadata?.soul_palace_index ?? 1

                  // 从 insights.feihua_by_palace 提取带 fh_type 的飞化记录
                  const buildFeihuaForVis = () => {
                    const fbp = result.insights?.feihua_by_palace
                    if (!fbp) {
                      // 降级到旧版 feihua（无 fh_type）
                      return (result.feihua||[]).map(f => ({
                        from: f.source_palace_idx||0,
                        to: f.target_palace_idx||0,
                        type: f.hua_type||'',
                        fh_type: '',
                        is_natal: false,
                      }))
                    }
                    // 收集所有宫的 4 化象
                    const items = []
                    for (const pIdxStr of Object.keys(fbp)) {
                      const rec = fbp[pIdxStr]
                      const fromIdx = rec.palace_idx
                      // 命宫干起的 4 化 = 生年四化（本命盘最核心）
                      const isNatalSihua = (fromIdx === soulPalaceIdx)
                      for (const tr of (rec.transformations||[])) {
                        const tIdx = tr.target_palace_idx
                        if (tIdx === undefined || tIdx < 0) continue
                        items.push({
                          from: fromIdx,
                          to: tIdx,
                          type: tr.hua_type,
                          fh_type: tr.fh_type,
                          is_natal: isNatalSihua,
                          // 化忌额外醒目
                          is_ji: tr.hua_type === '化忌',
                        })
                      }
                    }
                    return items
                  }

                  // 大限/三盘层：叠加 overlay 化象
                  const buildOverlayFeihuaForVis = () => {
                    const overlay = layer === 'triple'
                      ? tripleData?.overlay_insights
                      : layer === 'decade'
                        ? decadeData?.overlay_insights
                        : null
                    if (!overlay) return []
                    const items = []
                    const layers = []
                    if (overlay.decade) layers.push({ data: overlay.decade, fromPalace: overlay.decade.palace_idx })
                    if (layer === 'triple' && overlay.annual) {
                      // 流年由本命命宫干起化，from 用 soulIdx
                      const soulIdx = result.metadata?.soul_palace_index ?? 0
                      layers.push({ data: overlay.annual, fromPalace: soulIdx })
                    }
                    for (const l of layers) {
                      for (const tr of (l.data.transformations||[])) {
                        const tIdx = tr.target_palace_idx
                        if (tIdx === undefined || tIdx < 0) continue
                        items.push({
                          from: l.fromPalace,
                          to: tIdx,
                          type: tr.hua_type,
                          fh_type: tr.fh_type,
                          is_ji: tr.hua_type === '化忌',
                        })
                      }
                    }
                    return items
                  }

                  // 本命层始终显示，运程层叠加
                  const natalFeihua = buildFeihuaForVis()
                  const overlayFeihua = buildOverlayFeihuaForVis()
                  // 本命视图只显示本命，运程视图叠加
                  const visFeihua = layer === 'natal'
                    ? natalFeihua
                    : [...natalFeihua, ...overlayFeihua]

                  // 派别过滤（真正影响画面）：
                  //   feixing(飞星): 全部化象都显示（最详尽，48 条线）
                  //   sanhe(三合):   仅显示化禄+化忌（核心 24 条），略去化权/化科
                  //   sihua(四化):   仅显示命宫干起的 4 化（即生年四化，最简洁 4 条）
                  let filteredFeihua = visFeihua
                  if (school === 'sanhe') {
                    filteredFeihua = visFeihua.filter(f => f.type === '化禄' || f.type === '化忌')
                  } else if (school === 'sihua') {
                    filteredFeihua = visFeihua.filter(f => f.is_natal === true)
                  }

                  return (
                    <>
                      <div style={{
                        fontSize:'var(--text-xs)',
                        textAlign: 'center', marginBottom: '0.4rem',
                        fontFamily: 'var(--font-serif)',
                        padding: '6px 10px',
                        background: {
                          feixing: 'rgba(155,89,182,0.06)',
                          sanhe:   'rgba(243,156,18,0.06)',
                          sihua:   'rgba(231,76,60,0.06)',
                        }[school],
                        borderLeft: `3px solid ${{
                          feixing: '#9b59b6',
                          sanhe:   '#f39c12',
                          sihua:   '#e74c3c',
                        }[school]}`,
                      }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                          {{
                            feixing: '飞星派',
                            sanhe:   '三合派',
                            sihua:   '四化派',
                          }[school]}
                          <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: '6px' }}>
                            · 显示 {filteredFeihua.length} 条飞化
                          </span>
                        </div>
                        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
                          {{
                            feixing: '看：48 条四化飞化网络 + 自化（离心/向心）+ 禄忌交战 + 质能变',
                            sanhe:   '看：命/财/官/迁三方四正连线 + 主星格局 + 化禄化忌（化权科已弱化）',
                            sihua:   '看：仅命宫干起的 4 化（生年四化）+ 化禄宫金边 + 化忌宫红边',
                          }[school]}
                        </div>
                      </div>
                      <ZiweiVis
                        palaces={result.palaces}
                        feihua={filteredFeihua}
                        soulIdx={result.metadata?.soul_palace_index||0}
                        layer={layer}
                      />
                    </>
                  )
                })()}

                {/* ── Z-3/Z-4/Z-2 polish: insights bar ──
                    NOTE: 移到 12 宫盘之后，因为命盘本身是主体内容，
                    InsightsBar 是辅助警示/评分，不应抢夺第一注意力 */}

                {/* 综合论断 · 总汇合参（全功能激活后的最终汇总，紧随命盘之后，早于细项分析）*/}
                {result?.master_synthesis?.available && (() => {
                  const QC = { 吉:'#27ae60', 中:'var(--accent)', 凶:'#c0392b' }
                  const ms = result.master_synthesis
                  const pc = QC[ms.overall_quality] || 'var(--accent)'
                  return (
                    <div className="card card-glow" style={{ borderTop:`4px solid ${pc}`, marginBottom:'1rem' }}>
                      <div className="card-title">综合论断 · 总汇合参</div>
                      <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)', fontWeight:600,
                        color:pc, marginBottom:'0.6rem' }}>
                        {ms.ming_label} · 综评<span style={{ color:pc }}>{ms.overall_quality}</span>
                      </div>
                      <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', lineHeight:1.7,
                        color:'var(--text-secondary)', padding:'0.5rem 0.7rem', background:`${pc}10`,
                        borderLeft:`4px solid ${pc}`, marginBottom:'0.7rem' }}>
                        {ms.headline}
                      </div>
                      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))', gap:'6px', marginBottom:'0.7rem' }}>
                        {(ms.dimension_verdicts || []).map((dv, i) => {
                          const c = QC[dv.quality] || '#888'
                          return (
                            <div key={i} style={{ padding:'0.4rem 0.6rem', background:'var(--bg-subtle)',
                              borderRadius:'var(--r-sm)', borderLeft:`3px solid ${c}` }}>
                              <span style={{ fontWeight:700, fontSize:'var(--text-sm)' }}>{dv.domain}</span>
                              <span style={{ color:c, fontSize:'var(--text-xs)', marginLeft:6 }}>{dv.quality}</span>
                              <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginTop:2,
                                fontFamily:'var(--font-serif)', lineHeight:1.5 }}>{dv.verdict}</div>
                            </div>
                          )
                        })}
                      </div>
                      {(ms.integrated_paragraphs || []).map((p, i) => (
                        <p key={i} style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                          lineHeight:1.8, color:'var(--text-secondary)', margin:'0.3rem 0' }}>{p}</p>
                      ))}
                      {ms.master_advice && (
                        <div style={{ marginTop:'0.5rem', padding:'0.5rem 0.7rem', background:'var(--bg-subtle)',
                          borderRadius:'var(--r-sm)', fontSize:'var(--text-sm)', fontFamily:'var(--font-serif)',
                          color:'var(--text-secondary)' }}>
                          <b style={{ color:pc }}>总建议 · </b>{ms.master_advice}
                        </div>
                      )}
                      <NarrationPanel ms={ms} fullData={result} module="ziwei" companions={[{ module:'bazi', label:'八字', fetch: async () => (await baziApi.chart({ year:+form.year, month:+form.month, day:+form.day, hour:+form.hour, gender:form.gender==='男'?'male':'female', is_lunar:form.is_lunar!==false })).data }]} />
                    </div>
                  )
                })()}

                {/* 命盘总论 · 定盘（综合总论 hero） */}
                <ZiweiOverview data={result} />

                {/* 命格力量综合 · 推理链 */}
                <ZiweiMinggeSynthesis data={result} />

                {/* 多视角整合解读 */}
                <ZiweiPerspectives data={result} />

                {/* 命盘一致性审核 + AI 审定 */}
                <ZiweiConsistencyAudit data={result} />

                {/* 传统断语 · 古籍精要 */}
                <ZiweiClassical data={result} />

                {/* ── Layer selector: 本命/大限/三盘 ── */}
                <div style={{ display:'flex', gap:0, borderBottom:'1px solid var(--border)', marginBottom:'0.75rem' }}>
                  {[
                    { id:'natal', label:'本命盘' },
                    { id:'decade', label:'大限盘' },
                    { id:'triple', label:'三盘叠合' },
                  ].map(l => (
                    <button key={l.id} className={`tab ${layer===l.id?'active':''}`}
                      onClick={() => {
                        if (l.id==='natal') setLayer('natal')
                        else if (l.id==='decade') loadDecade(decadeAge)
                        else loadTriple()
                      }}>{l.label}</button>
                  ))}
                  {layer !== 'natal' && (
                    <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6, padding:'0 8px' }}>
                      <label style={{ margin:0, fontSize:'var(--text-xs)' }}>岁数</label>
                      <input type="number" min={1} max={120} value={decadeAge}
                        onChange={e => { setDecadeAge(+e.target.value); if (layer==='decade') loadDecade(+e.target.value) }}
                        style={{ width:56, padding:'2px 6px', fontSize:'var(--text-xs)' }}/>
                    </div>
                  )}
                </div>

                {/* ── Decade/Triple data display ── */}
                {layer === 'decade' && decadeData && (
                  <div className="card" style={{ marginBottom:'0.75rem' }}>
                    <div className="card-title">大限四化 · {decadeData.palace_name || ''} ({decadeData.age_range?.[0]}–{decadeData.age_range?.[1]}岁)</div>
                    <div style={{ display:'flex', gap:0, flexWrap:'wrap' }}>
                      {(decadeData.decade_feihua || decadeData.feihua || []).map((f, i) => (
                        <div key={i} style={{ flex:1, minWidth:100, padding:'6px 8px', borderRight:'1px solid var(--border)', textAlign:'center' }}>
                          <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{f.hua_type}</div>
                          <div style={{ fontSize:'var(--text-sm)', fontWeight:600, color:'var(--accent)' }}>{f.star}</div>
                          <div style={{ fontSize:'var(--text-xs)', color:'var(--text-secondary)' }}>→ {f.palace_name}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {layer === 'triple' && tripleData && (
                  <div className="card" style={{ marginBottom:'0.75rem' }}>
                    <div className="card-title">三盘叠合警示</div>
                    {(tripleData.combined_warnings || []).length > 0 ? (
                      <div style={{ display:'flex', flexDirection:'column', gap:4 }}>
                        {tripleData.combined_warnings.map((w, i) => (
                          <div key={i} style={{ fontSize:'var(--text-sm)', color:'var(--red)', padding:'4px 0',
                            borderBottom:'1px solid var(--border)' }}>⚠ {w}</div>
                        ))}
                      </div>
                    ) : <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)' }}>无叠忌冲突</div>}
                  </div>
                )}

                {/* ── 12-palace grid 工具栏（独立行，不再绝对定位避免重叠） ── */}
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  marginBottom: '0.5rem', padding: '0.4rem 0.6rem',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border)',
                }}>
                  <div style={{ display:'flex', gap:'0.85rem', fontSize:'var(--text-xs)', color:'var(--text-faint)' }}>
                    <span><span style={{ color: 'var(--jade)', fontWeight: 700 }}>命</span> 命宫</span>
                    <span><span style={{ color: 'var(--cyan-b, #3498db)', fontWeight: 700 }}>身</span> 身宫</span>
                    <span style={{ color: 'var(--text-muted)' }}>· 点击宫位查看详情</span>
                  </div>
                  <button
                    onClick={exportChart}
                    disabled={exporting}
                    style={{
                      padding: '4px 12px',
                      fontSize:'var(--text-xs)',
                      background: 'rgba(207,59,44,0.1)',
                      color: 'var(--accent)',
                      border: '1px solid var(--accent)',
                      cursor: exporting ? 'wait' : 'pointer',
                      fontFamily: 'var(--font-serif)',
                      fontWeight: 600,
                    }}
                    title="导出高清命盘 PNG（2× 分辨率）"
                  >
                    {exporting ? '生成中…' : '⬇ 导出 PNG'}
                  </button>
                  <button className="btn btn-sm" onClick={() => setShowShare(true)} title="生成分享图" style={{ marginLeft:6 }}>🖼 分享图</button>
                </div>

                {/* ── 12-palace grid（用 ZiweiDirections 包裹，加 8 方位边缘标注） ── */}
                <div className="card" style={{ padding: '0.5rem' }} data-ziwei-chart-export>
                  <ZiweiDirections>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gridTemplateRows: 'repeat(4, auto)',
                      gap: '2px',
                      position: 'relative',  // 让 SanheOverlay 能 absolute 定位
                    }}>
                      {/* 三合派：三方四正连线（仅 sanhe 派显示） */}
                      <ZiweiSanheOverlay
                        palaces={result.palaces}
                        soulIdx={result.metadata?.soul_palace_index ?? 1}
                        visible={school === 'sanhe'}
                      />
                      {PALACE_LAYOUT.map((row, ri) =>
                        row.map((pidx, ci) => {
                          if (pidx === null) {
                            // Center cells — 使用新的 ZiweiCenterPanel 组件
                            if (ri === 1 && ci === 1) {
                              return (
                                <ZiweiCenterPanel
                                  key={`c${ri}${ci}`}
                                  meta={meta}
                                  baziOverlay={result.bazi_overlay}
                                  layer={layer}
                                  decadeData={decadeData}
                                  tripleData={tripleData}
                                  onShiftDay={shiftDay}
                                  onShiftHour={shiftHour}
                                  school={school}
                                  onSchoolChange={setSchool}
                                />
                              )
                            }
                            return null
                          }
                          const p = palaceByIndex[pidx]
                          if (!p) return <div key={`e${ri}${ci}`} style={{ minHeight: 80, border: '1px solid var(--border)' }} />
                          // Z-7: 大限/流年宫名角标 — 仅在对应 layer 下显示
                          const decadeLayout = (layer === 'decade' || layer === 'triple')
                            ? (tripleData?.overlay_insights?.decade?.palaces_layout
                               || decadeData?.overlay_insights?.decade?.palaces_layout
                               || decadeData?.palaces_layout  // 扁平化后直接 .palaces_layout
                               || decadeData?.decade?.palaces_layout  // 老兼容
                               || null)
                            : null
                          const annualLayout = (layer === 'triple')
                            ? (tripleData?.overlay_insights?.annual?.palaces_layout || null)
                            : null
                          const decadeLabel = decadeLayout ? decadeLayout[p.index] : null
                          const annualLabel = annualLayout ? annualLayout[p.index] : null
                          return (
                            <PalaceCell
                              key={p.index}
                              palace={p}
                              isSoul={p.is_soul}
                              isBody={p.is_body}
                              selected={selected?.index === p.index}
                              onSelect={setSelected}
                              decadeLabel={decadeLabel}
                              annualLabel={annualLabel}
                              school={school}
                            />
                          )
                        })
                      )}
                    </div>
                  </ZiweiDirections>
                </div>

                {/* ── 底栏时间盘 — 大限/流年/流月/流日/流时 ── */}
                {result.bazi_overlay && (
                  <ZiweiTimePanel
                    bazi={result.bazi_overlay}
                    timePanel={result.time_panel}
                    selectedAge={decadeAge}
                    selectedYear={new Date().getFullYear()}
                    onAgeChange={(age) => { setDecadeAge(age); loadDecade(age) }}
                    onYearChange={(y) => { /* 流年切换 — 触发 triple 加载 */ loadTriple() }}
                  />
                )}

                {/* ── Selected palace detail（完整宫位详情面板，layer-aware） ── */}
                {selected && (
                  <ZiweiPalaceDetailPanel
                    palace={selected}
                    allPalaces={palaces}
                    feihuaByPalace={result?.insights?.feihua_by_palace}
                    layer={layer}
                    overlayInsights={
                      layer === 'triple'
                        ? tripleData?.overlay_insights
                        : layer === 'decade'
                          ? (decadeData?.overlay_insights || null)
                          : null
                    }
                  />
                )}

                {/* ── 派别专属解读面板（三派各自的命理学方法论）── */}
                <div style={{ marginTop: '1rem' }}>
                  <div className="card-title" style={{ marginBottom: '0.5rem', color: 'var(--accent)' }}>
                    {{ feixing: '飞星派解读', sanhe: '三合派解读', sihua: '四化派解读' }[school]}
                  </div>
                  <ZiweiSchoolPanel
                    school={school}
                    palaces={result.palaces}
                    insights={result.insights}
                    soulIdx={result.metadata?.soul_palace_index ?? 1}
                    baziOverlay={result.bazi_overlay}
                    birthSihua={result.birth_sihua}
                    feihuaChains={result.feihua_chains}
                  />
                </div>

                {/* ── 命格洞察栏（共通信息：评分、格局、飞化、冲宫、三方四正）── */}
                <div data-ziwei-insights-bar style={{ marginTop: '1rem' }}>
                  <div className="card-title" style={{ marginBottom: '0.5rem', color: 'var(--accent)' }}>
                    命格洞察（共通分析）
                  </div>
                  <ZiweiInsightsBar
                    insights={result.insights}
                    chongChains={
                      layer === 'triple' && tripleData?.chong_chains
                        ? tripleData.chong_chains
                        : (result.insights?.chong_chains || null)
                    }
                    highlightedSection={highlightedSection}
                    school={school}
                  />
                </div>

                {/* ── AI Interpret ── */}
                <div style={{ marginTop: '1rem' }}>
                  <AiInterpretPanel
                    module="ziwei"
                    data={enrichedResult}
                    extraContext={`${form.year}年${form.month}月${form.day}日 ${HOUR_OPTIONS.find(h=>h.value===+form.hour)?.label||''} ${form.gender}${
                      layer !== 'natal' ? ` · 当前视图: ${layer === 'decade' ? '大限' : '三盘叠合'}` : ''
                    } · 分析派别: ${
                      { feixing: '飞星派（重四化飞化网络与自化质能变）',
                        sanhe:   '三合派（重三方四正格局与主星组合）',
                        sihua:   '四化派（仅看生年四化所落宫位的命迁福财影响）',
                      }[school]
                    }`}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      {showShare && <ShareImage data={result} module="ziwei" onClose={() => setShowShare(false)} />}
    </div>
  )
}
