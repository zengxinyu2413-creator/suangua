/**
 * LiuyaoHologram.jsx — 六爻全息可视化（SVG）
 *
 * 一张 SVG 卦图同时呈现：
 *   1. 六爻象（阳/阴线）
 *   2. 纳甲地支
 *   3. 六亲（颜色编码）
 *   4. 六神
 *   5. 旺衰彩条
 *   6. 世应爻标
 *   7. 动爻 → 化爻箭头
 *   8. 用神/原神/忌神角标
 *   9. 三合三会局连接线
 *
 * 让用户一眼看完六爻所有关键信息。
 */
import React from 'react'

const QIN_COLOR = {
  父母: '#8e44ad', 兄弟: '#e67e22', 子孙: '#27ae60',
  妻财: '#d4a040', 官鬼: '#c0392b',
}
const SHEN_COLOR = {
  青龙: '#27ae60', 朱雀: '#e74c3c', 勾陈: '#d4a040',
  腾蛇: '#9b59b6', 白虎: '#bdc3c7', 玄武: '#5d8fa5',
}
const STR_COLOR = {
  旺: '#e74c3c', 相: '#e67e22', 休: '#7f8c8d', 囚: '#5d6d7e', 死: '#4a4a4a',
}
const JU_COLOR = {
  水局: '#3498db', 木局: '#27ae60', 火局: '#e74c3c', 金局: '#95a5a6',
  '北方水会': '#3498db', '东方木会': '#27ae60', '南方火会': '#e74c3c', '西方金会': '#95a5a6',
}

