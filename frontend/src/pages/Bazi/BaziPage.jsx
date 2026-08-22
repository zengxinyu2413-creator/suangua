import BirthFillBar from '../../components/UI/BirthFillBar'
import { clickable } from '../../utils/a11y'
import React, { useState, Component } from 'react'
import BirthForm    from '../../components/UI/BirthForm'
import { BaziVis } from '../../components/particles/Visualizations'
import AiInterpretPanel from '../../components/UI/AiInterpretPanel'
import BaziInsightsBar from './BaziInsightsBar'
import BaziMingjuSynthesis from './BaziMingjuSynthesis'
import BaziPerspectives from './BaziPerspectives'
import BaziConsistencyAudit from './BaziConsistencyAudit'
import BaziTiaohouPanel from './BaziTiaohouPanel'
import BaziSizhuPlate from './BaziSizhuPlate'
import { baziApi, ziweiApi }  from '../../api/client'
import { useNotifyStore, useSettingsStore } from '../../store/settingsStore'
import { useHistoryStore } from '../../store/historyStore'
import { useAuthStore } from '../../store/authStore'
import ShareImage from '../../components/UI/ShareImage'
import NarrationPanel from '../../components/NarrationPanel'

/* ── Error Boundary — prevents blank screen on any render crash ── */
class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(e) { return { error: e } }
  componentDidCatch(e, info) { console.error('BaZi render error:', e, info) }
  render() {
    if (this.state.error) return (
      <div className="card card-danger" style={{ textAlign:'center', padding:'2rem' }}>
        <div style={{ fontSize:'var(--text-2xl)', marginBottom:'0.75rem' }}>⚠</div>
        <p style={{ color:'var(--red-light)', fontFamily:'var(--font-serif)', marginBottom:'0.75rem' }}>
          显示结果时发生错误，请重新点击推算。
        </p>
        <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', fontFamily:'var(--font-mono)' }}>
          {this.state.error.message}
        </div>
        <button className="btn btn-sm" style={{ marginTop:'1rem' }}
          onClick={() => this.setState({ error: null })}>重试</button>
      </div>
    )
    return this.props.children
  }
}

const TABS = [
  { id: 'chart',    label: '命盘' },
  { id: 'profile',  label: '日主' },
  { id: 'fortune',  label: '运势' },
  { id: 'career',   label: '事业' },
  { id: 'marriage', label: '婚姻' },
  { id: 'health',   label: '健康' },
  { id: 'wealth',   label: '财运' },
  { id: 'compat',   label: '合婚' },
  { id: 'chenggu',  label: '称骨' },
]

const WX_COLOR = { 木:'#27ae60', 火:'#e74c3c', 土:'#f39c12', 金:'#95a5a6', 水:'#3498db' }
const defaultBirth = () => ({
  year:1990, month:5, day:22, hour:8, minute:0, gender:'male',
  is_lunar:true, is_leap_month:false, province:null, city:null,
})

