/**
 * XuankongPanel.jsx — 玄空飞星专业排盘面板
 *
 * 调用 /fengshui/xuankong 后端（《沈氏玄空学》专业版）
 * 展示：
 *   - 当前三元九运
 *   - 24 山坐山选择
 *   - 运/山/向三盘合参（九宫网格）
 *   - 令星到位判定（旺山旺向 / 上山下水 / 双星到坐 / 双星到向）
 *   - 特殊格局（合十 / 三般卦 / 七星打劫 / 五黄入山入向）
 *   - 化解建议（按宫位列表）
 *   - 城门诀
 */
import React, { useState, useEffect } from 'react'
import '../../styles/plates.css'
import { clickable } from '../../utils/a11y'
import ShareImage from '../../components/UI/ShareImage'
import XuankongCellDetail from './XuankongCellDetail'
import XuankongAdvanced from './XuankongAdvanced'
import XuankongOverview from './XuankongOverview'
import XuankongSynthesis from './XuankongSynthesis'
import XuankongPerspectives from './XuankongPerspectives'
import XuankongConsistencyAudit from './XuankongConsistencyAudit'
import NarrationPanel from '../../components/NarrationPanel'

const getApiBase = () => {
  try {
    return JSON.parse(localStorage.getItem('bagua-settings') || '{}')?.state?.apiBaseUrl ?? ''
  } catch {
    return ''
  }
}

// 九宫洛书布局（与后端 LUOSHU_POS 一致）
// 4 9 2
// 3 5 7
// 8 1 6
const LUOSHU_GRID = [
  [4, 9, 2],
  [3, 5, 7],
  [8, 1, 6],
]

// 24 山按八卦分组
const MOUNTAIN_GROUPS = [
  { gua: '坎', dir: '北', mountains: [{n:'壬',y:'阳'},{n:'子',y:'阴'},{n:'癸',y:'阴'}], color: '#3498db' },
  { gua: '艮', dir: '东北', mountains: [{n:'丑',y:'阴'},{n:'艮',y:'阳'},{n:'寅',y:'阳'}], color: '#8e44ad' },
  { gua: '震', dir: '东', mountains: [{n:'甲',y:'阳'},{n:'卯',y:'阴'},{n:'乙',y:'阴'}], color: '#27ae60' },
  { gua: '巽', dir: '东南', mountains: [{n:'辰',y:'阴'},{n:'巽',y:'阳'},{n:'巳',y:'阳'}], color: '#16a085' },
  { gua: '离', dir: '南', mountains: [{n:'丙',y:'阳'},{n:'午',y:'阴'},{n:'丁',y:'阴'}], color: '#e74c3c' },
  { gua: '坤', dir: '西南', mountains: [{n:'未',y:'阴'},{n:'坤',y:'阳'},{n:'申',y:'阳'}], color: '#d4a040' },
  { gua: '兑', dir: '西', mountains: [{n:'庚',y:'阳'},{n:'酉',y:'阴'},{n:'辛',y:'阴'}], color: '#95a5a6' },
  { gua: '乾', dir: '西北', mountains: [{n:'戌',y:'阴'},{n:'乾',y:'阳'},{n:'亥',y:'阳'}], color: '#f39c12' },
]

// 九星属性
const NINE_STARS = {
  1: { name:'一白贪狼', element:'水', nature:'吉', color:'#3498db', meaning:'桃花·文学' },
  2: { name:'二黑巨门', element:'土', nature:'大凶', color:'#7f3030', meaning:'病符·疾病' },
  3: { name:'三碧禄存', element:'木', nature:'凶', color:'#a04030', meaning:'是非·官司' },
  4: { name:'四绿文昌', element:'木', nature:'吉', color:'#27ae60', meaning:'文昌·学业' },
  5: { name:'五黄廉贞', element:'土', nature:'大凶', color:'#c0392b', meaning:'灾祸·死亡' },
  6: { name:'六白武曲', element:'金', nature:'吉', color:'#d4a040', meaning:'武职·权力' },
  7: { name:'七赤破军', element:'金', nature:'凶', color:'#9b59b6', meaning:'口舌·血光' },
  8: { name:'八白左辅', element:'土', nature:'大吉', color:'#e8b745', meaning:'财帛·房产' },
  9: { name:'九紫右弼', element:'火', nature:'吉', color:'#e74c3c', meaning:'喜庆·当令' },
}

