/*
 * ZiweiMinggeSynthesis — 命格力量综合 · 推理链
 * 显式呈现各子模块（命宫主星/三方四正/格局/煞星/四化）如何汇成命格综合评定。
 */
import React from 'react'

const POL_COLOR = { 利: '#27ae60', 害: '#c0392b', 中: 'var(--text-muted)' }
const POL_BG = { 利: 'rgba(39,174,96,0.07)', 害: 'rgba(192,57,43,0.07)', 中: 'var(--bg-raised)' }
const POL_SIGN = { 利: '＋', 害: '－', 中: '·' }

const LABEL_COLOR = {
  命格上乘: '#27ae60', 命格中上: '#2e9e6b',
  命格中平: 'var(--accent)', 命格偏弱: '#d4880a', 命格受损: '#c0392b',
}

export default function ZiweiMinggeSynthesis({ data }) {
  const s = data?.mingge_synthesis
  if (!s || !s.available) return null
  const compColor = LABEL_COLOR[s.composite_label] || 'var(--accent)'

  return (
    <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
        <div className="card-title" style={{ margin: 0 }}>命格力量综合 · 推理链</div>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          诸模块汇成命格评定
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
        padding: '0.55rem 0.85rem', marginBottom: '0.7rem',
        background: `${compColor}12`, borderLeft: `3px solid ${compColor}` }}>
        <span style={{ fontFamily: 'var(--font-serif)', color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
          {s.ming_branch}命 · 评等{s.rating}
        </span>
        <span style={{ color: 'var(--text-faint)' }}>→</span>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: compColor,
          fontSize: 'var(--text-lg)' }}>
          {s.composite_label}
        </span>
        <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
          综合力{s.composite_score >= 0 ? '+' : ''}{s.composite_score}
        </span>
      </div>

      <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.7, marginBottom: '0.7rem' }}>
        {s.composite_desc}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {s.factors.map((f, i) => {
          const col = POL_COLOR[f.polarity] || 'var(--text-muted)'
          return (
            <div key={i} style={{ display: 'flex', gap: '0.55rem', alignItems: 'flex-start',
              padding: '0.4rem 0.6rem', background: POL_BG[f.polarity] || 'var(--bg-raised)',
              borderLeft: `2px solid ${col}` }}>
              <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)', flexShrink: 0,
                minWidth: '4.2em', paddingTop: '0.1rem' }}>〔{f.module}〕</span>
              <span style={{ color: col, fontWeight: 700, fontSize: 'var(--text-sm)', flexShrink: 0 }}>
                {POL_SIGN[f.polarity]} {f.factor}
              </span>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.6 }}>{f.note}</span>
            </div>
          )
        })}
      </div>

      <div style={{ marginTop: '0.6rem', padding: '0.5rem 0.7rem', background: 'var(--bg-raised)',
        fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)',
        lineHeight: 1.85, borderRadius: 'var(--r-sm)' }}>
        {s.chain_text}
      </div>
    </div>
  )
}
