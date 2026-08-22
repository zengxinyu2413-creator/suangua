/**
 * LiuyaoDeepRelations.jsx — L-1 六爻关系深度分析展示
 *
 * 展示后端 deep_relations 字段：
 *   1. 四神五行（用神 / 原神 / 忌神 / 仇神）
 *   2. 各神所在爻位
 *   3. 动爻变化（回头生 / 回头克 / 进神 / 退神）
 *   4. 六爻力量评估（月令+日辰，十二长生）
 *   5. 关键提示（吉象/警示）
 */
import React from 'react'

const WX_COLOR = {
  木: '#27ae60', 火: '#e74c3c', 土: '#f39c12',
  金: '#95a5a6', 水: '#3498db',
}

const FORCE_COLOR = {
  极旺: '#c0392b', 旺相: '#e74c3c', 中和: '#7f8c8d',
  休囚: '#5d6d7e', 无气: '#4a4a4a',
}

const STATUS_COLOR = {
  长生: '#27ae60', 沐浴: '#bdc3c7', 冠带: '#27ae60',
  临官: '#27ae60', 帝旺: '#c0392b',
  衰: '#7f8c8d', 病: '#5d6d7e', 死: '#4a4a4a',
  墓: '#34495e', 绝: '#2c3e50', 胎: '#95a5a6', 养: '#7f8c8d',
}

