/**
 * ZiweiInsightsBar.jsx
 * ========================
 * 紫微命盘洞察栏 — 把后端 /chart 返回的 insights 字段渲染为 4 个卡片：
 *   1. 整体命格评级徽章（上格/中格等 + 分数）
 *   2. 经典格局徽章组（吉格绿 / 凶格红，可点击展开）
 *   3. 飞化关键警示卡（双忌叠加 / 化忌冲命 等）
 *   4. 命宫三方四正亮度评级简表
 *
 * 设计原则：
 *   · 全部基于 insights 字段，原生 React 状态管理 useState 展开/收起
 *   · 没有 insights 字段则不渲染（向后兼容）
 *   · 颜色与现有 BRIGHT_COLOR 体系保持一致
 *   · 信息密度优先，不堆装饰
 */
import React, { useState } from 'react'
import '../../styles/plates.css'
import { clickable } from '../../utils/a11y'

// 评级 → 朱印底色（保留原有语义色，仅用于印章底色而非大片背景）
const RATING_SEAL = {
  '上格':   '#cf3b2c',
  '中上格': '#cf3b2c',
  '中格':   '#8a8475',
  '中下格': '#c1953a',
  '下格':   '#8a8475',
}

// 评级 → 颜色（与命理传统色调一致：上格金色，下格红）
const RATING_COLOR = {
  '上格':   '#c8a04a',  // 金
  '中上格': '#7fb069',  // 浅绿
  '中格':   '#7f8c8d',  // 灰
  '中下格': '#e67e22',  // 橙
  '下格':   '#e74c3c',  // 红
}

// 亮度 → 颜色（与 ZiWeiPage.BRIGHT_COLOR 一致）
const BRIGHT_COLOR = {
  '庙': '#c8a04a', '旺': '#f39c12', '得': '#3498db',
  '利': '#27ae60', '平': '#7f8c8d', '不': '#e67e22', '陷': '#e74c3c',
}

