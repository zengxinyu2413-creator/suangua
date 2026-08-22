import React, { useState } from 'react'
import AiInterpretPanel from '../../components/UI/AiInterpretPanel'
import { FengshuiVis } from '../../components/particles/Visualizations'
import { fengshuiApi } from '../../api/client'
import { useAsyncAction } from '../../hooks/useAsyncAction'
import XuankongPanel from './XuankongPanel'
import YangzhaiSanyaoPanel from './YangzhaiSanyaoPanel'
import HouseReportPanel from './HouseReportPanel'

const DIRECTIONS = ['南','北','东','西','东南','西北','东北','西南']
const Q_COLOR = { '吉':'var(--jade)', '大吉':'var(--jade)', '凶':'var(--red-light)', '大凶':'var(--red)', '中':'var(--text-muted)' }

const STAR_META = {
  1: { name:'一白', wuxing:'坎水', nature:'吉', color:'#2270a8', desc:'贪狼星·水·主财帛聪明', icon:'一' },
  2: { name:'二黑', wuxing:'坤土', nature:'大凶', color:'#c8402a', desc:'巨门星·土·主疾病是非', icon:'二' },
  3: { name:'三碧', wuxing:'震木', nature:'凶', color:'#c8b08a', desc:'禄存星·木·主口舌争斗', icon:'三' },
  4: { name:'四绿', wuxing:'巽木', nature:'吉', color:'#4a7a5a', desc:'文曲星·木·主文昌学业', icon:'四' },
  5: { name:'五黄', wuxing:'中土', nature:'大凶', color:'#a85840', desc:'廉贞星·土·最凶忌动土', icon:'五' },
  6: { name:'六白', wuxing:'乾金', nature:'吉', color:'#2270a8', desc:'武曲星·金·主财帛官贵', icon:'六' },
  7: { name:'七赤', wuxing:'兑金', nature:'凶', color:'#c8b08a', desc:'破军星·金·盗贼口舌', icon:'七' },
  8: { name:'八白', wuxing:'艮土', nature:'大吉', color:'#4a7a5a', desc:'左辅星·土·八运旺星大吉', icon:'八' },
  9: { name:'九紫', wuxing:'离火', nature:'吉', color:'#8a5a9e', desc:'右弼星·火·九运旺星', icon:'九' },
}

// 后天八卦方位名 — 用于显示宅卦
// 注意：朝向"南"=坐"北"=坎宅（主流坐山派《八宅明镜》）
// 此映射是"朝向 → 实际宅卦"
const FACING_TO_HOUSE_GUA = {
  '南': '坎', '北': '离', '东': '兑', '西': '震',
  '东南': '乾', '西北': '巽', '东北': '坤', '西南': '艮',
}

// 朝向 → 坐山 反转表
const FACING_TO_SITTING = {
  '南': '北', '北': '南', '东': '西', '西': '东',
  '东南': '西北', '西北': '东南', '东北': '西南', '西南': '东北',
}

// 后天八卦方位（朝向所属，用于不需要反转的展示）
const EIGHT_DIR_NAMES = {
  '东': '震', '东南': '巽', '南': '离', '西南': '坤',
  '西': '兑', '西北': '乾', '北': '坎', '东北': '艮',
}

const BAGUA_POSITION = {
  '南':'top', '北':'bottom', '东':'left', '西':'right',
  '东南':'top-left', '西南':'top-right', '西北':'bottom-right', '东北':'bottom-left',
}

// The classic 8-direction compass grid
const COMPASS_CELLS = [
  ['西北', '北', '东北'],
  ['西',   '中', '东'],
  ['西南', '南', '东南'],
]

// Pinyin key → display name (吉/凶 label + Chinese name)
const PERSONAL_DIR_NAMES = {
  shengqi:  { zh:'生气', good:true  },
  tianyi:   { zh:'天医', good:true  },
  niannian: { zh:'延年', good:true  },
  fuwei:    { zh:'伏位', good:true  },
  jueming:  { zh:'绝命', good:false },
  wugui:    { zh:'五鬼', good:false },
  liusha:   { zh:'六煞', good:false },
  huohai:   { zh:'祸害', good:false },
}

