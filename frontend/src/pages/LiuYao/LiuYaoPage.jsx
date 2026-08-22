import React, { useState, useEffect, Component } from 'react'
import { clickable } from '../../utils/a11y'
import { liuyaoApi } from '../../api/client'
import { useNotifyStore } from '../../store/settingsStore'
import { useHistoryStore } from '../../store/historyStore'
import AiInterpretPanel from '../../components/UI/AiInterpretPanel'
import ShareImage from '../../components/UI/ShareImage'
import LiuyaoDingShiPanel from './LiuyaoDingShiPanel'

class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(e) { return { error: e } }
  render() {
    if (this.state.error) return (
      <div className="card card-danger" style={{ textAlign:'center', padding:'2rem' }}>
        <p style={{ color:'var(--red-light)', fontFamily:'var(--font-serif)' }}>显示出错，请重新起卦。</p>
        <button className="btn btn-sm" style={{ marginTop:'0.75rem' }}
          onClick={() => this.setState({ error: null })}>重试</button>
      </div>
    )
    return this.props.children
  }
}

import { SYM } from './liuyaoConstants'
import HexagramResult from './LiuyaoHexagramResult'

const METHODS = [
  { id:'coin',   label:'铜钱法', desc:'三枚铜钱摇六次' },
  { id:'yarrow', label:'蓍草法', desc:'传统蓍草概率' },
  { id:'time',   label:'时间法', desc:'以当前时间推算' },
  { id:'number', label:'梅花数字', desc:'输入数字起卦（《梅花易数》）' },
  { id:'manual', label:'手动输入', desc:'自行输入六爻数值' },
]

