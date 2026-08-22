/**
 * LiuyaoSanheCard.jsx — 三合局/三会方/半三合可视化
 *
 * 显示后端 sanhe_sanhui 字段：
 *   - 全三合（申子辰水/亥卯未木/寅午戌火/巳酉丑金）
 *   - 三会方（亥子丑北水/寅卯辰东木/巳午未南火/申酉戌西金）
 *   - 半三合（长生+帝旺 或 帝旺+墓库）
 *
 * 设计：用 SVG 在六爻表旁画连接线，显示哪几爻成局
 */
import React from 'react'

const JU_COLOR = {
  '水局': '#3498db', '木局': '#27ae60', '火局': '#e74c3c', '金局': '#95a5a6',
  '北方水会': '#3498db', '东方木会': '#27ae60', '南方火会': '#e74c3c', '西方金会': '#95a5a6',
}

function getJuColor(name) {
  for (const [k, v] of Object.entries(JU_COLOR)) {
    if (name.includes(k.slice(0, 2)) || name.includes(k)) return v
  }
  if (name.includes('水')) return '#3498db'
  if (name.includes('木')) return '#27ae60'
  if (name.includes('火')) return '#e74c3c'
  if (name.includes('金')) return '#95a5a6'
  return '#d4a040'
}

/**
 * 单个局的连接线显示
 * positions: [1, 2, 3] 等爻位序号 1-6
 * 1=初爻在下、6=上爻在上
 */
function JuLine({ positions, name, color, ju_type, isFull }) {
  // 6 个爻：初=1 在底部 y=140，上=6 在顶部 y=20，间距 24
  // 我们的SVG 高度 160，宽度 60
  const yaoY = (pos) => 152 - (pos - 1) * 24

  const sorted = [...positions].sort((a, b) => a - b)

  return (
    <div style={{
      display: 'flex', alignItems: 'stretch', gap: '0.7rem',
      padding: '0.45rem 0.7rem',
      background: `linear-gradient(90deg, ${color}11, transparent)`,
      borderLeft: `3px solid ${color}`,
      borderRadius: 'var(--r-sm)',
      marginBottom: '0.4rem',
    }}>
      {/* SVG 局线图（缩小版） */}
      <svg width="50" height="160" viewBox="0 0 50 160" style={{ flexShrink: 0 }}>
        {/* 6 个爻位的点 */}
        {[1,2,3,4,5,6].map(p => (
          <circle key={p}
            cx="25" cy={yaoY(p)} r={sorted.includes(p) ? 5 : 2.5}
            fill={sorted.includes(p) ? color : '#666'}
            stroke={sorted.includes(p) ? '#fff' : 'none'}
            strokeWidth="1"
            opacity={sorted.includes(p) ? 1 : 0.3}
          />
        ))}
        {/* 连接线 */}
        {sorted.length >= 2 && (
          <>
            {sorted.length === 3 ? (
              // 三合：三角形
              <polygon
                points={sorted.map(p => `${25},${yaoY(p)}`).join(' ')}
                fill="none" stroke={color} strokeWidth="1.8"
                strokeDasharray={isFull ? "" : "3,3"}
                opacity="0.7"
              />
            ) : (
              // 半三合：直线
              <line
                x1="25" y1={yaoY(sorted[0])}
                x2="25" y2={yaoY(sorted[sorted.length - 1])}
                stroke={color} strokeWidth="1.5"
                strokeDasharray="3,3"
                opacity="0.7"
              />
            )}
          </>
        )}
        {/* 爻位标签（极小） */}
        {[1,2,3,4,5,6].map(p => (
          <text key={`l${p}`} x="40" y={yaoY(p) + 3.5}
            fontSize="8" fill={sorted.includes(p) ? color : '#666'}
            opacity={sorted.includes(p) ? 1 : 0.4}>
            {['初','二','三','四','五','上'][p-1]}
          </text>
        ))}
      </svg>
      
      {/* 描述区 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <span style={{ fontSize:'var(--text-md)', fontWeight: 700, color }}>{name}</span>
          <span className={`badge`} style={{
            fontSize:'var(--text-2xs)', padding: '1px 5px',
            background: isFull ? `${color}33` : `${color}1a`,
            color: color, border: `1px solid ${color}66`,
          }}>
            {ju_type === 'sanhe' ? '三合局' : ju_type === 'sanhui' ? '三会方' : '半三合'}
          </span>
        </div>
        <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
          爻位：{positions.map(p => ['初','二','三','四','五','上'][p-1]+'爻').join(' / ')}
        </div>
        <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-faint)',
          fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>
          {ju_type === 'sanhe' && '三合局：三爻地支聚合成局，五行力量大增，原神若在局中得力'}
          {ju_type === 'sanhui' && '三会方：三爻地支汇聚一方，五行旺盛之极'}
          {ju_type === 'ban' && '半三合：缺一字，力量减半。冲合得位之爻可应'}
        </div>
      </div>
    </div>
  )
}

export default function LiuyaoSanheCard({ sanheData }) {
  if (!sanheData) return null
  const { sanhe = [], sanhui = [], ban_sanhe = [] } = sanheData
  if (sanhe.length === 0 && sanhui.length === 0 && ban_sanhe.length === 0) {
    return null
  }
  
  return (
    <div className="card">
      <div className="card-title">三合三会局 · 卦中聚气</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
        {sanhe.map((s, i) => (
          <JuLine key={`h${i}`}
            positions={s.positions} name={s.name}
            color={getJuColor(s.name)}
            ju_type="sanhe" isFull={true}
          />
        ))}
        {sanhui.map((s, i) => (
          <JuLine key={`hui${i}`}
            positions={s.positions} name={s.name}
            color={getJuColor(s.name)}
            ju_type="sanhui" isFull={true}
          />
        ))}
        {sanhe.length === 0 && sanhui.length === 0 && ban_sanhe.map((s, i) => (
          <JuLine key={`b${i}`}
            positions={s.positions} name={s.name}
            color={getJuColor(s.name)}
            ju_type="ban" isFull={false}
          />
        ))}
      </div>
      <div style={{ marginTop: '0.5rem', fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.65, fontStyle: 'italic',
        padding: '0.35rem 0.65rem', background: 'rgba(212,160,64,0.04)', borderRadius: 'var(--r-sm)' }}>
        《增删卜易·三合局》：申子辰会成水局、亥卯未会成木局、寅午戌会成火局、巳酉丑会成金局。
        三合局中之爻同气连枝，力量倍增；若用神在局中得旺，所谋必成。
      </div>
    </div>
  )
}