function FourGodsCard({ yyj }) {
  if (!yyj || !yyj['用神_wx']) return null
  
  // 5 角排列：用神中心，原神左上、食神左下、忌神右上、仇神右下
  // 实际古书顺序：用神 → 原神生用神 → 忌神克用神 → 仇神生忌神 → 食神耗用神
  const items = [
    { label: '用神', wx: yyj['用神_wx'], role: '所占之事', mood: 'core',  color: '#d4a040' },
    { label: '原神', wx: yyj['原神_wx'], role: '生用神（护神）',  mood: 'good', color: '#27ae60' },
    { label: '忌神', wx: yyj['忌神_wx'], role: '克用神（敌）',    mood: 'bad',  color: '#e74c3c' },
    { label: '仇神', wx: yyj['仇神_wx'], role: '生忌神（间接敌）', mood: 'bad',  color: '#7f8c8d' },
    { label: '食神', wx: yyj['食神_wx'], role: '用神所生（耗气）', mood: 'neutral', color: '#3498db' },
  ]
  
  return (
    <div className="card" style={{ padding: '0.85rem 1rem', borderLeft: '3px solid #c8a04a' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
          四神五行 · 断卦核心
        </span>
        <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontFamily: 'var(--font-serif)', fontStyle: 'italic' }}>
          《增删卜易》
        </span>
      </div>
      
      {/* 五行流转图（SVG） */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.7rem' }}>
        <svg width="280" height="120" viewBox="0 0 280 120">
          {/* 五个圆 */}
          {[
            { x:140, y:25,  label:'用神', wx:yyj['用神_wx'], color:'#d4a040', r:21 },  // 顶部中
            { x:55,  y:45,  label:'原神', wx:yyj['原神_wx'], color:'#27ae60', r:18 },  // 左上
            { x:225, y:45,  label:'忌神', wx:yyj['忌神_wx'], color:'#e74c3c', r:18 },  // 右上
            { x:90,  y:95,  label:'食神', wx:yyj['食神_wx'], color:'#3498db', r:16 },  // 左下
            { x:190, y:95,  label:'仇神', wx:yyj['仇神_wx'], color:'#7f8c8d', r:16 },  // 右下
          ].map((g, i) => (
            <g key={i}>
              <circle cx={g.x} cy={g.y} r={g.r}
                fill={`${g.color}22`} stroke={g.color} strokeWidth="1.5" />
              <text x={g.x} y={g.y-2} textAnchor="middle"
                fontSize="9" fill={g.color} fontWeight="700">
                {g.label}
              </text>
              <text x={g.x} y={g.y+9} textAnchor="middle"
                fontSize="11" fill={WX_COLOR[g.wx] || g.color} fontWeight="700">
                {g.wx}
              </text>
            </g>
          ))}
          
          {/* 关系箭头 */}
          {/* 原神 → 用神（生） */}
          <line x1="73" y1="35" x2="120" y2="25" stroke="#27ae60" strokeWidth="1.2" 
            markerEnd="url(#arrow-good)" opacity="0.7" />
          <text x="95" y="22" fontSize="7" fill="#27ae60">生</text>
          
          {/* 忌神 → 用神（克） */}
          <line x1="207" y1="35" x2="160" y2="25" stroke="#e74c3c" strokeWidth="1.2"
            strokeDasharray="3,2" markerEnd="url(#arrow-bad)" opacity="0.7" />
          <text x="180" y="22" fontSize="7" fill="#e74c3c">克</text>
          
          {/* 仇神 → 忌神（生） */}
          <line x1="195" y1="80" x2="218" y2="60" stroke="#7f8c8d" strokeWidth="1.2"
            markerEnd="url(#arrow-bad)" opacity="0.6" />
          <text x="212" y="78" fontSize="7" fill="#7f8c8d">生</text>
          
          {/* 用神 → 食神（生） */}
          <line x1="125" y1="40" x2="100" y2="82" stroke="#3498db" strokeWidth="1.2"
            markerEnd="url(#arrow-neutral)" opacity="0.6" />
          <text x="103" y="60" fontSize="7" fill="#3498db">泄</text>
          
          {/* 箭头定义 */}
          <defs>
            <marker id="arrow-good" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
              <polygon points="0,0 5,2.5 0,5" fill="#27ae60" />
            </marker>
            <marker id="arrow-bad" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
              <polygon points="0,0 5,2.5 0,5" fill="#e74c3c" />
            </marker>
            <marker id="arrow-neutral" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto">
              <polygon points="0,0 5,2.5 0,5" fill="#3498db" />
            </marker>
          </defs>
        </svg>
      </div>
      
      {/* 五行说明表 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.4rem' }}>
        {items.map((x, i) => (
          <div key={i} style={{
            padding: '0.4rem 0.6rem',
            background: `${x.color}11`,
            border: `1px solid ${x.color}55`,
            borderRadius: 'var(--r-sm)',
            display: 'flex', alignItems: 'center', gap: '0.5rem',
          }}>
            <span style={{ fontSize:'var(--text-xs)', fontWeight: 700, color: x.color, minWidth: '28px' }}>
              {x.label}
            </span>
            <span style={{ fontSize:'var(--text-md)', fontWeight: 700,
              color: WX_COLOR[x.wx] || x.color, minWidth: '14px' }}>{x.wx}</span>
            <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', flex: 1, textAlign: 'right' }}>
              {x.role}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function KeyLinesCard({ keyLines }) {
  if (!keyLines) return null
  const sections = [
    { label: '用神', key: '用神_lines', color: '#d4a040', desc: '所占之事的代表' },
    { label: '原神', key: '原神_lines', color: '#27ae60', desc: '生用神（吉，护神）' },
    { label: '忌神', key: '忌神_lines', color: '#e74c3c', desc: '克用神（凶，敌）' },
    { label: '仇神', key: '仇神_lines', color: '#7f8c8d', desc: '生忌神（助凶，间接敌）' },
  ].filter(s => (keyLines[s.key] || []).length > 0)

  if (sections.length === 0) return null

  return (
    <div className="card" style={{ padding: '0.7rem 1rem', borderLeft: '3px solid #9b59b6' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.55rem' }}>
        四神爻位详查 · 用神为本，原神为护
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {sections.map((s, i) => {
          const lines = keyLines[s.key] || []
          return (
            <div key={i}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.25rem' }}>
                <span style={{
                  fontSize:'var(--text-xs)', fontWeight: 700,
                  background: `${s.color}22`, color: s.color, border: `1px solid ${s.color}55`,
                  padding: '1px 6px', borderRadius: '3px',
                }}>{s.label}</span>
                <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontStyle: 'italic' }}>
                  {s.desc}
                </span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {lines.map((l, li) => {
                  const strength = l.strength?.label || ''
                  const isStrong = ['旺', '相'].includes(strength)
                  const isWeak = ['休', '囚', '死'].includes(strength)
                  const strColor = isStrong ? '#e74c3c' : isWeak ? '#7f8c8d' : 'var(--text-muted)'
                  return (
                    <div key={li} style={{
                      display: 'flex', alignItems: 'center', gap: '0.3rem',
                      padding: '0.3rem 0.5rem',
                      background: `${s.color}0a`,
                      border: `1px solid ${s.color}33`,
                      borderRadius: 'var(--r-sm)',
                      fontSize:'var(--text-xs)',
                    }}>
                      <span style={{ color: 'var(--text-muted)' }}>
                        {['初','二','三','四','五','上'][l.position-1]}爻
                      </span>
                      <span style={{ color: s.color, fontWeight: 600, fontFamily: 'var(--font-serif)' }}>
                        {l.liu_qin}
                      </span>
                      <span style={{ color: s.color, fontWeight: 700, fontFamily: 'var(--font-display)' }}>
                        {l.branch}
                      </span>
                      {l.kong_wang && <span style={{ color: '#e74c3c', fontSize:'var(--text-2xs)', fontWeight: 700 }}>空</span>}
                      {l.is_changing && <span style={{ color: '#d4a040', fontSize:'var(--text-2xs)' }}>动</span>}
                      {l.is_world && <span style={{ color: '#d4a040', fontSize:'var(--text-2xs)', fontWeight: 700,
                        padding: '0 3px', background: 'rgba(212,160,64,0.2)', borderRadius: '2px' }}>世</span>}
                      {l.is_application && <span style={{ color: '#3498db', fontSize:'var(--text-2xs)', fontWeight: 700,
                        padding: '0 3px', background: 'rgba(52,152,219,0.15)', borderRadius: '2px' }}>应</span>}
                      <span style={{ color: strColor, fontSize:'var(--text-2xs)', fontWeight: 700,
                        marginLeft: 'auto', paddingLeft: '0.2rem' }}>
                        {strength}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function LineStrengthCard({ details, keyLines }) {
  if (!details || details.length === 0) return null
  
  // 力量条的范围：combined_force 一般在 -5 到 +12 之间
  const maxAbsForce = 12
  
  // 反向查询：哪些爻位是用神/原神/忌神/仇神
  const yongPos = new Set((keyLines?.['用神_lines'] || []).map(l => l.position))
  const yuanPos = new Set((keyLines?.['原神_lines'] || []).map(l => l.position))
  const jiPos   = new Set((keyLines?.['忌神_lines'] || []).map(l => l.position))
  const chouPos = new Set((keyLines?.['仇神_lines'] || []).map(l => l.position))
  
  const getRoleBadge = (pos) => {
    if (yongPos.has(pos)) return { label: '用神', color: '#d4a040', bg: 'rgba(212,160,64,0.18)' }
    if (yuanPos.has(pos)) return { label: '原神', color: '#27ae60', bg: 'rgba(39,174,96,0.12)' }
    if (jiPos.has(pos))   return { label: '忌神', color: '#e74c3c', bg: 'rgba(231,76,60,0.12)' }
    if (chouPos.has(pos)) return { label: '仇神', color: '#7f8c8d', bg: 'rgba(127,140,141,0.12)' }
    return null
  }
  
  return (
    <div className="card" style={{ padding: '0.7rem 1rem' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.55rem',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>六爻力量评估（月令+日辰，十二长生）</span>
        <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
          力量范围：-5（绝） ↔ +12（极旺）
        </span>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
        {/* 从上到下显示（上爻在顶部） */}
        {[...details].reverse().map((d, ri) => {
          const i = details.length - 1 - ri
          const pos = i + 1
          const forceColor = FORCE_COLOR[d.overall] || 'var(--text-muted)'
          const role = getRoleBadge(pos)
          const force = d.combined_force || 0
          // 力量条宽度（百分比，正向）
          const barWidth = Math.min(Math.abs(force) / maxAbsForce * 100, 100)
          const isPositive = force >= 0
          
          return (
            <div key={i} style={{
              padding: '0.45rem 0.55rem',
              background: role ? role.bg : 'var(--bg-raised)',
              borderLeft: role ? `3px solid ${role.color}` : '3px solid transparent',
              borderRadius: 'var(--r-sm)',
              fontSize: 'var(--text-xs)',
              position: 'relative',
            }}>
              <div style={{ display: 'grid',
                gridTemplateColumns: '24px 60px 1fr 40px',
                gap: '0.4rem', alignItems: 'center', marginBottom: '0.3rem' }}>
                <span style={{ color: 'var(--text-faint)', fontFamily: 'var(--font-display)', fontSize:'var(--text-xs)' }}>
                  {['初','二','三','四','五','上'][i]}爻
                </span>
                <span style={{ color: WX_COLOR[d.wuxing] || 'var(--text-secondary)', fontWeight: 700 }}>
                  {d.liu_qin}{d.branch}
                  {role && (
                    <span style={{ marginLeft: '0.3rem', fontSize:'var(--text-2xs)', fontWeight: 700,
                      padding: '1px 4px', borderRadius: '3px',
                      background: role.color, color: '#000' }}>{role.label}</span>
                  )}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)' }}>
                  月<span style={{ color: STATUS_COLOR[d.month_chs?.status] }}>{d.month_chs?.status || '—'}</span>
                  {' · '}
                  日<span style={{ color: STATUS_COLOR[d.day_chs?.status] }}>{d.day_chs?.status || '—'}</span>
                  {d.is_yuepo && <span style={{ color:'#e74c3c', marginLeft:'0.3rem', fontWeight:700 }}>[月破]</span>}
                  {d.is_ripo && <span style={{ color:'#e74c3c', marginLeft:'0.3rem', fontWeight:700 }}>[日破]</span>}
                </span>
                <span style={{ color: forceColor, fontWeight: 700, fontSize:'var(--text-xs)', textAlign: 'right' }}>
                  {d.overall}
                </span>
              </div>
              
              {/* 力量条 */}
              <div style={{
                position: 'relative', height: '6px', borderRadius: '3px',
                background: 'var(--bg-subtle)', overflow: 'hidden',
              }}>
                {/* 中线（0 位置） */}
                <div style={{
                  position: 'absolute', left: '30%', top: 0, bottom: 0,
                  width: '1px', background: 'var(--text-faint)', opacity: 0.5,
                }} />
                {/* 力量条 */}
                <div style={{
                  position: 'absolute',
                  left: isPositive ? '30%' : `${30 - barWidth * 0.3}%`,
                  width: `${barWidth * (isPositive ? 0.7 : 0.3)}%`,
                  top: 0, bottom: 0,
                  background: `linear-gradient(90deg, transparent, ${forceColor})`,
                  borderRadius: '3px',
                }} />
                {/* 力量数字 */}
                <span style={{
                  position: 'absolute', right: '4px', top: '-1px',
                  fontSize:'var(--text-2xs)', fontFamily: 'var(--font-mono)',
                  color: forceColor, fontWeight: 700,
                }}>
                  {force > 0 ? '+' : ''}{force.toFixed(1)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
      
      <div style={{ marginTop: '0.5rem', fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.6, padding: '0.3rem 0.5rem',
        background: 'rgba(212,160,64,0.04)', borderRadius: 'var(--r-sm)' }}>
        力量分 = 月令长生分（×1.5）+ 日辰长生分（×1.0）；月破/日破额外扣分。
        《卜筮正宗》：用神得令为旺，失令为衰；旺相之爻力强，可决吉凶。
      </div>
    </div>
  )
}

function ChangingRelationsCard({ relations }) {
  if (!relations || relations.length === 0) return null
  
  // 化关系颜色 + 古书评价
  const REL_META = {
    '回头生': { color: '#27ae60', mood: 'good', desc: '化神反生本爻，事必成（大吉）' },
    '回头克': { color: '#c0392b', mood: 'bad',  desc: '化神反克本爻，事必败（大凶）' },
    '化进神': { color: '#27ae60', mood: 'good', desc: '同五行递进，气势渐增' },
    '化退神': { color: '#e74c3c', mood: 'bad',  desc: '同五行递退，气势渐衰' },
    '化空':   { color: '#bdc3c7', mood: 'neutral', desc: '化入旬空，有始无终' },
    '化破':   { color: '#e74c3c', mood: 'bad',  desc: '化爻与月建冲，功败垂成' },
    '化墓':   { color: '#5d6d7e', mood: 'bad',  desc: '化入墓库，事被埋藏' },
    '化绝':   { color: '#4a4a4a', mood: 'bad',  desc: '化入绝地，无气难发' },
    '化同（伏吟、扶持）': { color: '#7f8c8d', mood: 'neutral', desc: '同五行扶持，力量加倍但事重复' },
  }
  
  return (
    <div className="card" style={{ padding: '0.85rem 1rem', borderLeft: '3px solid #e67e22' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.55rem',
        display: 'flex', justifyContent: 'space-between' }}>
        <span>动爻变化分析（共 {relations.length} 处）</span>
        <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontStyle: 'italic' }}>
          《增删卜易·动爻论》
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
        {relations.map((r, i) => {
          const meta = REL_META[r.relation] || { color: '#7f8c8d', mood: 'neutral', desc: r.interpretation }
          const isGood = meta.mood === 'good'
          const isBad = meta.mood === 'bad'
          
          return (
            <div key={i} style={{
              padding: '0.6rem 0.7rem',
              background: isGood ? 'rgba(39,174,96,0.08)' : isBad ? 'rgba(231,76,60,0.08)' : 'var(--bg-raised)',
              borderLeft: `3px solid ${meta.color}`,
              borderRadius: 'var(--r-sm)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                <span style={{
                  fontSize:'var(--text-2xs)', fontWeight: 700,
                  background: 'var(--bg-subtle)', color: 'var(--text-muted)',
                  padding: '1px 5px', borderRadius: '2px',
                }}>第{r.position}爻</span>
                <span style={{ fontSize:'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {r.liu_qin}
                </span>
                
                {/* 化爻流转可视化 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem',
                  marginLeft: 'auto', fontSize:'var(--text-sm)', fontFamily: 'var(--font-display)' }}>
                  <span style={{
                    padding: '2px 8px', borderRadius: '12px',
                    background: `${WX_COLOR[r.orig_wx]}22`,
                    color: WX_COLOR[r.orig_wx],
                    fontWeight: 700, border: `1px solid ${WX_COLOR[r.orig_wx]}55`,
                  }}>
                    {r.orig_branch}
                  </span>
                  <svg width="28" height="14" viewBox="0 0 28 14">
                    <line x1="2" y1="7" x2="22" y2="7" stroke={meta.color} strokeWidth="1.5" />
                    <polygon points="20,3 26,7 20,11" fill={meta.color} />
                  </svg>
                  <span style={{
                    padding: '2px 8px', borderRadius: '12px',
                    background: `${WX_COLOR[r.changed_wx]}22`,
                    color: WX_COLOR[r.changed_wx],
                    fontWeight: 700, border: `1px solid ${WX_COLOR[r.changed_wx]}55`,
                  }}>
                    {r.changed_branch}
                  </span>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.2rem' }}>
                <span style={{
                  fontSize:'var(--text-xs)', fontWeight: 700, color: meta.color,
                  padding: '1px 6px', background: `${meta.color}22`, border: `1px solid ${meta.color}55`,
                  borderRadius: '3px',
                }}>{r.relation}</span>
                <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)' }}>
                  {meta.desc}
                </span>
              </div>
              
              <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)',
                lineHeight: 1.6, fontFamily: 'var(--font-serif)', marginTop: '0.3rem',
                paddingLeft: '0.5rem', borderLeft: '2px solid var(--border)' }}>
                {r.interpretation}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SummaryCard({ summary }) {
  if (!summary || summary.length === 0) return null
  return (
    <div className="card" style={{ padding: '0.65rem 1rem', background: 'var(--bg-subtle)' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
        关键提示
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {summary.map((s, i) => {
          const isBad = s.startsWith('⚠')
          const isGood = s.startsWith('✦')
          return (
            <div key={i} style={{
              fontSize: 'var(--text-xs)',
              color: isBad ? '#e74c3c' : isGood ? '#27ae60' : 'var(--text-secondary)',
              lineHeight: 1.55,
              padding: '2px 0',
            }}>
              {s}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function LiuyaoDeepRelations({ data }) {
  const dr = data?.deep_relations
  if (!dr) {
    return (
      <div className="card" style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>
        本次起卦未启用深度关系分析（仅在指定占问主题时计算）
      </div>
    )
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      <FourGodsCard yyj={dr.yong_yuan_ji_chou} />
      <KeyLinesCard keyLines={dr.key_lines} />
      <ChangingRelationsCard relations={dr.changing_relations} />
      <LineStrengthCard details={dr.line_details} keyLines={dr.key_lines} />
      <SummaryCard summary={dr.summary} />
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-faint)', textAlign:'center',
        padding: '0.3rem', fontFamily: 'var(--font-serif)', lineHeight: 1.6 }}>
        《增删卜易》：用神旺相又有原神生扶 = 大吉；用神死绝又被忌神克 = 大凶<br/>
        忌神动化回头克 = 化解；用神动化回头生 = 大利
      </div>
    </div>
  )
}