// ─────────────────────────────────────────────────────────
// 1. 命格评级徽章
// ─────────────────────────────────────────────────────────
function RatingBadge({ rating }) {
  if (!rating || !rating.overall) return null
  const sealColor = RATING_SEAL[rating.overall] || 'var(--gv-vermilion)'
  const scoreStr = rating.score >= 0 ? `+${rating.score.toFixed(2)}` : rating.score.toFixed(2)
  return (
    <div className="gv-plate">
      <div className="gv-zw-hero">
        <div className="gv-grade-seal" style={{ background: sealColor }}>
          <span className="gg">{rating.overall}</span>
          <span className="gs">命格</span>
        </div>
        <div className="txt">
          <div className="sc">
            亮度评分 {scoreStr}
            {rating.soul_rating && rating.soul_stars?.length > 0 && (
              <span> · 命宫 {rating.soul_stars.join('/')} → {rating.soul_rating}</span>
            )}
          </div>
          <div className="sm">{rating.summary}</div>
          {((rating.bright_in_sfsz?.length || 0) > 0 || (rating.fallen_in_sfsz?.length || 0) > 0) && (
            <div className="tags">
              {(rating.bright_in_sfsz?.length || 0) > 0 && (
                <span className="good">庙旺 · {rating.bright_in_sfsz.join('、')}</span>
              )}
              {(rating.fallen_in_sfsz?.length || 0) > 0 && (
                <span className="bad">失陷 · {rating.fallen_in_sfsz.join('、')}</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 2. 经典格局徽章组
// ─────────────────────────────────────────────────────────
function PatternsCard({ patterns }) {
  const [expanded, setExpanded] = useState(null)  // 当前展开的格局名
  if (!patterns || (!patterns.good?.length && !patterns.bad?.length)) {
    return null  // 无格局则不显示
  }

  const renderBadge = (p, isBad) => {
    const isOpen = expanded === p.name
    const color = isBad ? '#e74c3c' : '#7fb069'
    const bg = isBad ? 'rgba(231,76,60,0.08)' : 'rgba(127,176,105,0.08)'
    return (
      <span
        key={p.name}
        {...clickable(() => setExpanded(isOpen ? null : p.name), { label:`${p.name} 格局详情` })}
        style={{
          padding: '3px 9px',
          background: bg,
          color, fontSize: 'var(--text-xs)', fontWeight: 600,
          border: `1px solid ${color}`,
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        {isBad ? '⚠ ' : '◆ '}{p.name}
        {p.is_partial && '*'}
      </span>
    )
  }

  // 找到当前展开的格局
  const allPatterns = [
    ...(patterns.good || []).map(p => ({ ...p, _isBad: false })),
    ...(patterns.bad || []).map(p => ({ ...p, _isBad: true })),
  ]
  const expandedPattern = allPatterns.find(p => p.name === expanded)

  return (
    <div className="card" style={{ padding: '0.75rem 1rem' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.45rem' }}>
        经典格局检测 · 共 {patterns.total} 个（吉 {patterns.good?.length || 0} / 凶 {patterns.bad?.length || 0}）
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
        {(patterns.good || []).map(p => renderBadge(p, false))}
        {(patterns.bad  || []).map(p => renderBadge(p, true))}
      </div>
      {expandedPattern && (
        <div style={{
          marginTop: '0.6rem', paddingTop: '0.5rem',
          borderTop: '1px solid var(--border)',
          fontSize: 'var(--text-sm)', lineHeight: 1.55,
        }}>
          <div style={{ color: expandedPattern._isBad ? '#e74c3c' : 'var(--jade)', fontWeight: 700, marginBottom: '0.25rem' }}>
            {expandedPattern.name}
          </div>
          {expandedPattern.evidence?.length > 0 && (
            <div style={{ color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)' }}>成格条件：</span>
              {expandedPattern.evidence.join('；')}
            </div>
          )}
          <div style={{ color: 'var(--text-primary)', marginBottom: '0.3rem' }}>
            {expandedPattern.meaning}
          </div>
          {expandedPattern.break_conditions?.length > 0 && (
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              {expandedPattern._isBad ? '化解：' : '破格风险：'}
              {expandedPattern.break_conditions.join('；')}
            </div>
          )}
        </div>
      )}
      {expanded === null && (
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginTop: '0.4rem' }}>
          点击徽章查看详情；* 表示部分成格/破格风险
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 3. 飞化关键警示卡
// ─────────────────────────────────────────────────────────
function FeihuaWarningsCard({ feihua }) {
  const [showAllQuality, setShowAllQuality] = useState(false)
  if (!feihua) return null
  const items = []

  // 双忌叠加（极凶，先列）
  for (const d of feihua.double_ji || []) {
    items.push({
      type: 'danger',
      icon: '⚠⚠',
      text: `${d.from} 化忌${d.star} → ${d.to}（双忌叠加）`,
      desc: '本命化忌宫再被忌入，此宫主题极凶',
    })
  }
  // 化忌冲命宫
  for (const c of feihua.soul_chong || []) {
    items.push({
      type: 'danger',
      icon: '⚠',
      text: `${c.from} 化忌${c.star} 冲命宫`,
      desc: '一生有此宫的干扰',
    })
  }
  // 禄忌交战
  for (const w of feihua.lu_ji_war || []) {
    items.push({
      type: 'warn',
      icon: '⚠',
      text: `${w.from} 化忌${w.star} → ${w.to}（禄忌交战）`,
      desc: '化忌入本命化禄宫，主虚禄财损',
    })
  }
  // 禄解忌（转机）
  for (const r of feihua.lu_jie_ji || []) {
    items.push({
      type: 'good',
      icon: '✦',
      text: `${r.from} 化禄${r.star} → ${r.to}（禄解忌）`,
      desc: '化禄入本命化忌宫，主转机',
    })
  }
  // 命宫飞入
  for (const i of feihua.soul_incoming || []) {
    items.push({
      type: 'good',
      icon: '⊕',
      text: `${i.from} ${i.hua}${i.star} → 命宫`,
      desc: '影响一生格局',
    })
  }
  // 质能变（极强语象 — 可展开）
  const qcList = feihua.quality_changes || []
  const qcDisplay = showAllQuality ? qcList : qcList.slice(0, 3)
  for (const q of qcDisplay) {
    items.push({
      type: 'warn',
      icon: '◆',
      text: `${q.palace}：${q.star}${q.hua}（${q.fh_type}）质能变`,
      desc: '生年四化+自化，事必发生',
    })
  }

  if (items.length === 0) return null

  return (
    <div className="card" style={{ padding: '0.75rem 1rem' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.45rem',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>飞星派关键语象（{items.length} 项）</span>
        {qcList.length > 3 && (
          <button
            onClick={() => setShowAllQuality(s => !s)}
            style={{
              background: 'transparent', border: '1px solid var(--border)',
              color: 'var(--accent)', fontSize:'var(--text-2xs)', padding: '1px 6px',
              cursor: 'pointer', fontFamily: 'var(--font-serif)',
            }}
          >
            {showAllQuality ? '收起质能变' : `展开质能变 (+${qcList.length - 3})`}
          </button>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {items.map((it, i) => {
          const color = it.type === 'danger' ? '#e74c3c'
                      : it.type === 'warn'   ? '#e67e22'
                                             : '#7fb069'
          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: '6px',
              fontSize: 'var(--text-sm)', lineHeight: 1.45,
              paddingLeft: '3px', borderLeft: `2px solid ${color}`,
              paddingTop: '2px', paddingBottom: '2px',
            }}>
              <span style={{ color, fontWeight: 700, minWidth: '20px' }}>{it.icon}</span>
              <div>
                <span style={{ color: 'var(--text-primary)' }}>{it.text}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 'var(--text-xs)', marginLeft: '6px' }}>· {it.desc}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 4. 三方四正亮度评级表
// ─────────────────────────────────────────────────────────
function SfszRatingTable({ rating }) {
  const [showAllNotes, setShowAllNotes] = useState(false)
  if (!rating || !rating.sfsz_brief?.length) return null
  const notes = rating.star_notes || []
  const displayNotes = showAllNotes ? notes : notes.slice(0, 3)
  return (
    <div className="gv-plate">
      <div className="gv-sec-bar" style={{ marginBottom: '18px' }}>
        <span className="t" style={{ fontSize: '13px' }}>三方四正 · 亮度评级</span>
      </div>
      <div className="gv-sfsz-grid">
        {rating.sfsz_brief.map((s, i) => {
          const color = RATING_COLOR[s.rating] || 'var(--gv-ink-3)'
          return (
            <div className="gv-sfsz-cell" key={i}>
              <span className="bar" style={{ background: color }} />
              <div className="nm">{s.palace}（{s.branch}）</div>
              <div className={`st${s.stars?.length ? '' : ' empty'}`}>
                {s.stars?.length > 0 ? s.stars.join('·') : '空宫'}
              </div>
              <div className="ln">
                <span className="gd" style={{ color }}>{s.rating}</span>
                <span className="sc">{s.score >= 0 ? '+' : ''}{s.score?.toFixed(2)}</span>
              </div>
            </div>
          )
        })}
      </div>
      {notes.length > 0 && (
        <div style={{
          marginTop: '18px', paddingTop: '14px',
          borderTop: '1px solid var(--gv-hair)',
          fontSize: '12px', color: 'var(--gv-ink-2)', lineHeight: 1.8,
          fontFamily: 'var(--font-serif)',
        }}>
          {displayNotes.map((n, i) => (
            <div key={i}>· {n}</div>
          ))}
          {notes.length > 3 && (
            <button
              onClick={() => setShowAllNotes(s => !s)}
              style={{
                marginTop: '6px',
                background: 'transparent', border: '1px solid var(--gv-hair-2)',
                color: 'var(--gv-vermilion)', fontSize:'11px', padding: '2px 8px',
                cursor: 'pointer', fontFamily: 'var(--font-serif)',
              }}
            >
              {showAllNotes ? '收起断语' : `展开全部 (+${notes.length - 3})`}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 5. 冲宫连锁警示卡（Z-8）
// ─────────────────────────────────────────────────────────
function ChongChainsCard({ chains }) {
  const [expandedLayers, setExpandedLayers] = useState({})  // {natal: true, decade: false, ...}
  if (!chains || !chains.total) return null
  if (!chains.top_warnings?.length && !chains.events?.length) return null

  const events = chains.events || []
  // 按层分组
  const byLayer = { natal: [], decade: [], annual: [] }
  for (const e of events) {
    if (byLayer[e.layer] !== undefined) byLayer[e.layer].push(e)
  }

  const toggleLayer = (layer) => setExpandedLayers(s => ({ ...s, [layer]: !s[layer] }))

  return (
    <div className="card" style={{
      padding: '0.75rem 1rem',
      borderLeft: '3px solid #e74c3c',
    }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.45rem' }}>
        冲宫连锁警示 · 共 {chains.total} 个化忌冲事件
      </div>
      {/* 关键警示置顶（全显，不截断） */}
      {chains.top_warnings?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '0.5rem' }}>
          {chains.top_warnings.map((w, i) => (
            <div key={i} style={{
              fontSize: 'var(--text-sm)', color: 'var(--text-primary)',
              padding: '4px 7px',
              background: 'rgba(231,76,60,0.06)',
              borderLeft: '2px solid #e74c3c',
              lineHeight: 1.4,
            }}>{w}</div>
          ))}
        </div>
      )}
      {/* 每层冲宫详情（可展开/收起） */}
      {Object.entries(byLayer).map(([layer, list]) => {
        if (list.length === 0) return null
        const layerName = { natal: '本命层', decade: '大限层', annual: '流年层' }[layer]
        const layerColor = { natal: '#7f8c8d', decade: '#9b59b6', annual: '#d35400' }[layer]
        const isExpanded = expandedLayers[layer]
        const displayList = isExpanded ? list : list.slice(0, 3)
        return (
          <div key={layer} style={{ marginBottom: '0.35rem' }}>
            <div style={{
              fontSize: 'var(--text-xs)', color: layerColor,
              fontWeight: 600, marginBottom: '3px',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span>{layerName} · {list.length} 条冲宫</span>
              {list.length > 3 && (
                <button
                  onClick={() => toggleLayer(layer)}
                  style={{
                    background: 'transparent',
                    border: `1px solid ${layerColor}66`,
                    color: layerColor,
                    fontSize:'var(--text-2xs)',
                    padding: '1px 6px',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-serif)',
                  }}
                >
                  {isExpanded ? '收起' : `展开全部 (+${list.length - 3})`}
                </button>
              )}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              {displayList.map((e, i) => {
                const ml = e.multilayer || {}
                const chainParts = []
                if (ml.decade && layer === 'natal')
                  chainParts.push(`大限=${ml.decade.theme}`)
                if (ml.annual && layer === 'natal')
                  chainParts.push(`流年=${ml.annual.theme}`)
                return (
                  <div key={i} style={{
                    fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
                    paddingLeft: '8px', lineHeight: 1.5,
                  }}>
                    · {e.from_palace} {e.hua_type}{e.star} 冲【{e.chong_palace}】
                    {chainParts.length > 0 && (
                      <span style={{ color: 'var(--text-faint)' }}> → {chainParts.join(' · ')}</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 主组件：洞察栏（Z-9 加溯源高亮）
// ─────────────────────────────────────────────────────────
// section 名 → 哪个子卡片对应
const SECTION_TO_CARD = {
  '主星亮度评级': 'rating',
  '三方四正':     'rating',  // sfsz 也归到 rating 上下
  '经典格局':     'patterns',
  '飞星派飞化':   'feihua',
  '冲宫连锁':     'chong',
  '生年四化':     'feihua',  // 生年四化也归到 feihua 卡片
  '来因宫':       'feihua',
  '大限盘':       'feihua',
  '流年盘':       'feihua',
}

function HighlightWrapper({ children, active }) {
  return (
    <div style={{
      transition: 'all 0.3s',
      transform: active ? 'scale(1.01)' : 'scale(1)',
      boxShadow: active
        ? '0 0 0 2px var(--accent), 0 0 14px var(--accent-glow)'
        : 'none',
      borderRadius: 0,
    }}>{children}</div>
  )
}

export default function ZiweiInsightsBar({ insights, chongChains, highlightedSection, school = 'feixing' }) {
  if (!insights && !chongChains) return null
  const target = highlightedSection ? SECTION_TO_CARD[highlightedSection] : null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '0.75rem' }}>
      <HighlightWrapper active={target === 'rating'}>
        <RatingBadge rating={insights?.rating} />
      </HighlightWrapper>
      <HighlightWrapper active={target === 'patterns'}>
        <PatternsCard patterns={insights?.patterns} />
      </HighlightWrapper>
      <HighlightWrapper active={target === 'feihua'}>
        <FeihuaWarningsCard feihua={insights?.feihua_summary} />
      </HighlightWrapper>
      <HighlightWrapper active={target === 'chong'}>
        <ChongChainsCard chains={chongChains || insights?.chong_chains} />
      </HighlightWrapper>
      <HighlightWrapper active={target === 'rating'}>
        <SfszRatingTable rating={insights?.rating} />
      </HighlightWrapper>
    </div>
  )
}