export default function XuankongPanel() {
  const [year, setYear] = useState(new Date().getFullYear())
  const [analysisYear, setAnalysisYear] = useState(new Date().getFullYear())  // 分析流年（动态辅参）
  const [analysisMonth, setAnalysisMonth] = useState(new Date().getMonth() + 1)  // 分析流月
  const [sitting, setSitting] = useState('子')
  const [degree, setDegree] = useState('')           // 精确度数（可选）
  const [useDegree, setUseDegree] = useState(false)  // 是否启用度数模式
  const [birthYear, setBirthYear] = useState('')     // 主人生年（命卦人盘，可选）
  const [gender, setGender] = useState('male')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState(null)
  const [showShare, setShowShare] = useState(false)
  
  const run = async () => {
    setLoading(true); setErr(null)
    try {
      const body = useDegree && degree !== '' 
        ? { sitting_degree: Number(degree), year, analysis_year: analysisYear, analysis_month: analysisMonth }
        : { sitting_mountain: sitting, year, analysis_year: analysisYear, analysis_month: analysisMonth }
      if (birthYear && Number(birthYear) > 1900) { body.birth_year = Number(birthYear); body.gender = gender }
      const r = await fetch(getApiBase() + '/api/v1/fengshui/xuankong', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const j = await r.json()
      if (j.success === false) throw new Error(j.detail || '请求失败')
      setData(j.data)
    } catch (e) {
      setErr(e.message)
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => { run() }, [])  // 初次加载
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
      {/* 控制面板 */}
      <div className="card" style={{ padding: '0.85rem 1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div className="card-title" style={{ marginBottom: 0 }}>玄空飞星专业排盘</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-faint)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
            《沈氏玄空学》
          </div>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.6rem 0.85rem', alignItems: 'center' }}>
          {/* 年份 */}
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>建宅/入伙年</span>
          <input type="number" min="1864" max="2100" value={year}
            onChange={e => setYear(Number(e.target.value))}
            style={{ padding: '0.35rem 0.6rem', borderRadius: 'var(--r-sm)',
              border: '1px solid var(--border)', background: 'var(--bg-subtle)',
              fontFamily: 'var(--font-mono)', fontSize: '0.85rem', width: '120px' }} />

          {/* 分析流年（动态辅参：本盘定运不变，流年紫白/太岁随此年叠加） */}
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>分析流年</span>
          <input type="number" min="1864" max="2100" value={analysisYear}
            onChange={e => setAnalysisYear(Number(e.target.value))}
            title="本盘定运不变；此年决定流年紫白与太岁之动态叠加（宅静时动）"
            style={{ padding: '0.35rem 0.6rem', borderRadius: 'var(--r-sm)',
              border: '1px solid var(--border)', background: 'var(--bg-subtle)',
              fontFamily: 'var(--font-mono)', fontSize: '0.85rem', width: '120px' }} />

          {/* 分析流月（再细化：流月紫白叠流年，精确到月之吉凶方） */}
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>分析流月</span>
          <input type="number" min="1" max="12" value={analysisMonth}
            onChange={e => setAnalysisMonth(Number(e.target.value))}
            title="流月紫白叠流年，精确到该月之文昌/财位/五黄/病符方"
            style={{ padding: '0.35rem 0.6rem', borderRadius: 'var(--r-sm)',
              border: '1px solid var(--border)', background: 'var(--bg-subtle)',
              fontFamily: 'var(--font-mono)', fontSize: '0.85rem', width: '120px' }} />
          
          {/* 24 山选择 */}
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', alignSelf: 'flex-start', paddingTop: '0.3rem' }}>
            坐山方位
          </span>
          <div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem 0.6rem' }}>
              {MOUNTAIN_GROUPS.map(g => (
                <div key={g.gua} style={{
                  padding: '0.3rem 0.5rem', borderRadius: 'var(--r-sm)',
                  background: `${g.color}11`, border: `1px solid ${g.color}33`,
                }}>
                  <div style={{ fontSize: '0.6rem', color: g.color, fontWeight: 700, marginBottom: '0.2rem',
                    fontFamily: 'var(--font-serif)' }}>
                    {g.gua}·{g.dir}
                  </div>
                  <div style={{ display: 'flex', gap: '2px' }}>
                    {g.mountains.map(m => (
                      <button key={m.n}
                        onClick={() => setSitting(m.n)}
                        title={`${m.n}山 · ${m.y}`}
                        style={{
                          width: '26px', height: '26px',
                          border: sitting === m.n ? `2px solid ${g.color}` : '1px solid var(--border)',
                          background: sitting === m.n ? g.color : 'transparent',
                          color: sitting === m.n ? '#fff' : 'var(--text-secondary)',
                          fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.85rem',
                          borderRadius: '3px', cursor: 'pointer', padding: 0,
                          position: 'relative',
                        }}>
                        {m.n}
                        <span style={{
                          position: 'absolute', top: '-3px', right: '-3px',
                          fontSize: '0.5rem', color: m.y === '阳' ? '#e74c3c' : '#3498db',
                          fontWeight: 700,
                        }}>{m.y === '阳' ? '⊕' : '⊖'}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ fontSize: '0.62rem', color: 'var(--text-faint)', marginTop: '0.4rem', fontFamily: 'var(--font-serif)' }}>
              <span style={{ color:'#e74c3c' }}>⊕</span> 阳山顺飞 ·
              <span style={{ color:'#3498db', marginLeft:'0.3rem' }}>⊖</span> 阴山逆飞（《青囊奥语》挨星诀）
            </div>
            
            {/* 罗盘精确度数（专业派）— 可选 */}
            <div style={{ marginTop: '0.5rem', padding: '0.5rem 0.7rem',
              background: useDegree ? 'rgba(155,89,182,0.08)' : 'var(--bg-subtle)',
              border: `1px solid ${useDegree ? '#9b59b655' : 'var(--border)'}`,
              borderRadius: 'var(--r-sm)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: useDegree ? '0.4rem' : 0 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem',
                  fontSize: '0.72rem', color: 'var(--text-secondary)', cursor: 'pointer',
                  fontFamily: 'var(--font-serif)' }}>
                  <input type="checkbox" checked={useDegree}
                    onChange={e => setUseDegree(e.target.checked)} />
                  🧭 启用罗盘精确度数（专业派下卦/起星判定）
                </label>
              </div>
              {useDegree && (
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                  <input type="number" min="0" max="360" step="0.1" placeholder="0.0 ~ 360.0"
                    value={degree}
                    onChange={e => setDegree(e.target.value)}
                    style={{ padding: '0.3rem 0.5rem', borderRadius: 'var(--r-sm)',
                      border: '1px solid var(--border)', background: 'var(--bg-raised)',
                      fontFamily: 'var(--font-mono)', fontSize: '0.85rem', width: '120px' }} />
                  <span style={{ fontSize: '0.62rem', color: 'var(--text-faint)',
                    fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>
                    每山 15°，子=0°、卯=90°、午=180°、酉=270°；
                    偏离中心 &lt; 3° 为下卦，3°-6° 为起星（替卦），&gt; 6° 兼线过度须重立。
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 主人生年（命卦人盘 — 因人而宜，可选） */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.6rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>主人生年（命卦宜居方，可选）</div>
            <input type="number" min="1900" max="2100" value={birthYear} onChange={e => setBirthYear(e.target.value)}
              placeholder="如 1990" style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>性别</div>
            <select value={gender} onChange={e => setGender(e.target.value)}
              style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }}>
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
        </div>

        <button onClick={run} disabled={loading}
          style={{ marginTop: '0.7rem', width: '100%', padding: '0.55rem',
            background: 'var(--accent)', color: '#fff', border: 'none',
            borderRadius: 'var(--r-md)', fontSize: '0.85rem', fontWeight: 600,
            cursor: loading ? 'wait' : 'pointer' }}>
          {loading ? '排盘中…' : useDegree && degree !== ''
            ? `排盘：${year}年 · 坐山度数 ${degree}° ▶`
            : `排盘：${year}年 · 坐${sitting} ▶`}
        </button>
        
        {err && (
          <div style={{ marginTop: '0.5rem', padding: '0.4rem 0.6rem',
            background: 'rgba(231,76,60,0.1)', borderLeft: '3px solid #e74c3c',
            fontSize: '0.75rem', color: '#e74c3c' }}>
            {err}
          </div>
        )}
      </div>
      
      {data && (
        <>
          <div style={{ display:'flex', justifyContent:'flex-end' }}>
            <button className="btn btn-sm" onClick={() => setShowShare(true)} title="生成分享图">🖼 分享图</button>
          </div>
          <XuankongResult data={data} />
        </>
      )}
      {showShare && <ShareImage data={data} module="xuankong" onClose={() => setShowShare(false)} />}
    </div>
  )
}

function XuankongResult({ data }) {
  const verdictColor = data.verdict_level === 'auspicious_great' ? '#27ae60'
                    : data.verdict_level === 'inauspicious_great' ? '#c0392b'
                    : data.verdict_level === 'mixed' ? '#e67e22'
                    : '#7f8c8d'
  
  // 综合评级
  const overall = data.overall || {}
  const overallColor = overall.grade_level === 'auspicious_great' ? '#27ae60'
                    : overall.grade_level === 'auspicious' ? '#16a085'
                    : overall.grade_level === 'mixed' ? '#e67e22'
                    : overall.grade_level === 'inauspicious' ? '#c0392b'
                    : overall.grade_level === 'inauspicious_great' ? '#8b0000'
                    : '#7f8c8d'
  
  return (
    <>
      {/* 宅运总论 · 定盘（综合总论 hero） */}
      {/* 综合宅论 · 总汇合参（置于最前） */}
      {data.master_synthesis?.available && (() => {
        const QC = { 吉:'#27ae60', 中:'var(--accent)', 凶:'#c0392b' }
        const ms = data.master_synthesis
        const pc = QC[ms.overall_quality] || 'var(--accent)'
        return (
          <div className="card card-glow" style={{ borderTop:`4px solid ${pc}`, marginBottom:'1rem' }}>
            <div className="card-title">综合宅论 · 总汇合参</div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)', fontWeight:600,
              color:pc, marginBottom:'0.5rem' }}>
              {ms.sitting}山{ms.facing}向 · 综评<span style={{ color:pc }}>{ms.overall_quality}</span>
            </div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', lineHeight:1.7,
              color:'var(--text-secondary)', padding:'0.5rem 0.7rem', background:`${pc}10`,
              borderLeft:`4px solid ${pc}`, marginBottom:'0.7rem' }}>
              {ms.headline}
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(170px,1fr))', gap:'6px', marginBottom:'0.7rem' }}>
              {(ms.dimension_verdicts || []).map((dv, i) => {
                const c = QC[dv.quality] || '#888'
                return (
                  <div key={i} style={{ padding:'0.4rem 0.6rem', background:'var(--bg-subtle)',
                    borderRadius:'var(--r-sm)', borderLeft:`3px solid ${c}` }}>
                    <span style={{ fontWeight:700, fontSize:'var(--text-sm)' }}>{dv.dim}</span>
                    <span style={{ color:c, fontSize:'var(--text-xs)', marginLeft:6 }}>{dv.quality}</span>
                    <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginTop:2,
                      fontFamily:'var(--font-serif)', lineHeight:1.5 }}>{dv.verdict}</div>
                  </div>
                )
              })}
            </div>
            {(ms.integrated_paragraphs || []).map((p, i) => (
              <p key={i} style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                lineHeight:1.8, color:'var(--text-secondary)', margin:'0.3rem 0' }}>{p}</p>
            ))}
            {ms.master_advice && (
              <div style={{ marginTop:'0.5rem', padding:'0.5rem 0.7rem', background:'var(--bg-subtle)',
                borderRadius:'var(--r-sm)', fontSize:'var(--text-sm)', fontFamily:'var(--font-serif)',
                color:'var(--text-secondary)' }}>
                <b style={{ color:pc }}>总建议 · </b>{ms.master_advice}
              </div>
            )}
            <NarrationPanel ms={ms} fullData={data} module="xuankong" />
          </div>
        )
      })()}

      <XuankongOverview data={data} />

      {/* 命卦人盘 · 因人宜居方 */}
      {data.mingua_renpan && data.mingua_renpan.available && (
        <div className="card" style={{ marginBottom: '1rem', borderLeft: '4px solid var(--jade)' }}>
          <div className="card-title">命卦人盘 · {data.mingua_renpan.ming_gua}命（{data.mingua_renpan.ming_group}）宜居方</div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
            fontFamily: 'var(--font-serif)', lineHeight: 1.7, marginBottom: '0.6rem' }}>
            {data.mingua_renpan.summary}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '4px' }}>
            {data.mingua_renpan.directions.map((d, i) => {
              const c = d.combine_q === '吉' ? '#27ae60' : d.combine_q === '凶' ? '#c0392b' : '#888'
              return (
                <div key={i} style={{ textAlign: 'center', padding: '0.4rem 0.2rem',
                  background: `${c}10`, borderRadius: 'var(--r-sm)', border: `1px solid ${c}44` }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'var(--text-sm)' }}>{d.direction}</div>
                  <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>理气{d.liqi}·{d.ming_younian}</div>
                  <div style={{ fontSize: 'var(--text-2xs)', color: c, fontWeight: 600 }}>{d.combine}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}
      <XuankongSynthesis data={data} />
      <XuankongPerspectives data={data} />
      <XuankongConsistencyAudit data={data} />

      {/* 下卦 / 起星判定 */}
      {data.chart_type && data.chart_type.type && (
        <div style={{
          padding: '0.55rem 0.85rem',
          background: data.chart_type.valid ? 'rgba(155,89,182,0.08)' : 'rgba(192,57,43,0.1)',
          border: `1px solid ${data.chart_type.valid ? '#9b59b655' : '#c0392b'}`,
          borderRadius: 'var(--r-sm)',
          display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap',
        }}>
          <span style={{
            padding: '2px 8px', borderRadius: '10px',
            background: data.chart_type.valid ? '#9b59b6' : '#c0392b',
            color: '#fff', fontSize: '0.72rem', fontWeight: 700,
            fontFamily: 'var(--font-serif)',
          }}>
            🧭 {data.chart_type.type}
          </span>
          <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
            fontFamily: 'var(--font-serif)', lineHeight: 1.6, flex: 1, minWidth: '200px' }}>
            坐山度数 {data.sitting_degree}° · 偏离中线 {data.chart_type.diff?.toFixed?.(1)}°
            {data.chart_type.ti_star && (
              <span style={{ marginLeft: '0.4rem', color: '#9b59b6', fontWeight: 600 }}>
                替星 {data.chart_type.ti_star}
              </span>
            )}
            <br />
            <span style={{ fontSize: '0.66rem', color: 'var(--text-faint)' }}>
              {data.chart_type.desc}
            </span>
          </span>
        </div>
      )}
      
      {/* ━━ 综合 5 维评级（专业核心） ━━ */}
      {overall.grade && (
        <div className="card" style={{
          padding: '1rem 1.2rem',
          background: `linear-gradient(135deg, ${overallColor}15, ${overallColor}05)`,
          border: `2px solid ${overallColor}66`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            flexWrap: 'wrap', gap: '0.6rem', marginBottom: '0.6rem' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)' }}>
                综合 5 维专业评级
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: overallColor,
                fontFamily: 'var(--font-serif)', marginTop: '0.15rem' }}>
                {overall.grade}
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', marginTop: '0.2rem', lineHeight: 1.6 }}>
                {overall.desc}
              </div>
            </div>
            <div style={{
              padding: '0.6rem 1rem', borderRadius: '14px',
              background: overallColor, color: '#fff',
              fontWeight: 700, fontSize: '1.4rem',
              fontFamily: 'var(--font-display)', textAlign: 'center', minWidth: '70px',
            }}>
              {overall.score > 0 ? '+' : ''}{overall.score}
            </div>
          </div>
          
          {/* 5 维细分 */}
          {overall.factors && overall.factors.length > 0 && (
            <div style={{ marginTop: '0.5rem',
              padding: '0.5rem 0.7rem',
              background: 'var(--bg-raised)', borderRadius: 'var(--r-sm)',
            }}>
              <div style={{ fontSize: '0.62rem', color: 'var(--text-faint)',
                marginBottom: '0.35rem', fontFamily: 'var(--font-serif)' }}>
                ✦ 五维细分（令星 + 零正神 + 反伏吟 + 七星打劫 + 太岁）
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {overall.factors.map((f, i) => {
                  const fc = f.score > 0 ? '#27ae60' : f.score < 0 ? '#c0392b' : '#7f8c8d'
                  return (
                    <div key={i} style={{
                      padding: '0.25rem 0.55rem',
                      background: `${fc}11`, border: `1px solid ${fc}55`,
                      borderRadius: 'var(--r-sm)',
                      fontSize: '0.68rem', display: 'flex', gap: '0.4rem', alignItems: 'center',
                    }}>
                      <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-serif)' }}>
                        {f.dim}
                      </span>
                      <span style={{ color: fc, fontWeight: 700, fontFamily: 'var(--font-display)' }}>
                        {f.score > 0 ? '+' : ''}{f.score}
                      </span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.65rem',
                        fontFamily: 'var(--font-serif)' }}>
                        {f.note.length > 18 ? f.note.slice(0, 18) + '…' : f.note}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* 顶部信息条 */}
      <div className="card card-glow" style={{ padding: '0.85rem 1rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem 1.2rem', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>当令运</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent)',
              fontFamily: 'var(--font-display)' }}>
              {data.yun.yun_name}（{data.yun.yun}运）
            </div>
            <div style={{ fontSize: '0.62rem', color: 'var(--text-faint)' }}>
              {data.yun.sanyuan} · {data.yun.start}-{data.yun.end}
            </div>
          </div>
          <div style={{ width: '1px', height: '40px', background: 'var(--border)' }} />
          <div>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>坐山 → 朝向</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, fontFamily: 'var(--font-display)' }}>
              <span style={{ color: data.sitting_yin_yang === '阳' ? '#e74c3c' : '#3498db' }}>
                {data.sitting_mountain}
              </span>
              <span style={{ color: 'var(--text-faint)', margin: '0 0.3rem', fontSize: '0.85rem' }}>→</span>
              <span style={{ color: data.facing_yin_yang === '阳' ? '#e74c3c' : '#3498db' }}>
                {data.facing_mountain}
              </span>
            </div>
            <div style={{ fontSize: '0.62rem', color: 'var(--text-faint)' }}>
              {data.sitting_gua}卦·{data.sitting_yin_yang} → {data.facing_gua}卦·{data.facing_yin_yang}
            </div>
          </div>
          <div style={{ width: '1px', height: '40px', background: 'var(--border)' }} />
          <div style={{ flex: 1, minWidth: '140px' }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>令星到位判定</div>
            <div style={{
              padding: '0.3rem 0.6rem', borderRadius: '14px',
              background: `${verdictColor}22`, border: `1px solid ${verdictColor}66`,
              color: verdictColor, fontWeight: 700, fontSize: '0.95rem',
              fontFamily: 'var(--font-serif)', display: 'inline-block', marginTop: '2px',
            }}>
              {data.verdict}
            </div>
          </div>
        </div>
        
        <div style={{ marginTop: '0.55rem', padding: '0.5rem 0.7rem',
          background: `${verdictColor}0c`, borderLeft: `3px solid ${verdictColor}`,
          borderRadius: 'var(--r-sm)', fontSize: '0.8rem',
          fontFamily: 'var(--font-serif)', color: 'var(--text-secondary)', lineHeight: 1.75 }}>
          {data.verdict_desc}
        </div>
      </div>
      
      {/* 九宫三盘合参 */}
      <ThreePalaceChart data={data} />
      
      {/* 双星汇宫详解（点击宫位） */}
      <XuankongCellDetail data={data} />

      {/* ── 峦头形理 · 九宫砂水宜忌 ── */}
      {data.luantou_summary && <LuantouCard data={data} />}
      
      {/* ── 高级专业分析（零正神/反伏吟/太岁/流年/收山出煞） ── */}
      <XuankongAdvanced data={data} />
      
      {/* 特殊格局 */}
      {data.special_patterns && data.special_patterns.length > 0 && (
        <SpecialPatternsCard patterns={data.special_patterns} />
      )}
      
      {/* 化解建议 */}
      {data.remedies && data.remedies.length > 0 && (
        <RemediesCard remedies={data.remedies} />
      )}
      
      {/* 城门诀 */}
      {data.chengmen && data.chengmen.desc && (
        <ChengmenCard chengmen={data.chengmen} />
      )}
    </>
  )
}

