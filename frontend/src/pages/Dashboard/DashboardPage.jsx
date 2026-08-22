import React, { useState, useEffect, useCallback } from 'react'
import { clickable } from '../../utils/a11y'
import { Seal, MODULES, STONES, WXC, Mtn, InkBorder } from '../../components/UI/Shared'
import AiInterpretPanel from '../../components/UI/AiInterpretPanel'
import { ZiweiVis, LiuyaoVis, BaziVis, QimenVis, FengshuiVis } from '../../components/particles/Visualizations'
import { baziApi, ziweiApi, qimenApi, fengshuiApi, liuyaoApi, knowledgeApi } from '../../api/client'
import { useNotifyStore } from '../../store/settingsStore'

// ─── Helper: API call with loading ───────────────────────────────

function useApi(apiFn) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const { notify } = useNotifyStore()
  const execute = useCallback(async (...args) => {
    setLoading(true)
    try { const r = await apiFn(...args); setData(r); return r }
    catch (e) { notify(e.message, 'error') }
    finally { setLoading(false) }
  }, [apiFn])
  return { data, loading, execute, setData }
}

function Loading() {
  return <div style={{ textAlign:"center", padding:"30px", color:"var(--muted)", fontSize:12 }}>排算中…</div>
}

// ═══════════════════════════════════════════════════════════════
// PANELS
// ═══════════════════════════════════════════════════════════════

// ─── 八字 ────────────────────────────────────────────────────────