export default function LiuYaoPage() {
  const [method, setMethod]     = useState('coin')
  const [question, setQuestion] = useState('')
  const [topic, setTopic]       = useState('综合')
  const [gender, setGender]     = useState('male')
  const [isProxy, setIsProxy]   = useState(false)
  const [manual, setManual]     = useState([7,8,7,8,7,8])
  const [numbers, setNumbers]   = useState([null, null, null])  // 梅花数字
  const [result, setResult]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [hexList, setHexList]   = useState([])
  const [view, setView]         = useState('divine')
  const [selHex, setSelHex]     = useState(null)
  const [showShare, setShowShare] = useState(false)
  const { notify }              = useNotifyStore()

  useEffect(() => {
    liuyaoApi.hexagrams().then(setHexList).catch(() => {})
  }, [])

  const divine = async () => {
    setLoading(true)
    try {
      const req = { method, question, topic, gender, is_proxy: isProxy }
      if (method === 'manual') req.yao_values = manual
      if (method === 'number') {
        // 数字起卦：将数字转换为爻值（这里用简单映射，实际后端处理）
        const n1 = numbers[0] || 1
        const n2 = numbers[1] || 1
        const n3 = numbers[2] || 1
        // 上卦 = n1 % 8, 下卦 = n2 % 8, 变爻 = (n1+n2+n3) % 6
        const upper = ((n1 - 1) % 8) + 1
        const lower = ((n2 - 1) % 8) + 1
        const bian = ((n1 + n2 + n3 - 1) % 6) + 1
        // 八卦 → 6 爻（下卦3爻 + 上卦3爻），bian 爻为动
        const BAGUA_LINES = {
          1: [1,1,1], 2: [1,1,0], 3: [1,0,1], 4: [1,0,0],
          5: [0,1,1], 6: [0,1,0], 7: [0,0,1], 8: [0,0,0],
        }
        const lowerLines = BAGUA_LINES[lower] || [1,0,1]
        const upperLines = BAGUA_LINES[upper] || [1,0,1]
        const allLines = [...lowerLines, ...upperLines]  // 初爻到上爻
        const yaoVals = allLines.map((line, i) => {
          const isMoving = (i + 1) === bian
          // 阳爻 1 -> 老阳9 或 少阳7；阴爻 0 -> 老阴6 或 少阴8
          if (line === 1) return isMoving ? 9 : 7
          else            return isMoving ? 6 : 8
        })
        req.method = 'manual'
        req.yao_values = yaoVals
      }
      const data = await liuyaoApi.divine(req)
      setResult(data)
      notify('起卦完成', 'success')
      try { useHistoryStore.getState().addRecord({ module:'liuyao', summary:`${data.original?.name||'卦'} · ${data.topic||'占问'}`, question:data.question||'' }) } catch{}
    } catch (e) { notify(e.message, 'error') }
    finally { setLoading(false) }
  }

  const loadHex = async (num) => {
    try { const d = await liuyaoApi.hexagram(num); setSelHex(d) }
    catch (e) { notify(e.message, 'error') }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">六爻占卜</div>
          <div className="page-subtitle">纳甲筮法 · 六亲六神 · 世应爻 · 旺相休囚</div>
        </div>
        <div style={{ display:'flex', gap:'0.5rem' }}>
          <button className={`btn ${view==='divine'?'btn-primary':''}`} onClick={() => setView('divine')}>起卦</button>
          <button className={`btn ${view==='dingshi'?'btn-primary':''}`} onClick={() => setView('dingshi')}>卦定式</button>
          <button className={`btn ${view==='library'?'btn-primary':''}`} onClick={() => setView('library')}>卦象库</button>
          <button className={`btn ${view==='guide'?'btn-primary':''}`} onClick={() => setView('guide')}>用卦指南</button>
        </div>
      </div>

      <div className="page-body">
        {view === 'divine' && (
          <div className="page-cols">
            {/* ── Input panel ── */}
            <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
              <div className="card">
                <div className="card-title">起卦方式</div>
                {METHODS.map(m => (
                  <div key={m.id} {...clickable(() => setMethod(m.id))} style={{
                    padding:'0.6rem 0.85rem', marginBottom:'0.35rem',
                    borderRadius:'var(--r-md)', cursor:'pointer', transition:'all var(--t-fast)',
                    border:`1px solid ${method===m.id?'var(--accent-dim)':'var(--border)'}`,
                    background: method===m.id ? 'var(--accent-glow)' : 'var(--bg-raised)',
                  }}>
                    <div style={{ fontWeight:500, fontSize:'var(--text-base)',
                      color:method===m.id?'var(--accent)':'var(--text-primary)' }}>{m.label}</div>
                    <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginTop:'2px' }}>{m.desc}</div>
                  </div>
                ))}
              </div>

              <div className="card">
                <div className="card-title">占问事项</div>
                <textarea value={question} onChange={e => setQuestion(e.target.value)}
                  placeholder="请输入所占之事，如：此次求职是否顺利？" rows={3} />
                <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginTop:'0.4rem' }}>
                  心诚则灵，一次只问一事，方能卦象应验
                </div>
              </div>

              {/* ── 占问主题 + 性别 + 代占 ── */}
              <div className="card">
                <div className="card-title">用神选取（古书《增删卜易》）</div>
                <div style={{ marginBottom:'0.65rem' }}>
                  <label style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', display:'block', marginBottom:'0.3rem' }}>
                    占问主题（决定用神）
                  </label>
                  <select value={topic} onChange={e => setTopic(e.target.value)}
                    style={{ width:'100%', fontSize:'var(--text-sm)', padding:'0.4rem 0.5rem' }}>
                    <option value="综合">综合（以世爻论）</option>
                    <option value="求财">求财 — 用神：妻财 / 原神：子孙</option>
                    <option value="求官仕途">求官仕途 — 用神：官鬼 / 原神：父母</option>
                    <option value="考试功名">考试功名 — 用神：父母 / 原神：官鬼</option>
                    <option value="婚姻感情">婚姻感情 — 男占用妻财 / 女占用官鬼</option>
                    <option value="求医疾病">求医疾病 — 用神：世爻 / 子孙</option>
                    <option value="出行远行">出行远行 — 用神：世爻 / 父母</option>
                    <option value="官司诉讼">官司诉讼 — 用神：世爻 / 应爻</option>
                    <option value="求子嗣">求子嗣 — 用神：子孙</option>
                    <option value="找人行人">找人行人 — 用神：应爻</option>
                    <option value="失物寻物">失物寻物 — 用神：妻财</option>
                    <option value="家宅风水">家宅风水 — 用神：父母 / 世爻</option>
                  </select>
                </div>
                <div style={{ display:'flex', gap:'0.6rem', marginBottom:'0.55rem' }}>
                  <div style={{ flex:1 }}>
                    <label style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', display:'block', marginBottom:'0.3rem' }}>
                      占者性别
                    </label>
                    <select value={gender} onChange={e => setGender(e.target.value)}
                      style={{ width:'100%', fontSize:'var(--text-sm)', padding:'0.4rem 0.5rem' }}>
                      <option value="male">男</option>
                      <option value="female">女</option>
                    </select>
                  </div>
                  <div style={{ flex:1, display:'flex', alignItems:'flex-end' }}>
                    <label style={{ display:'flex', alignItems:'center', gap:'0.4rem', fontSize:'var(--text-sm)',
                      cursor:'pointer', padding:'0.45rem 0.5rem', background:'var(--bg-raised)',
                      borderRadius:'var(--r-sm)', width:'100%' }}>
                      <input type="checkbox" checked={isProxy}
                        onChange={e => setIsProxy(e.target.checked)}
                        style={{ accentColor:'var(--accent)' }} />
                      <span style={{ color:'var(--text-secondary)' }}>代他人占</span>
                    </label>
                  </div>
                </div>
                <div style={{ fontSize:'var(--text-2xs)', color:'var(--text-faint)',
                  fontFamily:'var(--font-serif)', lineHeight:1.55, marginTop:'0.4rem',
                  padding:'0.35rem 0.55rem', background:'rgba(212,160,64,0.04)', borderRadius:'var(--r-sm)' }}>
                  古书《卜筮正宗》：占者性别影响婚姻用神（男看妻财、女看官鬼）；
                  代占以应爻代表当事人，自占以世爻代表本人
                </div>
              </div>

              {method === 'manual' && (
                <div className="card">
                  <div className="card-title">手动输入六爻</div>
                  <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:'0.5rem' }}>
                    从初爻（下）到上爻（上）依次输入
                  </div>
                  <div style={{ display:'grid', gridTemplateColumns:'repeat(6,1fr)', gap:'0.35rem' }}>
                    {manual.map((v,i) => (
                      <div key={i} style={{ textAlign:'center' }}>
                        <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:'0.2rem' }}>
                          {['初','二','三','四','五','上'][i]}爻
                        </div>
                        <select value={v} onChange={e => {
                          const arr=[...manual]; arr[i]=Number(e.target.value); setManual(arr)
                        }} style={{ fontSize:'var(--text-sm)', padding:'0.3rem 0.2rem' }}>
                          <option value={6}>6 老阴×</option>
                          <option value={7}>7 少阳—</option>
                          <option value={8}>8 少阴--</option>
                          <option value={9}>9 老阳○</option>
                        </select>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── 梅花数字起卦法（《梅花易数》）── */}
              {method === 'number' && (
                <div className="card" style={{ borderLeft: '3px solid #9b59b6' }}>
                  <div className="card-title">
                    🌸 梅花易数 · 数字起卦
                  </div>
                  <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:'0.5rem',
                    fontFamily:'var(--font-serif)', lineHeight:1.6 }}>
                    《梅花易数》(邵雍)：心中默念问题，随意写下三个数字。
                    第一数 ÷ 8 余数 → 上卦；第二数 ÷ 8 余数 → 下卦；
                    三数之和 ÷ 6 余数 → 变爻。
                  </div>
                  <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:'0.5rem',
                    marginBottom:'0.5rem' }}>
                    {[0, 1, 2].map(i => (
                      <div key={i} style={{ textAlign:'center' }}>
                        <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)',
                          fontFamily:'var(--font-serif)', marginBottom:'0.3rem' }}>
                          {['第一数 (上卦)', '第二数 (下卦)', '第三数 (变爻)'][i]}
                        </div>
                        <input type="number" min="1" max="999"
                          value={numbers[i] || ''}
                          onChange={e => {
                            const arr = [...numbers]
                            arr[i] = e.target.value ? Number(e.target.value) : null
                            setNumbers(arr)
                          }}
                          placeholder={['任意1-999','任意1-999','任意1-999'][i]}
                          style={{ width:'100%', padding:'0.5rem 0.6rem',
                            border:'1px solid var(--border)', borderRadius:'var(--r-sm)',
                            background:'var(--bg-raised)', textAlign:'center',
                            fontFamily:'var(--font-mono)', fontSize:'var(--text-lg)' }} />
                      </div>
                    ))}
                  </div>
                  {numbers.every(n => n && n > 0) && (
                    <div style={{ padding:'0.45rem 0.65rem',
                      background:'rgba(155,89,182,0.06)',
                      borderLeft:'2px solid #9b59b6', borderRadius:'var(--r-sm)',
                      fontSize:'var(--text-xs)', color:'#9b59b6', fontFamily:'var(--font-serif)' }}>
                      ➤ 上卦: 第 {((numbers[0] - 1) % 8) + 1} (1乾 2兑 3离 4震 5巽 6坎 7艮 8坤)
                      　 下卦: 第 {((numbers[1] - 1) % 8) + 1}
                      　 变爻: 第 {((numbers[0] + numbers[1] + numbers[2] - 1) % 6) + 1} 爻
                    </div>
                  )}
                </div>
              )}

              <button className="btn btn-primary btn-full btn-lg" onClick={divine} disabled={loading}>
                {loading ? '推算中…' : '开始起卦 ▶'}
              </button>
            </div>

            {/* ── Result panel ── */}
            <div>
              {loading && <div className="loading"><div className="spinner"/><p>正在演算卦象…</p></div>}
              {!loading && (
                <ErrorBoundary key={result?.original?.number}>
                  {result
                    ? <>
                        <div style={{ display:'flex', justifyContent:'flex-end', marginBottom:'0.5rem' }}>
                          <button className="btn btn-sm" onClick={() => setShowShare(true)} title="生成分享图">🖼 分享图</button>
                        </div>
                        <HexagramResult data={result} />
                        <AiInterpretPanel module="liuyao" data={result}
                          extraContext={result.topic || result.question || '综合'} />
                      </>
                    : <div className="card" style={{ textAlign:'center', padding:'3rem', color:'var(--text-muted)' }}>
                        <div style={{ fontSize:'var(--text-2xl)', marginBottom:'1rem', opacity:0.3 }}>☵</div>
                        <p style={{ fontFamily:'var(--font-serif)' }}>心存问题，默念三遍，诚心起卦</p>
                      </div>
                  }
                </ErrorBoundary>
              )}
            </div>
          </div>
        )}

        {view === 'dingshi' && <LiuyaoDingShiPanel />}

        {view === 'library' && (
          <div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(80px,1fr))', gap:'0.4rem', marginBottom:'1.5rem' }}>
              {hexList.map(h => (
                <button key={h.number} onClick={() => loadHex(h.number)}
                  className={`btn ${selHex?.number===h.number?'btn-primary':''}`}
                  style={{ flexDirection:'column', gap:'0.2rem', padding:'0.5rem 0.3rem' }}>
                  <span style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)' }}>第{h.number}卦</span>
                  <span style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-base)' }}>{h.name}</span>
                </button>
              ))}
            </div>
            {selHex && <HexagramDetail data={selHex} />}
          </div>
        )}

        {view === 'guide' && <LiuYaoGuide />}
      </div>
      {showShare && <ShareImage data={result} module="liuyao" onClose={() => setShowShare(false)} />}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════
   HEXAGRAM RESULT — full tabbed view