export default function LiuyaoHologram({ data, role = {} }) {
  if (!data || !data.yaos) return null
  
  const yaos = data.yaos || []
  const sanhe = (data.sanhe_sanhui?.sanhe || []).concat(data.sanhe_sanhui?.sanhui || [])
  const yongShenName = data.topic_analysis?.yong_shen_name
  
  // 反向查询：哪些爻是用神/原神/忌神
  const dr = data.deep_relations || {}
  const yongPos = new Set((dr.key_lines?.['用神_lines'] || []).map(l => l.position))
  const yuanPos = new Set((dr.key_lines?.['原神_lines'] || []).map(l => l.position))
  const jiPos = new Set((dr.key_lines?.['忌神_lines'] || []).map(l => l.position))
  
  // SVG 尺寸
  const W = 480
  const H = 360
  const YAO_W = 70   // 爻象宽度
  const ROW_H = 50   // 每行高度
  const X_LINE = 105 // 爻象左边x
  const X_NAJIA = 195 // 六亲六神区
  const X_SHEN = 250
  const X_STR = 295
  const X_CHANGE = 340  // 化爻箭头区
  const X_JU = 410  // 三合局连线
  
  // 爻位 y 坐标（初爻在下，上爻在上）
  const yaoY = (pos) => 30 + (6 - pos) * ROW_H + ROW_H / 2
  
  return (
    <div className="card" style={{ padding: '0.85rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>六爻全息图</div>
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          {data.day_gan}{data.day_zhi} 日 · {data.month_zhi}月 · {data.palace_trigram}宫
        </div>
      </div>
      
      <div style={{ overflowX: 'auto' }}>
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', maxWidth: '100%' }}>
          {/* ── 顶部表头 ── */}
          <g style={{ fontFamily: 'var(--font-serif)' }}>
            <text x={20} y={20} fontSize="10" fill="#888">爻位</text>
            <text x={X_LINE + YAO_W / 2} y={20} fontSize="10" fill="#888" textAnchor="middle">爻象</text>
            <text x={X_NAJIA} y={20} fontSize="10" fill="#888">六亲/地支</text>
            <text x={X_SHEN} y={20} fontSize="10" fill="#888">六神</text>
            <text x={X_STR} y={20} fontSize="10" fill="#888">旺衰</text>
            <text x={X_CHANGE} y={20} fontSize="10" fill="#888">化爻</text>
            <text x={X_JU} y={20} fontSize="10" fill="#888">局</text>
          </g>
          
          {/* ── 六爻横线 ── */}
          {yaos.map((y, idx) => {
            const pos = idx + 1
            const y_coord = yaoY(pos)
            const isYong = yongPos.has(pos)
            const isYuan = yuanPos.has(pos)
            const isJi = jiPos.has(pos)
            const roleColor = isYong ? '#d4a040' : isYuan ? '#27ae60' : isJi ? '#e74c3c' : null
            const roleLabel = isYong ? '用神' : isYuan ? '原神' : isJi ? '忌神' : null
            
            return (
              <g key={idx}>
                {/* 行背景 */}
                {roleColor && (
                  <rect x={5} y={y_coord - 20} width={W - 10} height={40} rx={6}
                    fill={`${roleColor}0c`} stroke={`${roleColor}55`} strokeWidth="1" />
                )}
                
                {/* 爻位 + 角色标 */}
                <text x={20} y={y_coord + 2} fontSize="13" fill={roleColor || '#aaa'}
                  fontFamily="var(--font-display)" fontWeight={roleColor ? 700 : 400}>
                  {['初','二','三','四','五','上'][idx]}
                </text>
                {roleLabel && (
                  <g>
                    <rect x={42} y={y_coord - 8} width={28} height={14} rx={3}
                      fill={roleColor} />
                    <text x={56} y={y_coord + 3} fontSize="9" fill="#000" fontWeight="700"
                      textAnchor="middle">{roleLabel}</text>
                  </g>
                )}
                
                {/* 爻象（阳实/阴虚线） */}
                {y.line === '阳' ? (
                  <rect x={X_LINE} y={y_coord - 3} width={YAO_W} height={6} fill="#e6e6e6" rx={1} />
                ) : (
                  <>
                    <rect x={X_LINE} y={y_coord - 3} width={YAO_W * 0.4} height={6} fill="#e6e6e6" rx={1} />
                    <rect x={X_LINE + YAO_W * 0.6} y={y_coord - 3} width={YAO_W * 0.4} height={6} fill="#e6e6e6" rx={1} />
                  </>
                )}
                
                {/* 动爻标识 */}
                {y.is_changing && (
                  <text x={X_LINE + YAO_W + 6} y={y_coord + 4} fontSize="14"
                    fill="#d4a040" fontWeight="700">▸</text>
                )}
                
                {/* 六亲 + 地支 */}
                <text x={X_NAJIA} y={y_coord + 4} fontSize="13"
                  fill={QIN_COLOR[y.liu_qin] || '#aaa'} fontWeight="600">
                  {y.liu_qin}
                </text>
                <text x={X_NAJIA + 26} y={y_coord + 4} fontSize="13"
                  fill={y.kong_wang ? '#e74c3c' : '#d4a040'}
                  fontFamily="var(--font-display)" fontWeight="600">
                  {y.branch}
                  {y.kong_wang && <tspan fontSize="9" dx="1">空</tspan>}
                </text>
                
                {/* 六神 */}
                <text x={X_SHEN} y={y_coord + 4} fontSize="11"
                  fill={SHEN_COLOR[y.liu_shen] || '#888'}>
                  {y.liu_shen}
                </text>
                
                {/* 旺衰 */}
                <text x={X_STR} y={y_coord + 4} fontSize="11"
                  fill={STR_COLOR[y.strength?.label] || '#888'} fontWeight="600">
                  {y.strength?.label}
                </text>
                
                {/* 化爻显示 */}
                {y.is_changing && y.changed_branch && (
                  <g>
                    {/* 箭头 */}
                    <line x1={X_CHANGE - 5} y1={y_coord} x2={X_CHANGE + 15} y2={y_coord}
                      stroke="#d4a040" strokeWidth="1.5" />
                    <polygon points={`${X_CHANGE + 12},${y_coord - 3} ${X_CHANGE + 17},${y_coord} ${X_CHANGE + 12},${y_coord + 3}`}
                      fill="#d4a040" />
                    {/* 化爻地支 */}
                    <text x={X_CHANGE + 22} y={y_coord + 4} fontSize="13"
                      fill="#d4a040" fontFamily="var(--font-display)" fontWeight="600">
                      {y.changed_branch}
                    </text>
                    {/* 化爻六亲（小字） */}
                    {y.changed_liu_qin && (
                      <text x={X_CHANGE + 22} y={y_coord + 16} fontSize="9"
                        fill={QIN_COLOR[y.changed_liu_qin] || '#888'}>
                        {y.changed_liu_qin}
                      </text>
                    )}
                  </g>
                )}
                
                {/* 世应标记 */}
                {y.is_world && (
                  <g>
                    <circle cx={X_LINE - 12} cy={y_coord} r="8" fill="#d4a040" />
                    <text x={X_LINE - 12} y={y_coord + 4} fontSize="10" fill="#000"
                      fontWeight="700" textAnchor="middle">世</text>
                  </g>
                )}
                {y.is_application && (
                  <g>
                    <circle cx={X_LINE - 12} cy={y_coord} r="8" fill="#3498db" />
                    <text x={X_LINE - 12} y={y_coord + 4} fontSize="10" fill="#fff"
                      fontWeight="700" textAnchor="middle">应</text>
                  </g>
                )}
              </g>
            )
          })}
          
          {/* ── 三合三会局连线 ── */}
          {sanhe.slice(0, 3).map((ju, ji) => {
            const color = JU_COLOR[ju.name] || '#d4a040'
            const positions = (ju.positions || []).sort((a,b) => a - b)
            if (positions.length < 2) return null
            
            // 在右侧画一个细长矩形连接相关爻位
            const x_base = X_JU + ji * 10
            const points = positions.map(p => `${x_base},${yaoY(p)}`).join(' ')
            
            return (
              <g key={`ju${ji}`}>
                {/* 连接点 */}
                {positions.map((p, pi) => (
                  <circle key={pi} cx={x_base} cy={yaoY(p)} r="4"
                    fill={color} stroke="#000" strokeWidth="0.5" />
                ))}
                {/* 连线 */}
                {positions.length === 3 ? (
                  <polygon points={points} fill="none" stroke={color}
                    strokeWidth="1.5" opacity="0.7" />
                ) : (
                  <line x1={x_base} y1={yaoY(positions[0])}
                    x2={x_base} y2={yaoY(positions[positions.length-1])}
                    stroke={color} strokeWidth="1.5" opacity="0.7" />
                )}
                {/* 局名标 */}
                <text x={x_base + 10} y={yaoY(positions[Math.floor(positions.length/2)]) + 3}
                  fontSize="9" fill={color} fontWeight="700"
                  style={{ writingMode: 'vertical-rl' }}>
                  {ju.name.slice(0, 2)}
                </text>
              </g>
            )
          })}
          
          {/* 局图例 */}
          {sanhe.length > 0 && (
            <text x={W - 5} y={H - 5} fontSize="8" fill="#888" textAnchor="end" fontStyle="italic">
              {data.sanhe_sanhui?.summary || ''}
            </text>
          )}
        </svg>
      </div>
      
      {/* 图例 */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.65rem', justifyContent: 'center',
        fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginTop: '0.5rem',
        padding: '0.4rem', background: 'var(--bg-subtle)', borderRadius: 'var(--r-sm)' }}>
        <span><span style={{ color: '#d4a040', fontWeight: 700 }}>● 用神</span> 所占之事</span>
        <span><span style={{ color: '#27ae60', fontWeight: 700 }}>● 原神</span> 生用神</span>
        <span><span style={{ color: '#e74c3c', fontWeight: 700 }}>● 忌神</span> 克用神</span>
        <span><span style={{ color: '#d4a040', fontWeight: 700 }}>▸</span> 动爻</span>
        <span><span style={{ color: '#e74c3c', fontWeight: 700 }}>空</span> 旬空</span>
      </div>
    </div>
  )
}
