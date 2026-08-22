import React, { useState } from 'react'
import { clickable } from '../../utils/a11y'
import '../../styles/plates.css'
import AiInterpretPanel from '../../components/UI/AiInterpretPanel'
import ShareImage from '../../components/UI/ShareImage'
import { dateApi } from '../../api/client'
import { useAsyncAction } from '../../hooks/useAsyncAction'
import DateOverview from './DateOverview'
import DateSynthesis from './DateSynthesis'
import DatePerspectives from './DatePerspectives'
import DateConsistencyAudit from './DateConsistencyAudit'
import NarrationPanel from '../../components/NarrationPanel'

const PURPOSES = ['婚嫁','开业','动土','搬家','出行','求医','祭祀','签约','安床','剃胎发']
const PURPOSE_ICONS = { 婚嫁:'💍',开业:'🏪',动土:'🏗',搬家:'📦',出行:'✈',求医:'🏥',祭祀:'🕯',签约:'📝',安床:'🛏',剃胎发:'👶' }
const WEEKDAY = ['一','二','三','四','五','六','日']

const OFFICER_COLOR = {
  '除':'var(--jade)', '成':'var(--jade)', '开':'var(--jade)', '定':'var(--jade)', '收':'var(--jade)',
  '满':'var(--cyan-b)', '平':'var(--text-muted)',
  '建':'var(--orange)', '危':'var(--orange)', '执':'var(--orange)',
  '闭':'var(--text-muted)', '破':'var(--red-light)',
}
const JIANCHU_NATURE = { '建':'凶','除':'大吉','满':'中','平':'中','定':'吉','执':'小凶','破':'大凶','危':'小凶','成':'大吉','收':'吉','开':'大吉','闭':'凶' }

const THEORY = [
  { icon:'📅', t:'建除十二神', d:'成·开·除为三吉日，破日最凶；每月首日为建日，依次轮转，是择日第一要素。' },
  { icon:'☀', t:'黄道吉日', d:'青龙·明堂·金匮·天德·玉堂·司命为六黄道（吉），白虎·天牢·玄武·朱雀·勾陈·天刑为六黑道（凶）。' },
  { icon:'⭐', t:'天德月德', d:'天德月德贵神临日，可化百煞，婚嫁动土最宜，是日择事逢凶化吉。' },
  { icon:'🔺', t:'三大禁忌', d:'年三煞·太岁·五黄三方禁止动土修造，尤其动土开业必查这三煞。' },
  { icon:'🌙', t:'二十八宿', d:'28宿轮日值班，角房室壁娄毕井张轸等为吉宿，亢氐心牛女虚危奎昴觜鬼柳星翼等为凶宿。' },
]

function buildCalendar(year, month, result) {
  const firstDay = new Date(year, month - 1, 1)
  const lastDay  = new Date(year, month, 0).getDate()
  const startDow = (firstDay.getDay() + 6) % 7  // Mon=0
  const auspSet = new Set((result.auspicious_days || []).map(d => d.day))
  const bestSet = new Set((result.best_days || []).slice(0,3).map(d => d.day))
  const inauspSet = new Set((result.inauspicious_days || []).map(d => d.day))
  const dayMap = {}
  ;(result.auspicious_days || []).forEach(d => { dayMap[d.day] = d })
  ;(result.inauspicious_days || []).forEach(d => { dayMap[d.day] = d })
  const cells = Array(startDow).fill(null)
  for (let d = 1; d <= lastDay; d++) cells.push({ day:d, auspicious:auspSet.has(d), best:bestSet.has(d), inauspicious:inauspSet.has(d), info:dayMap[d] })
  return cells
}

