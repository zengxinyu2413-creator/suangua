/**
 * ZiweiTimePanel.jsx — 底栏时间盘
 *
 * 5 行可切换的时间维度：
 *   行 1: 大限（点击切换到对应大限）
 *   行 2: 流年小限（10 个年份）
 *   行 3: 流月（农历 1-12 月）
 *   行 4: 流日（初一到三十）
 *   行 5: 流时（子-亥 12 时辰）
 *
 * 比文墨更优：清晰的视觉层级、悬浮提示、当前 active 高亮
 */
import React, { useState } from 'react'

const HOUR_NAMES = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

const ROW_STYLES = {
  label: {
    padding: '4px 8px',
    fontSize:'var(--text-2xs)',
    fontWeight: 700,
    color: 'var(--accent)',
    background: 'var(--bg-subtle)',
    borderRight: '1px solid var(--border)',
    textAlign: 'center',
    minWidth: '48px',
    whiteSpace: 'nowrap',
  },
  cell: {
    padding: '3px 4px',
    fontSize:'var(--text-2xs)',
    border: '1px solid var(--border)',
    background: 'var(--bg-card)',
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'all 0.12s',
    fontFamily: 'var(--font-serif)',
    lineHeight: 1.2,
    color: 'var(--text-secondary)',
  },
  cellActive: {
    background: 'rgba(207,59,44,0.15)',
    color: 'var(--accent)',
    fontWeight: 700,
    border: '1px solid var(--accent)',
  },
}

function Cell({ children, active, onClick, title }) {
  const [hover, setHover] = useState(false)
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      title={title}
      style={{
        ...ROW_STYLES.cell,
        ...(active ? ROW_STYLES.cellActive : {}),
        ...(hover && !active ? { background: 'rgba(207,59,44,0.05)' } : {}),
      }}
    >
      {children}
    </div>
  )
}

export default function ZiweiTimePanel({
  bazi,             // {dayun: [...], qiyun: {...}}
  timePanel,        // {months: [...]}
  selectedAge,      // 当前选择岁数
  selectedYear,     // 当前选择年份
  selectedMonth,    // 当前选择农历月
  selectedDay,      // 当前选择农历日
  selectedHourIdx,  // 当前选择时辰索引
  onAgeChange,      // 切换大限/流年
  onYearChange,     // 切换流年（直接传年份）
  onMonthChange,    // 切换流月
  onDayChange,      // 切换流日
  onHourChange,     // 切换流时
}) {
  const dayun = bazi?.dayun || []
  const currentYear = new Date().getFullYear()

  // 流年：当前年起 ±5 年
  const annualYears = []
  for (let y = currentYear - 2; y <= currentYear + 7; y++) {
    annualYears.push(y)
  }

  // 流月
  const months = timePanel?.months || []

  // 流日（1-30）
  const days = []
  for (let d = 1; d <= 30; d++) {
    const cnDay = (d <= 10 ? '初' + ['','一','二','三','四','五','六','七','八','九','十'][d]
                  : d < 20 ? '十' + ['','一','二','三','四','五','六','七','八','九'][d-10]
                  : d === 20 ? '二十'
                  : d < 30 ? '廿' + ['','一','二','三','四','五','六','七','八','九'][d-20]
                  : '三十')
    days.push({ num: d, name: cnDay })
  }

  return (
    <div style={{
      border: '1px solid var(--border)',
      background: 'var(--surface)',
      marginTop: '1rem',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '6px 10px',
        fontSize:'var(--text-2xs)',
        fontWeight: 700,
        color: 'var(--accent)',
        background: 'var(--bg-subtle)',
        borderBottom: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span>时间盘 · 大运/流年/流月/流日/流时</span>
        {bazi?.qiyun?.summary && (
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', fontWeight: 400 }}>
            {bazi.qiyun.summary}
          </span>
        )}
      </div>

      {/* 行 1：大限 */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        <div style={ROW_STYLES.label}>大限</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '1px', flex: 1, padding: '2px' }}>
          {dayun.slice(0, 10).map((d, i) => {
            const active = selectedAge !== undefined &&
                           selectedAge >= d.start_age && selectedAge <= d.end_age
            return (
              <Cell key={i}
                active={active}
                onClick={() => onAgeChange?.(d.start_age + 1)}
                title={`${d.start_year}年起 · ${d.ganzhi || '童限'}`}
              >
                <div>{d.start_age}~{d.end_age}</div>
                <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)' }}>
                  {d.ganzhi || '童限'}
                </div>
              </Cell>
            )
          })}
        </div>
      </div>

      {/* 行 2：流年小限 */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        <div style={ROW_STYLES.label}>流年</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: '1px', flex: 1, padding: '2px' }}>
          {annualYears.map((y, i) => {
            const active = selectedYear === y
            return (
              <Cell key={i}
                active={active}
                onClick={() => onYearChange?.(y)}
                title={`${y}年流年`}
              >
                <div style={{ fontSize:'var(--text-2xs)' }}>{y}</div>
              </Cell>
            )
          })}
        </div>
      </div>

      {/* 行 3：流月 */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        <div style={ROW_STYLES.label}>流月</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1px', flex: 1, padding: '2px' }}>
          {months.length > 0 ? months.map((m, i) => {
            const active = selectedMonth === m.lunar_month
            return (
              <Cell key={i}
                active={active}
                onClick={() => onMonthChange?.(m.lunar_month)}
                title={`${m.month_name} · ${m.ganzhi}`}
              >
                <div>{m.month_name}</div>
                <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)' }}>{m.ganzhi}</div>
              </Cell>
            )
          }) : Array.from({length: 12}).map((_, i) => (
            <Cell key={i}>
              <div>{['正','二','三','四','五','六','七','八','九','十','冬','腊'][i]}月</div>
            </Cell>
          ))}
        </div>
      </div>

      {/* 行 4：流日（缩略，6 列展示） */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        <div style={ROW_STYLES.label}>流日</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(15, 1fr)', gap: '1px', flex: 1, padding: '2px' }}>
          {days.slice(0, 15).map((d, i) => (
            <Cell key={i}
              active={selectedDay === d.num}
              onClick={() => onDayChange?.(d.num)}
              title={`${d.name}（${d.num}日）`}
            >
              <div style={{ fontSize: '0.52rem' }}>{d.name}</div>
            </Cell>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        <div style={ROW_STYLES.label}>&nbsp;</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(15, 1fr)', gap: '1px', flex: 1, padding: '2px' }}>
          {days.slice(15, 30).map((d, i) => (
            <Cell key={i+15}
              active={selectedDay === d.num}
              onClick={() => onDayChange?.(d.num)}
              title={`${d.name}（${d.num}日）`}
            >
              <div style={{ fontSize: '0.52rem' }}>{d.name}</div>
            </Cell>
          ))}
        </div>
      </div>

      {/* 行 5：流时 */}
      <div style={{ display: 'flex' }}>
        <div style={ROW_STYLES.label}>流时</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1px', flex: 1, padding: '2px' }}>
          {HOUR_NAMES.map((h, i) => (
            <Cell key={i}
              active={selectedHourIdx === i}
              onClick={() => onHourChange?.(i)}
              title={`${h}时`}
            >
              <div style={{ fontSize:'var(--text-2xs)' }}>{h}</div>
            </Cell>
          ))}
        </div>
      </div>
    </div>
  )
}