export default function BaziPage() {
  const [tab, setTab]       = useState('chart')
  const [birth, setBirth]   = useState(defaultBirth())
  const [birth2, setBirth2] = useState({ ...defaultBirth(), year:1992, month:2, day:15, gender:'female' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState(null)
  const { notify }          = useNotifyStore()
  const { addRecord }       = useHistoryStore()
  const { user, saveChart } = useAuthStore()
  const [showShare, setShowShare] = useState(false)

  const run = async () => {
    setLoading(true); setError(null)
    try {
      let data
      if (tab === 'chart' || tab === 'profile') {
        const b = { ...birth, use_true_solar_time: !!(birth.province || birth.city) }
        data = await baziApi.chart(b)
      }
      else if (tab === 'fortune') {
        const now = new Date()
        data = await baziApi.fortune({
          birth: { ...birth, use_true_solar_time: !!(birth.province || birth.city) },
          query_year: now.getFullYear(), query_month: now.getMonth()+1, query_day: now.getDate()
        })
      }
      else if (tab === 'career')  data = await baziApi.career(birth)
      else if (tab === 'marriage') data = await baziApi.marriage(birth)
      else if (tab === 'health')  data = await baziApi.health(birth)
      else if (tab === 'wealth')  data = await baziApi.wealth(birth)
      else if (tab === 'chenggu') data = await baziApi.chenggu(birth)
      else if (tab === 'compat')  data = await baziApi.compatibility({ person_a: birth, person_b: birth2 })
      setResult(data)
      // Auto-save to history
      if (data && (tab === 'chart' || tab === 'profile') && data.day_master) {
        addRecord({
          module: 'bazi', tab,
          birth: { year:birth.year, month:birth.month, day:birth.day, hour:birth.hour, gender:birth.gender },
          summary: `${data.day_master}日主 · ${data.strength} · ${data.pattern}`,
          pillars: `${data.year_pillar?.tiangan||''}${data.year_pillar?.dizhi||''} ${data.month_pillar?.tiangan||''}${data.month_pillar?.dizhi||''} ${data.day_pillar?.tiangan||''}${data.day_pillar?.dizhi||''} ${data.hour_pillar?.tiangan||''}${data.hour_pillar?.dizhi||''}`,
        })
      }
      notify('计算完成', 'success')
    } catch (e) { setError(e.message); notify(e.message, 'error') }
    finally { setLoading(false) }
  }

  const exportText = () => {
    if (!result) return
    const lines = [
      '════════ 八字命盘 ════════',
      `四柱：${result.year_pillar?.tiangan||''}${result.year_pillar?.dizhi||''} ${result.month_pillar?.tiangan||''}${result.month_pillar?.dizhi||''} ${result.day_pillar?.tiangan||''}${result.day_pillar?.dizhi||''} ${result.hour_pillar?.tiangan||''}${result.hour_pillar?.dizhi||''}`,
      `日主：${result.day_master}（${result.day_master_wuxing}）· ${result.strength}`,
      `格局：${result.pattern} — ${result.pattern_desc||''}`,
      result.taiyuan ? `胎元：${result.taiyuan.label}` : '',
      result.minggong ? `命宫：${result.minggong.label}` : '',
      result.shengong ? `身宫：${result.shengong.label}` : '',
      result.renyuan_siling?.phase ? `人元司令：${result.renyuan_siling.phase}` : '',
      result.true_solar_time ? `真太阳时：${result.true_solar_time.corrected}（校正${result.true_solar_time.diff_minutes}分钟）` : '',
      '',
      `神煞：${(result.shensha||[]).map(s=>s.name).join('、')}`,
      '',
      '═══════════════════════════',
      `生成时间：${new Date().toLocaleString()}`,
      '中国术数平台',
    ].filter(Boolean).join('\n')
    navigator.clipboard.writeText(lines).then(() => notify('命盘已复制到剪贴板', 'success'))
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">八字推演</div>
          <div className="page-subtitle">四柱命理 · 干支五行 · 十神格局 · 大运流年</div>
        </div>
        {result && result.day_master && (
          <div style={{ display:'flex', gap:6 }}>
            <button className="btn btn-sm" onClick={exportText} title="复制命盘文本">📋 导出</button>
            <button className="btn btn-sm" onClick={() => setShowShare(true)} title="生成分享图">🖼 分享图</button>
            {user && (
              <button className="btn btn-sm" onClick={async () => {
                try {
                  await saveChart('bazi',
                    `${result.day_master}日主·${result.pattern}`,
                    `${result.year_pillar?.tiangan||''}${result.year_pillar?.dizhi||''} ${result.month_pillar?.tiangan||''}${result.month_pillar?.dizhi||''} ${result.day_pillar?.tiangan||''}${result.day_pillar?.dizhi||''} ${result.hour_pillar?.tiangan||''}${result.hour_pillar?.dizhi||''}`,
                    birth, result, '')
                  notify('已保存到云端', 'success')
                } catch { notify('保存失败', 'error') }
              }} title="保存到云端">☁ 保存</button>
            )}
          </div>
        )}
      </div>
      {showShare && <ShareImage data={result} module="bazi" onClose={() => setShowShare(false)} />}
      <div className="page-body">
        <div className="page-cols">
          {/* Left: input form */}
          <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
            {/* Tab selector — vertical pill list */}
            <div className="card" style={{ padding:'0.75rem 0.65rem' }}>
              <div style={{ fontSize:'var(--text-2xs)', textTransform:'uppercase', letterSpacing:'0.08em',
                color:'var(--text-faint)', fontWeight:700, marginBottom:'0.5rem', paddingLeft:'0.2rem' }}>
                分析类型
              </div>
              <div style={{ display:'flex', flexDirection:'column', gap:'2px' }}>
                {TABS.map(t => (
                  <button key={t.id} onClick={() => { setTab(t.id); setResult(null) }}
                    style={{
                      padding:'0.52rem 0.75rem', borderRadius:'var(--r-md)',
                      border:`1px solid ${tab===t.id?'var(--accent-dim)':'transparent'}`,
                      background:tab===t.id?'var(--accent-bg)':'transparent',
                      color:tab===t.id?'var(--accent)':'var(--text-secondary)',
                      fontSize:'var(--text-sm)', fontWeight:tab===t.id?600:500,
                      cursor:'pointer', textAlign:'left', transition:'all var(--t-fast)',
                    }}>{t.label}</button>
                ))}
              </div>
            </div>
            <BirthFillBar currentValues={birth} onFill={setBirth} />
            <BirthForm values={birth} onChange={setBirth} title={tab==='compat'?'当事人 A':'出生信息'} />
            {tab === 'compat' && <BirthForm values={birth2} onChange={setBirth2} title="当事人 B" />}
            <button className="btn btn-primary btn-full btn-lg" onClick={run} disabled={loading}>
              {loading ? '推算中…' : '开始推算 ▶'}
            </button>
            {error && <div className="error-box">⚠ {error}</div>}

            {/* ── 八字反查工具 ── */}
            <ReverseToolCard />
          </div>
          {/* Right: results */}
          <div>
            {loading && <div className="loading"><div className="spinner"/><p>正在推演命盘…</p></div>}
            {!loading && (
              <ErrorBoundary key={tab}>
                {result
                  ? <BaziResult tab={tab} data={result} birth={birth} />
                  : <BaziPlaceholder tab={tab} />}
              </ErrorBoundary>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function BaziPlaceholder({ tab }) {
  const descs = {
    chart:   '输入出生信息，推算四柱八字命盘、十神分布、格局神煞',
    profile: '深度解析日主性格特质、用神喜忌、幸运方向',
    fortune: '推算大运（十年周期）、流年运势、流月走向',
    career:  '根据命局五行分析最适合的职业方向与工作风格',
    marriage:'分析婚姻宫、配偶星，论断感情婚缘吉凶',
    health:  '五行偏枯分析，了解易患疾病与养生建议',
    wealth:  '财星分析，评估财富积累能力与理财方向',
    compat:  '两人八字对比，五行生克合冲，论断合婚吉凶',
  }
  return (
    <div className="card result-placeholder">
      <div className="result-placeholder-icon">☰</div>
      <p className="result-placeholder-text">{descs[tab]}</p>
    </div>
  )
}

function BaziResult({ tab, data, birth }) {
  if (tab === 'chart')    return <><ChartResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="命盘" /></>
  if (tab === 'profile')  return <><ProfileResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="日主性格" /></>
  if (tab === 'fortune')  return <><FortuneResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="运势" /></>
  if (tab === 'career')   return <><CareerResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="事业" /></>
  if (tab === 'marriage') return <><MarriageResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="婚姻" /></>
  if (tab === 'health')   return <><HealthResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="健康" /></>
  if (tab === 'wealth')   return <><WealthResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="财运" /></>
  if (tab === 'compat')   return <><CompatResult data={data} /><AiInterpretPanel module="bazi" data={data} extraContext="合婚" /></>
  if (tab === 'chenggu')  return <ChengguResult data={data} />
  return null
}

/* ── Chart ── */
function ChartResult({ data }) {
  const q = data.strength_info?.monthly_status
  const shensha = data.shensha || []
  const pillars = ['year_pillar','month_pillar','day_pillar','hour_pillar'].map(k=>data[k]).filter(Boolean)
  return (
    <div className="result-section">
      {pillars.length > 0 && <BaziVis pillars={pillars} dayun={data.dayun||[]}/>}

      {/* ── 命局总论（连贯叙述，串起各项·非词条罗列）── */}
      {/* ── 综合论断 · 总汇合参（全功能激活后的最终汇总，置于最前）── */}
      {data.master_synthesis?.available && (() => {
        const QC = { 吉:'#27ae60', 中:'var(--accent)', 凶:'#c0392b' }
        const ms = data.master_synthesis
        const pc = QC[ms.overall_quality] || 'var(--accent)'
        return (
          <div className="card card-glow" style={{ borderTop:`4px solid ${pc}`, marginBottom:'1rem' }}>
            <div className="card-title">综合论断 · 总汇合参</div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)', fontWeight:600,
              color:pc, marginBottom:'0.6rem' }}>
              {ms.day_master}日主 · {ms.ming_label} · 综评<span style={{ color:pc }}>{ms.overall_quality}</span>
            </div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', lineHeight:1.7,
              color:'var(--text-secondary)', padding:'0.5rem 0.7rem', background:`${pc}10`,
              borderLeft:`4px solid ${pc}`, marginBottom:'0.7rem' }}>
              {ms.headline}
            </div>
            {/* 单点：分域速览 */}
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))', gap:'6px', marginBottom:'0.7rem' }}>
              {(ms.dimension_verdicts || []).map((dv, i) => {
                const c = QC[dv.quality] || '#888'
                return (
                  <div key={i} style={{ padding:'0.4rem 0.6rem', background:'var(--bg-subtle)',
                    borderRadius:'var(--r-sm)', borderLeft:`3px solid ${c}` }}>
                    <span style={{ fontWeight:700, fontSize:'var(--text-sm)' }}>{dv.domain}</span>
                    <span style={{ color:c, fontSize:'var(--text-xs)', marginLeft:6 }}>{dv.quality}</span>
                    <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginTop:2,
                      fontFamily:'var(--font-serif)', lineHeight:1.5 }}>{dv.verdict}</div>
                  </div>
                )
              })}
            </div>
            {/* 组合：汇总段落 */}
            {(ms.integrated_paragraphs || []).map((p, i) => (
              <p key={i} style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                lineHeight:1.8, color:'var(--text-secondary)', margin:'0.3rem 0' }}>{p}</p>
            ))}
            {/* 汇总：总建议 */}
            {ms.master_advice && (
              <div style={{ marginTop:'0.5rem', padding:'0.5rem 0.7rem', background:'var(--bg-subtle)',
                borderRadius:'var(--r-sm)', fontSize:'var(--text-sm)', fontFamily:'var(--font-serif)',
                color:'var(--text-secondary)' }}>
                <b style={{ color:pc }}>总建议 · </b>{ms.master_advice}
              </div>
            )}
            <NarrationPanel ms={ms} fullData={data} module="bazi" companions={[{ module:'ziwei', label:'紫微', fetch: async () => (await ziweiApi.chart({ year:+birth.year, month:+birth.month, day:+birth.day, hour:+birth.hour, gender:birth.gender, is_lunar:birth.is_lunar })).data }]} />
          </div>
        )
      })()}

      {data.overview?.available && (() => {
        const QC = { 吉:'#27ae60', 中:'var(--accent)', 凶:'#c0392b' }
        const ov = data.overview
        const pc = QC[ov.quality] || 'var(--accent)'
        const WXC = { 木:'#27ae60', 火:'#e74c3c', 土:'#f39c12', 金:'#95a5a6', 水:'#3498db' }
        return (
          <div className="card card-glow" style={{ borderTop:`3px solid ${pc}` }}>
            <div className="card-title">命局总论 · 定盘</div>

            {/* 命局定盘·第一眼即见 */}
            <div style={{ display:'flex', alignItems:'center', gap:'0.9rem', flexWrap:'wrap',
              padding:'0.7rem 0.9rem', marginBottom:'0.75rem',
              background:`${pc}10`, borderLeft:`4px solid ${pc}` }}>
              <div style={{ display:'flex', flexDirection:'column', alignItems:'center', flexShrink:0 }}>
                <div style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-2xl)',
                  fontWeight:700, color:WXC[data.day_master_wuxing]||'var(--accent)', lineHeight:1 }}>
                  {data.day_master}
                </div>
                <div style={{ fontSize:'var(--text-2xs)', color:'var(--text-faint)', marginTop:2 }}>日主</div>
              </div>
              <div style={{ minWidth:0, flex:1 }}>
                <div style={{ display:'flex', alignItems:'center', gap:'0.45rem', flexWrap:'wrap' }}>
                  <span style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)',
                    color:'var(--text-primary)', fontWeight:600 }}>{ov.pattern || data.pattern}</span>
                  {ov.pattern_status && (
                    <span style={{ fontSize:'var(--text-xs)', fontWeight:700, color:pc,
                      padding:'1px 8px', background:`${pc}1a`, border:`1px solid ${pc}55` }}>
                      {ov.pattern_status}
                    </span>
                  )}
                  <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>· {data.strength}</span>
                </div>
                <div style={{ display:'flex', gap:'0.6rem', marginTop:'0.35rem', flexWrap:'wrap',
                  fontSize:'var(--text-xs)' }}>
                  {ov.yong_shen_wx && <span style={{ color:WXC[ov.yong_shen_wx] }}>用神 <b>{ov.yong_shen_wx}</b></span>}
                  {ov.ji_shen_wx && <span style={{ color:WXC[ov.ji_shen_wx] }}>忌神 <b>{ov.ji_shen_wx}</b></span>}
                </div>
                {ov.verdict_line && (
                  <div style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)',
                    fontFamily:'var(--font-serif)', lineHeight:1.6, marginTop:'0.35rem' }}>
                    {ov.verdict_line}
                  </div>
                )}
              </div>
            </div>

            {/* 逐节详论 */}
            <div style={{ display:'flex', flexDirection:'column', gap:'0.55rem' }}>
              {ov.paragraphs.filter(p => p.title !== '一生大局').map((p,i) => (
                <p key={i} style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)',
                  lineHeight:1.95, color:'var(--text-secondary)', margin:0 }}>
                  <span style={{ color:'var(--accent)', fontWeight:700 }}>{p.title}　</span>
                  {p.text}
                </p>
              ))}
            </div>
          </div>
        )
      })()}

      <BaziMingjuSynthesis data={data} />
      <BaziPerspectives data={data} />
      <BaziConsistencyAudit data={data} />
      <BaziInsightsBar data={data} />
      <BaziTiaohouPanel chart={data} />
      <div className="card">
        <BaziSizhuPlate chart={data} />
        <div style={{ marginTop:'1.25rem' }}>
          <div className="kv-grid">
            <span className="kv-label">日主</span>
            <span className="kv-value accent">{data.day_master}（{data.day_master_wuxing}）</span>
            <span className="kv-label">身强弱</span>
            <span className="kv-value">
              {data.strength}
              {q && <span className="badge badge-muted" style={{ marginLeft:'0.5rem', fontSize:'var(--text-xs)' }}>{q}</span>}
            </span>
            <span className="kv-label">月令</span>
            <span className="kv-value">
              {data.strength_info?.deling ? (
                <>✓ <strong style={{ color:'var(--jade)' }}>得令</strong>（{q}）</>
              ) : data.strength_info?.deqi ? (
                <>◐ <strong style={{ color:'var(--gold)' }}>得气</strong>（{q} — 月令生身但非同气）</>
              ) : (
                <>✗ 不得令（{q}）</>
              )}
              <span style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginLeft:'0.5rem' }}>
                帮{data.strength_info?.help_score || 0}/泄{data.strength_info?.drain_score || 0}
              </span>
            </span>
            <span className="kv-label">格局</span>
            <span className="kv-value accent">{data.pattern}</span>
            <span className="kv-label">格局解</span>
            <span className="kv-value" style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)' }}>{data.pattern_desc}</span>
          </div>
        </div>

        {/* ── 胎元·命宫·身宫·人元司令 ── */}
        <div style={{ display:'flex', flexWrap:'wrap', gap:'0.5rem', marginTop:'0.75rem' }}>
          {data.taiyuan && <span className="badge badge-gold">胎元 {data.taiyuan.label}</span>}
          {data.minggong && <span className="badge badge-jade">命宫 {data.minggong.label}</span>}
          {data.shengong && <span className="badge badge-muted">身宫 {data.shengong.label}</span>}
          {data.renyuan_siling?.phase && <span className="badge" style={{ background:'rgba(207,59,44,0.1)', color:'var(--accent)', border:'1px solid var(--accent-dim)' }}>人元 {data.renyuan_siling.phase}</span>}
        </div>

        {/* ── 真太阳时校正 ── */}
        {data.true_solar_time && (
          <div style={{ marginTop:'0.5rem', fontSize:'var(--text-xs)', color:'var(--text-muted)', fontFamily:'var(--font-mono)', padding:'0.4rem 0.6rem', background:'var(--bg-subtle)', borderLeft:'2px solid var(--accent-dim)' }}>
            真太阳时：{data.true_solar_time.original} → {data.true_solar_time.corrected}（{data.true_solar_time.city} {data.true_solar_time.longitude}°E，校正{data.true_solar_time.diff_minutes>0?'+':''}{data.true_solar_time.diff_minutes}分钟）
          </div>
        )}
      </div>

      {shensha.length > 0 && (
        <div className="card">
          <div className="card-title">神煞 · 特殊星曜</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:'0.5rem', marginBottom:'0.75rem' }}>
            {shensha.map((s, i) => (
              <span key={i} className="badge badge-gold">{s.name} · {s.pillar}</span>
            ))}
          </div>
          <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', fontFamily:'var(--font-serif)', lineHeight:1.7 }}>
            {shensha.some(s=>s.name==='天乙贵人') && <div>◆ 天乙贵人：一生贵人相助，化险为夷，遇难呈祥</div>}
            {shensha.some(s=>s.name==='文昌贵人') && <div>◆ 文昌贵人：智慧聪颖，学业顺遂，利于考试功名</div>}
            {shensha.some(s=>s.name==='驿马') && <div>◆ 驿马星：主动荡奔波，利出行、移居、外出求财</div>}
            {shensha.some(s=>s.name==='华盖') && <div>◆ 华盖星：孤高有才，利文艺宗教，但有孤独之象</div>}
            {shensha.some(s=>s.name==='羊刃') && <div>◆ 羊刃星：性格刚猛，有武职之才，但需防意外血光</div>}
            {/* ── 新增 8 神煞断语（《三命通会》《滴天髓》）── */}
            {shensha.some(s=>s.name==='天德贵人') && <div>◆ 天德贵人：行善积德，逢凶化吉，主一生有阴德庇佑</div>}
            {shensha.some(s=>s.name==='月德贵人') && <div>◆ 月德贵人：阴柔之德，暗中庇佑，主慈悲心善、得长辈缘</div>}
            {shensha.some(s=>s.name==='学堂') && <div>◆ 学堂：学业有成，利读书科考，主聪明早慧</div>}
            {shensha.some(s=>s.name==='词馆') && <div>◆ 词馆：文章名世，主口才文采、利文职清贵</div>}
            {shensha.some(s=>s.name==='国印') && <div>◆ 国印：贵人之印，主官职权柄，利从政掌印</div>}
            {shensha.some(s=>s.name==='天罗') && <div>◆ 天罗：丙丁日见戌亥，主男命困顿，事业多阻</div>}
            {shensha.some(s=>s.name==='地网') && <div>◆ 地网：壬癸日见辰巳，主女命困束，婚姻不顺</div>}
            {shensha.some(s=>s.name==='灾煞') && <div>◆ 灾煞：与劫煞相对，主突发灾难、需防意外</div>}
            {shensha.some(s=>s.name==='魁罡') && <div>◆ 魁罡贵格：性格刚毅果敢，富贵双全，但忌冲克</div>}
            {shensha.some(s=>s.name==='金舆') && <div>◆ 金舆：宝贵之星，主衣食富贵，多得贤助</div>}
            {shensha.some(s=>s.name==='红艳煞') && <div>◆ 红艳煞：风流多情，桃花重，需防情劫</div>}
            {shensha.some(s=>s.name==='天厨贵人') && <div>◆ 天厨贵人：食禄丰厚，衣食无忧</div>}
            {shensha.some(s=>s.name==='桃花') && <div>◆ 桃花星：异性缘佳，多才多艺，但需防色困</div>}
            {shensha.some(s=>s.name==='将星') && <div>◆ 将星：领袖之才，主威权统率</div>}
            {shensha.some(s=>s.name==='孤辰') && <div>◆ 孤辰：易孤独清冷，男命忌见</div>}
            {shensha.some(s=>s.name==='寡宿') && <div>◆ 寡宿：易孤独寡居，女命忌见</div>}
            {shensha.some(s=>s.name==='劫煞') && <div>◆ 劫煞：主破财、灾祸，需谨慎理财</div>}
            {shensha.some(s=>s.name==='亡神') && <div>◆ 亡神：主消耗失去，但亦主谋略</div>}
            {shensha.some(s=>s.name==='咸池') && <div>◆ 咸池（桃花）：异性缘重，需防淫煞</div>}
          </div>
        </div>
      )}

      {/* 人生四域详断（全功能激活：事业/财运/婚姻/健康 各专域单点专断） */}
      {data.life_aspects && (() => {
        const la = data.life_aspects
        const WXC = { 木:'#27ae60', 火:'#e74c3c', 土:'#f39c12', 金:'#95a5a6', 水:'#3498db' }
        const asText = (v) => Array.isArray(v) ? v.join('；') : (v || '')
        const domains = [
          ['career', '事业', la.career, (c) => ({
            line: c.analysis,
            tags: c.career_fields || [],
            extra: asText(c.shishen_advice),
          })],
          ['wealth', '财运', la.wealth, (w) => ({
            line: w.analysis, sub: w.level,
            tags: w.wealth_wx ? [`财星五行·${w.wealth_wx}`] : [],
            extra: asText(w.advice),
          })],
          ['marriage', '婚姻', la.marriage, (m) => ({
            line: m.analysis, sub: m.quality,
            tags: (m.spouse_stars || []).length ? [`配偶星·${(m.spouse_stars||[]).join('')}`] : [],
            extra: asText(m.advice),
          })],
          ['health', '健康', la.health, (h) => ({
            line: h.analysis,
            tags: [h.dm_organ && `日主·${h.dm_organ}`, h.weak_organ && `宜养·${h.weak_organ}`].filter(Boolean),
            extra: asText(h.advice),
          })],
        ].filter(([k, , v]) => v)
        if (!domains.length) return null
        return (
          <div className="card">
            <div className="card-title">人生四域详断 · 事业 / 财运 / 婚姻 / 健康</div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(260px,1fr))', gap:'10px' }}>
              {domains.map(([key, label, v, fn]) => {
                const info = fn(v)
                return (
                  <div key={key} style={{ padding:'0.7rem 0.8rem', background:'var(--bg-subtle)',
                    borderRadius:'var(--r-md)', borderTop:'2px solid var(--accent)' }}>
                    <div style={{ fontWeight:700, fontSize:'var(--text-base)', marginBottom:'0.3rem' }}>{label}</div>
                    {info.sub && <div style={{ fontSize:'var(--text-xs)', color:'var(--accent)', marginBottom:4 }}>{info.sub}</div>}
                    <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)', lineHeight:1.7,
                      color:'var(--text-secondary)' }}>{info.line}</div>
                    {(info.tags || []).length > 0 && (
                      <div style={{ display:'flex', flexWrap:'wrap', gap:4, margin:'0.4rem 0' }}>
                        {info.tags.map((t, i) => (
                          <span key={i} style={{ fontSize:'var(--text-xs)', padding:'1px 7px',
                            background:'var(--bg-card)', borderRadius:'var(--r-sm)', color:'var(--text-faint)' }}>{t}</span>
                        ))}
                      </div>
                    )}
                    {info.extra && (
                      <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginTop:4,
                        fontFamily:'var(--font-serif)', lineHeight:1.6 }}>建议：{info.extra}</div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )
      })()}

      {/* D: 组合断（神煞组合 + 格局成破评断） */}
      {data.combos && (
        <div className="card">
          <div className="card-title">组合断 · 格局成破 / 神煞相会</div>
          {data.combos.geju_evaluation?.verdict && (
            <div style={{ marginBottom:'0.7rem', padding:'0.6rem 0.85rem',
              borderRadius:'var(--r-sm)', background:'var(--accent-glow)',
              borderLeft:`3px solid ${
                data.combos.geju_evaluation.quality==='吉' ? '#27ae60' :
                data.combos.geju_evaluation.quality==='凶' ? '#c0392b' : 'var(--accent-dim)'}`,
              fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
              color:'var(--text-secondary)', lineHeight:1.75 }}>
              <b style={{ color:'var(--accent)' }}>
                {data.combos.geju_evaluation.status || '格局'}
              </b>　{data.combos.geju_evaluation.verdict}
            </div>
          )}
          {data.combos.shensha_combos?.combos?.length > 0 && (
            <div style={{ display:'flex', flexDirection:'column', gap:'0.4rem' }}>
              {data.combos.shensha_combos.combos.map((cb, i) => {
                const col = cb.nature==='吉' ? '#27ae60' : cb.nature==='凶' ? '#c0392b' : 'var(--accent-dim)'
                return (
                  <div key={i} style={{ display:'grid', gridTemplateColumns:'auto 1fr',
                    gap:'0.5rem', alignItems:'start', padding:'0.35rem 0.5rem',
                    background:'var(--bg-raised)', borderLeft:`3px solid ${col}`,
                    borderRadius:'var(--r-sm)' }}>
                    <span style={{ fontSize:'var(--text-sm)', fontWeight:700, color:col,
                      fontFamily:'var(--font-serif)', whiteSpace:'nowrap' }}>{cb.name}</span>
                    <span style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)',
                      fontFamily:'var(--font-serif)', lineHeight:1.6 }}>{cb.desc}</span>
                  </div>
                )
              })}
              <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)',
                fontFamily:'var(--font-serif)', fontStyle:'italic', marginTop:'0.2rem' }}>
                {data.combos.shensha_combos.summary}
              </div>
            </div>
          )}
        </div>
      )}

      {data.shishen_summary?.length > 0 && (
        <div className="card">
          <div className="card-title">十神分布 · 五行力量</div>
          <div style={{ display:'flex', flexDirection:'column', gap:'0.5rem' }}>
            {data.shishen_summary?.map((s, i) => {
              const SHISHEN_MEANING = {
                '比肩':'同类帮扶，主自立独立', '劫财':'竞争争财，主决断魄力',
                '食神':'发泄才华，主口福享乐', '伤官':'才华过人，主创新突破',
                '正财':'踏实求财，主正职薪资', '偏财':'意外之财，主投资偏业',
                '正官':'约束规范，主仕途地位', '七杀':'权威魄力，主竞争压力',
                '正印':'学问贵人，主文化修养', '偏印':'偏门技艺，主独特才能',
              }
              return (
                <div key={i} style={{ padding:'0.5rem 0.75rem', background:'var(--bg-raised)', borderRadius:'var(--radius-sm)', border:'1px solid var(--border)' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:'0.75rem', marginBottom:'0.25rem' }}>
                    <span style={{ width:'48px', color:'var(--accent)', fontFamily:'var(--font-display)', fontWeight:600 }}>{s.shishen}</span>
                    <div style={{ flex:1, background:'var(--bg-overlay)', borderRadius:0, height:'6px', overflow:'hidden' }}>
                      <div style={{ width:`${Math.min(100,s.count*22)}%`, height:'100%', background:'var(--accent)', borderRadius:0 }} />
                    </div>
                    <span style={{ width:'24px', textAlign:'right', color:'var(--text-muted)', fontSize:'var(--text-sm)' }}>{s.count}</span>
                    <span className="badge badge-muted" style={{ fontSize:'var(--text-xs)' }}>{s.strength}</span>
                  </div>
                  <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', paddingLeft:'56px' }}>{SHISHEN_MEANING[s.shishen]||''}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}
      {/* ── 传统断语 · 古籍原文（综合总论之据，AI 解读之本）── */}
      {data.classical_statements?.available && (
        <div className="card" style={{ borderLeft:'3px solid #a8741a' }}>
          <div className="card-title">传统断语 · 古籍精要</div>
          <div style={{ display:'flex', flexDirection:'column', gap:'0.55rem' }}>
            {data.classical_statements.statements.map((s,i) => (
              <div key={i} style={{ padding:'0.5rem 0.7rem', background:'var(--bg-raised)',
                borderLeft:'2px solid rgba(168,116,26,0.5)' }}>
                <div style={{ display:'flex', gap:'0.4rem', alignItems:'baseline', marginBottom:'2px', flexWrap:'wrap' }}>
                  <span style={{ fontSize:'var(--text-xs)', fontWeight:700, color:'#a8741a',
                    fontFamily:'var(--font-serif)' }}>{s.source}</span>
                  <span style={{ fontSize:'var(--text-2xs)', color:'var(--text-faint)' }}>{s.topic} · {s.title}</span>
                </div>
                <div style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)',
                  fontFamily:'var(--font-serif)', lineHeight:1.8 }}>{s.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Profile (日主深度) ── */
function ProfileResult({ data }) {
  const p = data.day_master_profile || {}
  const y = data.yong_shen || {}
  const rec = y.recommendations || {}
  const WX_COLOR = { 木:'#27ae60', 火:'#e74c3c', 土:'#f39c12', 金:'#95a5a6', 水:'#3498db' }
  const lucky = p.lucky || {}
  const health = p.health || {}
  const rels = p.relationships || {}

  return (
    <div className="result-section">
      <div className="card" style={{ borderColor:'var(--accent-dim)', background:'var(--accent-glow)' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'1rem', marginBottom:'1rem' }}>
          <div style={{ fontSize:'var(--text-display)', fontFamily:'var(--font-display)', color:'var(--accent)', lineHeight:1 }}>{data.day_master}</div>
          <div>
            <div style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-lg)', color:'var(--accent)' }}>{p.title}</div>
            <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginTop:'0.2rem' }}>
              {data.day_master_wuxing} · {data.strength} · {data.pattern}
            </div>
          </div>
        </div>
        <p style={{ fontFamily:'var(--font-serif)', lineHeight:1.8, color:'var(--text-secondary)' }}>{p.personality_detail}</p>
      </div>

      <div className="card">
        <div className="card-title">性格特质</div>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.5rem' }}>
          <div>
            <div style={{ fontSize:'var(--text-sm)', color:'#27ae60', marginBottom:'0.35rem', fontWeight:600 }}>✦ 优势</div>
            {(p.strengths||[]).map((s,i) => (
              <div key={i} style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', display:'flex', gap:'0.4rem', marginBottom:'0.2rem' }}>
                <span style={{ color:'#27ae60', flexShrink:0 }}>◆</span>{s}
              </div>
            ))}
          </div>
          <div>
            <div style={{ fontSize:'var(--text-sm)', color:'var(--red-light)', marginBottom:'0.35rem', fontWeight:600 }}>✦ 注意</div>
            {(p.weaknesses||[]).map((s,i) => (
              <div key={i} style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', display:'flex', gap:'0.4rem', marginBottom:'0.2rem' }}>
                <span style={{ color:'var(--red-light)', flexShrink:0 }}>◆</span>{s}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">用神喜忌分析</div>
        <div style={{ display:'flex', gap:'0.5rem', flexWrap:'wrap', marginBottom:'0.75rem' }}>
          {[['用神',y.yong_shen_wx,'#27ae60'],['喜神',y.xi_shen_wx,'#3498db'],
            ['忌神',y.ji_shen_wx,'var(--red-light)'],['仇神',y.chou_shen_wx,'#e67e22']].map(([label,wx,color]) => wx && (
            <div key={label} style={{ padding:'0.5rem 0.85rem', borderRadius:'var(--radius-md)',
              background:'var(--bg-raised)', border:`1px solid ${color}44`, textAlign:'center', minWidth:'80px' }}>
              <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{label}</div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-xl)', color }}>
                {wx}
              </div>
            </div>
          ))}
        </div>
        <p style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', fontFamily:'var(--font-serif)', lineHeight:1.7, marginBottom:'0.75rem' }}>
          {y.analysis}
        </p>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.5rem', fontSize:'var(--text-sm)' }}>
          {[
            ['✦ 幸运方向', rec.lucky_direction, '#27ae60'],
            ['✦ 幸运颜色', rec.lucky_color, '#27ae60'],
            ['✦ 幸运行业', rec.lucky_career, '#27ae60'],
            ['✦ 幸运数字', rec.lucky_number, '#27ae60'],
            ['✗ 回避方向', rec.avoid_direction, 'var(--red-light)'],
            ['✗ 回避颜色', rec.avoid_color, 'var(--red-light)'],
          ].map(([label,val,color]) => val && (
            <div key={label} style={{ padding:'0.35rem 0.5rem', background:'var(--bg-raised)', borderRadius:'var(--radius-sm)' }}>
              <span style={{ color, marginRight:'0.3rem' }}>{label.slice(0,1)}</span>
              <span style={{ color:'var(--text-muted)', fontSize:'var(--text-xs)' }}>{label.slice(1)}</span>
              <div style={{ color:'var(--text-primary)', marginTop:'0.15rem' }}>{val}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-title">健康注意事项</div>
        <div className="kv-grid">
          <span className="kv-label">关注脏腑</span>
          <span className="kv-value accent">{health.vulnerable_organs?.join('、')}</span>
          <span className="kv-label">常见问题</span>
          <span className="kv-value">{health.common_issues}</span>
          <span className="kv-label">养生建议</span>
          <span className="kv-value" style={{ color:'var(--text-secondary)', fontSize:'var(--text-sm)' }}>{health.health_advice}</span>
        </div>
      </div>

      <div className="card">
        <div className="card-title">感情婚姻特质</div>
        <p style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', color:'var(--text-secondary)', lineHeight:1.8 }}>{rels.style}</p>
        <div style={{ marginTop:'0.5rem', fontSize:'var(--text-sm)', color:'var(--text-muted)' }}>
          理想配偶五行：<span style={{ color:'var(--accent)' }}>{rels.ideal_partner_wx}</span>
        </div>
      </div>

      <div className="card">
        <div className="card-title">幸运元素</div>
        <div className="kv-grid">
          <span className="kv-label">幸运颜色</span>
          <span className="kv-value">{(lucky.colors||[]).join('、')}</span>
          <span className="kv-label">幸运方位</span>
          <span className="kv-value accent">{(lucky.directions||[]).join('、')}</span>
          <span className="kv-label">幸运数字</span>
          <span className="kv-value">{(lucky.numbers||[]).join('、')}</span>
          <span className="kv-label">旺盛季节</span>
          <span className="kv-value">{lucky.season}</span>
        </div>
      </div>
    </div>
  )
}

/* ── Fortune ── */
function FortuneResult({ data }) {
  const [view, setView] = useState('dayun')
  const [selectedLn, setSelectedLn] = useState(null)
  const [selectedLy, setSelectedLy] = useState(null)
  const [selectedLr, setSelectedLr] = useState(null)
  const Q_COLOR = { 吉:'#27ae60', 凶:'var(--red-light)', 平:'var(--text-muted)' }
  const Q_BADGE = q => q==='吉'?'badge-jade':q==='凶'?'badge-red':'badge-muted'
  return (
    <div className="result-section">
      <div className="tab-bar">
        {[['dayun','大运'],['liunian','流年'],['liuyue','流月'],['liuri','流日'],['liushi','流时']].map(([v,l]) => (
          <button key={v} className={`tab ${view===v?'active':''}`} onClick={() => setView(v)}>{l}</button>
        ))}
      </div>

      {view === 'dayun' && (
        <div className="card">
          <div className="card-title">大运十年周期</div>
          <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginBottom:'0.75rem', fontFamily:'var(--font-serif)' }}>
            大运每10年一换，决定人生各阶段整体运势基调。
          </div>
          <div style={{ display:'flex', flexDirection:'column', gap:'0.5rem' }}>
            {data.dayun?.map((dy, i) => (
              <div key={i} style={{
                display:'flex', alignItems:'center', gap:'1rem',
                padding:'0.65rem 0.9rem',
                background: dy.quality==='吉' ? 'var(--accent-glow)' : dy.quality==='凶' ? 'var(--red-glow)' : 'var(--bg-raised)',
                border:`1px solid ${dy.quality==='吉'?'var(--accent-dim)':dy.quality==='凶'?'var(--red-glow)':'var(--border)'}`,
              }}>
                <span style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-lg)', color:'var(--accent)', width:'44px', fontWeight:600 }}>
                  {dy.tiangan}{dy.dizhi}
                </span>
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)' }}>
                    {dy.start_year}–{dy.end_year}年 · {Math.floor(dy.start_age)}岁起
                  </div>
                  <div style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', marginTop:'0.1rem' }}>
                    {dy.dm_shishen} · {dy.quality==='吉'?'运势顺遂，宜积极进取':dy.quality==='凶'?'运势有阻，宜守成待机':'运势平稳，宜稳中求进'}
                  </div>
                </div>
                <span className={`badge ${Q_BADGE(dy.quality)}`}>{dy.quality}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {view === 'liunian' && (
        <div className="card">
          <div className="card-title">流年运势</div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(110px,1fr))', gap:'0.4rem' }}>
            {data.liunian?.slice(0,40).map((ly,i) => {
              const hasWarning = ly.warnings && ly.warnings.length > 0
              const suiyunTags = (ly.suiyun?.tags || []).filter(t =>
                t.includes('并临') || t.includes('相战')
              )
              const tagsBrief = (ly.tags || []).filter(t =>
                t.includes('冲') || t.includes('伏吟') || t.includes('反吟')
              ).concat(suiyunTags)
              return (
              <div key={i} {...clickable(() => setSelectedLn(selectedLn===i?null:i))} style={{
                padding:'0.5rem 0.4rem', textAlign:'center', cursor:'pointer',
                background: ly.quality==='吉'?'var(--accent-glow)':ly.quality==='凶'?'var(--red-glow)':'var(--bg-raised)',
                border:`1px solid ${selectedLn===i?'var(--accent)':ly.quality==='吉'?'var(--accent-dim)':ly.quality==='凶'?'var(--red-glow)':'var(--border)'}`,
                position: 'relative',
              }}
              title={(ly.warnings || []).concat(ly.auspicious || []).concat(ly.suiyun?.notes || []).join('；') || ''}
              >
                <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{ly.year}年</div>
                <div style={{ fontFamily:'var(--font-serif)', color:'var(--accent)', fontSize:'var(--text-md)', fontWeight:600 }}>{ly.tiangan}{ly.dizhi}</div>
                <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{ly.age}岁</div>
                <div style={{ fontSize:'var(--text-xs)', color: Q_COLOR[ly.quality]||'var(--text-muted)', marginTop:'2px' }}>{ly.shishen_gan}</div>
                {tagsBrief.length > 0 && (
                  <div style={{ marginTop: '3px',
                    display: 'flex', flexWrap: 'wrap', gap: '2px', justifyContent: 'center' }}>
                    {tagsBrief.slice(0,2).map((t,j) => (
                      <span key={j} style={{
                        padding: '1px 4px', fontSize:'var(--text-2xs)',
                        background: 'rgba(192,57,43,0.15)', color: '#c0392b',
                        borderRadius: '4px', fontFamily: 'var(--font-serif)',
                      }}>{t}</span>
                    ))}
                  </div>
                )}
                {hasWarning && (
                  <div style={{ position: 'absolute', top: '2px', right: '4px',
                    color: '#e67e22', fontSize:'var(--text-xs)' }}>⚠</div>
                )}
              </div>
            )})}
          </div>

          {/* 选中流年 · 逐年组合断详解 */}
          {selectedLn !== null && data.liunian?.[selectedLn]?.liunian_combo && (() => {
            const ly = data.liunian[selectedLn]
            const lc = ly.liunian_combo
            const col = lc.quality==='吉'?'#27ae60':lc.quality==='凶'?'#c0392b':'var(--accent)'
            return (
              <div style={{ marginTop:'0.8rem', padding:'0.75rem 1rem', borderRadius:'var(--r-sm)',
                background:'var(--bg-raised)', borderLeft:`3px solid ${col}` }}>
                <div style={{ display:'flex', gap:'0.6rem', alignItems:'center', marginBottom:'0.5rem', flexWrap:'wrap' }}>
                  <span style={{ fontFamily:'var(--font-serif)', fontWeight:700, fontSize:'var(--text-lg)', color:'var(--accent)' }}>
                    {ly.year}年 {lc.ganzhi}
                  </span>
                  <span style={{ fontSize:'var(--text-xs)', padding:'2px 8px', borderRadius:'4px',
                    background:`${col}22`, color:col, fontWeight:700 }}>
                    {lc.shishen_gan}{lc.shishen_zhi?`/${lc.shishen_zhi}`:''} · {lc.xiji}用 · {lc.quality}
                  </span>
                </div>
                <p style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                  color:'var(--text-primary)', lineHeight:1.85, marginBottom:'0.5rem' }}>
                  {lc.verdict}
                </p>
                {lc.themes?.length > 0 && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'0.25rem' }}>
                    {lc.themes.map((t,j) => (
                      <div key={j} style={{ fontSize:'var(--text-xs)', color:'var(--text-secondary)',
                        fontFamily:'var(--font-serif)', lineHeight:1.6 }}>· 应事 {t}</div>
                    ))}
                  </div>
                )}
                {ly.suiyun?.notes?.length > 0 && (
                  <div style={{ marginTop:'0.4rem', fontSize:'var(--text-xs)', color:'var(--text-muted)',
                    fontFamily:'var(--font-serif)', lineHeight:1.6 }}>
                    岁运：{ly.suiyun.notes.join('；')}
                  </div>
                )}
              </div>
            )
          })()}
          {/* 详细 warnings 列表 */}
          {data.liunian?.some(ly => ly.warnings && ly.warnings.length > 0) && (
            <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem',
              background: 'var(--bg-raised)', borderRadius: 'var(--r-sm)',
              borderLeft: '3px solid #e67e22' }}>
              <div style={{ fontSize: 'var(--text-xs)', color: '#e67e22', fontWeight: 700,
                marginBottom: '0.4rem' }}>
                ⚠ 关键警示流年：
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.7 }}>
                {data.liunian.filter(ly => ly.warnings && ly.warnings.length > 0).slice(0, 8).map((ly, i) => (
                  <div key={i} style={{ marginBottom: '0.35rem',
                    paddingBottom: '0.35rem',
                    borderBottom: '1px dashed var(--border)' }}>
                    <strong style={{ color: 'var(--accent)' }}>
                      {ly.year}年（{ly.tiangan}{ly.dizhi}）{ly.age}岁
                    </strong>
                    {(ly.warnings || []).map((w, j) => (
                      <div key={j} style={{ marginLeft: '0.5rem', marginTop: '2px' }}>
                        · {w}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {view === 'liuyue' && data.liuyue && (
        <div className="card">
          <div className="card-title">流月运势</div>
          {data.liuyue.map((lm,i) => (
            <div key={i}>
              <div {...clickable(()=>setSelectedLy(selectedLy===i?null:i))} style={{
                display:'flex', alignItems:'center', gap:'0.75rem', cursor:'pointer',
                padding:'0.5rem 0.75rem', borderBottom:'1px solid var(--border)',
                background: selectedLy===i?'var(--accent-bg)':'transparent',
              }}>
                <span style={{ width:'32px', color:'var(--text-muted)', fontSize:'var(--text-sm)' }}>{lm.month_num}月</span>
                <span style={{ fontFamily:'var(--font-serif)', color:'var(--accent)', width:'40px', fontWeight:600 }}>{lm.tiangan}{lm.dizhi}</span>
                <span style={{ flex:1, fontSize:'var(--text-sm)', color:'var(--text-secondary)' }}>{lm.summary}</span>
                <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{lm.season_status}</span>
                <span className={`badge ${Q_BADGE(lm.quality)}`}>{lm.quality}</span>
              </div>
              {selectedLy===i && lm.combo && (
                <div style={{ padding:'0.6rem 0.9rem', background:'var(--bg-raised)',
                  borderBottom:'1px solid var(--border)', fontFamily:'var(--font-serif)' }}>
                  <div style={{ fontSize:'var(--text-xs)', color:'var(--accent)', fontWeight:700, marginBottom:'3px' }}>
                    {lm.combo.shishen_gan}{lm.combo.shishen_zhi?`/${lm.combo.shishen_zhi}`:''} · {lm.combo.xiji}用
                  </div>
                  <div style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', lineHeight:1.8 }}>{lm.combo.verdict}</div>
                  {lm.combo.themes?.map((t,j)=>(
                    <div key={j} style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginTop:'2px' }}>· 应事 {t}</div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {view === 'liuri' && (
        <div className="card">
          <div className="card-title">流日运势</div>
          {data.liuri ? (
            <>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(80px,1fr))', gap:'0.3rem' }}>
              {data.liuri.map((ld,i) => (
                <div key={i} {...clickable(()=>setSelectedLr(selectedLr===i?null:i))} style={{
                  padding:'0.35rem', textAlign:'center', fontSize:'var(--text-xs)', cursor:'pointer',
                  background: ld.quality==='吉'?'var(--accent-glow)':ld.quality==='凶'?'var(--red-glow)':'var(--bg-raised)',
                  border:`1px solid ${selectedLr===i?'var(--accent)':ld.quality==='吉'?'var(--accent-dim)':ld.quality==='凶'?'var(--red-glow)':'var(--border)'}`,
                }}>
                  <div style={{ color:'var(--text-muted)' }}>{ld.day}日</div>
                  <div style={{ fontFamily:'var(--font-serif)', color:'var(--accent)', fontSize:'var(--text-sm)', fontWeight:600 }}>{ld.tiangan}{ld.dizhi}</div>
                  <div style={{ color:Q_COLOR[ld.quality]||'var(--text-muted)' }}>{ld.shishen_gan}</div>
                </div>
              ))}
            </div>
            {selectedLr !== null && data.liuri[selectedLr]?.combo && (
              <div style={{ marginTop:'0.7rem', padding:'0.6rem 0.9rem', background:'var(--bg-raised)',
                borderRadius:'var(--r-sm)', borderLeft:'3px solid var(--accent)', fontFamily:'var(--font-serif)' }}>
                <div style={{ fontSize:'var(--text-sm)', fontWeight:700, color:'var(--accent)', marginBottom:'3px' }}>
                  {data.liuri[selectedLr].date} {data.liuri[selectedLr].combo.ganzhi}
                  <span style={{ fontSize:'var(--text-xs)', fontWeight:400, marginLeft:'6px', color:'var(--text-muted)' }}>
                    {data.liuri[selectedLr].combo.shishen_gan} · {data.liuri[selectedLr].combo.xiji}用
                  </span>
                </div>
                <div style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', lineHeight:1.8 }}>
                  {data.liuri[selectedLr].combo.verdict}
                </div>
              </div>
            )}
            </>
          ) : (
            <div style={{ color:'var(--text-muted)', fontSize:'var(--text-sm)', padding:'1rem', fontFamily:'var(--font-serif)' }}>
              需先在运势查询中指定年份和月份，方可显示流日。请在查询时设置 query_year 和 query_month 参数。
            </div>
          )}
        </div>
      )}

      {view === 'liushi' && (
        <div className="card">
          <div className="card-title">流时运势 · 十二时辰</div>
          {data.liushi ? (
            <div style={{ display:'flex', flexDirection:'column', gap:'0.35rem' }}>
              {data.liushi.map((ls,i) => (
                <div key={i} style={{
                  display:'flex', alignItems:'center', gap:'0.6rem',
                  padding:'0.4rem 0.6rem',
                  background: ls.quality==='吉'?'var(--accent-glow)':ls.quality==='凶'?'var(--red-glow)':'var(--bg-raised)',
                  border:`1px solid ${ls.quality==='吉'?'var(--accent-dim)':ls.quality==='凶'?'var(--red-glow)':'var(--border)'}`,
                }}>
                  <span style={{ width:70, fontFamily:'var(--font-mono)', fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{ls.time_range}</span>
                  <span style={{ fontFamily:'var(--font-serif)', color:'var(--accent)', width:36, fontWeight:600 }}>{ls.tiangan}{ls.dizhi}</span>
                  <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{ls.dizhi}时</span>
                  <span style={{ flex:1, fontSize:'var(--text-xs)', color:'var(--text-secondary)' }}>{ls.shishen_gan}</span>
                  <span className={`badge ${Q_BADGE(ls.quality)}`}>{ls.quality}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color:'var(--text-muted)', fontSize:'var(--text-sm)', padding:'1rem', fontFamily:'var(--font-serif)' }}>
              需先在运势查询中指定具体日期，方可显示流时。请设置 query_year、query_month 和 query_day 参数。
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Career ── */
function CareerResult({ data }) {
  const pc = data.profile_career || {}
  return (
    <div className="result-section">
      <div className="card">
        <div className="card-title">事业运势分析</div>
        <p style={{ fontFamily:'var(--font-serif)', lineHeight:1.85, marginBottom:'1rem' }}>{data.analysis}</p>
        {data.career_fields?.length > 0 && (
          <div style={{ marginBottom:'1rem' }}>
            <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginBottom:'0.4rem' }}>推荐行业</div>
            <div style={{ display:'flex', flexWrap:'wrap', gap:'0.4rem' }}>
              {data.career_fields?.map((f,i) => <span key={i} className="badge badge-gold">{f}</span>)}
            </div>
          </div>
        )}
        {data.shishen_advice?.map((a,i) => (
          <div key={i} style={{ display:'flex', gap:'0.5rem', fontSize:'var(--text-base)', color:'var(--text-secondary)', marginTop:'0.4rem' }}>
            <span style={{ color:'var(--accent)', flexShrink:0 }}>◆</span><span>{a}</span>
          </div>
        ))}
      </div>
      {pc.best_fields && (
        <div className="card">
          <div className="card-title">日主性格与职场风格</div>
          <div style={{ marginBottom:'0.75rem' }}>
            <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginBottom:'0.35rem' }}>适合行业</div>
            <div style={{ display:'flex', flexWrap:'wrap', gap:'0.4rem' }}>
              {pc.best_fields?.map((f,i) => <span key={i} className="badge badge-muted">{f}</span>)}
            </div>
          </div>
          <p style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', fontFamily:'var(--font-serif)', lineHeight:1.7 }}>{pc.work_style}</p>
          <p style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginTop:'0.5rem' }}>财富观：{pc.wealth_approach}</p>
        </div>
      )}
      {data.personality_traits?.length > 0 && (
        <div className="card">
          <div className="card-title">核心性格优势</div>
          {data.personality_traits?.map((t,i) => (
            <div key={i} style={{ display:'flex', gap:'0.5rem', fontSize:'var(--text-base)', color:'var(--text-secondary)', marginBottom:'0.35rem' }}>
              <span style={{ color:'#27ae60', flexShrink:0 }}>✦</span><span>{t}</span>
            </div>
          ))}
          {data.weaknesses?.length > 0 && (
            <div style={{ marginTop:'0.75rem', paddingTop:'0.6rem', borderTop:'1px dashed var(--border)' }}>
              <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginBottom:'0.4rem' }}>需留意的短板</div>
              {data.weaknesses.map((t,i) => (
                <div key={i} style={{ display:'flex', gap:'0.5rem', fontSize:'var(--text-base)', color:'var(--text-secondary)', marginBottom:'0.35rem' }}>
                  <span style={{ color:'#c0392b', flexShrink:0 }}>△</span><span>{t}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Marriage ── */
function MarriageResult({ data }) {
  return (
    <div className="result-section">
      <div className="card">
        <div className="card-title">婚姻感情分析</div>
        <div style={{ display:'flex', gap:'0.5rem', marginBottom:'0.75rem', flexWrap:'wrap' }}>
          {data.clash_present && <span className="badge badge-red">日支受冲 · 婚姻有波折</span>}
          {data.harmony_present && <span className="badge badge-jade">日支六合 · 婚缘和谐</span>}
          {data.spouse_stars?.length > 0 && <span className="badge badge-gold">配偶星 {data.spouse_stars.join('·')}</span>}
        </div>
        <div className="kv-grid">
          <span className="kv-label">婚姻宫（日支）</span>
          <span className="kv-value accent">{data.spouse_palace}</span>
          <span className="kv-label">配偶星</span>
          <span className="kv-value">{data.spouse_stars?.join('、') || '未见'}</span>
          <span className="kv-label">综合论断</span>
          <span className="kv-value" style={{ fontFamily:'var(--font-serif)', color:'var(--text-secondary)' }}>{data.quality}</span>
        </div>
      </div>
      {data.advice?.length > 0 && (
        <div className="card">
          <div className="card-title">感情建议</div>
          {data.advice?.filter(Boolean).map((a,i) => (
            <div key={i} style={{ display:'flex', gap:'0.5rem', fontSize:'var(--text-base)', color:'var(--text-secondary)', marginBottom:'0.4rem' }}>
              <span style={{ color:'var(--accent)', flexShrink:0 }}>◆</span><span>{a}</span>
            </div>
          ))}
          <div style={{ marginTop:'0.75rem', padding:'0.75rem', background:'var(--bg-raised)', borderRadius:'var(--radius-sm)',
            fontSize:'var(--text-sm)', color:'var(--text-muted)', fontFamily:'var(--font-serif)', lineHeight:1.7 }}>
            注：婚姻宫（日支）为观察配偶宫位。日支与年支、时支六合，婚姻更易和谐；若遭月支、时支六冲，则婚姻多有波折，需多包容沟通。
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Health ── */
function HealthResult({ data }) {
  const wx = data.wx_distribution || {}
  const total = Object.values(wx).reduce((a,b)=>a+b,0) || 1
  const WX_COLOR = { 木:'#27ae60', 火:'#e74c3c', 土:'#f39c12', 金:'#95a5a6', 水:'#3498db' }
  const ph = data.profile_health || {}
  return (
    <div className="result-section">
      <div className="card">
        <div className="card-title">五行健康分析</div>
        <p style={{ fontFamily:'var(--font-serif)', lineHeight:1.85, marginBottom:'1rem' }}>{data.analysis}</p>
        <div style={{ marginBottom:'1rem' }}>
          <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginBottom:'0.5rem' }}>命局五行分布</div>
          <div style={{ display:'flex', gap:'3px', height:'28px', borderRadius:0, overflow:'hidden' }}>
            {Object.entries(wx).map(([el,cnt]) => cnt > 0 && (
              <div key={el} title={`${el}: ${cnt}`}
                style={{ flex:cnt, background:WX_COLOR[el], display:'flex', alignItems:'center',
                  justifyContent:'center', fontSize:'var(--text-xs)', color:'#fff', fontWeight:600 }}>
                {cnt >= 2 ? el : ''}
              </div>
            ))}
          </div>
          <div style={{ display:'flex', gap:'1rem', marginTop:'0.4rem', flexWrap:'wrap' }}>
            {Object.entries(wx).map(([el,cnt]) => (
              <span key={el} style={{ fontSize:'var(--text-sm)', color:WX_COLOR[el], fontWeight:600 }}>{el}：{cnt}</span>
            ))}
          </div>
        </div>
        <div className="kv-grid">
          <span className="kv-label">日主脏腑</span>
          <span className="kv-value accent">{data.dm_organ}</span>
          <span className="kv-label">注意症状</span>
          <span className="kv-value">{data.dm_condition}</span>
          <span className="kv-label">最弱五行</span>
          <span className="kv-value" style={{ color:WX_COLOR[data.weak_element] }}>{data.weak_element}</span>
          <span className="kv-label">弱势脏腑</span>
          <span className="kv-value">{data.weak_organ}</span>
        </div>
      </div>
      <div className="card">
        <div className="card-title">日主健康细则</div>
        {ph.vulnerable_organs && (
          <div style={{ marginBottom:'0.5rem' }}>
            <span style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)' }}>重点关注：</span>
            <span style={{ color:'var(--accent)', fontWeight:600 }}>{ph.vulnerable_organs?.join('、')}</span>
          </div>
        )}
        {data.advice?.filter(Boolean).map((a,i) => (
          <div key={i} style={{ display:'flex', gap:'0.5rem', fontSize:'var(--text-base)', color:'var(--text-secondary)', marginBottom:'0.35rem' }}>
            <span style={{ color:'#27ae60', flexShrink:0 }}>◆</span><span>{a}</span>
          </div>
        ))}
        {ph.health_advice && (
          <div style={{ marginTop:'0.75rem', padding:'0.75rem', background:'var(--accent-glow)',
            border:'1px solid var(--accent-dim)', borderRadius:'var(--radius-sm)',
            fontSize:'var(--text-sm)', fontFamily:'var(--font-serif)', color:'var(--text-secondary)', lineHeight:1.7 }}>
            {ph.health_advice}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Wealth ── */
function WealthResult({ data }) {
  const LEVEL_COLOR = { '财运丰厚':'var(--accent)', '财运稳健':'#27ae60', '财来财去':'#e67e22', '财运平稳':'var(--text-muted)' }
  return (
    <div className="result-section">
      <div className="card" style={{ textAlign:'center' }}>
        <div className="card-title">财运评估</div>
        <div style={{ fontSize:'var(--text-display)', fontFamily:'var(--font-display)', color:LEVEL_COLOR[data.level]||'var(--accent)',
          margin:'0.5rem 0', textShadow:'0 0 20px currentColor' }}>
          {data.level}
        </div>
        <p style={{ fontFamily:'var(--font-serif)', color:'var(--text-secondary)', lineHeight:1.8, marginBottom:'1rem' }}>
          {data.analysis}
        </p>
        <div style={{ display:'flex', gap:'0.5rem', justifyContent:'center', flexWrap:'wrap' }}>
          {data.wealth_stems?.map((s,i) => <span key={i} className="badge badge-gold">{s}</span>)}
        </div>
      </div>
      <div className="card">
        <div className="card-title">财运建议</div>
        {data.advice?.filter(Boolean).map((a,i) => (
          <div key={i} style={{ display:'flex', gap:'0.5rem', fontSize:'var(--text-base)', color:'var(--text-secondary)', marginBottom:'0.4rem' }}>
            <span style={{ color:'var(--accent)', flexShrink:0 }}>◆</span><span>{a}</span>
          </div>
        ))}
        <div style={{ marginTop:'0.75rem', padding:'0.75rem', background:'var(--bg-raised)',
          borderRadius:'var(--radius-sm)', fontSize:'var(--text-sm)', color:'var(--text-muted)', fontFamily:'var(--font-serif)', lineHeight:1.7 }}>
          正财（正财星）主稳定薪资与本业收入；偏财（偏财星）主投资、偏业与意外之财。
          身强者更能驾驭财星，身弱则财星重时反成负担。
        </div>
      </div>
    </div>
  )
}

/* ── Compat ── */
function CompatResult({ data }) {
  const score = data.score || 0
  const color = score>=80?'var(--accent)':score>=65?'#27ae60':'var(--red-light)'
  return (
    <div className="result-section">
      <div className="card" style={{ textAlign:'center' }}>
        <div className="card-title">合婚分析</div>
        <div style={{ fontSize:'5rem', fontFamily:'var(--font-display)', color, lineHeight:1.1,
          textShadow:`0 0 30px ${color}44`, margin:'0.5rem 0' }}>{score}</div>
        <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginBottom:'1rem' }}>合婚评分 / 100</div>
        <p style={{ fontFamily:'var(--font-serif)', color:'var(--text-secondary)', lineHeight:1.8 }}>{data.summary}</p>
        <div style={{ display:'flex', gap:'2rem', justifyContent:'center', marginTop:'1.5rem' }}>
          {['person_a','person_b'].map((k,i) => (
            <div key={k} style={{ textAlign:'center' }}>
              <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)' }}>{i===0?'甲方':'乙方'}</div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-lg)', color:'var(--accent)' }}>{data[k]?.day_master}</div>
              <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)' }}>{data[k]?.pattern}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="card">
        <div className="card-title">合婚详解</div>
        <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', color:'var(--text-secondary)', lineHeight:1.8 }}>
          <p>合婚以五行生克为基础。五行相生（木生火、火生土）为最佳，表明双方能互相扶持滋养；五行相同为同类，志同道合但需保持各自空间；五行相克则性格差异明显，需多磨合理解。</p>
          <p style={{ marginTop:'0.5rem' }}>此外还需参考日柱六合六冲：日支相合，夫妻宫和谐；日支相冲，婚姻多有摩擦，需双方主动化解。</p>
        </div>
      </div>
    </div>
  )
}

/* ── 称骨 Result ── */
function ChengguResult({ data }) {
  const LEVEL_COLOR = { '上上':'#b5361e', '中上':'var(--accent)', '中等':'var(--text-secondary)', '中下':'#b5a07a', '下等':'var(--text-muted)' }
  return (
    <div className="result-section">
      <div className="card" style={{ borderColor:'var(--accent-dim)', background:'var(--accent-glow)' }}>
        <div className="card-title">袁天罡称骨</div>
        <div style={{ display:'flex', alignItems:'center', gap:'1.5rem', marginBottom:'1rem' }}>
          <div style={{ textAlign:'center' }}>
            <div style={{ fontSize:'var(--text-display)', fontWeight:700, fontFamily:'var(--font-serif)', color:LEVEL_COLOR[data.level]||'var(--accent)' }}>
              {data.total_weight}两
            </div>
            <span className={`badge ${data.level==='上上'||data.level==='中上'?'badge-jade':'badge-muted'}`} style={{ marginTop:4 }}>
              {data.level}
            </span>
          </div>
          <div style={{ flex:1 }}>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)', color:'var(--text-primary)', fontWeight:600, marginBottom:4 }}>
              {data.verse_title}
            </div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)', color:'var(--text-secondary)', lineHeight:1.8 }}>
              {data.verse}
            </div>
          </div>
        </div>
        <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', fontFamily:'var(--font-mono)', padding:'0.4rem 0.6rem', background:'var(--bg-subtle)', borderLeft:'2px solid var(--accent-dim)' }}>
          {data.breakdown}
        </div>
        <div style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', marginTop:'0.75rem', fontFamily:'var(--font-serif)' }}>
          {data.level_desc}
        </div>
      </div>

      <div className="card">
        <div className="card-title">称骨说明</div>
        <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', fontFamily:'var(--font-serif)', lineHeight:1.8 }}>
          <p>称骨算命法相传为唐代袁天罡所创，以出生年月日时的骨重之和来推算一生命运轨迹。骨重越重，命越好，但非绝对。</p>
          <p style={{ marginTop:'0.5rem' }}>骨重2.1-3.0两为下等，3.0-3.5为中下，3.5-4.0为中等，4.0-5.0为中上，5.0以上为上上。此法仅作参考，不可过于执着。</p>
        </div>
      </div>
    </div>
  )
}

/* ── 八字反查工具 ── */
function ReverseToolCard() {
  const [open, setOpen] = React.useState(false)
  const [yearGz, setYearGz] = React.useState('')
  const [dayGz, setDayGz] = React.useState('')
  const [results, setResults] = React.useState(null)
  const [loading, setLoading] = React.useState(false)

  const doReverse = async () => {
    if (!yearGz || !dayGz) return
    setLoading(true)
    try {
      const data = await baziApi.reverse({ year_gz: yearGz, day_gz: dayGz, from_year: 1960, to_year: 2030 })
      setResults(data.matches || [])
    } catch (e) {
      setResults([])
    }
    setLoading(false)
  }

  const TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
  const DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
  const gzOptions = []
  for (let i = 0; i < 60; i++) gzOptions.push(TIANGAN[i%10] + DIZHI[i%12])

  return (
    <div className="card" style={{ marginTop:'0.5rem', padding:'0.65rem' }}>
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', cursor:'pointer' }}
        onClick={() => setOpen(!open)}>
        <span style={{ fontSize:'var(--text-xs)', fontWeight:600, color:'var(--text-muted)' }}>🔍 八字反查</span>
        <span style={{ fontSize:'var(--text-2xs)', color:'var(--text-faint)' }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && (
        <div style={{ marginTop:'0.5rem' }}>
          <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginBottom:6, lineHeight:1.5 }}>
            输入年柱+日柱干支，反查所有匹配的出生日期
          </div>
          <div style={{ display:'flex', gap:6, marginBottom:6 }}>
            <select value={yearGz} onChange={e => setYearGz(e.target.value)}
              style={{ flex:1, padding:'4px 6px', fontSize:'var(--text-xs)', border:'1px solid var(--border)', background:'var(--surface)' }}>
              <option value="">年柱</option>
              {gzOptions.map(gz => <option key={gz} value={gz}>{gz}</option>)}
            </select>
            <select value={dayGz} onChange={e => setDayGz(e.target.value)}
              style={{ flex:1, padding:'4px 6px', fontSize:'var(--text-xs)', border:'1px solid var(--border)', background:'var(--surface)' }}>
              <option value="">日柱</option>
              {gzOptions.map(gz => <option key={gz} value={gz}>{gz}</option>)}
            </select>
          </div>
          <button className="btn btn-sm btn-full" onClick={doReverse} disabled={loading || !yearGz || !dayGz}>
            {loading ? '查找中…' : '反查'}
          </button>
          {results && (
            <div style={{ marginTop:6, maxHeight:160, overflowY:'auto' }}>
              {results.length === 0 ? (
                <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', textAlign:'center', padding:8 }}>未找到匹配</div>
              ) : (
                <div style={{ display:'flex', flexDirection:'column', gap:2 }}>
                  <div style={{ fontSize:'var(--text-2xs)', color:'var(--text-faint)', marginBottom:2 }}>找到 {results.length} 个匹配：</div>
                  {results.slice(0, 20).map((r, i) => (
                    <div key={i} style={{ display:'flex', gap:6, fontSize:'var(--text-xs)', padding:'3px 6px', background:'var(--bg-subtle)', alignItems:'center' }}>
                      <span style={{ color:'var(--accent)', fontFamily:'var(--font-mono)', fontWeight:600 }}>{r.date}</span>
                      <span style={{ color:'var(--text-muted)' }}>{r.month_gz}月</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