export default function DateSelectPage() {
  const now = new Date()
  const [form, setForm] = useState({
    purpose:'婚嫁', is_lunar:false, year:now.getFullYear(), month:now.getMonth()+1,
    birth_year:'', birth_month:'', birth_day:'',
  })
  const [result, setResult]     = useState(null)
  const [showShare, setShowShare] = useState(false)
  const [selected, setSelected] = useState(null)
  const [viewMode, setViewMode] = useState('calendar')
  const { loading, error, run: runAsync } = useAsyncAction()

  const run = async () => {
    setSelected(null)
    const req = { ...form }
    if (!req.birth_year) { delete req.birth_year; delete req.birth_month; delete req.birth_day }
    else { req.birth_year=Number(req.birth_year); req.birth_month=Number(req.birth_month)||1; req.birth_day=Number(req.birth_day)||1 }
    const data = await runAsync(() => dateApi.select(req), { successMsg: '择日完成' })
    if (data) setResult(data)
  }

  const set = (k, v) => setForm(f => ({...f,[k]:v}))
  const calDays = result ? buildCalendar(form.year, form.month, result) : null

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">择日选时</div>
          <div className="page-subtitle">十二建除 · 黄道黑道 · 二十八宿 · 天德月德 · 三煞禁忌</div>
        </div>
      </div>

      <div className="page-body">
        <div className="page-cols">
          {/* ── Left ── */}
          <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
            <div className="card">
              <div className="card-title">占问事项</div>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.4rem' }}>
                {PURPOSES.map(p => (
                  <button key={p}
                    onClick={() => set('purpose', p)}
                    style={{
                      padding:'0.48rem 0.55rem', borderRadius:'var(--r-sm)',
                      border:`1px solid ${form.purpose===p?'var(--accent-dim)':'var(--border)'}`,
                      background:form.purpose===p?'var(--accent-bg)':'var(--bg-subtle)',
                      cursor:'pointer', display:'flex', alignItems:'center', gap:'0.4rem',
                      fontSize:'var(--text-sm)', fontWeight:form.purpose===p?600:400,
                      color:form.purpose===p?'var(--accent)':'var(--text-muted)',
                      transition:'all var(--t-fast)',
                    }}>
                    <span>{PURPOSE_ICONS[p]}</span>
                    <span>{p}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="card-title">查询月份</div>
              <div className="form-row-2">
                <div className="form-group">
                  <label>年份</label>
                  <input type="number" min="2024" max="2030" value={form.year} onChange={e=>set('year',Number(e.target.value))} />
                </div>
                <div className="form-group">
                  <label>月份</label>
                  <input type="number" min="1" max="12" value={form.month} onChange={e=>set('month',Number(e.target.value))} />
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-title">个人生辰（可选）</div>
              <p style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:'0.5rem', fontFamily:'var(--font-serif)' }}>
                填入后按本命八字用神/冲克过滤，择「日扶其用、不犯其冲」之吉日
              </p>
              <div className="form-row-3">
                <div className="form-group"><label>出生年（农历）</label><input type="number" placeholder="如1990" value={form.birth_year} onChange={e=>set('birth_year',e.target.value)} /></div>
                <div className="form-group"><label>出生月（农历）</label><input type="number" min="1" max="12" placeholder="1-12" value={form.birth_month} onChange={e=>set('birth_month',e.target.value)} /></div>
                <div className="form-group"><label>出生日（农历）</label><input type="number" min="1" max="31" placeholder="1-31" value={form.birth_day} onChange={e=>set('birth_day',e.target.value)} /></div>
              </div>
            </div>

            <button className="btn btn-primary btn-full btn-lg" onClick={run} disabled={loading}>
              {loading ? '推算中…' : '推算吉日 ▶'}
            </button>
            {error && <div className="error-box">⚠ {error}</div>}

            {/* Theory sidebar */}
            <div className="card">
              <div className="card-title">择日理论精要</div>
              {THEORY.map((t, i) => (
                <div key={i} style={{ display:'flex', gap:'0.65rem', padding:'0.5rem 0',
                  borderBottom:'1px solid var(--border)' }}>
                  <span style={{ fontSize:'0.95rem', flexShrink:0 }}>{t.icon}</span>
                  <div>
                    <div style={{ fontSize:'var(--text-xs)', fontWeight:700, color:'var(--accent)', marginBottom:'2px' }}>{t.t}</div>
                    <p style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', margin:0, fontFamily:'var(--font-serif)', lineHeight:1.65 }}>{t.d}</p>
                  </div>
                </div>
              ))}
            </div>

          </div>

          {/* ── Right ── */}
          <div>
            {loading && <div className="loading"><div className="spinner"/><p>推算吉日中…</p></div>}

            {!loading && !result && (
              <div className="card" style={{ textAlign:'center', padding:'3.5rem 2rem' }}>
                <div style={{ fontSize:'3.5rem', marginBottom:'1rem', opacity:0.18 }}>◈</div>
                <p style={{ fontFamily:'var(--font-serif)', color:'var(--text-muted)', fontSize:'var(--text-base)', lineHeight:1.9 }}>
                  《协纪辨方书》：择日须合建除、黄道、天德，<br/>避三煞五黄太岁，方为上吉之日
                </p>
              </div>
            )}

            {!loading && result && (
              <>
                {/* 综合总论 · 总汇合参（全功能激活后的最终汇总，作为右栏主体内容的开篇总纲）*/}
                {result?.master_synthesis?.available && (() => {
                  const QC = { 吉:'#27ae60', 中:'var(--accent)', 凶:'#c0392b' }
                  const ms = result.master_synthesis
                  const pc = QC[ms.overall_quality] || 'var(--accent)'
                  return (
                    <div className="card card-glow" style={{ borderTop:`4px solid ${pc}`, marginBottom:'1rem' }}>
                      <div className="card-title">综合总论 · 总汇合参</div>
                      <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)', fontWeight:600,
                        color:pc, marginBottom:'0.5rem' }}>
                        为「{ms.purpose}」择期 · 综评<span style={{ color:pc }}>{ms.overall_quality}</span>
                      </div>
                      <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', lineHeight:1.7,
                        color:'var(--text-secondary)', padding:'0.5rem 0.7rem', background:`${pc}10`,
                        borderLeft:`4px solid ${pc}`, marginBottom:'0.7rem' }}>
                        {ms.headline}
                      </div>
                      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))', gap:'6px', marginBottom:'0.7rem' }}>
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
                      <NarrationPanel ms={ms} fullData={result} module="date" />
                    </div>
                  )
                })()}

                {/* 本月择日概览统计 */}
                <div className="card card-glow" style={{ marginBottom:'1rem' }}>
                  <div className="card-title">本月择日概览</div>
                  <div style={{ display:'flex', gap:'0.75rem', justifyContent:'space-around' }}>
                    {[
                      ['吉日', (result.auspicious_days||[]).length, 'var(--jade)'],
                      ['最佳', (result.best_days||[]).length, 'var(--accent)'],
                      ['凶日', (result.inauspicious_days||[]).length, 'var(--red-light)'],
                    ].map(([l,n,c]) => (
                      <div key={l} style={{ textAlign:'center' }}>
                        <div style={{ fontFamily:'var(--font-display)', fontSize:'2rem', color:c, lineHeight:1 }}>{n}</div>
                        <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{l}</div>
                      </div>
                    ))}
                  </div>
                  {result.three_killings && (
                    <div style={{ marginTop:'0.65rem', padding:'0.45rem 0.7rem',
                      background:'rgba(207,59,44,0.07)', border:'1px solid var(--accent-dim)',
                      borderRadius:'var(--r-sm)', fontSize:'var(--text-xs)', color:'var(--accent)',
                      fontFamily:'var(--font-serif)' }}>
                      ⚠ 三煞方位：{result.three_killings} — 本月动土忌此方向
                    </div>
                  )}
                </div>

                <DateOverview data={result} />
                <DateSynthesis data={result} />
                <DatePerspectives data={result} />
                <DateConsistencyAudit data={result} />

                <div style={{ display:'flex', gap:'0.5rem', marginBottom:'1rem', alignItems:'center' }}>
                  <button className={`btn btn-sm ${viewMode==='calendar'?'btn-primary':''}`} onClick={() => setViewMode('calendar')}>📅 日历</button>
                  <button className={`btn btn-sm ${viewMode==='list'?'btn-primary':''}`} onClick={() => setViewMode('list')}>📋 列表</button>
                  <button className="btn btn-sm" onClick={() => setShowShare(true)} title="生成分享图">🖼 分享图</button>
                  <span style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', marginLeft:'auto', fontFamily:'var(--font-serif)' }}>
                    {form.year}年{form.month}月 · {form.purpose}
                  </span>
                </div>

                {viewMode === 'calendar' && calDays && (
                  <div className="card">
                    <div className="card-title">{form.year}年{form.month}月 择日历</div>
                    {/* Weekday headers */}
                    <div style={{ display:'grid', gridTemplateColumns:'repeat(7,1fr)', gap:'3px', marginBottom:'4px' }}>
                      {WEEKDAY.map(d => (
                        <div key={d} style={{ textAlign:'center', fontSize:'var(--text-xs)', color:'var(--text-faint)', padding:'4px 0', fontWeight:600 }}>{d}</div>
                      ))}
                    </div>
                    {/* Days grid */}
                    <div style={{ display:'grid', gridTemplateColumns:'repeat(7,1fr)', gap:'3px' }}>
                      {calDays.map((cell, i) => {
                        if (!cell) return <div key={i}/>
                        const jcOfficer = cell.info?.officer
                        const bgColor = cell.best ? 'var(--accent)' : cell.auspicious ? 'rgba(74,122,90,0.09)' : cell.inauspicious ? 'rgba(168,88,64,0.07)' : 'transparent'
                        const borderColor = cell.best ? 'var(--accent)' : cell.auspicious ? 'rgba(74,122,90,0.35)' : cell.inauspicious ? 'rgba(168,88,64,0.25)' : 'var(--border)'
                        const textColor = cell.best ? '#fff' : cell.auspicious ? 'var(--jade)' : cell.inauspicious ? 'var(--red)' : 'var(--text-primary)'
                        return (
                          <div key={i} {...clickable(() => setSelected(cell.info || cell))}
                            style={{
                              aspectRatio:'0.85', borderRadius:'var(--r-sm)',
                              border:`1.5px solid ${borderColor}`, background:bgColor,
                              cursor:'pointer', padding:'4px 2px',
                              display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
                              gap:'2px', transition:'all 0.12s',
                            }}>
                            <div style={{ fontSize:'var(--text-sm)', fontWeight:700, color:textColor, lineHeight:1 }}>{cell.day}</div>
                            {jcOfficer && (
                              <div style={{ fontSize:'8px', color: cell.best ? 'rgba(255,255,255,0.85)' : OFFICER_COLOR[jcOfficer] || 'var(--text-faint)', lineHeight:1 }}>
                                {jcOfficer}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                    <div style={{ display:'flex', gap:'1rem', marginTop:'0.75rem', fontSize:'var(--text-xs)', color:'var(--text-faint)', flexWrap:'wrap' }}>
                      <span><span style={{ color:'var(--accent)', fontWeight:700 }}>■</span> 最佳吉日</span>
                      <span><span style={{ color:'var(--jade)', fontWeight:700 }}>■</span> 普通吉日</span>
                      <span><span style={{ color:'var(--red)', fontWeight:700 }}>■</span> 凶日</span>
                    </div>
                  </div>
                )}

                {/* Selected day detail */}
                {selected && (
                  <div className="card card-glow" style={{ marginTop:'0.85rem' }}>
                    <div className="gv-plate">
                      <div className="gv-almanac-head">
                        <span className="gv-seal" style={{ background:'#d8ab3c', color:'#473205' }}>历</span>
                        <span className="dt">{form.year}年{form.month}月{selected.day || ''}日</span>
                      </div>

                      <div className="gv-almanac-tags">
                        {selected.officer && (
                          <span className="gv-almanac-tag" style={{
                            color: JIANCHU_NATURE[selected.officer]==='大吉'?'var(--gv-mu)':JIANCHU_NATURE[selected.officer]==='大凶'?'var(--gv-vermilion)':'var(--gv-ink-3)',
                          }}>{selected.officer}日 · {JIANCHU_NATURE[selected.officer]}</span>
                        )}
                        {selected.star && <span className="gv-almanac-tag" style={{ color:'var(--gv-shui)' }}>{selected.star}宿</span>}
                        {selected.score !== undefined && (
                          <span className="gv-almanac-tag" style={{ color: selected.score>0?'var(--gv-mu)':selected.score<0?'var(--gv-vermilion)':'var(--gv-ink-3)' }}>
                            综合评分 {selected.score>0?'+':''}{selected.score}
                          </span>
                        )}
                      </div>

                      {selected.reasons?.length > 0 && (
                        <div className="gv-almanac-list">
                          {selected.reasons.map((r,i) => (
                            <div key={i} className="gv-almanac-item">
                              <span className={`mk ${r.includes('忌')||r.includes('凶')?'ji':'yi'}`}>
                                {r.includes('忌')||r.includes('凶')?'✗':'✓'}
                              </span>
                              <span>{r}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {selected.shensha_purpose && (
                        <div className="gv-almanac-note">
                          <div className="lbl" style={{ color:'var(--gv-ink-3)' }}>
                            神煞 · 择「{selected.shensha_purpose.purpose}」专断 [{selected.shensha_purpose.level}]
                          </div>
                          <div className="row">{selected.shensha_purpose.verdict}</div>
                        </div>
                      )}

                      {selected.shensha_annotated?.ji_shen_explained?.length > 0 && (
                        <div className="gv-almanac-note">
                          <div className="lbl good">吉神释义</div>
                          {selected.shensha_annotated.ji_shen_explained.filter(e=>e.meaning).slice(0,6).map((e,i)=>(
                            <div key={i} className="row">
                              <span className="nm good">{e.name}</span>
                              <span className="lv">（{e.level}）</span>　{e.meaning}
                            </div>
                          ))}
                        </div>
                      )}

                      {selected.shensha_annotated?.xiong_sha_explained?.length > 0 && (
                        <div className="gv-almanac-note">
                          <div className="lbl bad">凶煞释义</div>
                          {selected.shensha_annotated.xiong_sha_explained.filter(e=>e.meaning).slice(0,6).map((e,i)=>(
                            <div key={i} className="row">
                              <span className="nm bad">{e.name}</span>
                              <span className="lv">（{e.level}）</span>　{e.meaning}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {viewMode === 'list' && (
                  <div style={{ display:'flex', flexDirection:'column', gap:'0.5rem', marginTop:'0.85rem' }}>
                    {[...(result.best_days||[]),...(result.auspicious_days||[])].slice(0,12).map((d,i) => (
                      <div key={i} className="card" style={{ padding:'0.75rem 1rem', cursor:'pointer',
                        borderColor: i < (result.best_days||[]).length ? 'var(--accent-dim)' : 'var(--border)' }}
                        {...clickable(() => setSelected(d), { label:`${form.year}年${form.month}月${d.day}日` })}>
                        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                          <span style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-md)',
                            color: i<(result.best_days||[]).length?'var(--accent)':'var(--text-primary)' }}>
                            {form.year}年{form.month}月{d.day}日
                          </span>
                          <div style={{ display:'flex', gap:'0.3rem' }}>
                            {d.officer && <span className="badge badge-gold">{d.officer}</span>}
                            {d.star && <span className="badge badge-cyan">{d.star}</span>}
                          </div>
                        </div>
                        {d.reasons?.slice(0,2).map((r,j) => (
                          <div key={j} style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)',
                            fontFamily:'var(--font-serif)', marginTop:'3px' }}>· {r}</div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ marginTop:'1rem' }}>
                  <AiInterpretPanel module="date" data={result} extraContext={`${form.year}年${form.month}月 · ${form.purpose}`} />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
      {showShare && <ShareImage data={result ? { ...result, year: form.year, month: form.month, purpose: form.purpose } : null} module="date" onClose={() => setShowShare(false)} />}
    </div>
  )
}
