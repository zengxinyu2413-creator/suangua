/*
 * ZiweiOverview — 命盘总论 · 定盘
 * 综合总论层（hero化）：命格评等 + 命宫主星第一眼即见，下接逐节详论。
 */
import React from 'react'

const QC = { 吉: '#27ae60', 中: 'var(--accent)', 凶: '#c0392b' }

export default function ZiweiOverview({ data }) {
  const ov = data?.overview
  if (!ov || !ov.available) return null
  const pc = QC[ov.quality] || 'var(--accent)'

  return (
    <div className="card card-glow" style={{ borderTop: `3px solid ${pc}` }}>
      <div className="card-title">命盘总论 · 定盘</div>

      {/* 命格定盘·第一眼即见 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', flexWrap: 'wrap',
        padding: '0.7rem 0.9rem', marginBottom: '0.75rem',
        background: `${pc}10`, borderLeft: `4px solid ${pc}` }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)',
            fontWeight: 700, color: pc, lineHeight: 1.1 }}>{ov.rating}</div>
          <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)', marginTop: 2 }}>命格</div>
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 'var(--text-md)',
            color: 'var(--text-primary)', fontWeight: 600 }}>
            {ov.ming_branch}宫立命 · {ov.ming_stars}
          </div>
          <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.3rem', flexWrap: 'wrap',
            fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
            {ov.top_pattern && <span style={{ color: pc }}>格局 <b>{ov.top_pattern}</b></span>}
            <span>命主{ov.soul_star} · 身主{ov.body_star}</span>
            <span>{ov.five_elements}</span>
          </div>
          {ov.verdict_line && (
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.6, marginTop: '0.35rem' }}>
              {ov.verdict_line}
            </div>
          )}
        </div>
      </div>

      {/* 逐节详论（去命格总评，已上提 hero） */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
        {ov.paragraphs.filter(p => p.title !== '命格总评').map((p, i) => (
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
