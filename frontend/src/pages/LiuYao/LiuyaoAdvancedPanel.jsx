/**
 * LiuyaoAdvancedPanel.jsx — 六爻高级特性面板
 *
 * 展示：
 *   1. 卦身（《增删卜易·安卦身诀》）+ 在卦中的位置
 *   2. 世身（六合定位）
 *   3. 独发独静（动静格局）
 *   4. 化合/化冲/化进神/化退神
 */
import React from 'react'

const LEVEL_COLOR = {
  'auspicious_great': '#27ae60',
  'auspicious': '#16a085',
  'mixed': '#e67e22',
  'inauspicious': '#c0392b',
  'inauspicious_great': '#8b0000',
  'important': '#3498db',
  'warning': '#e67e22',
  'neutral': '#7f8c8d',
}

export default function LiuyaoAdvancedPanel({ result }) {
  if (!result) return null
  
  const guaShen = result.gua_shen
  const shiShen = result.shi_shen
  const dongJing = result.dong_jing_analysis
  const huaHeChong = result.hua_he_chong || []
  
  if (!guaShen && !shiShen && !dongJing && huaHeChong.length === 0) return null
  
  return (
    <div className="card" style={{ padding: '1rem 1.15rem', borderLeft: '4px solid #9b59b6' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '0.8rem' }}>
        <div className="card-title" style={{ marginBottom: 0, color: '#9b59b6' }}>
          🔮 六爻高级特性
        </div>
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontStyle: 'italic',
          fontFamily: 'var(--font-serif)' }}>
          《增删卜易》《卜筮正宗》
        </div>
      </div>
      
      <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.85rem',
        fontFamily: 'var(--font-serif)', lineHeight: 1.7, padding: '0.5rem 0.7rem',
        background: 'rgba(155,89,182,0.06)', borderRadius: 'var(--r-sm)' }}>
        以下为六爻派的高级判读：卦身、世身、独发独静、化合化冲。
        这些不是表面的旺衰冲合，而是断卦的"骨干"。
      </div>
      
      {guaShen && <GuaShenCard guaShen={guaShen} />}
      {shiShen && shiShen.he_zhi && <ShiShenCard shiShen={shiShen} />}
      {dongJing && <DongJingCard dongJing={dongJing} />}
      {huaHeChong.length > 0 && <HuaHeChongCard items={huaHeChong} />}
    </div>
  )
}

function GuaShenCard({ guaShen }) {
  const inChart = guaShen.in_chart || {}
  const onChart = inChart.on_chart
  
  return (
    <SubCard
      title="① 卦身（《增删卜易·安卦身诀》）"
      color={onChart ? '#16a085' : '#c0392b'}
      source="《增删卜易·卷一·安卦身诀》"
    >
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem',
        flexWrap: 'wrap' }}>
        <div style={{ padding: '0.5rem 0.85rem',
          background: `${onChart ? '#16a085' : '#c0392b'}11`,
          border: `2px solid ${onChart ? '#16a085' : '#c0392b'}66`,
          borderRadius: 'var(--r-sm)' }}>
          <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)' }}>卦身地支</div>
          <div style={{ fontSize:'var(--text-2xl)', fontWeight: 700,
            color: onChart ? '#16a085' : '#c0392b',
            fontFamily: 'var(--font-display)' }}>
            {guaShen.zhi}
          </div>
        </div>
        <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
          fontFamily: 'var(--font-serif)', lineHeight: 1.7, flex: 1, minWidth: '200px' }}>
          {guaShen.rule}（世爻 {guaShen.world_position} 爻 · {guaShen.world_yin_yang}）<br/>
          → 卦身 = <strong style={{ color: '#9b59b6' }}>{guaShen.zhi}</strong>
        </div>
      </div>
      
      <div style={{ padding: '0.55rem 0.75rem',
        background: 'rgba(155,89,182,0.06)',
        borderLeft: '3px solid #9b59b6',
        borderRadius: 'var(--r-sm)',
        fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.7 }}>
        {inChart.interpretation}
        {onChart && inChart.positions && inChart.positions.length > 0 && (
          <div style={{ marginTop: '0.35rem', color: '#9b59b6', fontSize:'var(--text-xs)' }}>
            卦身在第 {inChart.positions.map(p => `${p.line}（${p.yao_name}爻）`).join('、')} 爻
          </div>
        )}
      </div>
    </SubCard>
  )
}

