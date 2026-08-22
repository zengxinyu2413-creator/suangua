/**
 * BaziInsightsBar.jsx — B-3 八字洞察栏（命格速览）
 * ================================================
 * 5 个卡片：
 *   1. 用神/喜神/忌神 — 命格指南针
 *   2. 关键特殊格局（吉/凶）— 一眼抓格局
 *   3. 地支刑冲合害 — 命理师必看
 *   4. 神煞速览
 *   5. 大运高低评级
 */
import React from 'react'

// ─────────────────────────────────────────────────────────
// 1. 用神/喜神/忌神卡
// ─────────────────────────────────────────────────────────
function YongShenCard({ yong }) {
  if (!yong || !yong.yong_shen_wx) return null
  const WX_COLOR = yong.wuxing_colors || {
    木: '#27ae60', 火: '#e74c3c', 土: '#f39c12', 金: '#95a5a6', 水: '#3498db',
  }
  const items = [
    { label: '用神', wx: yong.yong_shen_wx, mood: '吉', color: WX_COLOR[yong.yong_shen_wx] },
    { label: '喜神', wx: yong.xi_shen_wx,   mood: '吉', color: WX_COLOR[yong.xi_shen_wx] },
    { label: '忌神', wx: yong.ji_shen_wx,   mood: '凶', color: WX_COLOR[yong.ji_shen_wx] },
    { label: '仇神', wx: yong.chou_shen_wx, mood: '凶', color: WX_COLOR[yong.chou_shen_wx] },
  ].filter(x => x.wx)

  return (
    <div className="card" style={{
      padding: '0.65rem 1rem',
      borderLeft: '3px solid #c8a04a',
    }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
        用神 · 喜忌 · 命格指南针
      </div>
      <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
        {items.map((x, i) => (
          <div key={i} style={{
            padding: '4px 10px',
            background: `${x.color}11`,
            border: `1px solid ${x.color}66`,
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            minWidth: '54px',
          }}>
            <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>{x.label}</div>
            <div style={{ fontSize:'var(--text-md)', fontWeight: 700, color: x.color }}>{x.wx}</div>
          </div>
        ))}
      </div>
      {yong.analysis && (
        <div style={{ marginTop: '0.45rem', fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          {yong.analysis}
        </div>
      )}
      {yong.tiao_hou?.desc && (
        <div style={{ marginTop: '0.3rem', fontSize: 'var(--text-xs)', color: 'var(--text-faint)' }}>
          《穷通宝鉴》调候：{yong.tiao_hou.desc}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 2. 特殊格局卡
// ─────────────────────────────────────────────────────────
function SpecialPatternsCard({ sp }) {
  if (!sp || !sp.total) return null
  return (
    <div className="card" style={{
      padding: '0.65rem 1rem',
      borderLeft: '3px solid #9b59b6',
    }}>
      <div style={{
        fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.45rem',
        display: 'flex', justifyContent: 'space-between',
      }}>
        <span>特殊格局深度识别</span>
        <span>共 {sp.total} 格 · 吉 {sp.total_aus} / 凶 {sp.total_inaus}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {(sp.matched || []).map((p, i) => (
          <div key={i} style={{
            display: 'flex', flexDirection: 'column', gap: '2px',
            padding: '5px 8px',
            background: p.auspicious ? 'rgba(39,174,96,0.06)' : 'rgba(231,76,60,0.06)',
            borderLeft: `2px solid ${p.auspicious ? '#27ae60' : '#e74c3c'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
              <span style={{
                fontSize:'var(--text-xs)', fontWeight: 700,
                color: p.auspicious ? '#27ae60' : '#e74c3c',
              }}>{p.auspicious ? '✦' : '⚠'} {p.name}</span>
              <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
                {p.condition}
              </span>
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
              {p.interpretation}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 3. 刑冲合害卡
// ─────────────────────────────────────────────────────────
function RelationsCard({ relations }) {
  if (!relations || !relations.summary) return null
  const s = relations.summary
  const total = (s.total_he || 0) + (s.total_chong || 0) + (s.total_xing || 0) + (s.total_hai || 0)
  if (total === 0) return null

  return (
    <div className="card" style={{
      padding: '0.65rem 1rem',
      borderLeft: '3px solid #e74c3c',
    }}>
      <div style={{
        fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.45rem',
        display: 'flex', justifyContent: 'space-between',
      }}>
        <span>地支刑冲合害</span>
        <span style={{ display: 'flex', gap: '0.4rem' }}>
          {s.total_he > 0 && <span style={{ color: '#27ae60' }}>合×{s.total_he}</span>}
          {s.total_chong > 0 && <span style={{ color: '#e74c3c' }}>冲×{s.total_chong}</span>}
          {s.total_xing > 0 && <span style={{ color: '#e67e22' }}>刑×{s.total_xing}</span>}
          {s.total_hai > 0 && <span style={{ color: '#9b59b6' }}>害×{s.total_hai}</span>}
        </span>
      </div>
      {s.key_blessings?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', marginBottom: '0.3rem' }}>
          {s.key_blessings.slice(0, 3).map((b, i) => (
            <div key={i} style={{
              fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
              padding: '3px 6px', background: 'rgba(39,174,96,0.05)',
              borderLeft: '2px solid #27ae60', lineHeight: 1.5,
            }}>{b}</div>
          ))}
        </div>
      )}
      {s.key_warnings?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          {s.key_warnings.slice(0, 4).map((w, i) => (
            <div key={i} style={{
              fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
              padding: '3px 6px', background: 'rgba(231,76,60,0.05)',
              borderLeft: '2px solid #e74c3c', lineHeight: 1.5,
            }}>{w}</div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 4. 神煞速览
// ─────────────────────────────────────────────────────────
function ShenshaCard({ shensha }) {
  if (!shensha || shensha.length === 0) return null
  return (
    <div className="card" style={{ padding: '0.6rem 1rem' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
        神煞速览 · 共 {shensha.length} 项
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
        {shensha.slice(0, 12).map((s, i) => (
          <span key={i} style={{
            padding: '2px 7px',
            fontSize:'var(--text-xs)',
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)',
          }}>
            {s.name}{s.pillar && <span style={{ color: 'var(--text-faint)', marginLeft: 2 }}>·{s.pillar}</span>}
          </span>
        ))}
        {shensha.length > 12 && (
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
            ……还有 {shensha.length - 12} 项
          </span>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 主组件
// ─────────────────────────────────────────────────────────
export default function BaziInsightsBar({ data }) {
  if (!data) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '0.75rem' }}>
      <YongShenCard yong={data.yong_shen} />
      <SpecialPatternsCard sp={data.special_patterns} />
      <RelationsCard relations={data.relations} />
      <ShenshaCard shensha={data.shensha} />
    </div>
  )
}
