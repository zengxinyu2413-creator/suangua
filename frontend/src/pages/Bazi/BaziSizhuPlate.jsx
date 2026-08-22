import React from 'react'
import '../../styles/plates.css'

// 五行 → 颜色 class
const WX = { '木':'gv-wx-mu', '火':'gv-wx-huo', '土':'gv-wx-tu', '金':'gv-wx-jin', '水':'gv-wx-shui' }
const WX_ORDER = ['木','火','土','金','水']

const COLS = [
  { k:'year_pillar',  cap:'年',     key:'年' },
  { k:'month_pillar', cap:'月',     key:'月' },
  { k:'day_pillar',   cap:'日 · 元', key:'日', day:true },
  { k:'hour_pillar',  cap:'时',     key:'时' },
]

export default function BaziSizhuPlate({ chart }) {
  if (!chart) return null
  const cols = COLS.map(c => ({ ...c, p: chart[c.k] })).filter(c => c.p)
  if (!cols.length) return null

  // 神煞按柱归组（pillar 字段形如 "年支"/"月支"/"日支"/"时支"）
  const shByPillar = { 年:[], 月:[], 日:[], 时:[] }
  ;(chart.shensha || []).forEach(s => {
    const pos = s.pillar || ''
    const k = ['年','月','日','时'].find(x => pos.includes(x))
    if (k) shByPillar[k].push(s.name)
  })

  // 五行分布（仅统计可见 8 字：天干+地支）
  const wxCount = { 木:0, 火:0, 土:0, 金:0, 水:0 }
  cols.forEach(c => {
    if (wxCount[c.p.wuxing_gan] != null) wxCount[c.p.wuxing_gan]++
    if (wxCount[c.p.wuxing_zhi] != null) wxCount[c.p.wuxing_zhi]++
  })
  const wxMax = Math.max(1, ...Object.values(wxCount))

  // 综断文字
  const pattern = chart.pattern || ''
  const dm = chart.day_master || (chart.day_pillar && chart.day_pillar.tiangan) || ''
  const monthZhi = chart.month_pillar && chart.month_pillar.dizhi
  const patternDesc = chart.pattern_desc || ''
  const tiaohou = chart.tiaohou || {}
  const tiaohouVerdict = (tiaohou && tiaohou.available) ? (tiaohou.verdict || '') : ''

  const Row = ({ label, render }) => (
    <>
      <div className="gv-sz-lbl">{label}</div>
      {cols.map(c => render(c))}
    </>
  )

  return (
    <div className="gv-plate">
      <div className="gv-sec-bar">
        <span className="gv-seal" style={{ background:'#d8ab3c', color:'#473205' }}>柱</span>
        <span className="t">四柱排盘</span>
        <span className="cap">{dm ? `${dm}日元` : ''}{monthZhi ? ` · ${monthZhi}月` : ''}</span>
      </div>

      <div className="gv-sizhu">
        {/* 表头 */}
        <div className="gv-sz-lbl" />
        {cols.map(c => (
          <div key={c.k} className={`gv-sz-ph${c.day ? ' day' : ''}`}>{c.cap}</div>
        ))}

        {/* 主星 */}
        <Row label="主星" render={c => (
          <div key={c.k} className="gv-sz-c">
            {c.day ? <span className="gv-day-em">日元</span> : (c.p.shishen_gan || '—')}
          </div>
        )} />

        {/* 天干 */}
        <Row label="天干" render={c => (
          <div key={c.k} className={`gv-sz-c gan ${WX[c.p.wuxing_gan] || ''}`}>{c.p.tiangan}</div>
        )} />

        {/* 地支 */}
        <Row label="地支" render={c => (
          <div key={c.k} className={`gv-sz-c zhi ${WX[c.p.wuxing_zhi] || ''}`}>{c.p.dizhi}</div>
        )} />

        {/* 五行标 */}
        <Row label="" render={c => (
          <div key={c.k} className="gv-sz-c">
            <span className="gv-wxg">{c.p.wuxing_gan}·{c.p.wuxing_zhi}</span>
          </div>
        )} />

        {/* 藏干 */}
        <Row label="藏干" render={c => (
          <div key={c.k} className="gv-sz-c ss">{(c.p.canggan || []).join(' ') || '—'}</div>
        )} />

        {/* 副星 */}
        <Row label="副星" render={c => (
          <div key={c.k} className="gv-sz-c">{c.p.shishen_zhi || '—'}</div>
        )} />

        {/* 纳音 */}
        <Row label="纳音" render={c => (
          <div key={c.k} className="gv-sz-c dim">{c.p.nayin || '—'}</div>
        )} />

        {/* 神煞 */}
        <Row label="神煞" render={c => {
          const names = shByPillar[c.key] || []
          return <div key={c.k} className="gv-sz-c shensha">{names.length ? names.join(' ') : '—'}</div>
        }} />
      </div>

      {/* 综断 + 五行分布 */}
      <div className="gv-verdict">
        <div className="gv-vb">
          <div className="gv-vb-h">
            {pattern && <span className="em">{pattern}</span>}
            {dm && <span> · 日主{dm}{monthZhi ? `生于${monthZhi}月` : ''}</span>}
          </div>
          {patternDesc && <p>{patternDesc}</p>}
          {tiaohouVerdict && <p style={{ marginTop:'0.5rem', color:'var(--gv-ink-3)' }}>{tiaohouVerdict}</p>}
        </div>
        <div className="gv-wx-dist">
          <div className="gv-wd-cap">五行 · 干支</div>
          {WX_ORDER.map(w => (
            <div className="gv-wd-row" key={w}>
              <span className={`nm ${WX[w]}`}>{w}</span>
              <span className="gv-wd-track">
                <span className="gv-wd-fill" style={{ width:`${(wxCount[w]/wxMax)*100}%`, background:`var(--gv-${({木:'mu',火:'huo',土:'tu',金:'jin',水:'shui'})[w]})` }} />
              </span>
              <span className="vl">{wxCount[w]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