function BaziPanel({ birth }) {
  const { data, loading, execute } = useApi(baziApi.chart)
  const fortune = useApi(baziApi.fortune)

  useEffect(() => { if (birth?.year) execute(birth) }, [birth])
  useEffect(() => {
    if (data && birth?.year) {
      fortune.execute({ ...birth, from_year: new Date().getFullYear(), to_year: new Date().getFullYear() + 5 })
    }
  }, [data])

  if (loading || !data) return <Loading/>

  const pillars = ['year_pillar','month_pillar','day_pillar','hour_pillar']
  const wxMap = { 木:'var(--wx-wood)',火:'var(--wx-fire)',土:'var(--wx-earth)',金:'var(--wx-metal)',水:'var(--wx-water)' }

  return (
    <div>
      {/* Particle visualization */}
      <BaziVis pillars={pillars.map(k=>data[k]).filter(Boolean)} dayun={data.dayun||[]}/>

      {/* Four pillars */}
      <div style={{ display:"flex", gap:0, justifyContent:"center", marginBottom:14 }}>
        {pillars.map((k, i) => {
          const p = data[k]
          if (!p) return null
          const isDay = k === 'day_pillar'
          return (
            <div key={k} style={{
              width:88, textAlign:"center", padding:"12px 6px",
              borderLeft:`1px solid var(--faint)`, borderRight:i===3?`1px solid var(--faint)`:"none",
              background:isDay?"var(--accent-l)":"transparent", position:"relative",
            }}>
              {isDay && <div style={{ position:"absolute",top:0,left:0,right:0,height:2,background:"var(--accent)" }}/>}
              <div style={{ fontSize:12,color:"var(--muted)",letterSpacing:2,marginBottom:8 }}>{p.label}</div>
              <div style={{ fontSize:18,fontWeight:600,color:wxMap[p.wuxing_gan]||"var(--text)",fontFamily:"var(--font-serif)",lineHeight:1 }}>{p.tiangan}</div>
              <div style={{ fontSize:11,color:"var(--faint)",margin:"3px 0" }}>{p.wuxing_gan}</div>
              <div style={{ width:16,height:1,background:"var(--faint)",margin:"3px auto" }}/>
              <div style={{ fontSize:18,fontWeight:600,color:wxMap[p.wuxing_zhi]||"var(--text)",fontFamily:"var(--font-serif)",lineHeight:1 }}>{p.dizhi}</div>
              <div style={{ fontSize:11,color:"var(--faint)",margin:"3px 0" }}>{p.wuxing_zhi}</div>
              {p.shishen_gan && <div style={{ fontSize:12,color:isDay?"var(--accent)":"var(--sub)",marginTop:6,fontWeight:500 }}>{p.shishen_gan}</div>}
              {p.nayin && <div style={{ fontSize:11,color:"var(--muted)",marginTop:2 }}>{p.nayin}</div>}
            </div>
          )
        })}
      </div>

      {/* Metrics */}
      <div style={{ display:"flex",gap:0,borderTop:"1px solid var(--faint)",borderBottom:"1px solid var(--faint)" }}>
        {[
          { label:"身强弱", value:data.strength, color:data.strength==="身强"?"var(--accent)":"var(--danger)" },
          { label:"格局", value:data.pattern, color:"var(--warm)" },
          { label:"月令", value:data.strength_info?.deling?"得令":"不得令", color:data.strength_info?.deling?"var(--accent)":"var(--danger)" },
        ].map((m,i) => (
          <div key={i} style={{ flex:1,textAlign:"center",padding:"8px 4px",borderRight:i<2?"1px solid var(--faint)":"none" }}>
            <div style={{ fontSize:11,color:"var(--muted)",marginBottom:3 }}>{m.label}</div>
            <div style={{ fontSize:14,fontWeight:700,color:m.color,fontFamily:"var(--font-serif)" }}>{m.value||'—'}</div>
          </div>
        ))}
      </div>

      {/* Shensha */}
      {data.shensha?.length > 0 && (
        <div style={{ marginTop:10,display:"flex",gap:6,flexWrap:"wrap" }}>
          {data.shensha.map((s,i) => (
            <span key={i} style={{ fontSize:11,color:"var(--warm)",border:"1px solid var(--warm)",padding:"1px 6px" }}>
              {s.name}·{s.pillar}
            </span>
          ))}
        </div>
      )}

      {/* Dayun */}
      {data.dayun?.length > 0 && (
        <div style={{ marginTop:14 }}>
          <div style={{ fontSize:13,fontWeight:700,color:"var(--text)",fontFamily:"var(--font-serif)",marginBottom:8 }}>大运</div>
          <div style={{ display:"flex",gap:0,borderTop:"1px solid var(--faint)" }}>
            {data.dayun.slice(0,6).map((dy,i) => (
              <div key={i} style={{ flex:1,textAlign:"center",padding:"8px 2px",borderRight:i<5?"1px solid var(--faint)":"none" }}>
                <div style={{ fontSize:14,fontWeight:600,fontFamily:"var(--font-serif)" }}>{dy.tiangan}{dy.dizhi}</div>
                <div style={{ fontSize:11,color:"var(--muted)" }}>{Math.floor(dy.start_age)}岁</div>
                <div style={{ fontSize:11,color:dy.quality==="吉"?"var(--accent)":"var(--danger)",fontWeight:600 }}>{dy.quality}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <AiInterpretPanel module="bazi" data={data} extraContext="命盘" />
    </div>
  )
}

// ─── 紫微 ────────────────────────────────────────────────────────

function ZiweiPanel({ birth }) {
  const { data, loading, execute } = useApi(ziweiApi.chart)
  const [sel, setSel] = useState(null)

  useEffect(() => {
    if (birth?.year) {
      const hourIdx = Math.floor((birth.hour || 0) / 2)
      const dt = `${birth.year}-${String(birth.month).padStart(2,'0')}-${String(birth.day).padStart(2,'0')}`
      execute({ solar_date:dt, birth_hour_index:hourIdx, gender:birth.gender==='female'?'女':'男' })
    }
  }, [birth])

  if (loading || !data) return <Loading/>

  const palaces = data.palaces || []
  const LAYOUT = [[11,10,9,8],[0,-1,-1,7],[1,-1,-1,6],[2,3,4,5]]
  const soulIdx = data.metadata?.soul_palace_index ?? 0

  return (
    <div style={{ display:"flex",gap:14,flexWrap:"wrap" }}>
      {/* Particle four-hua flying threads */}
      <div style={{ width:"100%",marginBottom:4 }}>
        <ZiweiVis palaces={palaces} feihua={(data.feihua||[]).map(f=>({from:f.source_palace_idx||0,to:f.target_palace_idx||0,type:f.hua_type||''}))} soulIdx={soulIdx}/>
      </div>
      <div style={{ flex:"1 1 300px" }}>
        <div style={{ display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:0,border:"1px solid var(--faint)" }}>
          {LAYOUT.flat().map((idx, i) => {
            if (idx === -1) {
              if (i === 5) return (
                <div key={i} style={{ gridColumn:"span 2",gridRow:"span 2",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",borderRight:"1px solid var(--faint)",borderBottom:"1px solid var(--faint)" }}>
                  <div style={{ width:20,height:2,background:"var(--seal-red)",marginBottom:6 }}/>
                  <span style={{ fontSize:18,fontWeight:800,color:"var(--text)",fontFamily:"var(--font-serif)",letterSpacing:3 }}>命主</span>
                  <span style={{ fontSize:11,color:"var(--muted)",marginTop:4 }}>
                    {data.metadata?.five_elements || ''}
                  </span>
                  <div style={{ width:20,height:2,background:"var(--seal-red)",marginTop:6 }}/>
                </div>
              )
              return null
            }
            const p = palaces[idx]
            if (!p) return <div key={i}/>
            const isSoul = idx === soulIdx
            const isSel = sel === idx
            return (
              <div key={i} {...clickable(() => setSel(isSel?null:idx))} style={{
                padding:"7px 6px",minHeight:68,cursor:"pointer",
                borderRight:"1px solid var(--faint)",borderBottom:"1px solid var(--faint)",
                background:isSel?"var(--accent-l)":isSoul?"rgba(192,48,32,0.02)":"transparent",
                transition:"background .15s",position:"relative",
              }}>
                {isSoul && <div style={{ position:"absolute",left:0,top:0,bottom:0,width:2,background:"var(--seal-red)" }}/>}
                <div style={{ display:"flex",justifyContent:"space-between",marginBottom:3 }}>
                  <span style={{ fontSize:13,fontWeight:700,color:isSoul?"var(--seal-red)":"var(--text)" }}>{p.name}</span>
                  <span style={{ fontSize:11,color:"var(--faint)" }}>{p.heavenly_stem}{p.earthly_branch}</span>
                </div>
                {(p.major_stars||[]).map((s,si) => (
                  <div key={si} style={{ fontSize:12,color:"var(--wx-fire)",fontWeight:500 }}>
                    {typeof s === 'string' ? s : s.name}{s.brightness ? ` ${s.brightness}` : ''}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      </div>

      {sel !== null && palaces[sel] && (
        <div style={{ flex:"0 0 200px",animation:"fadeIn .25s ease" }}>
          <InkBorder active>
            <div style={{ fontSize:14,fontWeight:700,fontFamily:"var(--font-serif)",color:"var(--text)",marginBottom:6 }}>
              {palaces[sel].name}
            </div>
            <div style={{ fontSize:12,color:"var(--sub)",marginBottom:4 }}>
              {palaces[sel].heavenly_stem}{palaces[sel].earthly_branch}
            </div>
            <div style={{ fontSize:12,color:"var(--wx-fire)",marginBottom:8 }}>
              {(palaces[sel].major_stars||[]).map(s => typeof s === 'string' ? s : s.name).join(' · ')}
            </div>
            {palaces[sel].minor_stars?.length > 0 && (
              <div style={{ fontSize:11,color:"var(--muted)",marginBottom:6 }}>
                辅星：{palaces[sel].minor_stars.slice(0,5).map(s => typeof s === 'string' ? s : s.name).join(' ')}
              </div>
            )}
            {palaces[sel].decadal_range && (
              <div style={{ fontSize:11,color:"var(--muted)" }}>
                大限 {palaces[sel].decadal_range[0]}–{palaces[sel].decadal_range[1]}岁
              </div>
            )}
          </InkBorder>
        </div>
      )}

      <div style={{ width:"100%" }}>
        <AiInterpretPanel module="ziwei" data={data} extraContext="紫微命盘" />
      </div>
    </div>
  )
}

// ─── 运程 ────────────────────────────────────────────────────────

function DayunPanel({ birth }) {
  const { data, loading, execute } = useApi(baziApi.fortune)
  useEffect(() => {
    if (birth?.year) {
      const yr = new Date().getFullYear()
      execute({ ...birth, from_year: yr - 1, to_year: yr + 10 })
    }
  }, [birth])
  if (loading || !data) return <Loading/>

  const dayun = data.dayun || []
  const liunian = data.liunian || []

  return (
    <div>
      {dayun.length > 0 && (
        <div style={{ marginBottom:16 }}>
          <div style={{ fontSize:13,fontWeight:700,fontFamily:"var(--font-serif)",marginBottom:8 }}>大运</div>
          <div style={{ display:"flex",gap:0,borderTop:"1px solid var(--faint)" }}>
            {dayun.slice(0,8).map((dy,i) => (
              <div key={i} style={{ flex:1,textAlign:"center",padding:"8px 2px",borderRight:i<7?"1px solid var(--faint)":"none" }}>
                <div style={{ fontSize:14,fontWeight:600,fontFamily:"var(--font-serif)" }}>{dy.tiangan}{dy.dizhi}</div>
                <div style={{ fontSize:11,color:"var(--muted)" }}>{Math.floor(dy.start_age)}岁</div>
                <div style={{ fontSize:11,color:dy.quality==="吉"?"var(--accent)":"var(--danger)",fontWeight:600 }}>{dy.quality}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {liunian.length > 0 && (
        <div>
          <div style={{ fontSize:13,fontWeight:700,fontFamily:"var(--font-serif)",marginBottom:8 }}>流年</div>
          <div style={{ display:"flex",gap:0,flexWrap:"wrap",borderTop:"1px solid var(--faint)" }}>
            {liunian.map((ly,i) => (
              <div key={i} style={{ width:"16.66%",textAlign:"center",padding:"6px 2px",borderRight:"1px solid var(--faint)",borderBottom:"1px solid var(--faint)" }}>
                <div style={{ fontSize:11,color:"var(--muted)" }}>{ly.year}</div>
                <div style={{ fontSize:13,fontWeight:600,fontFamily:"var(--font-serif)" }}>{ly.tiangan}{ly.dizhi}</div>
                <div style={{ fontSize:11,color:ly.quality==="吉"?"var(--accent)":"var(--danger)" }}>{ly.quality}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── 奇门 ────────────────────────────────────────────────────────

function QimenPanel() {
  const { data, loading, execute } = useApi(qimenApi.now)
  useEffect(() => { execute() }, [])
  if (loading || !data) return <Loading/>

  const palaces = data.palaces || []
  const order = [4,9,2,3,5,7,8,1,6]
  const qc = { true:"var(--accent)", false:"var(--danger)" }

  return (
    <div>
      {/* Particle palace energy flow */}
      <QimenVis palaces={palaces}/>
      <div style={{ fontSize:12,color:"var(--muted)",marginBottom:8 }}>
        {data.ju_type || ''}第{data.ju_number || data.ju || ''}局 · {data.yuan || ''}
      </div>
      <div style={{ display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:0,border:"1px solid var(--faint)",maxWidth:420 }}>
        {order.map(pos => {
          const p = palaces.find(pp => pp.position === pos) || {}
          const isGood = p.is_auspicious
          const col = isGood ? "var(--accent)" : p.is_auspicious === false ? "var(--danger)" : "var(--muted)"
          return (
            <div key={pos} style={{ padding:"8px 7px",minHeight:60,borderRight:"1px solid var(--faint)",borderBottom:"1px solid var(--faint)",position:"relative" }}>
              {isGood !== undefined && <div style={{ position:"absolute",top:0,left:0,right:0,height:2,background:col }}/>}
              <div style={{ display:"flex",justifyContent:"space-between",alignItems:"baseline" }}>
                <span style={{ fontSize:13,fontWeight:700,color:col }}>{p.star||'—'}</span>
                <span style={{ fontSize:14,fontWeight:600,color:`${col}90`,fontFamily:"var(--font-serif)" }}>{p.stem||''}</span>
              </div>
              <div style={{ fontSize:12,color:"var(--sub)",marginTop:3 }}>{p.door||'—'}</div>
              <div style={{ fontSize:11,color:"var(--muted)" }}>{p.deity||''}</div>
              {p.is_zhifu && <span style={{ fontSize:9,color:"var(--danger)",fontWeight:700,position:"absolute",bottom:3,right:5 }}>符</span>}
              {p.is_zhishi && <span style={{ fontSize:9,color:"var(--wx-water)",fontWeight:700,position:"absolute",bottom:3,right:5 }}>使</span>}
            </div>
          )
        })}
      </div>
      <AiInterpretPanel module="qimen" data={data} extraContext="奇门遁甲" />
    </div>
  )
}

// ─── 六爻 ────────────────────────────────────────────────────────

function LiuyaoPanel() {
  const { data, loading, execute } = useApi(liuyaoApi.divine)
  const [question, setQuestion] = useState('')
  const [topic, setTopic] = useState('综合')
  const topics = ['求财','求官仕途','考试功名','婚姻感情','求医疾病','出行远行','家宅风水','综合']

  const doDiv = () => execute({ method:'coin', question, topic })

  if (data) {
    const yaos = data.yaos || []
    const orig = data.original || {}
    return (
      <div>
        <div style={{ display:"flex",alignItems:"center",gap:8,marginBottom:12 }}>
          <span style={{ fontSize:16,fontWeight:700,fontFamily:"var(--font-serif)" }}>{orig.name || `第${orig.number}卦`}</span>
          <span style={{ fontSize:12,color:"var(--muted)" }}>{data.palace_trigram}宫</span>
          <span onClick={() => { /* reset */ }} style={{ fontSize:12,color:"var(--accent)",cursor:"pointer",marginLeft:"auto" }}>重新起卦</span>
        </div>
        {/* Particle yao energy lines */}
        <LiuyaoVis yaos={yaos}/>
        {/* Yao table */}
        <div style={{ border:"1px solid var(--faint)" }}>
          {[...yaos].reverse().map((y,ri) => {
            const i = yaos.length - 1 - ri
            return (
              <div key={i} style={{
                display:"flex",alignItems:"center",gap:8,padding:"6px 8px",
                borderBottom:"1px solid var(--faint)",
                background:y.is_changing?"var(--accent-l)":y.is_world?"rgba(181,160,122,0.06)":"transparent",
              }}>
                <span style={{ width:20,fontSize:12,color:"var(--muted)",textAlign:"center" }}>
                  {['初','二','三','四','五','上'][i]}
                </span>
                {/* Yao line */}
                <div style={{ width:60,display:"flex",alignItems:"center",gap:4 }}>
                  {y.line==='阳'
                    ? <div style={{ flex:1,height:3,background:"var(--text)" }}/>
                    : <><div style={{ flex:1,height:3,background:"var(--text)" }}/><div style={{ width:8 }}/><div style={{ flex:1,height:3,background:"var(--text)" }}/></>
                  }
                </div>
                <span style={{ width:8,fontSize:11,color:"var(--accent)",fontWeight:700 }}>{y.is_changing?'▸':''}</span>
                <span style={{ width:36,fontSize:12,fontWeight:600,color:WXC[y.wuxing]||"var(--sub)" }}>{y.liu_qin||'—'}</span>
                <span style={{ fontSize:14,fontWeight:600,color:"var(--accent)",fontFamily:"var(--font-serif)" }}>{y.branch||'—'}</span>
                <span style={{ fontSize:11,color:"var(--muted)",marginLeft:"auto" }}>{y.liu_shen||''}</span>
                {y.is_world && <span style={{ fontSize:11,color:"var(--warm)",fontWeight:700 }}>世</span>}
                {y.is_application && <span style={{ fontSize:11,color:"var(--wx-water)",fontWeight:700 }}>应</span>}
              </div>
            )
          })}
        </div>
        <AiInterpretPanel module="liuyao" data={data} extraContext="六爻" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom:10 }}>
        <label>问事主题</label>
        <div style={{ display:"flex",gap:0,flexWrap:"wrap",border:"1px solid var(--faint)" }}>
          {topics.map(t => (
            <button key={t} onClick={() => setTopic(t)} style={{
              padding:"5px 10px",border:"none",borderRight:"1px solid var(--faint)",
              background:topic===t?"var(--accent-l)":"transparent",
              color:topic===t?"var(--accent)":"var(--muted)",
              fontSize:12,cursor:"pointer",fontWeight:topic===t?600:400,
            }}>{t}</button>
          ))}
        </div>
      </div>
      <div style={{ marginBottom:10 }}>
        <label>问题（选填）</label>
        <input value={question} onChange={e=>setQuestion(e.target.value)} placeholder="心诚则灵，一次只问一事"/>
      </div>
      <button className="btn btn-primary" onClick={doDiv} disabled={loading} style={{ width:"100%" }}>
        {loading ? '起卦中…' : '摇卦起卦'}
      </button>
    </div>
  )
}

// ─── 风水 ────────────────────────────────────────────────────────

function FengshuiPanel({ birth }) {
  const { data, loading, execute } = useApi(fengshuiApi.analysis)
  const [facing, setFacing] = useState('南')
  const dirs = ['北','东北','东','东南','南','西南','西','西北']

  const doCalc = () => execute({ birth_year:birth?.year||1990, gender:birth?.gender||'male', house_facing:facing })

  if (data) {
    const fs = data.flying_star || {}
    const palaces = fs.palaces || []
    const order = [4,9,2,3,5,7,8,1,6]
    return (
      <div>
        {/* Particle compass */}
        <FengshuiVis palaces={palaces}/>
        <div style={{ fontSize:12,color:"var(--muted)",marginBottom:8 }}>{fs.facing||''}向 · {fs.mountain||''}山 · {fs.period||''}运</div>
        <div style={{ display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:0,border:"1px solid var(--faint)",maxWidth:360 }}>
          {order.map(pos => {
            const p = palaces.find(pp=>pp.position===pos) || {}
            return (
              <div key={pos} style={{ padding:"6px",minHeight:50,borderRight:"1px solid var(--faint)",borderBottom:"1px solid var(--faint)",textAlign:"center" }}>
                <div style={{ fontSize:11,color:"var(--muted)" }}>{p.direction||''}</div>
                <div style={{ display:"flex",justifyContent:"center",gap:8,marginTop:2 }}>
                  <span style={{ fontSize:14,fontWeight:600,color:"var(--wx-water)",fontFamily:"var(--font-serif)" }}>{p.mountain_star||''}</span>
                  <span style={{ fontSize:14,fontWeight:600,color:"var(--accent)",fontFamily:"var(--font-serif)" }}>{p.facing_star||''}</span>
                </div>
              </div>
            )
          })}
        </div>
        <AiInterpretPanel module="fengshui" data={data} extraContext="风水" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom:10 }}>
        <label>房屋朝向</label>
        <div style={{ display:"flex",gap:0,flexWrap:"wrap",border:"1px solid var(--faint)" }}>
          {dirs.map(d => (
            <button key={d} onClick={() => setFacing(d)} style={{
              padding:"5px 10px",border:"none",borderRight:"1px solid var(--faint)",
              background:facing===d?"var(--accent-l)":"transparent",
              color:facing===d?"var(--accent)":"var(--muted)",
              fontSize:12,cursor:"pointer",fontWeight:facing===d?600:400,
            }}>{d}</button>
          ))}
        </div>
      </div>
      <button className="btn btn-primary" onClick={doCalc} disabled={loading} style={{ width:"100%" }}>
        {loading?'计算中…':'排飞星盘'}
      </button>
    </div>
  )
}

// ─── 典籍 ────────────────────────────────────────────────────────

function KnowledgePanel() {
  const { data, loading, execute } = useApi(knowledgeApi.search)
  const [kw, setKw] = useState('')

  return (
    <div>
      <div style={{ display:"flex",gap:6,marginBottom:12 }}>
        <input value={kw} onChange={e=>setKw(e.target.value)}
          onKeyDown={e=>{if(e.key==='Enter'&&kw.trim()) execute(kw.trim())}}
          placeholder="搜索古籍：如「伏神飞神」「调候用神」" style={{ flex:1 }}/>
        <button className="btn btn-primary btn-sm" onClick={()=>kw.trim()&&execute(kw.trim())} disabled={loading}>
          {loading?'…':'搜索'}
        </button>
      </div>
      {data && Array.isArray(data) && data.length > 0 && (
        <div>
          {data.slice(0,8).map((r,i) => (
            <InkBorder key={i} style={{ marginBottom:6,padding:"8px 12px" }}>
              <div style={{ fontSize:12,fontWeight:600,color:"var(--text)",marginBottom:2 }}>{r.title || r.category || ''}</div>
              <div style={{ fontSize:12,color:"var(--sub)",lineHeight:1.7 }}>{(r.content||r.text||'').slice(0,200)}</div>
              {r.score && <div style={{ fontSize:11,color:"var(--faint)",marginTop:2 }}>相关度 {r.score.toFixed(1)}</div>}
            </InkBorder>
          ))}
        </div>
      )}
      {data && Array.isArray(data) && data.length === 0 && (
        <div style={{ color:"var(--muted)",fontSize:12,textAlign:"center",padding:20 }}>未找到相关内容</div>
      )}
    </div>
  )
}

// ─── 问答 ────────────────────────────────────────────────────────

function AgentPanel({ birth }) {
  const { apiBaseUrl, llmProvider, llmKey, llmModel, llmBaseUrl } = useSettingsStore.getState ? useSettingsStore.getState() : {}
  const [question, setQuestion] = useState('')
  const [text, setText] = useState('')
  const [streaming, setStreaming] = useState(false)

  const ask = async () => {
    if (!question.trim() || !llmKey) return
    setStreaming(true); setText('')
    try {
      const resp = await fetch(`${apiBaseUrl}/api/v1/agent/consult`, {
        method:'POST',
        headers:{ 'Content-Type':'application/json','X-LLM-Key':llmKey,'X-LLM-Provider':llmProvider||'anthropic','X-LLM-Model':llmModel||'claude-sonnet-4-6','X-LLM-Base-Url':llmBaseUrl||'' },
        body:JSON.stringify({ question, context: birth ? { birth } : null }),
      })
      const reader = resp.body.getReader(), decoder = new TextDecoder()
      let buf = ''
      while (true) {
        const {done,value} = await reader.read()
        if (done) break
        buf += decoder.decode(value,{stream:true})
        const lines = buf.split('\n'); buf = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const raw = line.slice(5).trim()
          if (raw==='[DONE]') break
          try { const c=JSON.parse(raw); if(c.text) setText(p=>p+c.text) } catch {}
        }
      }
    } catch(e) { setText(`错误: ${e.message}`) }
    finally { setStreaming(false) }
  }

  return (
    <div>
      {text && (
        <div style={{ padding:"12px 14px",borderLeft:"2px solid var(--accent)",borderBottom:"1px solid var(--faint)",marginBottom:12,fontSize:13,lineHeight:1.85,color:"var(--sub)",fontFamily:"var(--font-serif)",whiteSpace:"pre-wrap" }}>
          {text}
          {streaming && <span style={{ display:"inline-block",width:2,height:"1em",background:"var(--accent)",marginLeft:2,animation:"blink-cursor .8s step-end infinite" }}/>}
        </div>
      )}
      <div style={{ display:"flex",gap:6 }}>
        <input value={question} onChange={e=>setQuestion(e.target.value)}
          onKeyDown={e=>{if(e.key==='Enter')ask()}}
          placeholder="问命理相关问题…" style={{ flex:1 }}/>
        <button className="btn btn-primary btn-sm" onClick={ask} disabled={streaming||!llmKey}>
          {streaming?'…':'提问'}
        </button>
      </div>
      {!llmKey && <div style={{ fontSize:11,color:"var(--danger)",marginTop:4 }}>请先在设置中配置 API Key</div>}
    </div>
  )
}

// ─── Panel Router ────────────────────────────────────────────────

function getPanel(id, birth) {
  switch(id) {
    case 'bazi':      return <BaziPanel birth={birth}/>
    case 'ziwei':     return <ZiweiPanel birth={birth}/>
    case 'dayun':     return <DayunPanel birth={birth}/>
    case 'qimen':     return <QimenPanel/>
    case 'liuyao':    return <LiuyaoPanel/>
    case 'fengshui':  return <FengshuiPanel birth={birth}/>
    case 'knowledge': return <KnowledgePanel/>
    case 'agent':     return <AgentPanel birth={birth}/>
    default:          return <div style={{ padding:20,color:"var(--muted)",fontSize:13,textAlign:"center" }}>模块加载中…</div>
  }
}

// ─── Cross Insights ──────────────────────────────────────────────

function CrossInsights({ visible }) {
  if (visible.size < 2) return null
  const insights = [
    { cond:s=>s.has('bazi')&&s.has('ziwei'), text:'八字格局与紫微命宫主星可交叉验证——两盘指向一致时判断更可靠' },
    { cond:s=>s.has('bazi')&&s.has('dayun'), text:'大运转折节点可与紫微大限对照——运程先抑后扬或先扬后抑的节奏' },
    { cond:s=>s.has('qimen')&&s.has('liuyao'), text:'奇门八门吉凶可与六爻用神旺衰对照——两套系统互为佐证' },
  ].filter(ins => ins.cond(visible))
  if (!insights.length) return null

  return (
    <div style={{ marginTop:16 }}>
      <Mtn color="rgba(207,59,44,0.06)" h={24}/>
      <div style={{ fontSize:13,fontWeight:700,color:"var(--accent)",fontFamily:"var(--font-serif)",marginBottom:8,letterSpacing:2 }}>交叉洞察</div>
      {insights.map((ins,i) => (
        <InkBorder key={i} style={{ marginBottom:8,padding:"10px 12px" }}>
          <div style={{ fontSize:12,color:"var(--sub)",lineHeight:1.8 }}>{ins.text}</div>
        </InkBorder>
      ))}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ═══════════════════════════════════════════════════════════════

export default function DashboardPage({ birth }) {
  const [stamped, setStamped] = useState(new Set())
  const toggle = id => {
    setStamped(prev => {
      const n = new Set(prev)
      if (n.has(id)) n.delete(id); else n.add(id)
      return n
    })
  }

  return (
    <div>
      {/* Seal matrix */}
      <div style={{ textAlign:"center",marginBottom:6 }}>
        <span style={{ fontSize:11,color:"var(--muted)",letterSpacing:2 }}>印章激活 · 多选对比</span>
      </div>
      <div style={{ display:"flex",gap:6,flexWrap:"wrap",justifyContent:"center",marginBottom:6 }}>
        {MODULES.map(m => <Seal key={m.id} mod={m} isStamped={stamped.has(m.id)} onClick={() => toggle(m.id)}/>)}
      </div>

      <Mtn h={28} style={{ margin:"4px 0" }}/>

      {/* Content */}
      {stamped.size > 0 ? (
        <div style={{ animation:"fadeIn .3s ease" }}>
          <div style={{
            display:"grid",
            gridTemplateColumns: stamped.size===1 ? "1fr" : `repeat(${Math.min(stamped.size,2)},1fr)`,
            gap:0,
          }}>
            {[...stamped].map((id,i) => {
              const mod = MODULES.find(m=>m.id===id)
              const st = STONES[mod.stone]
              return (
                <div key={id} style={{
                  padding:"16px 14px",position:"relative",
                  borderLeft:i>0?"1px solid var(--faint)":"none",
                  borderTop:i>=2?"1px solid var(--faint)":"none",
                }}>
                  {/* Watermark glyph */}
                  <div style={{ position:"absolute",top:8,right:8,fontSize:36,fontWeight:900,fontFamily:"var(--font-serif)",color:st.inkLight,lineHeight:1,pointerEvents:"none" }}>
                    {mod.glyph}
                  </div>
                  {/* Header with stone bar */}
                  <div style={{ display:"flex",alignItems:"center",gap:8,marginBottom:12 }}>
                    <div style={{ width:3,height:16,background:st.bg }}/>
                    <div>
                      <div style={{ fontSize:14,fontWeight:700,fontFamily:"var(--font-serif)",color:"var(--text)" }}>{mod.name}</div>
                      <div style={{ fontSize:11,color:"var(--muted)" }}>{st.name} · {mod.desc}</div>
                    </div>
                  </div>
                  {getPanel(id, birth)}
                </div>
              )
            })}
          </div>
          <CrossInsights visible={stamped}/>
        </div>
      ) : (
        <div style={{ textAlign:"center",padding:"30px 16px",color:"var(--muted)" }}>
          <Mtn color="rgba(140,136,125,0.05)" h={50}/>
          <div style={{ fontSize:14,fontFamily:"var(--font-serif)",marginTop:8,letterSpacing:2 }}>选印落章，展卷论命</div>
          <div style={{ fontSize:12,marginTop:4 }}>
            {birth?.year ? '点击上方印章激活模块 · 可同时多选对比' : '请先点击顶部「输入生辰」按钮'}
          </div>
        </div>
      )}
    </div>
  )
}
