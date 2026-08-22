/*
 * QimenSynthesis — 用神力量综合推理链
 * 显式呈现各子模块（日主旺衰/格局成破/用神调候/刑冲）如何汇成命局综合评定，
 * 互相辅助。把「模块间的关系」从隐性变为可见——分析路径全显。
 */
import React from 'react'

const POL_COLOR = { 利: '#27ae60', 害: '#c0392b', 中: 'var(--text-muted)' }
const POL_BG = { 利: 'rgba(39,174,96,0.07)', 害: 'rgba(192,57,43,0.07)', 中: 'var(--bg-raised)' }
const POL_SIGN = { 利: '＋', 害: '－', 中: '·' }

const LABEL_COLOR = {
  用神大有力: '#27ae60', 用神有力: '#2e9e6b',
  用神中平: 'var(--accent)', 用神乏力: '#d4880a', 用神受制: '#c0392b',
}

export default function QimenSynthesis({ data }) {
  const s = data?.yongshen_synthesis
  if (!s || !s.available) return null
  const compColor = LABEL_COLOR[s.composite_label] || 'var(--accent)'

  return (
    <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
        <div className="card-title" style={{ margin: 0 }}>用神力量综合 · 推理链</div>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          诸模块汇成用神评定
        </span>
      </div>

      {/* 综合结论条 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
        padding: '0.55rem 0.85rem', marginBottom: '0.7rem',
        background: `${compColor}12`, borderLeft: `3px solid ${compColor}` }}>
        <span style={{ fontFamily: 'var(--font-serif)', color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
          所问{s.topic} · 用神落{s.yongshen_palace}
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

      {/* 因子流：每子模块如何汇入 */}
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

      {/* 推理链一行式 */}
      <div style={{ marginTop: '0.6rem', padding: '0.5rem 0.7rem', background: 'var(--bg-raised)',
        fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)',
        lineHeight: 1.85, borderRadius: 'var(--r-sm)' }}>
        {s.chain_text}
      </div>
    </div>
  )
}