══════════════════════════════════════════════════════════ */
function HexagramDetail({ data }) {
  return (
    <div className="result-section">
      <div className="card">
        <div style={{ display:'flex', alignItems:'center', gap:'1.5rem', marginBottom:'1rem' }}>
          <div style={{ fontSize:'var(--text-display)', color:'var(--accent)', lineHeight:1 }}>
            {SYM[data.upper?.name]}{SYM[data.lower?.name]}
          </div>
          <div>
            <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-lg)', fontWeight:600, color:'var(--accent)' }}>
              第{data.number}卦 · {data.name}卦
            </div>
            <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginTop:'0.2rem' }}>
              上{data.upper?.name}（{data.upper?.nature}）下{data.lower?.name}（{data.lower?.nature}）
            </div>
          </div>
        </div>
        {[['卦辞', data.judgment], ['象传', data.image]].map(([label, text]) => text && (
          <div key={label} style={{ background:'var(--bg-raised)', borderRadius:'var(--r-md)',
            padding:'0.85rem', marginBottom:'0.75rem' }}>
            <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:'0.25rem' }}>{label}</div>
            <p style={{ fontFamily:'var(--font-serif)', color:'var(--text-primary)' }}>{text}</p>
          </div>
        ))}
        <div>
          <div style={{ fontSize:'var(--text-sm)', color:'var(--text-muted)', marginBottom:'0.5rem' }}>爻辞</div>
          {Object.entries(data.lines||{}).reverse().map(([pos, text]) => (
            <div key={pos} style={{ padding:'0.4rem 0.6rem', borderBottom:'1px solid var(--border)',
              fontSize:'var(--text-sm)', fontFamily:'var(--font-serif)', color:'var(--text-secondary)' }}>
              <span style={{ color:'var(--accent)', marginRight:'0.5rem' }}>
                {['初','二','三','四','五','上'][Number(pos)-1]}爻
              </span>
              {text}
            </div>
          ))}
        </div>
        {data.interpretation && (
          <div style={{ marginTop:'0.75rem', padding:'0.75rem', background:'var(--accent-glow)',
            border:'1px solid var(--accent-dim)', borderRadius:'var(--r-md)' }}>
            <p style={{ fontFamily:'var(--font-serif)', color:'var(--text-secondary)', lineHeight:1.85 }}>
              {data.interpretation}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

/* ── LiuYao Guide ── */
function LiuYaoGuide() {
  const LIUQIN = [
    { name:'父母爻', sym:'父', color:'#8e44ad', role:'文书·长辈·房屋·船车', 用神:'问功名学业·文书合同', 喜忌:'旺则文书顺，克则学业受阻' },
    { name:'兄弟爻', sym:'兄', color:'#e67e22', role:'竞争·朋友·兄弟·阻碍', 用神:'独占情境下代表竞争者', 喜忌:'兄弟发动则散财、阻碍' },
    { name:'子孙爻', sym:'子', color:'#27ae60', role:'福气·后代·医药·和平', 用神:'问疾病（药神）·问讼事（和解）', 喜忌:'子孙旺则病愈讼散，克官鬼大吉' },
    { name:'妻财爻', sym:'财', color:'#d4a040', role:'钱财·妻子·财物·享受', 用神:'男问婚姻·问财运', 喜忌:'财旺而身强则财来，身弱则财为祸' },
    { name:'官鬼爻', sym:'官', color:'#c0392b', role:'官府·丈夫·疾病·鬼神', 用神:'女问婚姻·问功名仕途', 喜忌:'官旺身弱则官非疾病，官旺身强则升官' },
  ]

  const LIUSHEN = [
    { name:'青龙', color:'#27ae60', symbol:'龙', nature:'吉', desc:'喜庆·婚嫁·财帛·贵人·酒食·文采', 断法:'临父母：文书喜庆；临财：横财；临官：升官有喜；婚姻最吉' },
    { name:'朱雀', color:'#e74c3c', symbol:'雀', nature:'凶', desc:'口舌·文书·是非·消息·争讼', 断法:'临官：官司文书；临兄弟：口舌纷争；临父母：文书有变动；动则消息至' },
    { name:'勾陈', color:'#d4a040', symbol:'陈', nature:'凶', desc:'勾连·牵绊·田土·迟滞·契约纠纷·缓慢', 断法:'临财：财被勾住难得；临官：官司田土；动则事情拖延不决' },
    { name:'腾蛇', color:'#9b59b6', symbol:'蛇', nature:'凶', desc:'虚惊·怪异·谎言·梦境·心神不宁·缠绕', 断法:'临官：虚惊官非；临妻财：财来财去；主事情虚假不实' },
    { name:'白虎', color:'#95a5a6', symbol:'虎', nature:'大凶', desc:'血光·伤亡·刚猛·凶险·丧事·武职', 断法:'临官：血光官非；临父母：父母有灾；主凶险事件；亦主武职贵' },
    { name:'玄武', color:'#5d8fa5', symbol:'武', nature:'凶', desc:'盗贼·奸情·暗昧·奸邪·私情·欺诈', 断法:'临财：财被盗；临妻财：妻有私情；主暗中之事' },
  ]

  const KOUJUE = [
    { t:'用神纲领', c:'凡占须先定用神，用神旺相则事成，休囚克泄则事败——《卜筮正宗》' },
    { t:'月建第一', c:'月建生克最有力，月令生用神则旺，克用神则衰——六爻第一法' },
    { t:'动爻变化', c:'动者变也，变爻为结果；化进神好转，化退神消退，回头克大凶' },
    { t:'旬空之义', c:'空亡之爻力量大减。逢冲则出空，往往在冲空之日应验' },
    { t:'黄金五诀', c:'旺发当日应·空亡出旬应·入墓冲开应·进神越来越好·退神逐渐消退' },
  ]

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:"1rem" }}>
      <div className="card">
        <div className="card-title">六亲爻系 — 六爻核心</div>
        <div style={{ display:"flex", flexDirection:"column", gap:"0.4rem" }}>
          {LIUQIN.map(q => (
            <div key={q.name} style={{ display:"flex", gap:"0.75rem", padding:"0.55rem 0.65rem",
              background:"var(--bg-subtle)", borderRadius:"var(--r-sm)", border:"1px solid var(--border)",
              alignItems:"flex-start" }}>
              <div style={{ width:32, height:32, borderRadius:"50%", flexShrink:0,
                background:q.color+"22", border:`1.5px solid ${q.color}55`,
                display:"flex", alignItems:"center", justifyContent:"center",
                fontFamily:"var(--font-display)", color:q.color, fontWeight:700, fontSize:'var(--text-sm)' }}>
                {q.sym}
              </div>
              <div style={{ flex:1 }}>
                <div style={{ display:"flex", gap:"0.5rem", alignItems:"center", marginBottom:"3px" }}>
                  <span style={{ fontWeight:700, color:q.color, fontSize:'var(--text-sm)' }}>{q.name}</span>
                  <span className="badge" style={{ background:q.color+"15", color:q.color, border:`1px solid ${q.color}40`, borderRadius:0, fontSize:'var(--text-2xs)', padding:"1px 6px" }}>{q.用神}</span>
                </div>
                <div style={{ fontSize:'var(--text-xs)', color:"var(--text-muted)", lineHeight:1.55, fontFamily:"var(--font-serif)" }}>
                  象意：{q.role} · {q.喜忌}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-title">六神详解 — 天干附神</div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"0.4rem" }}>
          {LIUSHEN.map(s => (
            <div key={s.name} style={{ padding:"0.55rem 0.7rem",
              background:`${s.color}0d`, borderRadius:"var(--r-sm)",
              border:`1px solid ${s.color}33` }}>
              <div style={{ display:"flex", alignItems:"center", gap:"0.4rem", marginBottom:"4px" }}>
                <div style={{ width:22, height:22, borderRadius:"50%",
                  background:s.color, display:"flex", alignItems:"center", justifyContent:"center",
                  color:"#fff", fontSize:'var(--text-2xs)', fontWeight:700, flexShrink:0 }}>{s.symbol}</div>
                <span style={{ fontWeight:700, color:s.color, fontSize:'var(--text-sm)' }}>{s.name}</span>
                <span className="badge" style={{ fontSize:'var(--text-2xs)', padding:"1px 5px", marginLeft:"auto",
                  background:s.nature==="吉"?"rgba(74,122,90,0.12)":"rgba(207,59,44,0.1)",
                  color:s.nature==="吉"?"var(--jade)":"var(--accent)", borderRadius:0,
                  border:`1px solid ${s.nature==="吉"?"rgba(74,122,90,0.3)":"rgba(207,59,44,0.25)"}` }}>
                  {s.nature}
                </span>
              </div>
              <div style={{ fontSize:'var(--text-xs)', color:"var(--text-muted)", fontFamily:"var(--font-serif)", lineHeight:1.6 }}>
                {s.desc}
              </div>
              <div style={{ fontSize:'var(--text-xs)', color:"var(--text-secondary)", fontFamily:"var(--font-serif)", lineHeight:1.6, marginTop:"3px" }}>
                {s.断法}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-title">断卦核心口诀</div>
        {KOUJUE.map((k, i) => (
          <div key={i} style={{ padding:"0.55rem 0", borderBottom:"1px solid var(--border)" }}>
            <div style={{ fontSize:'var(--text-xs)', fontWeight:700, color:"var(--accent)", marginBottom:"3px", letterSpacing:"0.04em" }}>
              {k.t}
            </div>
            <div style={{ fontSize:'var(--text-xs)', color:"var(--text-secondary)", fontFamily:"var(--font-serif)", lineHeight:1.7 }}>
              {k.c}
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">旺相休囚死速查（严格四时派）</div>
        <div style={{ fontSize:'var(--text-xs)', color:"var(--text-muted)", marginBottom:"0.5rem", fontFamily:"var(--font-serif)" }}>
          六爻论旺衰严格按月令地支当令五行（《增删卜易》《卜筮正宗》），不考虑藏干
        </div>
        {[
          ['春（寅卯辰）', '木旺·火相·水休·金囚·土死'],
          ['夏（巳午未）', '火旺·土相·木休·水囚·金死'],
          ['秋（申酉戌）', '金旺·水相·土休·火囚·木死'],
          ['冬（亥子丑）', '水旺·木相·金休·土囚·火死'],
        ].map(([season, desc]) => (
          <div key={season} style={{ display:"flex", gap:"0.75rem", padding:"0.35rem 0",
            borderBottom:"1px solid var(--border)", fontSize:'var(--text-xs)' }}>
            <span style={{ color:"var(--accent)", fontWeight:600, width:90, flexShrink:0 }}>{season}</span>
            <span style={{ color:"var(--text-secondary)", fontFamily:"var(--font-serif)" }}>{desc}</span>
          </div>
        ))}
        <div style={{ marginTop:'0.5rem', fontSize:'var(--text-2xs)', color:'var(--text-faint)',
          fontFamily:'var(--font-serif)', lineHeight:1.6, fontStyle:'italic' }}>
          注：八字"气势派"考虑藏干会判辰月土旺，但六爻严格派判辰月土死。本系统采用六爻严格派。
        </div>
      </div>

      {/* ── 用神选取（按古书） ── */}
      <div className="card">
        <div className="card-title">用神选取（古书《增删卜易》《卜筮正宗》）</div>
        <div style={{ display:'flex', flexDirection:'column', gap:'0.3rem', fontSize:'var(--text-xs)' }}>
          {[
            ['求财', '妻财（用神）/ 子孙（原神，生财之源）/ 兄弟（忌神，劫财）'],
            ['求官仕途', '官鬼（用神）/ 父母（原神，印星生官）/ 子孙（忌神，克官）'],
            ['考试功名', '父母（用神，文书印星）/ 官鬼（原神，功名贵气）/ 子孙（忌神）'],
            ['婚姻 · 男', '妻财（用神）/ 应爻代表对方'],
            ['婚姻 · 女', '官鬼（用神，夫星）/ 应爻代表对方'],
            ['求医疾病', '世爻（病人）/ 子孙（药神）/ 官鬼（病神，忌动）'],
            ['出行远行', '世爻（本人）/ 父母（车船舟舆）/ 应爻（远方）'],
            ['官司诉讼', '世爻（己方）/ 应爻（对方）/ 子孙（化解官非）'],
            ['求子嗣', '子孙（用神）/ 妻财（生子孙之原神）'],
            ['失物寻物', '妻财（财物）/ 父母（文书凭证）/ 子孙（家畜）'],
            ['家宅风水', '父母（家宅）/ 世爻（住者）/ 二爻（宅）'],
          ].map(([topic, neuro]) => (
            <div key={topic} style={{ display:'grid', gridTemplateColumns:'85px 1fr', gap:'0.5rem',
              padding:'0.35rem 0.55rem', background:'var(--bg-subtle)', borderRadius:'var(--r-sm)' }}>
              <span style={{ color:'var(--accent)', fontWeight:600, fontFamily:'var(--font-serif)' }}>{topic}</span>
              <span style={{ color:'var(--text-secondary)', fontFamily:'var(--font-serif)', lineHeight:1.6 }}>{neuro}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── 三合三会局 ── */}
      <div className="card">
        <div className="card-title">三合三会局 · 五行聚气</div>
        <div style={{ display:'flex', flexDirection:'column', gap:'0.4rem' }}>
          {[
            { name:'三合局', items:[
              { combo:'申子辰', wx:'水局', color:'#3498db' },
              { combo:'亥卯未', wx:'木局', color:'#27ae60' },
              { combo:'寅午戌', wx:'火局', color:'#e74c3c' },
              { combo:'巳酉丑', wx:'金局', color:'#95a5a6' },
            ]},
            { name:'三会方', items:[
              { combo:'亥子丑', wx:'北方水会', color:'#3498db' },
              { combo:'寅卯辰', wx:'东方木会', color:'#27ae60' },
              { combo:'巳午未', wx:'南方火会', color:'#e74c3c' },
              { combo:'申酉戌', wx:'西方金会', color:'#95a5a6' },
            ]},
          ].map(({ name, items }) => (
            <div key={name}>
              <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:'0.3rem', fontFamily:'var(--font-serif)' }}>{name}</div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:'0.3rem' }}>
                {items.map(({ combo, wx, color }) => (
                  <div key={combo} style={{
                    padding:'0.4rem 0.5rem', textAlign:'center',
                    background:`${color}11`, border:`1px solid ${color}55`,
                    borderRadius:'var(--r-sm)',
                  }}>
                    <div style={{ fontFamily:'var(--font-display)', fontSize:'var(--text-sm)',
                      color, fontWeight:600 }}>{combo}</div>
                    <div style={{ fontSize:'var(--text-2xs)', color:'var(--text-muted)', marginTop:'2px' }}>{wx}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div style={{ marginTop:'0.5rem', padding:'0.4rem 0.65rem',
          background:'rgba(212,160,64,0.06)', borderRadius:'var(--r-sm)',
          fontSize:'var(--text-xs)', color:'var(--text-secondary)', fontFamily:'var(--font-serif)', lineHeight:1.65 }}>
          《增删卜易·三合局》：三爻地支同会一局，五行力量大增。
          若用神在局中得旺，原神又得力，则所占必应；
          若忌神成局，则凶象加重。
        </div>
      </div>

      {/* ── 应期推算七法 ── */}
      <div className="card">
        <div className="card-title">应期推算七法（《黄金策》《增删卜易》）</div>
        <div style={{ display:'flex', flexDirection:'column', gap:'0.35rem' }}>
          {[
            ['用神旺相不动', '逢冲之月日（动以冲应）', '#27ae60'],
            ['用神有气发动', '逢合之日（合而后应）或当日', '#27ae60'],
            ['用神化进神', '应于进神所化之地支日', '#27ae60'],
            ['用神化退神', '应于退神之地支日（事必反复）', '#e74c3c'],
            ['用神化回头生', '应于化神冲之日（事必成）', '#27ae60'],
            ['用神化回头克', '应于化神冲之日（事必败）', '#c0392b'],
            ['用神入墓', '冲开墓库之日（木墓未/火墓戌/金墓丑/水墓辰）', '#5d6d7e'],
            ['用神旺空', '出旬之日填实而应', '#e67e22'],
            ['用神衰空', '真空难应；唯逢冲空起爻或出旬可看', '#bdc3c7'],
            ['用神月破', '出月之后填实方应，大事不应', '#c0392b'],
            ['用神伏藏', '冲飞神之日伏神出现；飞克伏则永不出', '#7f8c8d'],
            ['用神受制被克', '制克忌神之月日（药日应）', '#3498db'],
            ['六合卦', '合处逢冲方应（聚而后散）', '#27ae60'],
            ['六冲卦', '事散应快，但难持久', '#e74c3c'],
          ].map(([cond, result, color], i) => (
            <div key={i} style={{ display:'grid', gridTemplateColumns:'130px 1fr', gap:'0.6rem',
              padding:'0.35rem 0.55rem',
              background: i%2===0 ? 'var(--bg-subtle)' : 'transparent',
              borderLeft:`3px solid ${color}`,
              borderRadius:'var(--r-sm)' }}>
              <span style={{ color, fontWeight:600, fontFamily:'var(--font-serif)', fontSize:'var(--text-xs)' }}>{cond}</span>
              <span style={{ color:'var(--text-secondary)', fontFamily:'var(--font-serif)', fontSize:'var(--text-xs)', lineHeight:1.6 }}>{result}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop:'0.5rem', padding:'0.45rem 0.65rem',
          background:'rgba(212,160,64,0.06)', borderRadius:'var(--r-sm)',
          fontSize:'var(--text-xs)', color:'var(--text-secondary)', fontFamily:'var(--font-serif)', lineHeight:1.65,
          fontStyle:'italic' }}>
          总则：急事应日时，寻常事应月，大事应年。
          《黄金策》：空破墓合为病（阻碍），出空填实冲墓为药（解除）。
        </div>
      </div>

      {/* ── 飞神伏神 5 种关系 ── */}
      <div className="card">
        <div className="card-title">飞神伏神五种关系（《增删卜易·飞伏吉凶论》）</div>
        <div style={{ display:'flex', flexDirection:'column', gap:'0.3rem' }}>
          {[
            ['飞生伏', '飞神生伏神，长生扶起，伏神得力，最吉', '#27ae60', '伏神可出，待用之时'],
            ['伏生飞', '伏神生飞神，泄气难出，凶', '#e74c3c', '伏神被泄，难显其用'],
            ['飞克伏', '飞神克伏神，事难成，凶', '#c0392b', '飞神压制，伏神永不能出'],
            ['伏克飞', '伏神反克飞神，克出可期，吉', '#27ae60', '克出之日伏神出现'],
            ['比和', '飞伏同类相助，待冲飞日出伏', '#7f8c8d', '冲飞神之日伏神可现'],
          ].map(([name, def, color, ying]) => (
            <div key={name} style={{ display:'grid', gridTemplateColumns:'70px 1fr 1fr', gap:'0.55rem',
              padding:'0.4rem 0.6rem',
              borderLeft:`3px solid ${color}`,
              background:`${color}08`, borderRadius:'var(--r-sm)' }}>
              <span style={{ color, fontWeight:700, fontFamily:'var(--font-display)' }}>{name}</span>
              <span style={{ color:'var(--text-secondary)', fontFamily:'var(--font-serif)', fontSize:'var(--text-xs)', lineHeight:1.55 }}>{def}</span>
              <span style={{ color:'var(--text-muted)', fontFamily:'var(--font-serif)', fontSize:'var(--text-xs)', lineHeight:1.55, fontStyle:'italic' }}>{ying}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}


