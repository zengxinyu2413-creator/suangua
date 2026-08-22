/**
 * BaziTiaohouPanel.jsx — 调候用神 + 子平真诠格局成败救应面板
 *
 * 展示：
 *   1. 调候用神（《穷通宝鉴》— 主用神 + 辅用神是否到位）
 *   2. 格局成败救应（《子平真诠》— 8 大正格）
 */
import React from 'react'

const LEVEL_COLOR = {
  'auspicious_great': '#27ae60',
  'auspicious': '#16a085',
  'mixed': '#e67e22',
  'inauspicious': '#c0392b',
  'inauspicious_great': '#8b0000',
  'neutral': '#7f8c8d',
}

export default function BaziTiaohouPanel({ chart }) {
  if (!chart) return null
  
  const tiaohou = chart.tiaohou
  const geju = chart.geju_cheng_bai
  
  if (!tiaohou?.available && !geju?.available) return null
  
  return (
    <div className="card" style={{ padding: '1rem 1.15rem', borderLeft: '4px solid #9b59b6' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '0.8rem' }}>
        <div className="card-title" style={{ marginBottom: 0, color: '#9b59b6' }}>
          📜 经典派深度分析
        </div>
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontStyle: 'italic',
          fontFamily: 'var(--font-serif)' }}>
          《穷通宝鉴》《子平真诠》
        </div>
      </div>
      
      {tiaohou?.available && <TiaohouCard tiaohou={tiaohou} />}
      {geju?.available && <GejuCard geju={geju} />}
    </div>
  )
}

function TiaohouCard({ tiaohou }) {
  const color = LEVEL_COLOR[tiaohou.level] || '#7f8c8d'
  
  return (
    <SubCard
      title="① 调候用神（《穷通宝鉴》）"
      color={color}
      source="《穷通宝鉴》"
    >
      <div style={{ padding: '0.55rem 0.7rem',
        background: `${color}11`,
        borderLeft: `3px solid ${color}`,
        borderRadius: 'var(--r-sm)', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
          flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.4rem' }}>
          <span style={{ fontSize:'var(--text-xs)', color: 'var(--text-muted)',
            fontFamily: 'var(--font-serif)' }}>
            {tiaohou.day_master}日主 · {tiaohou.month_zhi}月
          </span>
          <span style={{
            padding: '2px 10px', borderRadius: '10px',
            background: color, color: '#fff',
            fontSize:'var(--text-xs)', fontWeight: 700, fontFamily: 'var(--font-serif)',
          }}>
            {tiaohou.grade}
          </span>
        </div>
        
        {/* 用神三层 */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
          {tiaohou.primary && (
            <UserShenChip label="主用神" stem={tiaohou.primary} inChart={tiaohou.primary_in_chart} />
          )}
          {tiaohou.secondary && (
            <UserShenChip label="辅用神" stem={tiaohou.secondary} inChart={tiaohou.secondary_in_chart} />
          )}
          {tiaohou.secondary2 && (
            <UserShenChip label="辅 2" stem={tiaohou.secondary2} inChart={tiaohou.secondary2_in_chart} />
          )}
        </div>
        
        <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
          fontFamily: 'var(--font-serif)', lineHeight: 1.75, marginBottom: '0.35rem' }}>
          {tiaohou.verdict}
        </div>
        
        <div style={{ fontSize:'var(--text-2xs)', color: '#9b59b6',
          fontFamily: 'var(--font-serif)', fontStyle: 'italic',
          padding: '0.35rem 0.5rem', background: 'rgba(155,89,182,0.05)',
          borderRadius: '4px', borderLeft: '2px solid #9b59b655' }}>
          📜 古书释义：{tiaohou.desc}
        </div>
        
        {tiaohou.advice && (
          <div style={{ fontSize:'var(--text-xs)', color: '#d4a040', marginTop: '0.35rem',
            fontFamily: 'var(--font-serif)' }}>
            ▸ 古法建议：{tiaohou.advice}
          </div>
        )}
      </div>
    </SubCard>
  )
}

function UserShenChip({ label, stem, inChart }) {
  const present = inChart === true
  const color = present ? '#27ae60' : '#c0392b'
  return (
    <div style={{
      padding: '0.35rem 0.55rem',
      background: `${color}11`, border: `1.5px solid ${color}55`,
      borderRadius: 'var(--r-sm)',
      display: 'flex', alignItems: 'center', gap: '0.35rem',
    }}>
      <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)',
        fontFamily: 'var(--font-serif)' }}>
        {label}
      </span>
      <span style={{ fontSize:'var(--text-lg)', fontWeight: 700, color,
        fontFamily: 'var(--font-display)' }}>
        {stem}
      </span>
      <span style={{ fontSize:'var(--text-2xs)', color: present ? '#27ae60' : '#c0392b' }}>
        {present ? '✓ 到位' : '✗ 缺'}
      </span>
    </div>
  )
}

