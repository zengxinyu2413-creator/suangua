import React, { useState } from 'react'
import { SYM, QIN_COLOR, SHEN_COLOR, STR_COLOR } from './liuyaoConstants'
import { VerdictCard, RoleGrid, polarityColor, polarityBg } from '../../components/UI/Primitives'
import { LiuyaoVis } from '../../components/particles/Visualizations'
import LiuyaoDeepRelations from './LiuyaoDeepRelations'
import LiuyaoSanheCard from './LiuyaoSanheCard'
import LiuyaoHologram from './LiuyaoHologram'
import LiuyaoYongShenStatus from './LiuyaoYongShenStatus'
import LiuyaoYongShenSynthesis from './LiuyaoYongShenSynthesis'
import LiuyaoYongShenJudgment from './LiuyaoYongShenJudgment'
import LiuyaoConsistencyAudit from './LiuyaoConsistencyAudit'
import LiuyaoPerspectives from './LiuyaoPerspectives'
import LiuyaoYingqiCalendar from './LiuyaoYingqiCalendar'
import LiuyaoAdvancedPanel from './LiuyaoAdvancedPanel'
import LiuyaoLadderPlate from './LiuyaoLadderPlate'
import NarrationPanel from '../../components/NarrationPanel'

export default function HexagramResult({ data }) {
  const [tab, setTab] = useState('hexagram')
  const orig    = data.original
  const changed = data.changed
  const yaos    = data.yaos || []
  const kong    = data.kong_wang_branches || []
  const topic   = data.topic || '综合'
  const ta      = data.topic_analysis || {}
  const cp      = data.classical_points || []
  const ca      = data.changing_analysis || []
  const timing  = ta.timing || {}

  const TABS = [
    { id:'hexagram', label:'卦象', badge: !!data.sanhe_sanhui?.summary && data.sanhe_sanhui.summary !== '无三合三会' },
    { id:'relations', label:'深度关系', badge: !!data.deep_relations },
    { id:'analysis', label:'断法分析', badge: cp.length > 0 },
    { id:'timing',   label:'应期推算', badge: (timing.rules_applied?.length || 0) > 0 },
  ]

  return (
    <div className="result-section">
      {/* ── Hexagram header ── */}
      <div className="card card-glow" style={{ textAlign:'center' }}>
        <div style={{ display:'flex', justifyContent:'center', alignItems:'center', gap:'1.75rem', marginBottom:'0.85rem' }}>
          {/* Original hexagram symbols */}
          <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'0.3rem' }}>
            <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', letterSpacing:'0.06em', textTransform:'uppercase' }}>本卦</div>
            <div style={{ fontSize:'var(--text-display)', lineHeight:1, color:'var(--accent)',
              textShadow:'0 0 24px var(--accent-glow), 0 0 48px var(--accent-glow2)' }}>
              {SYM[orig.upper?.name]}{SYM[orig.lower?.name]}
            </div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-lg)', fontWeight:600, color:'var(--accent)', letterSpacing:'0.08em' }}>
              {orig.name}
            </div>
            <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>第{orig.number}卦</div>
          </div>

          {changed && (
            <>
              <div style={{ color:'var(--accent-dim)', fontSize:'var(--text-md)' }}>→</div>
              <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'0.3rem', opacity:0.85 }}>
                <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', letterSpacing:'0.06em', textTransform:'uppercase' }}>变卦</div>
                <div style={{ fontSize:'var(--text-display)', lineHeight:1, color:'var(--text-secondary)' }}>
                  {SYM[changed.upper?.name]}{SYM[changed.lower?.name]}
                </div>
                <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-lg)', fontWeight:600, color:'var(--text-secondary)' }}>
                  {changed.name}
                </div>
                <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>第{changed.number}卦</div>
              </div>
            </>
          )}
        </div>

        {/* Palace + world/app info + 日辰月建 */}
        <div style={{ display:'flex', justifyContent:'center', gap:'1rem', flexWrap:'wrap',
          fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:'0.75rem' }}>
          {data.palace_trigram && <span>{data.palace_trigram}宫 · {data.palace_element}行</span>}
          <span>世爻第{data.world_line}爻</span>
          <span>应爻第{data.application_line}爻</span>
          {kong.length > 0 && <span style={{ color:'var(--red-light)' }}>旬空：{kong.join('、')}</span>}
        </div>

        {/* ── 日辰月建（六爻最关键外部信息） ── */}
        {(data.day_gan || data.day_zhi || data.month_zhi) && (
          <div style={{ display:'flex', justifyContent:'center', gap:'1.2rem', flexWrap:'wrap',
            padding:'0.45rem 0.85rem', marginBottom:'0.75rem',
            background:'linear-gradient(90deg, rgba(212,160,64,0.05), rgba(212,160,64,0.12), rgba(212,160,64,0.05))',
            borderTop:'1px solid var(--accent-dim)', borderBottom:'1px solid var(--accent-dim)',
            fontSize:'var(--text-sm)', fontFamily:'var(--font-serif)' }}>
            {(data.day_gan || data.day_zhi) && (
              <span style={{ color:'var(--text-secondary)' }}>
                <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginRight:'0.3em' }}>日辰</span>
                <span style={{ color:'var(--accent)', fontWeight:600 }}>
                  {data.day_gan || ''}{data.day_zhi || ''}
                </span>
                <span style={{ fontSize:'var(--text-2xs)', color:'var(--text-muted)', marginLeft:'0.3em' }}>(看用神冲合)</span>
              </span>
            )}
            {data.month_zhi && (
              <span style={{ color:'var(--text-secondary)' }}>
                <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginRight:'0.3em' }}>月建</span>
                <span style={{ color:'var(--accent)', fontWeight:600 }}>{data.month_zhi}</span>
                <span style={{ fontSize:'var(--text-2xs)', color:'var(--text-muted)', marginLeft:'0.3em' }}>(论旺衰)</span>
              </span>
            )}
            {ta.yong_shen_name && ta.yong_shen_name !== '世爻' && ta.yong_shen_name !== '应爻' && (
              <span style={{ color:'var(--text-secondary)' }}>
                <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginRight:'0.3em' }}>用神</span>
                <span style={{ color: QIN_COLOR[ta.yong_shen_name] || 'var(--accent)', fontWeight:700 }}>
                  {ta.yong_shen_name}爻
                </span>
              </span>
            )}
          </div>
        )}

        {/* Judgment */}
        <div style={{ fontSize:'var(--text-base)', fontFamily:'var(--font-serif)', color:'var(--text-secondary)',
          lineHeight:1.85, maxWidth:'500px', margin:'0 auto 0.75rem' }}>
          {orig.judgment}
        </div>

        {/* Topic badge + question */}
        <div style={{ display:'flex', justifyContent:'center', gap:'0.5rem', flexWrap:'wrap' }}>
          <span className="badge badge-gold">{topic}</span>
          {data.question && (
            <span style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', fontStyle:'italic' }}>
              「{data.question}」
            </span>
          )}
        </div>
      </div>

      {/* ── 综合总断 · 总汇合参（用神×世应×动爻×卦型×应期 → 成败+应期）── */}
      {data.master_synthesis?.available && (() => {
        const QC = { 吉:'#27ae60', 中:'var(--accent)', 凶:'#c0392b' }
        const ms = data.master_synthesis
        const pc = QC[ms.overall_quality] || 'var(--accent)'
        return (
          <div className="card card-glow" style={{ borderTop:`4px solid ${pc}`, marginBottom:'1rem' }}>
            <div className="card-title">综合总断 · 总汇合参</div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)', fontWeight:600,
              color:pc, marginBottom:'0.5rem' }}>
              所占「{ms.question}」· 用神{ms.yong_shen || '—'} · 综断<span style={{ color:pc }}>{ms.overall_quality}</span>
            </div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)', lineHeight:1.7,
              color:'var(--text-secondary)', padding:'0.5rem 0.7rem', background:`${pc}10`,
              borderLeft:`4px solid ${pc}`, marginBottom:'0.7rem' }}>
              {ms.headline}
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))', gap:'6px', marginBottom:'0.7rem' }}>
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
                <b style={{ color:pc }}>总提示 · </b>{ms.master_advice}
              </div>
            )}
            <NarrationPanel ms={ms} fullData={data} module="liuyao" />
          </div>
        )
      })()}

      {/* ── 断卦总论（以所问为纲，串全卦信号成篇·扣题作答）── */}
      {data.full_reading?.available && (
        <div className="card card-glow" style={{ borderTop:`3px solid ${polarityColor(data.full_reading.polarity)}` }}>
          <div className="card-title">断卦总论 · 答所问</div>

          {/* 吉凶答案·第一眼即见 */}
          {(() => {
            const pc = polarityColor(data.full_reading.polarity)
            const concl = (data.full_reading.paragraphs || []).find(p => p.title === '结论')
            return (
              <div style={{ display:'flex', alignItems:'center', gap:'0.9rem',
                padding:'0.7rem 0.9rem', marginBottom:'0.75rem',
                background:polarityBg(data.full_reading.polarity), borderLeft:`4px solid ${pc}` }}>
                <div style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-display)',
                  fontWeight:700, color:pc, lineHeight:1, flexShrink:0,
                  textShadow:`0 0 20px ${pc}55` }}>
                  {data.full_reading.polarity || '—'}
                </div>
                <div style={{ minWidth:0 }}>
                  <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)',
                    color:'var(--text-primary)', fontWeight:600 }}>
                    所问：{data.full_reading.question || question || '综合'}
                  </div>
                  <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)',
                    fontFamily:'var(--font-serif)', marginTop:'0.15rem' }}>
                    {data.full_reading.headline}
                  </div>
                  {concl && (
                    <div style={{ fontSize:'var(--text-sm)', color:'var(--text-secondary)',
                      fontFamily:'var(--font-serif)', lineHeight:1.6, marginTop:'0.3rem' }}>
                      {concl.text}
                    </div>
                  )}
                </div>
              </div>
            )
          })()}

          {/* 逐节详断 */}
          <div style={{ display:'flex', flexDirection:'column', gap:'0.5rem' }}>
            {data.full_reading.paragraphs.filter(p => p.title !== '结论').map((p,i) => (
              <p key={i} style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)',
                lineHeight:1.95, color:'var(--text-secondary)', margin:0 }}>
                <span style={{ color:'var(--accent)', fontWeight:700 }}>{p.title}　</span>
                {p.text}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* ── 综合断卦（用神四位生克总断） ── */}
      {data.zonghe_duan?.available && (
        <VerdictCard
          title="用神四位 · 生克总断"
          conclusion={data.zonghe_duan.conclusion}
          confidence={data.zonghe_duan.confidence}
          verdict={data.zonghe_duan.verdict}
          reasons={data.zonghe_duan.reasoning}
        >
          {data.zonghe_duan.roles && (
            <div style={{ margin: '0.2rem 0 0.7rem' }}>
              <RoleGrid cols={4} items={['用神','原神','忌神','仇神'].map(rn => {
                const st = data.zonghe_duan.roles[rn] || {}
                const col = rn==='用神' ? 'var(--accent)' : rn==='原神' ? '#27ae60' : rn==='忌神' ? '#c0392b' : '#a8741a'
                return {
                  label: rn, labelColor: col, borderColor: col,
                  value: st.present ? `${st.liu_qin}${st.branch}` : null,
                  sub: st.present ? `${st.wangshuai}${st.is_dong?'·动':'·静'}${st.is_kong?'·空':''}${st.entombed?'·墓':''}` : null,
                  dim: '不上卦',
                }
              })} />
            </div>
          )}
        </VerdictCard>
      )}

      {/* ── 用神力量综合评估·推理链（子模块互助逻辑显式呈现）── */}
      <LiuyaoYongShenJudgment data={data} />
      <LiuyaoYongShenSynthesis data={data} />

      {/* ── 多视角整合解读（全部子模块尽汇于六视角）── */}
      <LiuyaoPerspectives data={data} />

      {/* ── 断卦一致性审核（确定性检测 + AI 审定）── */}
      <LiuyaoConsistencyAudit data={data} />

      {/* ── Tabs ── */}
      <div className="tab-bar">
        {TABS.map(t => (
          <button key={t.id} className={`tab ${tab===t.id?'active':''}`} onClick={() => setTab(t.id)}>
            {t.label}
            {t.badge && <span style={{ marginLeft:'0.3rem', display:'inline-block',
              width:'6px', height:'6px', borderRadius:'50%', background:'var(--accent)',
              verticalAlign:'middle', marginBottom:'1px' }} />}
          </button>
        ))}
      </div>

      {/* ══ TAB: 卦象 ══ */}
      {tab === 'hexagram' && (
        <div style={{ display:'flex', flexDirection:'column', gap:'0.9rem' }}>
          {/* ── 六爻全息图 ── */}
          <LiuyaoHologram data={data} />
          
          {/* Six yao ladder plate */}
          <div className="card">
            {yaos?.length > 0 && <LiuyaoVis yaos={yaos}/>}
            <LiuyaoLadderPlate data={data} />

            {/* Kong wang note */}
            {kong.length > 0 && (
              <div style={{ marginTop:'0.6rem', padding:'0.4rem 0.65rem',
                background:'rgba(212,75,58,0.07)', border:'1px solid rgba(212,75,58,0.2)',
                borderRadius:'var(--r-sm)', fontSize:'var(--text-xs)', color:'var(--text-muted)',
                fontFamily:'var(--font-serif)' }}>
                ⚠ 旬空：{kong.join('、')} — 空亡之爻力量虚化，所代事物难以成就，待出空后再验
              </div>
            )}
          </div>

          {/* Changed hexagram detail */}
          {changed && (
            <div className="card">
              <div className="card-title">变卦 · 第{changed.number}卦 {changed.name}</div>
              <div style={{ display:'flex', gap:'1rem', alignItems:'flex-start' }}>
                <div style={{ fontSize:'var(--text-2xl)', color:'var(--text-secondary)', lineHeight:1, flexShrink:0 }}>
                  {SYM[changed.upper?.name]}{SYM[changed.lower?.name]}
                </div>
                <div style={{ flex:1 }}>
                  <p style={{ fontSize:'var(--text-sm)', fontFamily:'var(--font-serif)',
                    color:'var(--text-secondary)', lineHeight:1.82 }}>
                    {changed.interpretation || changed.judgment}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* World / app summary */}
          {data.world_summary && (
            <div className="card" style={{ padding:'0.85rem 1.2rem' }}>
              <div className="card-title">世应概况</div>
              <p style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                color:'var(--text-secondary)', lineHeight:1.8 }}>
                {data.world_summary}
              </p>
            </div>
          )}

          {/* ── 高级特性：卦身 / 世身 / 独发独静 / 化合化冲 ── */}
          <LiuyaoAdvancedPanel result={data} />

          {/* ── 三合三会局（六爻聚气）── */}
          <LiuyaoSanheCard sanheData={data.sanhe_sanhui} />

          {/* ── 伏神显示 (Layer 2.2) ── */}
          {data.fu_shen && (() => {
            const fuList = Array.isArray(data.fu_shen) ? data.fu_shen : [data.fu_shen]
            return (
            <div className="card">
              <div className="card-title">伏神</div>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.5rem' }}>
                {fuList.map((f, i) => (
                  <div key={i} style={{ display:'flex', alignItems:'center', gap:'0.5rem', flexWrap:'wrap',
                    padding:'0.4rem 0.6rem', borderLeft:'2px solid var(--accent)', fontSize:'var(--text-sm)' }}>
                    <span className="badge badge-gold" style={{ fontSize:'var(--text-xs)' }}>
                      {f.fu_liuqin || '伏'}
                    </span>
                    <span style={{ color:'var(--text-secondary)' }}>
                      伏于第{f.position}爻下（{f.fu_branch}）
                    </span>
                    {f.emerge_type && (
                      <span className={`badge ${f.emerge_severity === 'auspicious' ? 'badge-jade' : f.emerge_severity === 'inauspicious' ? 'badge-red' : ''}`}
                        style={{ fontSize:'var(--text-xs)' }}>
                        {f.emerge_type}
                      </span>
                    )}
                    {f.desc && <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>{f.desc}</span>}
                  </div>
                ))}
                <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginTop:'0.25rem',
                  fontStyle:'italic', lineHeight:1.6 }}>
                  《增删卜易》：用神不上卦，须在本宫寻伏神。飞来生伏为吉，伏去克飞名曰出暴亦吉。
                </div>
              </div>
            </div>
            )
          })()}
        </div>
      )}

      {/* ══ TAB: 深度关系（L-1）══ */}
      {tab === 'relations' && (
        <LiuyaoDeepRelations data={data} />
      )}

      {/* ══ TAB: 断法分析 ══ */}
      {tab === 'analysis' && (
        <div style={{ display:'flex', flexDirection:'column', gap:'0.9rem' }}>

          {/* ── 用神状态总评卡（吉凶分） ── */}
          <LiuyaoYongShenStatus data={data} />

          {/* ── C: 世爻持世断 ── */}
          {data.chi_shi && data.chi_shi.world_liu_qin && (
            <div className="card">
              <div className="card-title">世爻持世断 · {data.chi_shi.world_liu_qin}持世</div>
              {data.chi_shi.kou_jue && (
                <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                  color:'var(--accent)', fontStyle:'italic', lineHeight:1.7, marginBottom:'0.4rem' }}>
                  「{data.chi_shi.kou_jue}」
                </div>
              )}
              <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                color:'var(--text-secondary)', lineHeight:1.7 }}>
                {data.chi_shi.jie_xi}　{data.chi_shi.pos_note}
              </div>
            </div>
          )}

          {/* ── C: 动爻化变全谱断 ── */}
          {data.hua_bian && data.hua_bian.count > 0 && (
            <div className="card">
              <div className="card-title">动爻化变断（{data.hua_bian.count}爻发动）</div>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.5rem' }}>
                {data.hua_bian.moving_lines.map((m, i) => {
                  const xiong = m.score < 0
                  const col = xiong ? '#c0392b' : (m.score > 0 ? '#27ae60' : 'var(--accent-dim)')
                  return (
                    <div key={i} style={{ padding:'0.5rem 0.7rem', borderRadius:'var(--r-sm)',
                      background:'var(--bg-raised)', borderLeft:`3px solid ${col}` }}>
                      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline',
                        marginBottom:'0.3rem' }}>
                        <span style={{ fontSize:'var(--text-sm)', fontWeight:700, color:'var(--text-secondary)',
                          fontFamily:'var(--font-serif)' }}>
                          {m.name}爻　{m.orig_liu_qin}{m.orig_branch}→{m.changed_liu_qin}{m.changed_branch}
                        </span>
                        <span style={{ fontSize:'var(--text-xs)', fontWeight:700, color:col }}>{m.tendency}</span>
                      </div>
                      <div style={{ display:'flex', flexWrap:'wrap', gap:'0.3rem', marginBottom:'0.3rem' }}>
                        {m.facets.map((f, j) => (
                          <span key={j} title={f.desc} style={{ fontSize:'var(--text-xs)', padding:'1px 6px',
                            borderRadius:'3px', background:'var(--bg-subtle)', color:'var(--text-muted)', cursor:'help' }}>
                            {f.type}
                          </span>
                        ))}
                      </div>
                      <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)',
                        fontFamily:'var(--font-serif)', lineHeight:1.6 }}>{m.full_text}</div>
                    </div>
                  )
                })}
              </div>
              <div style={{ marginTop:'0.4rem', fontSize:'var(--text-xs)', color:'var(--text-faint)',
                fontFamily:'var(--font-serif)', fontStyle:'italic' }}>{data.hua_bian.summary}</div>
            </div>
          )}


          {/* Verdict — 综合判断卡（含用神状态可视化） */}
          {ta.verdict && (
            <div className="card card-glow">
              <div className="card-title">综合判断 · {topic}</div>
              <div style={{ padding:'0.75rem 1rem', background:'var(--accent-glow)',
                border:'1px solid var(--accent-dim)', borderRadius:'var(--r-md)',
                fontFamily:'var(--font-serif)', fontSize:'var(--text-base)',
                color:'var(--text-primary)', lineHeight:1.85, marginBottom:'0.7rem' }}>
                {ta.verdict}
              </div>
              
              {/* 用神状态详情 */}
              {(() => {
                const ysName = ta.yong_shen_name
                if (!ysName || ysName === '世爻' || ysName === '应爻') return null
                const ysYao = yaos.find(y => y.liu_qin === ysName)
                if (!ysYao) return null
                const strength = ysYao.strength?.label || ''
                const isStrong = ['旺', '相'].includes(strength)
                const isWeak = ['休', '囚', '死'].includes(strength)
                return (
                  <div style={{ display:'grid', gridTemplateColumns:'auto 1fr auto', gap:'0.5rem',
                    padding:'0.55rem 0.85rem', background:'var(--bg-raised)',
                    borderLeft:`3px solid ${isStrong ? '#27ae60' : isWeak ? '#e74c3c' : 'var(--accent-dim)'}`,
                    borderRadius:'var(--r-sm)', fontSize:'var(--text-sm)' }}>
                    <span style={{ color:'var(--text-muted)' }}>用神</span>
                    <span>
                      <span style={{ color: QIN_COLOR[ysName], fontWeight:700 }}>{ysName}爻</span>
                      {' · '}
                      <span style={{ color:'var(--accent)', fontFamily:'var(--font-display)' }}>
                        第{ysYao.position}爻 {ysYao.branch}
                        {ysYao.kong_wang && <span style={{ color:'var(--red-light)', fontSize:'0.7em' }}> 空</span>}
                      </span>
                    </span>
                    <span style={{
                      fontSize:'var(--text-xs)', fontWeight:700,
                      color: isStrong ? '#27ae60' : isWeak ? '#e74c3c' : 'var(--text-muted)',
                      padding:'2px 8px', background: isStrong ? 'rgba(39,174,96,0.12)' : isWeak ? 'rgba(231,76,60,0.12)' : 'var(--bg-subtle)',
                      borderRadius:'10px',
                    }}>
                      {strength || '中和'}
                    </span>
                  </div>
                )
              })()}

              {/* 三合三会摘要 */}
              {data.sanhe_sanhui?.summary && data.sanhe_sanhui.summary !== '无三合三会' && (
                <div style={{ marginTop:'0.5rem', padding:'0.45rem 0.85rem',
                  background:'rgba(46,204,113,0.06)', borderLeft:'3px solid #27ae60',
                  borderRadius:'var(--r-sm)', fontSize:'var(--text-sm)',
                  fontFamily:'var(--font-serif)', color:'var(--text-secondary)' }}>
                  ◆ 卦中聚气：{data.sanhe_sanhui.summary}
                </div>
              )}
            </div>
          )}

          {/* Classical analysis points from interpreter */}
          {cp.length > 0 && (
            <div className="card">
              <div className="card-title">经典断法要点</div>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.55rem' }}>
                {cp.map((point, i) => (
                  <div key={i} style={{ display:'flex', gap:'0.65rem', alignItems:'flex-start',
                    padding:'0.55rem 0.75rem', background:'var(--bg-raised)',
                    borderRadius:'var(--r-sm)', borderLeft:'2px solid var(--accent-dim)' }}>
                    <span style={{ color:'var(--accent)', fontSize:'var(--text-xs)',
                      flexShrink:0, marginTop:'0.22em', fontWeight:700 }}>{i+1}</span>
                    <span style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                      color:'var(--text-secondary)', lineHeight:1.78 }}>{point}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Topic key points */}
          {ta.key_points?.length > 0 && (
            <div className="card">
              <div className="card-title">《增删卜易》占{topic}规则</div>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.4rem' }}>
                {ta.key_points.map((r, i) => (
                  <div key={i} style={{ display:'flex', gap:'0.5rem', alignItems:'flex-start',
                    fontSize:'var(--text-sm)', color:'var(--text-secondary)', lineHeight:1.75,
                    padding:'0.4rem 0', borderBottom:'1px solid var(--border)' }}>
                    <span style={{ color:'var(--accent)', flexShrink:0, fontSize:'var(--text-xs)', marginTop:'0.4em' }}>◆</span>
                    <span style={{ fontFamily:'var(--font-serif)' }}>{r}</span>
                  </div>
                ))}
              </div>
              {ta.classical_ref && (
                <div style={{ marginTop:'0.65rem', padding:'0.5rem 0.75rem',
                  background:'var(--accent-glow)', border:'1px solid var(--accent-dim)',
                  borderRadius:'var(--r-sm)', fontSize:'var(--text-sm)',
                  color:'var(--accent-light)', fontFamily:'var(--font-serif)', lineHeight:1.7 }}>
                  引典：{ta.classical_ref}
                </div>
              )}
            </div>
          )}

          {/* Changing lines analysis */}
          {ca.length > 0 && (
            <div className="card">
              <div className="card-title">动爻详析（{ca.length}爻动）</div>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.5rem' }}>
                {ca.map((y, i) => {
                  const shenInfo = { 白虎:'主凶险血光', 玄武:'主暗昧欺诈', 青龙:'主喜庆贵人',
                    朱雀:'主口舌文书', 勾陈:'主拖延田土', 腾蛇:'主虚惊怪异' }
                  return (
                    <div key={i} style={{ display:'flex', gap:'0.85rem', alignItems:'center',
                      padding:'0.65rem 0.85rem', borderRadius:'var(--r-md)',
                      background:'var(--accent-glow2)', border:'1px solid var(--accent-dim)' }}>
                      <div style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-md)',
                        color:'var(--accent)', flexShrink:0 }}>
                        {['初','二','三','四','五','上'][Number(y.position)-1] || y.position || y.line}爻
                      </div>
                      <div style={{ flex:1 }}>
                        <div style={{ display:'flex', gap:'0.4rem', marginBottom:'0.25rem', flexWrap:'wrap' }}>
                          <span style={{ fontWeight:600, fontSize:'var(--text-sm)',
                            color: QIN_COLOR[y.liu_qin] || 'var(--text-primary)' }}>{y.liu_qin}爻</span>
                          <span style={{ fontSize:'var(--text-sm)', color:'var(--accent)',
                            fontFamily:'var(--font-display)' }}>{y.branch}</span>
                          {y.changed_branch && (
                            <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>
                              → <span style={{ color: QIN_COLOR[y.changed_liu_qin] || 'var(--accent)',
                                fontFamily:'var(--font-display)', fontWeight:600 }}>{y.changed_branch}</span>
                              {y.changed_liu_qin && (
                                <span style={{ marginLeft:'0.2rem', fontSize:'var(--text-xs)',
                                  color: QIN_COLOR[y.changed_liu_qin] }}>({y.changed_liu_qin})</span>
                              )}
                            </span>
                          )}
                          <span style={{ fontSize:'var(--text-sm)',
                            color: SHEN_COLOR[y.liu_shen] || 'var(--text-muted)' }}>{y.liu_shen}</span>
                          {y.strength && (
                            <span className="badge" style={{ fontSize:'var(--text-2xs)',
                              background:'var(--bg-raised)', color: STR_COLOR[y.strength] || 'var(--text-muted)' }}>
                              {y.strength}
                            </span>
                          )}
                          {y.jin_tui && (
                            <span className={`badge ${y.jin_tui==='进'?'badge-jade':'badge-red'}`}
                              style={{ fontSize:'var(--text-xs)' }}>化{y.jin_tui}神</span>
                          )}
                          {y.kong_wang && <span className="badge badge-red" style={{ fontSize:'var(--text-xs)' }}>空亡</span>}
                        </div>
                        <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)',
                          fontFamily:'var(--font-serif)', lineHeight:1.6 }}>
                          {shenInfo[y.liu_shen] || ''}
                          {y.jin_tui === '进' && '，化进神主事态好转'}
                          {y.jin_tui === '退' && '，化退神主事态消退'}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
              {ca.length === 1 && (
                <div style={{ marginTop:'0.5rem', fontSize:'var(--text-sm)', color:'var(--text-muted)',
                  fontFamily:'var(--font-serif)' }}>
                  《增删卜易》：独发易取——唯此一爻动，以此爻论断为主，吉凶明确
                </div>
              )}
              {ca.length >= 5 && (
                <div style={{ marginTop:'0.5rem', fontSize:'var(--text-sm)', color:'var(--red-light)',
                  fontFamily:'var(--font-serif)' }}>
                  《增删卜易》：乱动难寻——爻动过多，吉凶交错，宜以之卦为准综合论断
                </div>
              )}
            </div>
          )}

          {/* Full interpretation text */}
          <div className="card">
            <div className="card-title">卦象全解</div>
            {data.question && (
              <div style={{ padding:'0.45rem 0.7rem', background:'var(--bg-raised)',
                borderRadius:'var(--r-sm)', fontSize:'var(--text-sm)',
                color:'var(--text-muted)', marginBottom:'0.75rem', fontStyle:'italic' }}>
                占问：{data.question}
              </div>
            )}
            <p style={{ fontFamily:'var(--font-serif)', lineHeight:1.92,
              whiteSpace:'pre-line', color:'var(--text-secondary)', fontSize:'var(--text-base)' }}>
              {data.interpretation}
            </p>
          </div>
        </div>
      )}

      {/* ══ TAB: 应期推算 ══ */}
      {tab === 'timing' && (
        <div style={{ display:'flex', flexDirection:'column', gap:'0.9rem' }}>

          {/* ── 应期日历（未来 60 天可视化） ── */}
          <LiuyaoYingqiCalendar data={data} />

          {/* 用神核心信息 */}
          <div className="card card-glow">
            <div className="card-title">用神 · 应期核心</div>
            <div style={{ display:'grid', gridTemplateColumns:'auto 1fr', gap:'0.5rem 1rem',
              padding:'0.6rem 0.8rem', fontSize:'var(--text-sm)' }}>
              <span style={{ color:'var(--text-muted)' }}>占问</span>
              <span style={{ color:'var(--accent)', fontWeight:600 }}>{topic}</span>
              <span style={{ color:'var(--text-muted)' }}>用神</span>
              <span style={{ color: QIN_COLOR[timing.yong_shen_name] || 'var(--accent)', fontWeight:700 }}>
                {timing.yong_shen_name || ta.yong_shen_name || '世爻'}爻
              </span>
              {data.day_zhi && (
                <>
                  <span style={{ color:'var(--text-muted)' }}>日辰</span>
                  <span style={{ color:'var(--text-secondary)' }}>
                    {data.day_gan}{data.day_zhi} <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>(冲合用神)</span>
                  </span>
                </>
              )}
              {data.month_zhi && (
                <>
                  <span style={{ color:'var(--text-muted)' }}>月建</span>
                  <span style={{ color:'var(--text-secondary)' }}>
                    {data.month_zhi} <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>(论旺衰)</span>
                  </span>
                </>
              )}
              {timing.summary && (
                <>
                  <span style={{ color:'var(--text-muted)' }}>总判</span>
                  <span style={{ fontFamily:'var(--font-serif)', lineHeight:1.7,
                    color:'var(--text-secondary)' }}>{timing.summary}</span>
                </>
              )}
            </div>
          </div>

          {/* 应期规则（按类别分组）*/}
          {timing.rules_applied?.length > 0 && (
            <div className="card">
              <div className="card-title">应期推算规则（{timing.rules_applied.length} 条）</div>
              <div style={{ display:'flex', flexDirection:'column', gap:'0.4rem' }}>
                {timing.rules_applied.map((rule, i) => {
                  // 解析规则的类型（开头 【XXX】 是类型）
                  const match = rule.match(/^【(.+?)】(.+)/)
                  const ruleType = match ? match[1] : ''
                  const ruleBody = match ? match[2] : rule
                  
                  // 类型分色
                  const colorMap = {
                    '进神': '#27ae60', '退神': '#e74c3c',
                    '化回头生': '#27ae60', '化回头克': '#c0392b',
                    '化入墓': '#5d6d7e', '化空': '#7f8c8d', '化破': '#c0392b',
                    '化绝': '#4a4a4a',
                    '旺空可填实': '#e67e22', '衰空难应': '#bdc3c7',
                    '卦中旬空': '#e67e22', '出空应期': '#e67e22',
                    '冲动应期': '#3498db', '冲散难应': '#95a5a6',
                    '速应': '#27ae60', '迟应': '#7f8c8d',
                    '六合卦': '#27ae60', '六冲卦': '#e74c3c',
                    '病药通则': '#d4a040',
                  }
                  const color = colorMap[ruleType] || 'var(--accent-dim)'
                  
                  return (
                    <div key={i} style={{
                      padding:'0.55rem 0.75rem',
                      background: ruleType === '病药通则' ? 'rgba(212,160,64,0.06)' : 'var(--bg-raised)',
                      borderLeft:`3px solid ${color}`,
                      borderRadius:'var(--r-sm)',
                    }}>
                      {ruleType && (
                        <span style={{
                          display:'inline-block', marginRight:'0.5rem', marginBottom:'0.15rem',
                          padding:'1px 6px', fontSize:'var(--text-2xs)', fontWeight:600,
                          background:`${color}22`, color, border:`1px solid ${color}66`,
                          borderRadius:'3px',
                        }}>{ruleType}</span>
                      )}
                      <span style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-sm)',
                        color:'var(--text-secondary)', lineHeight:1.78 }}>
                        {ruleBody}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* 应期速查表（黄金策）*/}
          <div className="card">
            <div className="card-title">《黄金策》应期速查（七条铁律）</div>
            <div style={{ display:'flex', flexDirection:'column', gap:'0.3rem', fontSize:'var(--text-sm)' }}>
              {[
                ['用神旺相不动', '逢冲动之月日'],
                ['用神有气发动', '逢合日 / 当日'],
                ['用神受制被克', '制克忌神之月日'],
                ['用神太旺遇生', '入墓月日（器满则倾）'],
                ['用神无气发动', '逢生扶之月日'],
                ['用神入墓', '冲破墓库之日'],
                ['用神旬空', '出旬 / 冲空之日'],
              ].map(([cond, result], i) => (
                <div key={i} style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.5rem',
                  padding:'0.4rem 0.65rem', background: i%2===0 ? 'var(--bg-raised)' : 'transparent',
                  borderRadius:'var(--r-sm)' }}>
                  <span style={{ color:'var(--text-muted)', fontFamily:'var(--font-serif)' }}>{cond}</span>
                  <span style={{ color:'var(--accent)', fontFamily:'var(--font-serif)' }}>{result}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 综合建议 */}
          {data.advice && (
            <div className="card">
              <div className="card-title">综合建议</div>
              <p style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-base)',
                color:'var(--text-secondary)', lineHeight:1.88 }}>
                {data.advice}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Hexagram Detail (library) ── */
