/*
 * HouseReportPanel — 统一宅报告（理气 × 形法 合断）
 * 玄空飞星(理气)定旺衰 × 阳宅三要(形法)定门主灶，交叉合断同一栋房。
 */
import React, { useState } from 'react'

const GUA8 = ['坎', '坤', '震', '巽', '乾', '兑', '艮', '离']
const SHAN24 = ['壬', '子', '癸', '丑', '艮', '寅', '甲', '卯', '乙', '辰', '巽', '巳',
  '丙', '午', '丁', '未', '坤', '申', '庚', '酉', '辛', '戌', '乾', '亥']
const QC = { 吉: '#27ae60', 中: '#e67e22', 凶: '#c0392b' }

const getApiBase = () => {
  try { return JSON.parse(localStorage.getItem('bagua-settings') || '{}')?.state?.apiBaseUrl ?? '' }
  catch { return '' }
}

export default function HouseReportPanel() {
  const [sitting, setSitting] = useState('子')
  const [men, setMen] = useState('坎')
  const [zhu, setZhu] = useState('巽')
  const [zao, setZao] = useState('震')
  const [birthYear, setBirthYear] = useState('1990')
  const [gender, setGender] = useState('male')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const run = async () => {
    setLoading(true)
    try {
      const body = { sitting_mountain: sitting, year: 2026, men, zhu, zao }
      if (birthYear && parseInt(birthYear) > 1900) { body.birth_year = parseInt(birthYear); body.gender = gender }
      const r = await fetch(getApiBase() + '/api/v1/fengshui/house_report', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      })
      const j = await r.json()
      setData(j.data || j)
    } catch { setData(null) } finally { setLoading(false) }
  }

  const sel = (val, set, opts) => (
    <select value={val} onChange={e => set(e.target.value)} style={{ padding: '5px 8px', fontSize: '0.78rem',
      borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }}>
      {opts.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="card">
        <div className="card-title">理气 × 形法 — 统一宅报告</div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-faint)', marginBottom: '0.7rem' }}>
          玄空飞星(理气)定各方旺衰 × 阳宅三要(形法)定门主灶，交叉合断：门主灶是否落当运旺方。
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>坐山<br />{sel(sitting, setSitting, SHAN24)}</label>
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>门<br />{sel(men, setMen, GUA8)}</label>
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>主<br />{sel(zhu, setZhu, GUA8)}</label>
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>灶<br />{sel(zao, setZao, GUA8)}</label>
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>主人生年<br />
            <input type="number" value={birthYear} onChange={e => setBirthYear(e.target.value)}
              style={{ width: '78px', padding: '5px 8px', fontSize: '0.78rem', borderRadius: 'var(--r-sm)',
                border: '1px solid var(--border)', background: 'var(--bg-subtle)' }} /></label>
          <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>性别<br />{sel(gender, setGender, ['male', 'female'])}</label>
          <button className="btn-primary" onClick={run} disabled={loading}
            style={{ padding: '6px 16px' }}>{loading ? '合断中…' : '合断'}</button>
        </div>
      </div>

      {data && data.available && (
        <>
          <div className="card card-glow" style={{ borderTop: `3px solid ${QC[data.unified_quality] || '#7f8c8d'}` }}>
            <div className="card-title">理气形法 · 合断</div>
            <div style={{ fontFamily: 'var(--font-serif)', fontSize: 'var(--text-md)', fontWeight: 600, marginBottom: '0.5rem' }}>
              {data.house_type} · 理气[<span style={{ color: 'var(--accent)' }}>{data.liqi_verdict}</span>]
              × 形法[<span style={{ color: 'var(--accent)' }}>{data.xingfa_grade}</span>]
              {data.mingua_match && <> · 命卦[<span style={{ color: QC[data.unified_quality] }}>{data.mingua_match.match_level}</span>]</>}
            </div>
            <div style={{ fontFamily: 'var(--font-serif)', fontSize: 'var(--text-base)', lineHeight: 1.8,
              color: 'var(--text-secondary)', padding: '0.6rem 0.8rem', background: `${QC[data.unified_quality] || '#7f8c8d'}12`,
              borderLeft: `4px solid ${QC[data.unified_quality] || '#7f8c8d'}` }}>
              {data.unified_verdict}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-faint)', marginTop: '0.5rem' }}>
              当运旺方：{(data.wang_directions || []).join('、')}　|　衰方：{(data.shuai_directions || []).join('、')}
            </div>
          </div>

          <div className="card">
            <div className="card-title">门主灶 · 理气×形法交叉</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {(data.cross_items || []).map((it, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.7rem', flexWrap: 'wrap',
                  padding: '0.5rem 0.7rem', background: 'var(--bg-subtle)', borderRadius: 'var(--r-sm)',
                  borderLeft: `3px solid ${QC[it.combine_q] || '#7f8c8d'}` }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'var(--text-md)' }}>
                    {it.role}<span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-faint)', marginLeft: 3 }}>{it.direction}</span>
                  </span>
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
                    理气<b style={{ color: it.liqi === '旺' ? '#27ae60' : it.liqi === '衰' ? '#c0392b' : '#888' }}>{it.liqi}</b>
                    × 形法<b style={{ color: QC[it.xingfa] || '#888' }}>{it.xingfa}</b>（{it.xingfa_label}）
                  </span>
                  <span style={{ fontFamily: 'var(--font-serif)', fontWeight: 600, color: QC[it.combine_q] }}>→ {it.combine}</span>
                  <span style={{ flexBasis: '100%', fontSize: 'var(--text-xs)', color: 'var(--text-faint)',
                    fontFamily: 'var(--font-serif)' }}>{it.note}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
