/**
 * ZiweiDirections.jsx — 12 宫盘 8 方位边缘装饰
 *
 * 在 12 宫盘的外围标注：正南方/南偏西/西偏南/正西方等 8 方位。
 * 包裹在一个 wrapper div 中，让 children（12 宫盘）居中。
 *
 * 文墨天机风格 + 更精细的箭头指示
 */
import React from 'react'

const TOP_LABELS = ['正南方', '南偏西']      // 上方 = 南方位（午在顶）
const BOTTOM_LABELS = ['北偏东', '正北方']    // 下方 = 北方位（子在底）
const LEFT_LABELS = ['南偏东', '正东方', '东偏北', '北偏西']   // 左边 = 东方位（卯在左）
const RIGHT_LABELS = ['西偏南', '正西方', '西偏北']  // 右边 = 西方位（酉在右）

const corner = {
  fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
  fontFamily: 'var(--font-serif)',
  writingMode: 'vertical-rl', textOrientation: 'upright',
  letterSpacing: '0.05em',
  whiteSpace: 'nowrap',
}

const horizontal = {
  fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
  fontFamily: 'var(--font-serif)',
  letterSpacing: '0.1em',
}

export default function ZiweiDirections({ children }) {
  return (
    <div style={{
      position: 'relative',
      padding: '26px 30px',  // 给四周留出方位标注空间，避免重叠到宫位
    }}>
      {/* 顶部：正南方/南偏西 (因为命盘上方对应南方) */}
      <div style={{
        position: 'absolute', top: 6, left: '30px', right: '30px',
        display: 'flex', justifyContent: 'space-between',
        pointerEvents: 'none',  // 不阻挡按钮点击
      }}>
        <div style={{ display: 'flex', gap: '24px' }}>
          <span style={horizontal}>↑ 正南方</span>
          <span style={horizontal}>南偏西 ↗</span>
        </div>
      </div>

      {/* 底部：北偏东/正北方 */}
      <div style={{
        position: 'absolute', bottom: 6, left: '30px', right: '30px',
        display: 'flex', justifyContent: 'space-between',
        pointerEvents: 'none',
      }}>
        <span style={horizontal}>↙ 北偏东</span>
        <span style={horizontal}>正北方 ↓</span>
      </div>

      {/* 左侧（西边）：南偏东 / 东偏南 / 东偏北 / 北偏西 */}
      <div style={{
        position: 'absolute', left: 6, top: '26px', bottom: '26px',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        alignItems: 'center',
        pointerEvents: 'none',
      }}>
        <span style={corner}>南偏东</span>
        <span style={corner}>正东方</span>
        <span style={corner}>东偏北</span>
        <span style={corner}>北偏西</span>
      </div>

      {/* 右侧（东边）：西偏南 / 正西方 / 西偏北 */}
      <div style={{
        position: 'absolute', right: 6, top: '26px', bottom: '26px',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        alignItems: 'center',
        pointerEvents: 'none',
      }}>
        <span style={corner}>西偏南</span>
        <span style={corner}>正西方</span>
        <span style={corner}>西偏北</span>
      </div>

      {/* 子内容 */}
      {children}
    </div>
  )
}
