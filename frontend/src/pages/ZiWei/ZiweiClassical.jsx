/*
 * ZiweiClassical — 传统断语 · 古籍精要
 * 呈命宫主星《紫微斗数全书》多层深度释义 + 格局典籍。
 */
import React from 'react'

export default function ZiweiClassical({ data }) {
  const cs = data?.classical_statements
  if (!cs || !cs.available || !cs.statements?.length) return null

  return (
    <div className="card" style={{ borderLeft: '3px solid var(--accent-dim)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
        <div className="card-title" style={{ margin: 0 }}>传统断语 · 古籍精要</div>
        <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
          {cs.count} 则 · 据《紫微斗数全书》
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {cs.statements.map((s, i) => (
          <div key={i} style={{ padding: '0.45rem 0.65rem', background: 'var(--bg-raised)',
            borderLeft: '2px solid var(--accent-dim)' }}>
            <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'baseline',
              flexWrap: 'wrap', marginBottom: '0.2rem' }}>
              <span style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--accent)',
                fontFamily: 'var(--font-serif)' }}>{s.title}</span>
              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
                {s.source}·{s.topic}
              </span>
            </div>
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.85 }}>{s.text}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
