/*
 * DateOverview — 选期总论 · 定盘
 * 综合总论层（hero化）：吉日数 + 首选吉日第一眼即见，下接逐节详论。
 */
import React from 'react'

const QC = { 吉: '#27ae60', 中: '#e67e22', 凶: '#c0392b' }

export default function DateOverview({ data }) {
  const ov = data?.overview
  if (!ov || !ov.available) return null
  const pc = QC[ov.quality] || '#7f8c8d'

  return (
    <div className="card card-glow" style={{ borderTop: `3px solid ${pc}` }}>
      <div className="card-title">选期总论 · 定盘</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', flexWrap: 'wrap',
        padding: '0.7rem 0.9rem', marginBottom: '0.75rem',
        background: `${pc}14`, borderLeft: `4px solid ${pc}` }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-2xl)',
            fontWeight: 700, color: pc, lineHeight: 1 }}>{ov.good_count}</div>
          <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)', marginTop: 2 }}>本月吉日</div>
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 'var(--text-md)',
            color: 'var(--text-primary)', fontWeight: 600 }}>
            择「{ov.purpose}」· 首选 {ov.top_date}（{ov.top_ganzhi}）
          </div>
          {ov.top_score !== '' && (
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              首选日评分 <b style={{ color: pc }}>{ov.top_score}</b>
            </div>
          )}
          {ov.verdict_line && (
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.6, marginTop: '0.35rem' }}>
              {ov.verdict_line}
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
        {ov.paragraphs.filter(p => p.title !== '选期总评').map((p, i) => (
          <p key={i} style={{ fontFamily: 'var(--font-serif)', fontSize: 'var(--text-base)',
            lineHeight: 1.95, color: 'var(--text-secondary)', margin: 0 }}>
            <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{p.title}　</span>
            {p.text}
          </p>
        ))}
      </div>
    </div>
  )
}