function ThreePalaceChart({ data }) {
  const currentYun = data.current_yun_star
  const sittingLuoshu = ({ '坎':1,'坤':2,'震':3,'巽':4,'乾':6,'兑':7,'艮':8,'离':9 })[data.sitting_gua]
  const facingLuoshu = ({ '坎':1,'坤':2,'震':3,'巽':4,'乾':6,'兑':7,'艮':8,'离':9 })[data.facing_gua]
  
  return (
    <div className="card" style={{ padding: '1rem 1.1rem' }}>
      <div className="gv-plate">
        <div className="gv-sec-bar" style={{ marginBottom:'16px' }}>
          <span className="gv-seal" style={{ background:'#a890c0', color:'#281840' }}>飞</span>
          <span className="t">九宫三盘合参</span>
          <span className="cap">运 · 山 · 向（左上 / 右上 / 下中）</span>
        </div>
      </div>

      <div className="gv-xk-grid">
        {LUOSHU_GRID.flat().map(pos => {
          const cell = data.combined[pos]
          if (!cell) return <div key={pos} style={{ background:'#fff' }} />

          const isSitting = pos === sittingLuoshu
          const isFacing = pos === facingLuoshu

          // 标记
          let positionTag = null
          if (isSitting && isFacing) positionTag = '坐+向'
          else if (isSitting) positionTag = '坐山'
          else if (isFacing) positionTag = '朝向'

          // 高亮当令星
          const yunIsWang = cell.yun === currentYun
          const mtnIsWang = cell.mountain === currentYun
          const dirIsWang = cell.facing === currentYun

          // 五黄警示
          const has5 = cell.yun === 5 || cell.mountain === 5 || cell.facing === 5

          return (
            <div key={pos} className={`gv-xk-cell${positionTag ? ' mark' : ''}${has5 ? ' warn5' : ''}`}>
              {/* 方位 */}
              <div className="gv-xk-head">
                <span className="gv-xk-dir">{cell.direction}</span>
                {positionTag && <span className="gv-xk-tag">{positionTag}</span>}
              </div>

              {/* 三星显示：山(左上)、向(右上)、运(下中) */}
              <div className="gv-xk-stars">
                {/* 山星（左上） */}
                <div title={`山星 ${NINE_STARS[cell.mountain]?.name}`} className="gv-xk-star"
                  style={{ color: NINE_STARS[cell.mountain]?.color || 'var(--gv-ink-3)' }}>
                  {cell.mountain}
                  {mtnIsWang && <span className="ling">令</span>}
                </div>
                {/* 向星（右上） */}
                <div title={`向星 ${NINE_STARS[cell.facing]?.name}`} className="gv-xk-star"
                  style={{ color: NINE_STARS[cell.facing]?.color || 'var(--gv-ink-3)' }}>
                  {cell.facing}
                  {dirIsWang && <span className="ling">令</span>}
                </div>
                {/* 运星（下中，跨两列） */}
                <div title={`运星 ${NINE_STARS[cell.yun]?.name}`} className="gv-xk-yun"
                  style={{ color: NINE_STARS[cell.yun]?.color || 'var(--gv-ink-3)' }}>
                  ({cell.yun})
                </div>
              </div>
            </div>
          )
        })}
      </div>
      
      {/* 图例 */}
      <div style={{ marginTop: '0.7rem', padding: '0.5rem 0.7rem',
        background: 'var(--bg-subtle)', borderRadius: 'var(--r-sm)',
        fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)',
        lineHeight: 1.7 }}>
        <div style={{ marginBottom: '0.25rem' }}>
          <span style={{ color: 'var(--accent)', fontWeight: 700 }}>读盘法</span>：
          左上 = 山星（管丁口），右上 = 向星（管财帛），下方 = 运星（背景气场）。
        </div>
        <div>
          <span style={{ color: '#27ae60', fontWeight: 700 }}>「令」</span> = 当令旺星（{data.yun.yun_name}）到此宫；
          双星到坐 / 到向是判断旺衰的核心。
        </div>
      </div>
    </div>
  )
}

