/*
 * components/UI/Primitives.jsx
 * 共享表现层组件库 —— 收敛各占测模块重复的卡片/网格/标签/断语结构，
 * 消除散落各页的上千处内联样式，统一视觉与维护。
 *
 * 设计原则：
 *   · 纯表现、无业务逻辑，props 即数据。
 *   · 配合 index.css 工具类（.serif/.prose/.chip/.role-cell/.detail-box…）。
 *   · 吉凶极性着色统一由 polarityColor() 决定。
 */
import React from 'react'
import { clickable } from '../../utils/a11y'

// ── 吉凶极性 → 颜色 ──
export const POLARITY = {
  吉: '#27ae60', 偏吉: '#27ae60',
  凶: '#c0392b', 偏凶: '#c0392b', 大凶: '#c0392b',
  中: 'var(--accent)', 平: 'var(--accent)', 待: 'var(--text-muted)',
}
export function polarityColor(p = '') {
  if (p.includes('吉')) return '#27ae60'
  if (p.includes('凶')) return '#c0392b'
  return 'var(--accent)'
}
export function polarityBg(p = '') {
  if (p.includes('吉')) return 'rgba(39,174,96,0.12)'
  if (p.includes('凶')) return 'rgba(192,57,43,0.12)'
  return 'var(--accent-bg)'
}

// ── 带标题的卡片 ──
export function SectionCard({ title, extra, children, glow, style, className = '' }) {
  return (
    <div className={`card ${glow ? 'card-glow' : ''} ${className}`} style={style}>
      {(title || extra) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.7rem' }}>
          {title && <div className="card-title" style={{ margin: 0 }}>{title}</div>}
          {extra}
        </div>
      )}
      {children}
    </div>
  )
}

// ── 着色小标签 ──
export function Chip({ children, color = 'var(--accent)', bg, tone, style }) {
  const c = tone ? polarityColor(tone) : color
  const b = bg || (tone ? polarityBg(tone) : `${typeof c === 'string' && c.startsWith('#') ? c + '22' : 'var(--accent-bg)'}`)
  return (
    <span className="chip" style={{ color: c, background: b, ...style }}>{children}</span>
  )
}

// ── 极性结论徽章 ──
export function VerdictBadge({ conclusion, confidence }) {
  const c = polarityColor(conclusion)
  return (
    <span className="badge serif fw7" style={{ background: polarityBg(conclusion), color: c }}>
      {conclusion}{confidence ? ` · 信心${confidence}` : ''}
    </span>
  )
}

/*
 * 断语卡：标题 + 极性徽章 + （可选）总览横幅 + 主断语 + （可选）理由链
 * props: title, conclusion, confidence, banner, verdict, reasons[], polarity, children
 */
export function VerdictCard({ title, conclusion, confidence, banner, verdict,
                             reasons, polarity, children, glow }) {
  const pol = polarity || conclusion || ''
  const col = polarityColor(pol)
  return (
    <div className={`card ${glow ? 'card-glow' : ''}`}
      style={{ border: `1.5px solid ${col === 'var(--accent)' ? 'var(--accent-dim)' : col + '66'}` }}>
      {(title || conclusion) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.7rem' }}>
          {title && <div className="card-title" style={{ margin: 0 }}>{title}</div>}
          {conclusion && <VerdictBadge conclusion={conclusion} confidence={confidence} />}
        </div>
      )}
      {banner && (
        <div className="verdict-banner" style={{
          background: 'linear-gradient(135deg, var(--accent-bg), transparent)',
          borderLeft: `3px solid ${col}`, marginBottom: '0.7rem',
          color: 'var(--text-primary)' }}>
          {banner}
        </div>
      )}
      {verdict && (
        <div className="verdict-banner" style={{
          background: polarityBg(pol), border: `1px solid ${col === 'var(--accent)' ? 'var(--accent-dim)' : col + '44'}`,
          color: 'var(--text-primary)', marginBottom: reasons?.length ? '0.6rem' : 0 }}>
          {verdict}
        </div>
      )}
      {reasons?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          {reasons.map((r, i) => (
            <div key={i} className="reason-row t-sm secondary">
              <span style={{ color: 'var(--accent-dim)' }}>{i + 1}.</span>
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}
      {children}
    </div>
  )
}

/*
 * 角色/状态网格：四位（用神/原神/忌神/仇神）、生年四化等
 * props: cols, items[{label, labelColor, value, sub, dim}]
 */
export function RoleGrid({ cols = 4, items = [] }) {
  return (
    <div className="role-grid" style={{ gridTemplateColumns: `repeat(${cols},1fr)` }}>
      {items.map((it, i) => (
        <div key={i} className="role-cell" style={it.borderColor ? { borderColor: it.borderColor + '33' } : undefined}>
          <div className="t-xs fw7" style={{ color: it.labelColor || 'var(--accent)', marginBottom: '2px' }}>{it.label}</div>
          {it.value != null ? (
            <>
              <div className="serif t-sm" style={{ color: 'var(--text-primary)' }}>{it.value}</div>
              {it.sub && <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginTop: '2px' }}>{it.sub}</div>}
            </>
          ) : (
            <div className="faint" style={{ fontSize: '0.62rem', marginTop: '4px' }}>{it.dim || '—'}</div>
          )}
        </div>
      ))}
    </div>
  )
}

/*
 * 可选网格：点击单元展开详情
 * props: items[], minWidth, selected, onSelect, renderCell(item,i,isSel), renderDetail(item,i)
 */
export function SelectableGrid({ items = [], minWidth = 100, gap = '0.4rem',
                                selected, onSelect, renderCell, renderDetail }) {
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(auto-fill,minmax(${minWidth}px,1fr))`, gap }}>
        {items.map((it, i) => (
          <div key={i} className="sel-cell" {...clickable(() => onSelect(selected === i ? null : i))}>
            {renderCell(it, i, selected === i)}
          </div>
        ))}
      </div>
      {selected != null && items[selected] && renderDetail && (
        <div style={{ marginTop: '0.8rem' }}>{renderDetail(items[selected], selected)}</div>
      )}
    </>
  )
}

// ── 标签-值行 ──
export function KVRow({ label, value, color }) {
  return (
    <div className="info-row">
      <span className="info-row-icon">◈</span>
      <span className="t-sm"><span className="muted">{label}：</span>
        <span style={{ color: color || 'var(--text-primary)' }}>{value}</span></span>
    </div>
  )
}