export default function FengShuiPage() {
  const [form, setForm]   = useState({ birth_year:1990, gender:'male', house_facing:'南' })
  const [result, setResult] = useState(null)
  const [tab, setTab]     = useState('bazhai')   // bazhai | flying | personal | theory
  const { loading, error, run: runAsync } = useAsyncAction()

  const run = async () => {
    const data = await runAsync(() => fengshuiApi.analysis(form), { successMsg: '分析完成' })
    if (data) setResult(data)
  }

  const sectorMap = {}
  result?.auspicious_sectors?.forEach(s => { sectorMap[s.direction] = { ...s, kind:'auspicious' } })
  result?.inauspicious_sectors?.forEach(s => { sectorMap[s.direction] = { ...s, kind:'inauspicious' } })
  const flyingStars = result?.annual_flying_stars?.direction_stars || {}
  const personalDirs = result?.personal_directions || {}

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">风水分析</div>
          <div className="page-subtitle">
            八宅派 · 玄空飞星 · 个人吉方 · 《八宅明镜》《沈氏玄空学》
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="page-cols">
          {/* ── Left: Input ── */}
          <div style={{ display:'flex', flexDirection:'column', gap:'1rem', minWidth: 0 }}>
            <div className="card">
              <div className="card-title">分析参数</div>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.75rem' }}>
                <div className="form-group">
                  <label>出生年份</label>
                  <input type="number" min="1900" max="2010" value={form.birth_year}
                    onChange={e => setForm(f=>({...f,birth_year:Number(e.target.value)}))} />
                </div>
                <div className="form-group">
                  <label>性别</label>
                  <div style={{ display:'flex', gap:'0.5rem', marginTop:'0.2rem' }}>
                    {[['male','男命'],['female','女命']].map(([v,l]) => (
                      <button key={v} className={`btn ${form.gender===v?'btn-primary':''}`}
                        style={{ flex:1 }} onClick={() => setForm(f=>({...f,gender:v}))}>{l}</button>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label>房屋朝向（坐山取宅卦）</label>
                  <div style={{ fontSize:'0.66rem', color:'var(--text-muted)',
                    marginBottom:'0.3rem', lineHeight:1.5, wordBreak:'break-word' }}>
                    朝向 = 大门方位；宅卦取"坐"
                  </div>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.3rem', marginTop:'0.2rem' }}>
                    {DIRECTIONS.map(d => (
                      <button key={d} className={`btn btn-sm ${form.house_facing===d?'btn-primary':''}`}
                        onClick={() => setForm(f=>({...f,house_facing:d}))}
                        style={{ textAlign:'left', padding:'0.35rem 0.45rem',
                          minWidth: 0, overflow: 'hidden' }}>
                        <div style={{ fontWeight:600, fontSize:'0.72rem' }}>朝{d}</div>
                        <div style={{ fontSize:'0.6rem', opacity:0.75, whiteSpace:'nowrap',
                          overflow:'hidden', textOverflow:'ellipsis' }}>
                          坐{FACING_TO_SITTING[d]}·{FACING_TO_HOUSE_GUA[d]}宅
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <button className="btn btn-primary btn-full btn-lg" onClick={run} disabled={loading}>
              {loading ? '分析中…' : '开始风水分析 ▶'}
            </button>
            {error && <div className="error-box">⚠ {error}</div>}

            {/* Classical theory panel - 可折叠 */}
            <details style={{ minWidth: 0 }}>
              <summary style={{
                listStyle: 'none', cursor: 'pointer',
                padding: '0.65rem 0.85rem',
                background: 'var(--bg-raised)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--r-md)',
                fontSize: '0.78rem', fontWeight: 600, color: 'var(--accent)',
                fontFamily: 'var(--font-serif)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span>📚 风水理论参考</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-faint)' }}>展开 ▾</span>
              </summary>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.35rem',
                marginTop: '0.5rem', padding: '0.5rem 0.6rem',
                background: 'var(--bg-subtle)', borderRadius: 'var(--r-md)',
                minWidth: 0, overflow: 'hidden' }}>
                {[
                  { t:'八宅派', desc:'东四命配东四宅' },
                  { t:'玄空飞星', desc:'山管丁，向管财' },
                  { t:'九运', desc:'2024-2043 九紫当令' },
                  { t:'三元', desc:'上中下元 各 60 年' },
                  { t:'形家', desc:'青龙白虎朱雀玄武' },
                ].map(item => (
                  <div key={item.t} style={{ display:'flex', flexDirection:'column', gap:'0.1rem',
                    paddingBottom:'0.3rem', borderBottom:'1px dashed var(--border)',
                    minWidth: 0, overflow: 'hidden' }}>
                    <span style={{ color:'var(--accent)', fontWeight:700, fontSize:'0.66rem' }}>{item.t}</span>
                    <span style={{ color:'var(--text-muted)', fontFamily:'var(--font-serif)',
                      lineHeight:1.5, fontSize:'0.62rem', wordBreak:'break-word' }}>{item.desc}</span>
                  </div>
                ))}
              </div>
            </details>

            {/* Five Yellow warning for current year */}
            <div className="card card-danger" style={{ padding:'0.65rem 0.8rem', minWidth: 0, overflow: 'hidden' }}>
              <div style={{ fontWeight:700, color:'var(--accent)', marginBottom:'0.3rem', fontSize:'0.72rem' }}>
                ⚠ 2026 年三煞提示
              </div>
              <p style={{ fontSize:'0.66rem', color:'var(--text-muted)', fontFamily:'var(--font-serif)',
                lineHeight:1.6, wordBreak:'break-word', margin: 0 }}>
                五黄、三煞、太岁方为三大忌，忌动土修造。
              </p>
            </div>
          </div>

          {/* ── Right: Result ── */}
          <div>
            {loading && <div className="loading"><div className="spinner"/><p>计算风水局势…</p></div>}

            {!loading && !result && (
              <div className="card" style={{ padding:'3rem 2rem', textAlign:'center' }}>
                <div style={{ fontSize:'3.5rem', marginBottom:'1rem', opacity:0.18, fontFamily:'var(--font-display)' }}>
                  龙穴砂水
                </div>
                <p style={{ fontFamily:'var(--font-serif)', color:'var(--text-muted)', fontSize:'var(--text-base)', lineHeight:1.8 }}>
                  请输入出生年份、性别和房屋朝向，<br/>系统将综合八宅派和玄空飞星进行分析
                </p>
                <p style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginTop:'0.75rem', fontFamily:'var(--font-serif)' }}>
                  《青囊经》：内气萌生，外气成形，内外相乘，风水自成
                </p>
              </div>
            )}

            {!loading && result && (
              <>
                {/* Summary */}
                <div className="card card-glow" style={{ marginBottom:'1rem' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'0.75rem' }}>
                    <div>
                      <div style={{ fontFamily:'var(--font-title)', fontSize:'var(--text-lg)', color:'var(--accent)', marginBottom:'0.3rem' }}>
                        {result.ming_gua_name || result.life_trigram || '命卦'} 命
                        <span style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', fontWeight:400, marginLeft:'0.5rem' }}>
                          {result.ming_gua_group || (result.life_group === 'east_group' ? '东四命' : '西四命')}
                        </span>
                      </div>
                      <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', fontFamily:'var(--font-mono)' }}>
                        朝向{form.house_facing} · 坐{result.house_sitting || FACING_TO_SITTING[form.house_facing]} · {result.house_gua_name || FACING_TO_HOUSE_GUA[form.house_facing]}宅（{result.house_group || (result.house_group === 'east_group' ? '东四宅' : '西四宅')}）
                      </div>
                    </div>
                    <span className={`badge ${result.is_compatible ? 'badge-jade' : 'badge-red'}`}>
                      {result.is_compatible ? '命宅相合 ✓' : '命宅相克 !'}
                    </span>
                  </div>
                  {result.compatibility && (
                    <p style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)', fontFamily:'var(--font-serif)',
                      lineHeight:1.8, marginTop:'0.65rem' }}>
                      {result.compatibility}
                    </p>
                  )}
                </div>

                {/* Tabs */}
                <div className="tab-bar">
                  {[
                    { id:'bazhai',   label:'八宅九星' },
                    { id:'flying',   label:'飞星盘' },
                    { id:'sanyao',   label:'阳宅三要' },
                    { id:'unified',  label:'理气×形法' },
                    { id:'personal', label:'个人方位' },
                    { id:'advice',   label:'布局建议' },
                  ].map(t => (
                    <button key={t.id} className={`tab ${tab===t.id?'active':''}`} onClick={() => setTab(t.id)}>
                      {t.label}
                    </button>
                  ))}
                </div>

                {/* ── TAB: 八宅 ── */}
                {tab === 'bazhai' && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
                    {/* Compass grid */}
                    <div className="card">
                      <div className="card-title">八宅九星罗盘</div>
                      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'4px', maxWidth:'380px', margin:'0 auto' }}>
                        {COMPASS_CELLS.flat().map(dir => {
                          if (dir === '中') return (
                            <div key="center" style={{ aspectRatio:'1', display:'flex', flexDirection:'column',
                              alignItems:'center', justifyContent:'center', background:'var(--bg-subtle)',
                              borderRadius:'var(--r-md)', border:'1px solid var(--border)' }}>
                              <div style={{ fontFamily:'var(--font-display)', fontSize:'1.5rem', color:'var(--text-muted)' }}>中</div>
                              <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', fontFamily:'var(--font-mono)' }}>五行土</div>
                            </div>
                          )
                          const s = sectorMap[dir]
                          const qc = s ? Q_COLOR[s.quality] || Q_COLOR['中'] : 'var(--text-muted)'
                          return (
                            <div key={dir} style={{
                              aspectRatio:'1', display:'flex', flexDirection:'column',
                              alignItems:'center', justifyContent:'center', padding:'0.4rem',
                              background: s?.kind==='auspicious' ? 'rgba(74,122,90,0.08)' : s?.kind==='inauspicious' ? 'rgba(168,88,64,0.07)' : 'var(--bg-subtle)',
                              border:`1px solid ${s?.kind==='auspicious'?'rgba(74,122,90,0.3)': s?.kind==='inauspicious'?'rgba(168,88,64,0.25)':'var(--border)'}`,
                              borderRadius:'var(--r-md)', textAlign:'center',
                            }}>
                              <div style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginBottom:'2px', fontFamily:'var(--font-mono)' }}>{dir}</div>
                              <div style={{ fontWeight:700, color: qc, fontSize:'var(--text-sm)', lineHeight:1.1 }}>
                                {s?.star || s?.star_name || EIGHT_DIR_NAMES[dir]}
                              </div>
                              {s?.quality && <span className={`badge ${s.kind==='auspicious'?'badge-jade':'badge-red'}`}
                                style={{ fontSize:'9px', marginTop:'3px', padding:'1px 5px' }}>{s.quality}</span>}
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    {/* Detail list */}
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.75rem' }}>
                      {[...(result.auspicious_sectors||[]), ...(result.inauspicious_sectors||[])].map((s, i) => (
                        <div key={i} className="card" style={{ padding:'0.85rem 1rem',
                          borderLeft:`3px solid ${s.quality?.includes('吉') ? 'var(--jade)' : 'var(--accent)'}` }}>
                          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'0.35rem' }}>
                            <span style={{ fontWeight:700, color:'var(--text-primary)', fontFamily:'var(--font-title)', letterSpacing:'0.05em' }}>
                              {s.direction} · {s.star || s.star_name}
                              {s.classical_name && <span style={{ fontSize:'0.65rem', color:'var(--text-faint)', fontWeight:400, marginLeft:'0.4rem' }}>{s.classical_name}</span>}
                            </span>
                            <span className={`badge ${s.quality?.includes('吉')?'badge-jade':'badge-red'}`}>{s.quality}</span>
                          </div>
                          <p style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', fontFamily:'var(--font-serif)', lineHeight:1.65, margin:0 }}>
                            {s.meaning || s.description || s.classical_meaning}
                          </p>
                          {s.advice && (
                            <p style={{ fontSize:'var(--text-xs)', color:'var(--accent)', fontFamily:'var(--font-serif)', lineHeight:1.5, margin:'0.3rem 0 0', fontStyle:'italic' }}>
                              ▸ {s.advice}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── TAB: 阳宅三要 ── */}
                {tab === 'sanyao' && (
                  <YangzhaiSanyaoPanel />
                )}

                {/* ── TAB: 理气×形法 统一宅报告 ── */}
                {tab === 'unified' && (
                  <HouseReportPanel />
                )}

                {/* ── TAB: 飞星 — 玄空飞星专业版 ── */}
                {tab === 'flying' && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
                    <XuankongPanel />
                    
                    {/* 流年紫白（保留作为辅助参考） */}
                    <details>
                      <summary style={{
                        listStyle: 'none', cursor: 'pointer',
                        padding: '0.6rem 0.85rem',
                        background: 'var(--bg-subtle)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--r-md)',
                        fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)',
                        fontFamily: 'var(--font-serif)',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      }}>
                        <span>📅 流年紫白飞星（年盘辅参）</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-faint)' }}>展开 ▾</span>
                      </summary>
                      <div className="card" style={{ marginTop: '0.5rem' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.5rem',
                          fontFamily: 'var(--font-serif)', fontStyle: 'italic' }}>
                          流年紫白用于辅助判断当年特定方位的吉凶，是玄空盘的「时间加成」。
                          专业排盘应以上方"玄空飞星专业排盘"（三盘合参）为主。
                        </div>
                        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'4px', maxWidth:'380px', margin:'0 auto 1rem' }}>
                          {COMPASS_CELLS.flat().map(dir => {
                            const _starEntry = flyingStars[dir]
                            const starNum = _starEntry ? (typeof _starEntry === 'object' ? _starEntry.star_num : _starEntry) : null
                            const _starName  = _starEntry?.name  || null
                            const _starColor = _starEntry?.color || null
                            const _starNature = _starEntry?.nature || null
                            const displayColor  = _starColor  || (STAR_META[starNum]?.color  || 'var(--text-muted)')
                            const displayName   = _starName   ? _starName.replace(/[星]$/, '').slice(-2) : (STAR_META[starNum]?.name || '?')
                            const displayNature = _starNature || STAR_META[starNum]?.nature || ''
                            const natColor = displayNature.includes('大凶') ? 'var(--red)' : displayNature === '凶' ? 'var(--orange)' : displayNature.includes('吉') ? 'var(--jade)' : 'var(--text-muted)'
                            if (!starNum) return <div key={dir} style={{ aspectRatio:'1', background:'var(--bg-subtle)', borderRadius:'var(--r-sm)', border:'1px solid var(--border)' }}/>
                            return (
                              <div key={dir} style={{
                                aspectRatio:'1', display:'flex', flexDirection:'column', alignItems:'center',
                                justifyContent:'center', padding:'0.35rem',
                                background: `${displayColor}14`,
                                border:`1.5px solid ${displayColor}40`,
                                borderRadius:'var(--r-sm)', textAlign:'center',
                              }}>
                                <div style={{ fontSize:'9px', color:'var(--text-faint)', fontFamily:'var(--font-mono)', marginBottom:'1px' }}>{dir}</div>
                                <div style={{ fontFamily:'var(--font-display)', fontSize:'1.45rem', color:displayColor, lineHeight:1 }}>{starNum}</div>
                                <div style={{ fontSize:'10px', color:displayColor, fontWeight:700, marginTop:'1px' }}>{displayName}</div>
                                <div style={{ fontSize:'8.5px', color:natColor }}>{displayNature}</div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    </details>
                  </div>
                )}

                {/* ── TAB: 个人方位 ── */}
                {tab === 'personal' && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'0.75rem' }}>
                    <div className="card">
                      <div className="card-title">个人命卦四吉四凶方位</div>
                      <p style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', fontFamily:'var(--font-serif)', lineHeight:1.7, marginBottom:'0.85rem' }}>
                        《八宅明镜》：生气·天医·延年·伏位为四吉方（宜床位·书桌·大门）；
                        绝命·五鬼·六煞·祸害为四凶方（忌床位·大门·久坐）。
                      </p>
                      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.5rem' }}>
                        {Object.entries(personalDirs)
                          .filter(([k]) => PERSONAL_DIR_NAMES[k])
                          .map(([dirKey, dirInfo]) => {
                          const pdMeta   = PERSONAL_DIR_NAMES[dirKey] || {}
                          const isGood   = pdMeta.good === true
                          const label    = pdMeta.zh || dirKey
                          const dirLabel = dirInfo?.direction || ''
                          const desc     = dirInfo?.meaning || dirInfo?.description || ''
                          return (
                            <div key={dirKey} style={{
                              padding:'0.65rem 0.85rem',
                              background: isGood ? 'rgba(74,122,90,0.07)' : 'rgba(168,88,64,0.06)',
                              border:`1px solid ${isGood?'rgba(74,122,90,0.25)':'rgba(168,88,64,0.22)'}`,
                              borderRadius:'var(--r-md)',
                            }}>
                              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'0.3rem' }}>
                                <span style={{ fontWeight:700, color: isGood?'var(--jade)':'var(--accent)', fontSize:'var(--text-sm)' }}>
                                  {label}
                                </span>
                                <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', fontFamily:'var(--font-serif)' }}>{dirLabel}</span>
                              </div>
                              <p style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', fontFamily:'var(--font-serif)', lineHeight:1.6, margin:0 }}>
                                {desc}
                              </p>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                    {/* Practical tips */}
                    <div className="card">
                      <div className="card-title">实用布局建议</div>
                      {[
                        { title:'床位安置', desc:'主卧床头宜朝向个人生气方或天医方，有益健康睡眠' },
                        { title:'书桌方向', desc:'书桌宜面向文昌方（四绿文曲星所在）或天医方，利学习工作' },
                        { title:'灶口朝向', desc:'灶口宜朝向延年方或伏位方，忌朝向绝命五鬼方' },
                        { title:'大门开向', desc:'大门宜开向生气或延年方，是整宅纳气的关键' },
                      ].map(item => (
                        <div key={item.title} style={{ padding:'0.45rem 0', borderBottom:'1px solid var(--border)',
                          display:'flex', gap:'0.6rem', fontSize:'var(--text-sm)' }}>
                          <span style={{ color:'var(--accent)', fontWeight:700, width:'60px', flexShrink:0 }}>{item.title}</span>
                          <span style={{ color:'var(--text-secondary)', fontFamily:'var(--font-serif)', lineHeight:1.7 }}>{item.desc}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── TAB: 建议 ── */}
                {tab === 'advice' && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
                    {result.advice && (
                      <div className="card card-glow">
                        <div className="card-title">综合布局建议</div>
                        <p style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', color:'var(--text-secondary)', lineHeight:1.88 }}>
                          {result.advice}
                        </p>
                      </div>
                    )}
                    {/* Fengshui principles */}
                    <div className="card">
                      <div className="card-title">风水核心原则</div>
                      {[
                        { t:'藏风聚气', c:'《葬经》：气乘风则散，界水则止。风水之道，藏风聚气为上，明堂宽大，四水归堂' },
                        { t:'山水格局', c:'左青龙（东）高而蜿蜒，右白虎（西）低而驯顺，前朱雀（南）宽阔，后玄武（北）靠山' },
                        { t:'水法聚财', c:'水流缓曲而来为进财，直冲而去为破财，玉带环绕为大富之局，反弓背离为破败' },
                        { t:'室内煞气', c:'门冲梁压镜煞开门见灶等室内煞气，影响气场流通，须化解' },
                        { t:'九运应用', c:'2024-2043年九运，九紫当旺，南方·火属性·科技传媒人工智能行业最利' },
                      ].map(item => (
                        <div key={item.t} style={{ display:'flex', gap:'0.6rem', padding:'0.52rem 0', borderBottom:'1px solid var(--border)', fontSize:'var(--text-sm)' }}>
                          <span style={{ color:'var(--accent)', fontWeight:700, flexShrink:0, width:'55px' }}>{item.t}</span>
                          <span style={{ color:'var(--text-secondary)', fontFamily:'var(--font-serif)', lineHeight:1.75 }}>{item.c}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI */}
                <div style={{ marginTop:'1rem' }}>
                  <AiInterpretPanel module="fengshui" data={result} extraContext={`朝向${form.house_facing}`} />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