function ShiShenCard({ shiShen }) {
  return (
    <SubCard
      title="② 世身（六合之神）"
      color="#3498db"
      source="《增删卜易·世身论》"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem',
        padding: '0.5rem 0.75rem', background: 'rgba(52,152,219,0.06)',
        borderLeft: '3px solid #3498db', borderRadius: 'var(--r-sm)',
        marginBottom: '0.4rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)' }}>世爻</span>
          <span style={{ fontSize:'var(--text-lg)', fontWeight: 700, color: '#3498db',
            fontFamily: 'var(--font-display)' }}>
            {shiShen.world_zhi}
          </span>
          <span style={{ color: 'var(--text-faint)' }}>合</span>
          <span style={{ fontSize:'var(--text-lg)', fontWeight: 700, color: '#16a085',
            fontFamily: 'var(--font-display)' }}>
            {shiShen.he_zhi}
          </span>
        </div>
        
        {/* 世身在卦中状态 */}
        {shiShen.on_chart !== undefined && (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{
              padding: '2px 8px', borderRadius: '10px',
              background: shiShen.on_chart ? '#16a085' : '#c0392b',
              color: '#fff', fontSize:'var(--text-2xs)', fontWeight: 600,
              fontFamily: 'var(--font-serif)',
            }}>
              {shiShen.on_chart ? `上卦（第${shiShen.position_in_chart}爻）` : '不上卦'}
            </span>
            {shiShen.wang_shuai && (
              <span style={{
                padding: '2px 8px', borderRadius: '10px',
                background: 'rgba(155,89,182,0.12)',
                color: '#9b59b6', fontSize:'var(--text-2xs)', fontWeight: 600,
                fontFamily: 'var(--font-serif)',
                border: '1px solid #9b59b6',
              }}>
                月令：{shiShen.wang_shuai}
              </span>
            )}
          </div>
        )}
      </div>
      
      <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.75,
        padding: '0.4rem 0.65rem', background: 'rgba(52,152,219,0.04)',
        borderRadius: 'var(--r-sm)' }}>
        {shiShen.desc}
      </div>
    </SubCard>
  )
}

function DongJingCard({ dongJing }) {
  const color = LEVEL_COLOR[dongJing.level] || '#7f8c8d'
  
  return (
    <SubCard
      title="③ 动静格局识别"
      color={color}
      source={dongJing.source}
    >
      <div style={{ padding: '0.55rem 0.75rem',
        background: `${color}11`, borderLeft: `3px solid ${color}`,
        borderRadius: 'var(--r-sm)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
          marginBottom: '0.35rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <span style={{ fontSize:'var(--text-lg)', fontWeight: 700, color,
            fontFamily: 'var(--font-serif)' }}>
            {dongJing.type}
          </span>
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
            fontFamily: 'var(--font-mono)' }}>
            动爻 {dongJing.moving_count} / 6
          </span>
        </div>
        <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
          fontFamily: 'var(--font-serif)', lineHeight: 1.75, marginBottom: '0.35rem' }}>
          {dongJing.desc}
        </div>
        {dongJing.advice && (
          <div style={{ fontSize:'var(--text-xs)', color: '#d4a040',
            fontFamily: 'var(--font-serif)', fontStyle: 'italic' }}>
            ▸ 断法：{dongJing.advice}
          </div>
        )}
      </div>
    </SubCard>
  )
}

function HuaHeChongCard({ items }) {
  return (
    <SubCard
      title={`④ 化象分析（${items.length} 处）`}
      color="#d4a040"
      source="《增删卜易·化合化冲化进退章》"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {items.map((it, i) => {
          const c = LEVEL_COLOR[it.level] || '#7f8c8d'
          return (
            <div key={i} style={{ padding: '0.45rem 0.65rem',
              background: `${c}11`, borderLeft: `3px solid ${c}`,
              borderRadius: 'var(--r-sm)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.25rem', flexWrap: 'wrap', gap: '0.4rem' }}>
                <span style={{ fontSize:'var(--text-sm)', fontWeight: 700, color: c,
                  fontFamily: 'var(--font-serif)' }}>
                  第 {it.line} 爻 · {it.type}
                </span>
                <span style={{ fontSize:'var(--text-xs)', fontFamily: 'var(--font-display)',
                  color: 'var(--text-secondary)' }}>
                  {it.orig_zhi} → {it.changed_zhi}
                </span>
              </div>
              <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.65 }}>
                {it.desc}
              </div>
            </div>
          )
        })}
      </div>
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