function SpecialPatternsCard({ patterns }) {
  return (
    <div className="card" style={{ padding: '0.85rem 1rem', borderLeft: '3px solid #9b59b6' }}>
      <div className="card-title">特殊格局识别 <span style={{ fontSize: '0.7rem', color: 'var(--text-faint)', fontWeight: 400 }}>（{patterns.length} 个）</span></div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {patterns.map((p, i) => {
          const color = p.level === 'auspicious_great' ? '#27ae60'
                      : p.level === 'auspicious' ? '#16a085'
                      : p.level === 'inauspicious' ? '#c0392b'
                      : '#7f8c8d'
          return (
            <div key={i} style={{
              padding: '0.55rem 0.75rem', borderRadius: 'var(--r-sm)',
              background: `${color}10`, borderLeft: `3px solid ${color}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.25rem', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color,
                  fontFamily: 'var(--font-serif)' }}>
                  {p.name}
                </span>
                {p.source && (
                  <span style={{ fontSize: '0.6rem', color: 'var(--text-faint)',
                    fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
                    {p.source}
                  </span>
                )}
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
                lineHeight: 1.65, fontFamily: 'var(--font-serif)' }}>
                {p.desc}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function LuantouCard({ data }) {
  const s = data.luantou_summary || {}
  const lt = data.luantou || {}
  const LUOSHU_GRID = [[4,9,2],[3,5,7],[8,1,6]]
  const [sel, setSel] = React.useState(null)
  const qColor = (q) => q==='旺方' ? '#27ae60' : q==='进气方' ? '#7cb342'
    : q==='煞方' ? '#c0392b' : '#a8741a'
  return (
    <div className="card" style={{ padding: '0.85rem 1rem' }}>
      <div className="card-title">峦头形理 · 九宫砂水宜忌</div>
      <p style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
        color:'var(--text-secondary)', lineHeight:1.8, marginBottom:'0.4rem' }}>{s.desc}</p>
      <p style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)',
        fontFamily:'var(--font-serif)', fontStyle:'italic', marginBottom:'0.7rem' }}>{s.principle}</p>

      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'4px', marginBottom:'0.6rem' }}>
        {LUOSHU_GRID.flat().map(pos => {
          const c = lt[pos] || lt[String(pos)]
          if (!c) return <div key={pos} />
          const col = qColor(c.quality)
          return (
            <div key={pos} {...clickable(()=>setSel(sel===pos?null:pos))}
              style={{ cursor:'pointer', textAlign:'center', padding:'0.45rem 0.2rem',
                borderRadius:'var(--r-sm)', background: sel===pos?'var(--accent-bg)':'var(--surface)',
                border:`1px solid ${col}55` }}>
              <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{c.direction}</div>
              <div style={{ fontSize:'var(--text-sm)', fontWeight:700, color:col }}>{c.quality}</div>
              <div style={{ fontSize:'0.6rem', color:'var(--text-faint)' }}>
                山{c.mountain_star}向{c.facing_star}{c.annual_star?`年${c.annual_star}`:''}
              </div>
            </div>
          )
        })}
      </div>

      {sel && lt[sel] && (
        <div style={{ padding:'0.6rem 0.8rem', background:'var(--surface)',
          borderRadius:'var(--r-sm)', border:'1px solid var(--border)' }}>
          <div style={{ fontWeight:700, color:qColor(lt[sel].quality),
            fontFamily:'var(--font-serif)', marginBottom:'0.4rem' }}>
            {lt[sel].direction}方 · {lt[sel].quality}
          </div>
          {lt[sel].advice.map((a,i)=>(
            <p key={i} style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)',
              fontFamily:'var(--font-serif)', lineHeight:1.7, marginBottom:'0.3rem' }}>· {a}</p>
          ))}
          {(lt[sel].flags||[]).map((f,i)=>(
            <p key={i} style={{ fontSize:'var(--text-sm)', color:'#c0392b',
              fontFamily:'var(--font-serif)', lineHeight:1.7 }}>⚠ {f.desc}</p>
          ))}
          {lt[sel].annual_note && (
            <p style={{ fontSize:'var(--text-sm)', color:'var(--accent)',
              fontFamily:'var(--font-serif)', lineHeight:1.7, marginTop:'0.3rem' }}>◈ {lt[sel].annual_note}</p>
          )}
        </div>
      )}
    </div>
  )
}

function RemediesCard({ remedies }) {
  // 分吉/凶
  const ausp = remedies.filter(r => r.is_auspicious)
  const inausp = remedies.filter(r => !r.is_auspicious)
  
  return (
    <div className="card" style={{ padding: '0.85rem 1rem' }}>
      <div className="card-title">化解建议 · 方位布局</div>
      
      {ausp.length > 0 && (
        <>
          <div style={{ fontSize: '0.7rem', color: '#27ae60', fontWeight: 700,
            marginBottom: '0.35rem', marginTop: '0.3rem' }}>
            ✓ 吉位布局（{ausp.length}）
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '0.7rem' }}>
            {ausp.map((r, i) => (
              <RemedyItem key={i} item={r} good={true} />
            ))}
          </div>
        </>
      )}
      
      {inausp.length > 0 && (
        <>
          <div style={{ fontSize: '0.7rem', color: '#c0392b', fontWeight: 700,
            marginBottom: '0.35rem' }}>
            ⚠ 凶位化解（{inausp.length}）
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {inausp.map((r, i) => (
              <RemedyItem key={i} item={r} good={false} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function RemedyItem({ item, good }) {
  const color = good ? '#27ae60' : '#c0392b'
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '46px 1fr',
      gap: '0.6rem', alignItems: 'center',
      padding: '0.4rem 0.55rem',
      background: `${color}0a`, borderLeft: `2px solid ${color}`,
      borderRadius: 'var(--r-sm)', fontSize: '0.73rem',
    }}>
      <span style={{ color, fontWeight: 700, fontSize: '0.75rem',
        fontFamily: 'var(--font-display)', textAlign: 'center' }}>
        {item.direction}
      </span>
      <div>
        <div style={{ color: 'var(--text-primary)', marginBottom: '2px' }}>
          {item.issue}
        </div>
        <div style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)',
          lineHeight: 1.55, fontSize: '0.7rem' }}>
          {item.remedy}
          {item.color_suggestion && (
            <span style={{ marginLeft: '0.4rem', color: 'var(--text-faint)' }}>
              · 色：{item.color_suggestion}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function ChengmenCard({ chengmen }) {
  return (
    <div className="card" style={{ padding: '0.7rem 1rem', borderLeft: '3px solid #d4a040' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        marginBottom: '0.4rem' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>城门诀</div>
        <span style={{ fontSize: '0.6rem', color: 'var(--text-faint)',
          fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          《青囊奥语》
        </span>
      </div>
      <div style={{ display: 'flex', gap: '1.2rem', justifyContent: 'center', alignItems: 'center',
        padding: '0.4rem 0', marginBottom: '0.4rem' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>左城门</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#d4a040',
            fontFamily: 'var(--font-display)' }}>
            {chengmen.left_chengmen}
          </div>
        </div>
        <div style={{ width: '40px', height: '1px', background: 'var(--border)' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>朝向</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)',
            fontFamily: 'var(--font-display)' }}>
            {chengmen.facing}
          </div>
        </div>
        <div style={{ width: '40px', height: '1px', background: 'var(--border)' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>右城门</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#d4a040',
            fontFamily: 'var(--font-display)' }}>
            {chengmen.right_chengmen}
          </div>
        </div>
      </div>
      <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-serif)', lineHeight: 1.7,
        padding: '0.45rem 0.6rem', background: 'rgba(212,160,64,0.05)',
        borderRadius: 'var(--r-sm)' }}>
        {chengmen.desc}
      </div>
    </div>
  )
}
