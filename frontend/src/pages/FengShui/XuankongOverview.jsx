/*
 * XuankongOverview — 宅运总论 · 定盘
 * 综合总论层（hero化）：山向格局（旺山旺向/上山下水）+ 吉凶等第第一眼即见。
 */
import React from 'react'

const QC = { 吉: '#27ae60', 中: '#e67e22', 凶: '#c0392b' }

export default function XuankongOverview({ data }) {
  const ov = data?.overview
  if (!ov || !ov.available) return null
  const pc = QC[ov.quality] || '#7f8c8d'

  return (
    <div className="card card-glow" style={{ borderTop: `3px solid ${pc}`, marginBottom: '1rem' }}>
      <div className="card-title">宅运总论 · 定盘</div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.9rem', flexWrap: 'wrap',
        padding: '0.7rem 0.9rem', marginBottom: '0.75rem',
        background: `${pc}14`, borderLeft: `4px solid ${pc}` }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-xl)',
            fontWeight: 700, color: pc, lineHeight: 1.1, whiteSpace: 'nowrap' }}>{ov.verdict}</div>
          <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)', marginTop: 2 }}>山向格局</div>
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 'var(--text-md)',
            color: 'var(--text-primary)', fontWeight: 600 }}>
            {ov.sitting}山{ov.facing}向 · {ov.yun_name}运
          </div>
          {ov.verdict_line && (
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.6, marginTop: '0.35rem' }}>
              {ov.verdict_line}
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
        {ov.paragraphs.filter(p => p.title !== '宅运总评').map((p, i) => (
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
