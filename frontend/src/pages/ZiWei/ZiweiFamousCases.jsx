/**
 * ZiweiFamousCases.jsx — 名人命例选择器
 *
 * 在排盘前的输入区下方提供 8 个经典命例的快速导入按钮。
 * 点击后自动填充表单并触发排盘。
 */
import React, { useState } from 'react'
import { FAMOUS_CASES, groupCasesByCategory } from './famousCases'

export default function ZiweiFamousCases({ onSelect }) {
  const [open, setOpen] = useState(false)
  const groups = groupCasesByCategory()

  return (
    <div className="card" style={{ padding: '0.5rem' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%',
          padding: '0.5rem',
          border: 'none',
          background: 'transparent',
          color: 'var(--accent)',
          fontFamily: 'var(--font-serif)',
          fontSize: 'var(--text-sm)',
          fontWeight: 700,
          cursor: 'pointer',
          textAlign: 'left',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
        <span>📖 名人命例库 · {FAMOUS_CASES.length} 例</span>
        <span style={{ fontSize:'var(--text-xs)', color: 'var(--text-muted)' }}>{open ? '▼' : '▶'}</span>
      </button>
      
      {open && (
        <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {Object.entries(groups).map(([category, cases]) => (
            <div key={category}>
              <div style={{
                fontSize:'var(--text-2xs)',
                color: 'var(--text-faint)',
                marginBottom: '0.25rem',
                letterSpacing: '0.05em',
                fontFamily: 'var(--font-serif)',
              }}>
                ── {category} ──
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {cases.map(c => (
                  <button
                    key={c.id}
                    onClick={() => { onSelect?.(c); setOpen(false) }}
                    style={{
                      padding: '0.4rem 0.6rem',
                      border: '1px solid var(--border)',
                      background: 'var(--bg-card)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.12s',
                      fontFamily: 'var(--font-serif)',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = 'var(--bg-subtle)'
                      e.currentTarget.style.borderColor = 'var(--accent)'
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = 'var(--bg-card)'
                      e.currentTarget.style.borderColor = 'var(--border)'
                    }}
                  >
                    <div style={{ fontWeight: 700, fontSize:'var(--text-xs)', color: 'var(--text-primary)' }}>
                      {c.name}
                    </div>
                    <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', marginTop: '1px' }}>
                      {c.desc}
                    </div>
                    {c.highlights && (
                      <div style={{ fontSize:'var(--text-2xs)', color: 'var(--accent)', marginTop: '2px',
                        display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {c.highlights.slice(0, 2).map((h, i) => (
                          <span key={i} style={{
                            background: 'rgba(207,59,44,0.08)',
                            padding: '1px 4px',
                            border: '1px solid var(--accent-dim, rgba(207,59,44,0.3))',
                          }}>{h}</span>
                        ))}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          ))}
          
          <div style={{
            marginTop: '0.4rem',
            padding: '0.4rem',
            fontSize:'var(--text-2xs)',
            color: 'var(--text-faint)',
            background: 'var(--bg-subtle)',
            border: '1px dashed var(--border)',
            fontFamily: 'var(--font-serif)',
            lineHeight: 1.5,
          }}>
            ⚠ 命例数据仅供学术研究与排盘学习用，历史人物生辰多有争议，<br/>
            实际占断请以可靠出生证明为准
          </div>
        </div>
      )}
    </div>
  )
}
