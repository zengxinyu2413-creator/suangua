/**
 * ZiweiSanheOverlay.jsx — 三合派"三方四正"连线
 *
 * 紫微 12 宫呈 4x4 网格（中宫 2x2 空）。三方四正：
 *   - 命宫 ↔ 财帛宫（120°，三合）
 *   - 命宫 ↔ 官禄宫（120°，三合）
 *   - 命宫 ↔ 迁移宫（180°，对宫四正）
 *   - 财帛 ↔ 官禄（120°）
 *
 * 4 宫组成一个矩形 + 内部对角线，是三合派分析格局的核心。
 *
 * 仅在 school === 'sanhe' 时显示。
 */
import React from 'react'

// 12 宫地支顺序（按盘内布局位置）
// 标准紫微命盘 4×4，中宫 2×2。库 palace.index 固定：0=寅 1=卯 … 9=亥 10=子 11=丑
// 标准布局（文墨天机式，寅在左下、顺时针）：
//   巳 午 未 申      idx: 3  4  5  6
//   辰      酉       idx: 2  _  _  7
//   卯      戌       idx: 1  _  _  8
//   寅 丑 子 亥      idx: 0 11 10  9
// index → (row, col)
const PALACE_GRID_POS = {
  0:  [3, 0], 1:  [2, 0], 2:  [1, 0], 3:  [0, 0],
  4:  [0, 1], 5:  [0, 2], 6:  [0, 3], 7:  [1, 3],
  8:  [2, 3], 9:  [3, 3], 10: [3, 2], 11: [3, 1],
}

// 12 宫名（标准顺序 — 命宫位置由 soul_palace_index 决定）
// 三方四正：命宫(0) → 财帛宫(8) → 官禄宫(4) → 迁移宫(6) （以"命宫"为起点的相对偏移）
const SANFANG_OFFSETS = {
  '命': 0,
  '财': 8,   // 命前 4 宫 = 财帛（逆数）
  '官': 4,   // 命后 4 宫 = 官禄
  '迁': 6,   // 命对宫 = 迁移
}

export default function ZiweiSanheOverlay({ palaces, soulIdx, visible }) {
  if (!visible || !palaces || palaces.length < 12) return null

  // 计算 4 个三方四正宫位的盘内坐标
  // soulIdx 是本命命宫的 index（0-11）
  // 命/财/官/迁 对应 (soulIdx + 0/8/4/6) % 12
  const points = {}
  for (const [name, offset] of Object.entries(SANFANG_OFFSETS)) {
    const idx = (soulIdx + offset) % 12
    const pos = PALACE_GRID_POS[idx]
    if (pos) {
      const [r, c] = pos
      // 转换为百分比（cell 中心）
      points[name] = {
        x: (c + 0.5) * 25,  // 4 列 → 每列 25%
        y: (r + 0.5) * 25,  // 4 行 → 每行 25%
        idx,
        palaceName: palaces.find(p => p.index === idx)?.name || '',
      }
    }
  }

  if (Object.keys(points).length < 4) return null

  // 连线对：命-财、命-官、命-迁、财-官、财-迁、官-迁
  const lines = [
    { from: '命', to: '财', color: '#27ae60', label: '三合·禄' },
    { from: '命', to: '官', color: '#27ae60', label: '三合·权' },
    { from: '命', to: '迁', color: '#e74c3c', label: '四正·对冲', dashed: true },
    { from: '财', to: '官', color: '#27ae60', label: '三合' },
    { from: '财', to: '迁', color: '#7f8c8d', label: '' },
    { from: '官', to: '迁', color: '#7f8c8d', label: '' },
  ]

  return (
    <svg
      style={{
        position: 'absolute',
        top: 0, left: 0,
        width: '100%', height: '100%',
        pointerEvents: 'none',
        zIndex: 5,
      }}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
    >
      {/* 4 宫连线 */}
      {lines.map((l, i) => {
        const p1 = points[l.from], p2 = points[l.to]
        if (!p1 || !p2) return null
        return (
          <g key={i}>
            <line
              x1={p1.x} y1={p1.y}
              x2={p2.x} y2={p2.y}
              stroke={l.color}
              strokeWidth="0.3"
              strokeOpacity="0.55"
              strokeDasharray={l.dashed ? '1.5 0.8' : 'none'}
            />
          </g>
        )
      })}
      {/* 4 个宫位的标记圆点 */}
      {Object.entries(points).map(([name, p]) => (
        <g key={name}>
          <circle cx={p.x} cy={p.y} r="1.5"
            fill={name === '命' ? '#c0392b' : '#f39c12'}
            fillOpacity="0.85"
            stroke="#fff" strokeWidth="0.2"
          />
          <text x={p.x} y={p.y - 2.5}
            fontSize="2"
            textAnchor="middle"
            fill={name === '命' ? '#c0392b' : '#7f8c8d'}
            fontWeight="700"
          >{name}</text>
        </g>
      ))}
    </svg>
  )
}
