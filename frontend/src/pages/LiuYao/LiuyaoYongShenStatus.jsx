/**
 * LiuyaoYongShenStatus.jsx — 用神状态综合评估卡
 *
 * 一目了然看出"用神能否成事"：
 *   - 用神在何爻
 *   - 用神旺/相/休/囚/死
 *   - 用神是否空/破/墓/动
 *   - 原神生扶情况
 *   - 忌神冲克情况
 *   - 总体吉凶分（-5 到 +5）
 *   - 古书断语
 */
import React from 'react'

const QIN_COLOR = {
  父母: '#8e44ad', 兄弟: '#e67e22', 子孙: '#27ae60',
  妻财: '#d4a040', 官鬼: '#c0392b',
}

export default function LiuyaoYongShenStatus({ data }) {
  if (!data) return null
  
  const ta = data.topic_analysis || {}
  const dr = data.deep_relations || {}
  const yaos = data.yaos || []
  const yongShenName = ta.yong_shen_name
  
  if (!yongShenName || yongShenName === '世爻' || yongShenName === '应爻') return null
  
  // 找用神爻
  const yongYao = yaos.find(y => y.liu_qin === yongShenName)
  if (!yongYao) return null
  
  // 用神状态
  const strength = yongYao.strength?.label || '中和'
  const isKong = yongYao.kong_wang
  const isChanging = yongYao.is_changing
  const isStrong = ['旺', '相'].includes(strength)
  const isWeak = ['休', '囚', '死'].includes(strength)
  
  // 原神/忌神状态
  const yuanLines = dr.key_lines?.['原神_lines'] || []
  const jiLines = dr.key_lines?.['忌神_lines'] || []
  
  const yuanCount = yuanLines.length
  const jiCount = jiLines.length
  const yuanStrong = yuanLines.filter(l => ['旺','相'].includes(l.strength?.label)).length
  const jiStrong = jiLines.filter(l => ['旺','相'].includes(l.strength?.label)).length
  const yuanChanging = yuanLines.filter(l => l.is_changing).length
  const jiChanging = jiLines.filter(l => l.is_changing).length
  
  // 综合吉凶分（-5 到 +5）
  let score = 0
  if (isStrong) score += 2
  else if (strength === '相') score += 1
  else if (strength === '休') score -= 0.5
  else if (strength === '囚') score -= 1
  else if (strength === '死') score -= 2
  if (isKong) score -= 1.5
  if (yuanStrong > 0) score += 1
  if (yuanChanging > 0) score += 0.5
  if (jiStrong > 0) score -= 1
  if (jiChanging > 0) score -= 1
  // 化爻情况
  const changingRels = (dr.changing_relations || []).filter(r => r.liu_qin === yongShenName)
  changingRels.forEach(r => {
    if (r.relation === '回头生') score += 2
    else if (r.relation === '回头克') score -= 2
    else if (r.relation === '化进神') score += 1
    else if (r.relation === '化退神') score -= 1
    else if (r.relation === '化空' || r.relation === '化破' || r.relation === '化墓' || r.relation === '化绝') score -= 1
  })
  score = Math.max(-5, Math.min(5, score))
  
  // 总体评价
  const scoreColor = score >= 3 ? '#27ae60'
                   : score >= 1 ? '#16a085'
                   : score >= -1 ? '#f39c12'
                   : score >= -3 ? '#e67e22'
                   : '#c0392b'
  const scoreLabel = score >= 3 ? '大吉'
                   : score >= 1 ? '吉'
                   : score >= -1 ? '中平'
                   : score >= -3 ? '凶'
                   : '大凶'
  
  // 古书断语
  const verdict = (() => {
    if (isKong && isWeak) return '《卜筮正宗》：用神衰空，事难应；真空难起'
    if (isKong && isStrong) return '《卜筮正宗》：旺空不真空，出旬填实可应'
    if (isStrong && yuanStrong > 0) return '《增删卜易》：用神旺相又得原神生扶 — 大吉，事必成'
    if (isWeak && jiStrong > 0) return '《增删卜易》：用神死绝又被忌神克 — 大凶，事难成'
    if (isStrong && jiCount === 0) return '《增删卜易》：用神旺相无忌神冲克 — 吉，所谋顺遂'
    if (isWeak && yuanCount === 0) return '《增删卜易》：用神衰无原神生扶 — 力有不逮，须待生扶'
    if (changingRels.some(r => r.relation === '回头生')) return '《增删卜易》：用神动化回头生 — 大利，事必成'
    if (changingRels.some(r => r.relation === '回头克')) return '《增删卜易》：用神动化回头克 — 大凶，事必败'
    return '《卜筮正宗》：用神状态中和，须结合三方四正综合参断'
  })()
  
  return (
    <div className="card card-glow" style={{ padding: '0.95rem 1.1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.7rem' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>用神状态总评</div>
        <div style={{
          padding: '4px 12px', borderRadius: '14px',
          background: `${scoreColor}22`, border: `1px solid ${scoreColor}66`,
          fontWeight: 700, fontSize:'var(--text-sm)', color: scoreColor,
          fontFamily: 'var(--font-serif)',
        }}>
          {scoreLabel} {score >= 0 ? '+' : ''}{score.toFixed(1)}
        </div>
      </div>
      
      {/* 用神核心信息 */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.4rem 0.85rem',
        padding: '0.6rem 0.85rem', background: 'var(--bg-raised)',
        borderRadius: 'var(--r-md)', fontSize: 'var(--text-sm)',
      }}>
        <span style={{ color: 'var(--text-muted)' }}>用神</span>
        <span>
          <span style={{ color: QIN_COLOR[yongShenName], fontWeight: 700, fontSize:'var(--text-md)' }}>
            {yongShenName}爻
          </span>
          <span style={{ marginLeft: '0.5rem', color: 'var(--accent)', fontFamily: 'var(--font-display)' }}>
            第{yongYao.position}爻 · {yongYao.branch}({yongYao.element})
          </span>
        </span>
        
        <span style={{ color: 'var(--text-muted)' }}>旺衰</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{
            color: isStrong ? '#e74c3c' : isWeak ? '#7f8c8d' : 'var(--text-secondary)',
            fontWeight: 700,
          }}>{strength}</span>
          {isKong && <span className="badge" style={{ fontSize:'var(--text-2xs)', background: '#e74c3c22', color: '#e74c3c', border: '1px solid #e74c3c55' }}>旬空</span>}
          {isChanging && <span className="badge" style={{ fontSize:'var(--text-2xs)', background: '#d4a04022', color: '#d4a040', border: '1px solid #d4a04055' }}>发动</span>}
          {yongYao.is_world && <span className="badge" style={{ fontSize:'var(--text-2xs)', background: '#d4a04022', color: '#d4a040' }}>临世</span>}
          {yongYao.is_application && <span className="badge" style={{ fontSize:'var(--text-2xs)', background: '#3498db22', color: '#3498db' }}>临应</span>}
        </span>
        
        <span style={{ color: 'var(--text-muted)' }}>原神</span>
        <span style={{ fontSize:'var(--text-xs)' }}>
          {yuanCount > 0 ? (
            <>
              共 <span style={{ color: '#27ae60', fontWeight: 700 }}>{yuanCount}</span> 爻
              {yuanStrong > 0 && <span style={{ marginLeft: '0.3rem', color: '#27ae60' }}> · {yuanStrong} 爻旺相生扶 ✓</span>}
              {yuanChanging > 0 && <span style={{ marginLeft: '0.3rem', color: '#27ae60' }}> · {yuanChanging} 爻发动 ✓</span>}
              {yuanStrong === 0 && yuanChanging === 0 && <span style={{ marginLeft: '0.3rem', color: 'var(--text-muted)' }}> · 衰静无力</span>}
            </>
          ) : <span style={{ color: '#e74c3c' }}>原神不上卦，须看伏神</span>}
        </span>
        
        <span style={{ color: 'var(--text-muted)' }}>忌神</span>
        <span style={{ fontSize:'var(--text-xs)' }}>
          {jiCount > 0 ? (
            <>
              共 <span style={{ color: '#e74c3c', fontWeight: 700 }}>{jiCount}</span> 爻
              {jiStrong > 0 && <span style={{ marginLeft: '0.3rem', color: '#e74c3c' }}> · {jiStrong} 爻旺相 ⚠</span>}
              {jiChanging > 0 && <span style={{ marginLeft: '0.3rem', color: '#e74c3c' }}> · {jiChanging} 爻发动 ⚠</span>}
              {jiStrong === 0 && jiChanging === 0 && <span style={{ marginLeft: '0.3rem', color: '#27ae60' }}> · 衰静无力 ✓</span>}
            </>
          ) : <span style={{ color: '#27ae60' }}>忌神不显，无冲克之虞 ✓</span>}
        </span>
      </div>
      
      {/* 古书断语 */}
      <div style={{
        marginTop: '0.7rem', padding: '0.55rem 0.8rem',
        background: `${scoreColor}0c`, borderLeft: `3px solid ${scoreColor}`,
        borderRadius: 'var(--r-sm)',
        fontSize: 'var(--text-sm)', fontFamily: 'var(--font-serif)',
        color: 'var(--text-secondary)', lineHeight: 1.7,
      }}>
        {verdict}
      </div>
    </div>
  )
}
