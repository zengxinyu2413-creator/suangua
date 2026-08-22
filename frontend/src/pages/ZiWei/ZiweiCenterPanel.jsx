/**
 * ZiweiCenterPanel.jsx — 紫微命盘中宫信息板
 *
 * 文墨天机风格 + 现代布局：
 *   - 标题：紫微斗数 · 五行局
 *   - 基本信息（公历/农历/时辰/性别/生肖）
 *   - 真太阳时校正（如有）
 *   - 节气四柱 + 十神 + 藏干
 *   - 命主/身主
 *   - 起运信息
 *   - 工具栏：日↑↓/时↑↓/天盘 + 派别切换
 */
import React, { useState } from 'react'

// 十神颜色（按吉凶分类）
const SHISHEN_COLOR = {
  '比肩': '#7f8c8d', '劫财': '#95a5a6',
  '食神': '#27ae60', '伤官': '#16a085',
  '偏财': '#d4a040', '正财': '#f39c12',
  '七杀': '#c0392b', '正官': '#e67e22',
  '偏印': '#9b59b6', '正印': '#8e44ad',
  '日主': '#2c3e50',
}

// 干支颜色
const PILLAR_COLOR = ['#27ae60', '#2980b9', '#c0392b', '#f39c12']  // 年月日时

export default function ZiweiCenterPanel({
  meta, baziOverlay, layer, decadeData, tripleData,
  onShiftDay, onShiftHour,
  school = 'feixing', onSchoolChange,
}) {
  const [showSect, setShowSect] = useState('jieqi')  // 'jieqi' / 'nonjieqi'

  // 根据派别选择数据集
  const suffix = showSect === 'jieqi' ? 'jieqi' : 'nonjieqi'
  const sizhu       = baziOverlay?.[`sizhu_${suffix}`]       || baziOverlay?.sizhu_jieqi   || {}
  const shishen     = baziOverlay?.[`shishen_${suffix}`]     || baziOverlay?.shishen       || {}
  const shishenZhi  = baziOverlay?.[`shishen_zhi_${suffix}`] || baziOverlay?.shishen_zhi   || {}
  const canggan     = baziOverlay?.[`canggan_${suffix}`]     || baziOverlay?.canggan       || {}
  const nayin       = baziOverlay?.[`nayin_${suffix}`]       || baziOverlay?.nayin         || {}
  const qiyun = baziOverlay?.qiyun || {}
  const dayun = baziOverlay?.dayun || []
  const realTime = baziOverlay?.real_time

  const pillars = [
    { label: '年柱', gz: sizhu.year,  ss: shishen.year,  ssZhi: shishenZhi.year,  cg: canggan.year,  ny: nayin.year },
    { label: '月柱', gz: sizhu.month, ss: shishen.month, ssZhi: shishenZhi.month, cg: canggan.month, ny: nayin.month },
    { label: '日柱', gz: sizhu.day,   ss: shishen.day,   ssZhi: shishenZhi.day,   cg: canggan.day,   ny: nayin.day },
    { label: '时柱', gz: sizhu.time,  ss: shishen.time,  ssZhi: shishenZhi.time,  cg: canggan.time,  ny: nayin.time },
  ]

  return (
    <div style={{
      gridColumn: 'span 2', gridRow: 'span 2',
      border: '1px solid var(--border)',
      background: 'linear-gradient(135deg, var(--bg-subtle) 0%, var(--bg-card) 100%)',
      display: 'flex', flexDirection: 'column',
      padding: '8px 10px',
      fontFamily: 'var(--font-serif)',
      fontSize:'var(--text-2xs)',
      lineHeight: 1.4,
      color: 'var(--text-secondary)',
      overflow: 'auto',
      gap: '4px',
    }}>
      {/* ── 顶栏：标题 + 五行局 ─────────────────────────── */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        borderBottom: '1px solid var(--border)', paddingBottom: '3px',
      }}>
        <div style={{ fontSize:'var(--text-sm)', fontWeight: 700, color: 'var(--accent)' }}>
          紫微斗数
        </div>
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)' }}>
          {meta?.five_elements}
        </div>
      </div>

      {/* ── 基本信息（紧凑双列） ─────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '38px 1fr', gap: '1px 4px',
        fontSize:'var(--text-2xs)' }}>
        <span style={{ color: 'var(--text-faint)' }}>公历</span>
        <span>{meta?.solar_date}</span>
        <span style={{ color: 'var(--text-faint)' }}>农历</span>
        <span>{meta?.lunar_date}</span>
        <span style={{ color: 'var(--text-faint)' }}>时辰</span>
        <span>{meta?.birth_hour_name} <span style={{ color: 'var(--text-faint)' }}>{meta?.birth_hour_range}</span></span>
        <span style={{ color: 'var(--text-faint)' }}>性别</span>
        <span>{meta?.gender} · {meta?.zodiac} · {meta?.sign}</span>
      </div>

      {/* ── 真太阳时校正（如有） ─────────────────────────── */}
      {realTime && (
        <div style={{
          fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
          background: 'rgba(207,59,44,0.05)', padding: '2px 4px',
          borderLeft: '2px solid var(--accent)',
        }}>
          钟表 {realTime.clock_time} → 真太阳时 <strong style={{ color: 'var(--accent)' }}>{realTime.real_solar_time}</strong>
          {' '}（经度 {realTime.longitude}° · 差 {realTime.offset_minutes > 0 ? '+' : ''}{realTime.offset_minutes}分）
        </div>
      )}

      {/* ── 命主/身主 ─────────────────────────────────── */}
      {(meta?.soul_star || meta?.body_star) && (
        <div style={{ display: 'flex', gap: '8px', fontSize:'var(--text-2xs)',
          borderTop: '1px dashed var(--border)', paddingTop: '3px' }}>
          {meta.soul_star && <span><span style={{ color: 'var(--text-faint)' }}>命主</span> <strong style={{ color: 'var(--jade)' }}>{meta.soul_star}</strong></span>}
          {meta.body_star && <span><span style={{ color: 'var(--text-faint)' }}>身主</span> <strong style={{ color: 'var(--cyan-b, #3498db)' }}>{meta.body_star}</strong></span>}
        </div>
      )}

      {/* ── 派别切换（带差异提示） ───────────────────── */}
      {baziOverlay && (() => {
        const sjq = baziOverlay.sizhu_jieqi || {}
        const snj = baziOverlay.sizhu_nonjieqi || {}
        // 检查两派是否一致
        const sameYear  = sjq.year  === snj.year
        const sameMonth = sjq.month === snj.month
        const allSame   = sameYear && sameMonth && sjq.day === snj.day && sjq.time === snj.time
        // 找出哪些柱不同
        const diffCols = []
        if (!sameYear)  diffCols.push('年柱')
        if (!sameMonth) diffCols.push('月柱')
        if (sjq.day  !== snj.day)  diffCols.push('日柱')
        if (sjq.time !== snj.time) diffCols.push('时柱')

        return (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap',
            borderTop: '1px dashed var(--border)', paddingTop: '3px',
          }}>
            <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>四柱派别</span>
            <div style={{ display: 'flex', background: 'var(--bg-subtle)', padding: '1px' }}>
              {[
                { id:'jieqi',    label:'节气', title:'立春切换年柱、月节气切换月柱（业内主流）' },
                { id:'nonjieqi', label:'非节气', title:'农历正月初一切换年柱、月份切换月柱（民间俗派）' },
              ].map(s => (
                <button key={s.id}
                  onClick={() => setShowSect(s.id)}
                  title={s.title}
                  style={{
                    padding: '1px 6px',
                    fontSize:'var(--text-2xs)',
                    border: 'none',
                    background: showSect === s.id ? 'var(--surface)' : 'transparent',
                    color: showSect === s.id ? 'var(--accent)' : 'var(--text-muted)',
                    fontWeight: showSect === s.id ? 600 : 400,
                    cursor: 'pointer',
                  }}>{s.label}</button>
              ))}
            </div>
            {/* 差异提示 */}
            {allSame ? (
              <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
                两派一致（远离节气交界）
              </span>
            ) : (
              <span style={{ fontSize:'var(--text-2xs)', color: '#d35400', fontWeight: 600 }}>
                ⚠ {diffCols.join('+')} 不同（节气交界）
              </span>
            )}
          </div>
        )
      })()}

      {/* ── 四柱表（八字 + 十神 + 藏干） ────────────────── */}
      {sizhu.year && (
        <div style={{ marginTop: '2px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '2px',
            background: 'var(--bg-subtle)',
            padding: '3px',
            border: '1px solid var(--border)',
          }}>
            {pillars.map((p, i) => (
              <div key={i} style={{
                textAlign: 'center',
                padding: '2px 1px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
              }}>
                {/* 柱名 */}
                <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>{p.label}</div>
                {/* 十神 */}
                {p.ss && (
                  <div style={{ fontSize: '0.52rem', fontWeight: 600,
                    color: SHISHEN_COLOR[p.ss] || 'var(--text-muted)' }}>
                    {p.ss}
                  </div>
                )}
                {/* 干支（核心） */}
                <div style={{ fontSize:'var(--text-md)', fontWeight: 700, lineHeight: 1.1,
                  color: PILLAR_COLOR[i] }}>
                  {p.gz?.[0]}<br/>{p.gz?.[1]}
                </div>
                {/* 藏干 */}
                {p.cg && p.cg.length > 0 && (
                  <div style={{ fontSize: '0.45rem', color: 'var(--text-muted)',
                    fontFamily: 'var(--font-serif)', marginTop: '1px' }}>
                    {p.cg.join('')}
                  </div>
                )}
                {/* 纳音 */}
                {p.ny && (
                  <div style={{ fontSize: '0.45rem', color: 'var(--text-faint)' }}>
                    {p.ny}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 起运信息 ───────────────────────────────── */}
      {qiyun.summary && (
        <div style={{
          fontSize:'var(--text-2xs)', color: 'var(--text-muted)',
          textAlign: 'center', padding: '2px',
          background: 'rgba(155,89,182,0.05)',
          borderLeft: '2px solid #9b59b6',
        }}>
          ◈ {qiyun.summary}
        </div>
      )}

      {/* ── 当前 layer 提示 ───────────────────────── */}
      {layer !== 'natal' && (
        <div style={{
          marginTop: '2px', fontSize:'var(--text-2xs)',
          color: layer === 'decade' ? '#9b59b6' : '#d35400',
          textAlign: 'center', fontWeight: 700,
          padding: '2px',
          background: layer === 'decade' ? 'rgba(155,89,182,0.08)' : 'rgba(211,84,0,0.08)',
        }}>
          ◈ {layer === 'decade' ? '大限盘视图' : '三盘叠合视图'}
          {(decadeData?.age_range) && <> · {decadeData.age_range[0]}–{decadeData.age_range[1]}岁</>}
        </div>
      )}

      {/* ── 紫微派别切换 ────────────────────────── */}
      {onSchoolChange && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px',
          borderTop: '1px dashed var(--border)', paddingTop: '3px' }}>
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>紫微派别</span>
          <div style={{ display: 'flex', background: 'var(--bg-subtle)', padding: '1px', flex: 1 }}>
            {[
              { id:'feixing', label:'飞星', desc:'重四化飞化' },
              { id:'sanhe',   label:'三合', desc:'重三方四正' },
              { id:'sihua',   label:'四化', desc:'生年四化' },
            ].map(s => (
              <button key={s.id}
                onClick={() => onSchoolChange(s.id)}
                title={s.desc}
                style={{
                  padding: '1px 6px',
                  fontSize:'var(--text-2xs)',
                  border: 'none',
                  background: school === s.id ? 'var(--surface)' : 'transparent',
                  color: school === s.id ? 'var(--accent)' : 'var(--text-muted)',
                  fontWeight: school === s.id ? 600 : 400,
                  cursor: 'pointer',
                  flex: 1,
                }}>{s.label}</button>
            ))}
          </div>
        </div>
      )}

      {/* ── 工具栏：日↑↓ / 时↑↓ ─────────────────── */}
      {(onShiftDay || onShiftHour) && (
        <div style={{
          display: 'flex', gap: '3px', justifyContent: 'center',
          borderTop: '1px dashed var(--border)', paddingTop: '3px', marginTop: 'auto',
        }}>
          {onShiftDay && (
            <>
              <button onClick={() => onShiftDay(-1)} style={btnStyle} title="上一天">日↓</button>
              <button onClick={() => onShiftDay(1)}  style={btnStyle} title="下一天">日↑</button>
            </>
          )}
          {onShiftHour && (
            <>
              <button onClick={() => onShiftHour(-1)} style={btnStyle} title="上一时辰">时↓</button>
              <button onClick={() => onShiftHour(1)}  style={btnStyle} title="下一时辰">时↑</button>
            </>
          )}
        </div>
      )}
    </div>
  )
}

const btnStyle = {
  padding: '2px 6px',
  fontSize:'var(--text-2xs)',
  background: 'var(--bg-card)',
  border: '1px solid var(--border)',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  fontFamily: 'var(--font-serif)',
}