function GejuCard({ geju }) {
  return (
    <SubCard
      title={`② 格局成败救应（${geju.pattern}）`}
      color="#3498db"
      source="《子平真诠·成败救应》"
    >
      <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.7,
        padding: '0.5rem 0.7rem', background: 'rgba(52,152,219,0.06)',
        borderLeft: '3px solid #3498db', borderRadius: 'var(--r-sm)',
        marginBottom: '0.5rem' }}>
        <strong style={{ color: '#3498db' }}>总论：</strong>{geju["总论"]}
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '0.5rem', marginBottom: '0.5rem' }}>
        <div style={{ padding: '0.5rem 0.65rem', background: 'rgba(39,174,96,0.06)',
          borderLeft: '2px solid #27ae60', borderRadius: 'var(--r-sm)' }}>
          <div style={{ fontSize:'var(--text-xs)', color: '#27ae60', fontWeight: 700, marginBottom: '0.3rem' }}>
            ✓ 成格条件
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize:'var(--text-xs)',
            color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)', lineHeight: 1.65 }}>
            {(geju["成格条件"] || []).map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>
        <div style={{ padding: '0.5rem 0.65rem', background: 'rgba(192,57,43,0.06)',
          borderLeft: '2px solid #c0392b', borderRadius: 'var(--r-sm)' }}>
          <div style={{ fontSize:'var(--text-xs)', color: '#c0392b', fontWeight: 700, marginBottom: '0.3rem' }}>
            ✗ 破格条件
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize:'var(--text-xs)',
            color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)', lineHeight: 1.65 }}>
            {(geju["破格条件"] || []).map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>
      </div>
      
      {geju["救应模式"] && geju["救应模式"].length > 0 && (
        <div style={{ padding: '0.5rem 0.65rem', background: 'rgba(212,160,64,0.06)',
          borderLeft: '2px solid #d4a040', borderRadius: 'var(--r-sm)' }}>
          <div style={{ fontSize:'var(--text-xs)', color: '#d4a040', fontWeight: 700, marginBottom: '0.4rem' }}>
            🌀 救应模式（破格反成贵）
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {geju["救应模式"].map((r, i) => (
              <div key={i} style={{ fontSize:'var(--text-xs)', fontFamily: 'var(--font-serif)',
                color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <span style={{ color: '#c0392b' }}>破：{r["破"]}</span>
                <span style={{ color: 'var(--text-faint)' }}> → </span>
                <span style={{ color: '#27ae60' }}>救：{r["救"]}</span>
                <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginTop: '2px' }}>
                  {r["desc"]}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </SubCard>
  )
}

function SubCard({ title, color, source, children }) {
  return (
    <div style={{ marginBottom: '0.85rem',
      padding: '0.75rem 0.9rem', background: 'var(--bg-raised)',
      border: `1px solid ${color}33`, borderRadius: 'var(--r-md)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        marginBottom: '0.55rem', borderBottom: `1px dashed ${color}33`, paddingBottom: '0.3rem',
        gap: '0.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize:'var(--text-sm)', fontWeight: 700, color,
          fontFamily: 'var(--font-serif)' }}>
          {title}
        </span>
        {source && (
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
            fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
            {source}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}
