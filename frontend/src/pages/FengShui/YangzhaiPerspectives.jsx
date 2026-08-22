/*
 * YangzhaiPerspectives — 多视角整合解读
 * 把全部八字子模块编为六视角，每视角言明所汇子模块。
 * 体现「子模块必尽其用、几个拼成一视角」之根本逻辑。
 */
import React, { useState } from 'react'

const ACCENT = 'var(--accent)'

export default function YangzhaiPerspectives({ data }) {
  const pv = data?.perspectives
  const [active, setActive] = useState(0)
  if (!pv || !pv.available || !pv.lenses?.length) return null
  const lens = pv.lenses[active]

  return (
    <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
        <div className="card-title" style={{ margin: 0 }}>多视角整合解读</div>
        <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
          全部子模块尽汇于此·无一孤置
        </span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginBottom: '0.6rem' }}>
        {pv.lenses.map((ln, i) => (
          <button key={ln.id} onClick={() => setActive(i)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.3rem',
              padding: '0.3rem 0.6rem', cursor: 'pointer',
              fontSize: 'var(--text-xs)', fontFamily: 'var(--font-serif)',
              background: i === active ? `${ACCENT}1a` : 'var(--bg-raised)',
              color: i === active ? ACCENT : 'var(--text-muted)',
              border: `1px solid ${i === active ? 'var(--accent-dim)' : 'var(--border)'}`,
              fontWeight: i === active ? 700 : 400,
            }}>
            <span>{ln.icon}</span>{ln.title}
          </button>
        ))}
      </div>

      <div style={{ padding: '0.7rem 0.85rem', background: 'var(--bg-raised)',
        borderLeft: `2px solid ${ACCENT}` }}>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '0.45rem' }}>
          {lens.modules.map((m, i) => (
            <span key={i} style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)',
              padding: '1px 6px', border: '1px solid var(--border)', borderRadius: 'var(--r-sm)' }}>
              {m}
            </span>
          ))}
        </div>
        <p style={{ fontFamily: 'var(--font-serif)', fontSize: 'var(--text-base)', lineHeight: 1.9,
          color: 'var(--text-secondary)', margin: 0 }}>
          {lens.text}
        </p>
      </div>

      <div style={{ marginTop: '0.5rem', fontSize: 'var(--text-2xs)', color: 'var(--text-faint)',
        fontFamily: 'var(--font-serif)' }}>
        六视角各执一隅，合参方见全宅——每一视角即数子模块拼合之一种观照。
      </div>
    </div>
  )
}
