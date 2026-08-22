/*
 * LiuyaoYongShenSynthesis — 用神力量综合评估·推理链
 * 显式呈现各子模块（旺衰/动变/三合/空破墓/四位）如何汇于用神一身、
 * 互相辅助，合成综合力量判断。把「模块间的关系」从隐性变为可见。
 */
import React from 'react'

const POL_COLOR = { 利: '#27ae60', 害: '#c0392b', 中: 'var(--text-muted)' }
const POL_BG = { 利: 'rgba(39,174,96,0.07)', 害: 'rgba(192,57,43,0.07)', 中: 'var(--bg-raised)' }

const LABEL_COLOR = {
  综合大有力: '#27ae60', 综合有力: '#2e9e6b',
  综合中和: 'var(--accent)', 综合无力: '#c0392b',
}

export default function LiuyaoYongShenSynthesis({ data }) {
  const s = data?.yongshen_strength
  if (!s || !s.available) return null
  const compColor = LABEL_COLOR[s.composite_label] || 'var(--accent)'

  return (
    <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.6rem' }}>
        <div className="card-title" style={{ margin: 0 }}>用神力量综合评估 · 推理链</div>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          诸模块汇于用神一身
        </span>
      </div>

      {/* 综合结论条 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap',
        padding: '0.55rem 0.85rem', marginBottom: '0.7rem',
        background: `${compColor}12`, borderLeft: `3px solid ${compColor}` }}>
        <span style={{ fontFamily: 'var(--font-serif)', color: 'var(--text-secondary)', fontSize: 'var(--text-sm)' }}>
          用神{s.yong_liuqin}{s.yong_branch}
        </span>
        <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
          基力{s.base_force >= 0 ? '+' : ''}{s.base_force}
        </span>
        <span style={{ color: 'var(--text-faint)' }}>→</span>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: compColor,
          fontSize: 'var(--text-lg)' }}>
          {s.composite_label}
        </span>
        <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
          综合力{s.composite_force >= 0 ? '+' : ''}{s.composite_force}
        </span>
      </div>

      {/* 推理链：用神 → 各模块修正 → 综合 */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'stretch', gap: '0.4rem' }}>
        <Node label="用神" main={`${s.yong_liuqin}${s.yong_branch}`}
          sub={`基力${s.base_force >= 0 ? '+' : ''}${s.base_force}`} color="var(--accent)" />
        {s.factors.filter(f => !f.source.startsWith('旺衰')).map((f, i) => (
          <React.Fragment key={i}>
            <Arrow w={f.weight} />
            <Factor f={f} />
          </React.Fragment>
        ))}
        <Arrow w={0} terminal />
        <Node label="综合" main={s.composite_label.replace('综合', '')}
          sub={`${s.composite_force >= 0 ? '+' : ''}${s.composite_force}`} color={compColor} strong />
      </div>

      {/* 月日基力构成（旺衰来源） */}
      {s.factors.some(f => f.source.startsWith('旺衰')) && (
        <div style={{ marginTop: '0.6rem', fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
          基力来源（旺衰·月日令）：
          {s.factors.filter(f => f.source.startsWith('旺衰')).map((f, i) => (
            <span key={i} style={{ color: POL_COLOR[f.polarity], marginLeft: 4 }}>{f.label}</span>
          ))}
        </div>
      )}

      <div style={{ marginTop: '0.6rem', fontFamily: 'var(--font-serif)', fontSize: 'var(--text-sm)',
        color: 'var(--text-secondary)', lineHeight: 1.75 }}>
        {s.composite_desc}。
      </div>
      {s.structural && (
        <div style={{ marginTop: '0.35rem', fontSize: 'var(--text-xs)', color: 'var(--accent)',
          fontFamily: 'var(--font-serif)' }}>◆ {s.structural}</div>
      )}
    </div>
  )
}

function Node({ label, main, sub, color, strong }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '0.4rem 0.6rem', minWidth: '64px',
      background: strong ? `${color}18` : 'var(--bg-raised)',
      border: `1px solid ${color}${strong ? '' : '55'}` }}>
      <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color, fontSize: 'var(--text-sm)' }}>{main}</span>
      <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-muted)' }}>{sub}</span>
    </div>
  )
}

function Factor({ f }) {
  const col = POL_COLOR[f.polarity]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center',
      padding: '0.35rem 0.55rem', maxWidth: '230px',
      background: POL_BG[f.polarity], borderLeft: `2px solid ${col}` }}>
      <span style={{ fontSize: 'var(--text-2xs)', color: col, fontWeight: 700 }}>
        〔{f.source}〕{f.weight > 0 ? '＋' : f.weight < 0 ? '－' : '·'}
      </span>
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.5 }}>{f.label}</span>
    </div>
  )
}

function Arrow({ w, terminal }) {
  const col = terminal ? 'var(--text-faint)' : w > 0 ? '#27ae60' : w < 0 ? '#c0392b' : 'var(--text-faint)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', color: col, fontSize: 'var(--text-sm)' }}>
      {terminal ? '⟹' : '→'}
    </div>
  )
}
