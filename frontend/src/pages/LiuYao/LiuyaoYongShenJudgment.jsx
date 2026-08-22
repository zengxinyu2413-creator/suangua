/*
 * LiuyaoYongShenJudgment — 用神落爻多维断
 * 现伏×旺衰×动静化象×空破墓×元神×忌神×世应 七维具体断 + 综合成败。
 * 数据源 data.yongshen_judgment（处理用神现/伏两态）。
 */
import React from 'react'

const POL_COLOR = { 利: '#27ae60', 害: '#c0392b', 中: 'var(--text-muted)' }
const LEVEL_COLOR = { auspicious: '#27ae60', inauspicious: '#c0392b', neutral: 'var(--accent)' }
const LEVEL_LABEL = { auspicious: '成', inauspicious: '阻', neutral: '参半' }

export default function LiuyaoYongShenJudgment({ data }) {
  const j = data?.yongshen_judgment
  if (!j || !j.available) return null
  const lvColor = LEVEL_COLOR[j.verdict_level] || 'var(--accent)'

  return (
    <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
        <div className="card-title" style={{ margin: 0 }}>用神落爻 · 多维断</div>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          用神{j.yong_shen_name}（{j.present_state}）
        </span>
      </div>

      {/* 综合成败条 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap',
        padding: '0.55rem 0.85rem', marginBottom: '0.7rem',
        background: `${lvColor}12`, borderLeft: `3px solid ${lvColor}` }}>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: lvColor,
          fontSize: 'var(--text-sm)' }}>{LEVEL_LABEL[j.verdict_level] || ''}</span>
        <span style={{ fontFamily: 'var(--font-serif)', color: 'var(--text-secondary)',
          fontSize: 'var(--text-sm)', lineHeight: 1.7 }}>{j.verdict}</span>
      </div>

      {/* 七维 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {(j.dimensions || []).map((d, i) => (
          <div key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
            padding: '0.45rem 0.6rem', background: 'var(--bg-subtle)', borderRadius: 'var(--r-sm)' }}>
            <span style={{ flexShrink: 0, fontSize: 'var(--text-2xs)', fontWeight: 700,
              color: POL_COLOR[d.polarity] || 'var(--text-muted)', minWidth: '4.2em' }}>
              {d.dim}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.7 }}>{d.text}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
