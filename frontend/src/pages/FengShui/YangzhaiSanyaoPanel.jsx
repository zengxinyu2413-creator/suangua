/**
 * YangzhaiSanyaoPanel.jsx — 《阳宅三要》门主灶断
 *
 * 用户选择 大门 / 主房 / 灶位 三者卦位，调后端大游年断吉凶。
 */
import React, { useState } from 'react'
import { fengshuiApi } from '../../api/client'
import ShareImage from '../../components/UI/ShareImage'
import YangzhaiChainPlate from './YangzhaiChainPlate'
import YangzhaiOverview from './YangzhaiOverview'
import YangzhaiSynthesis from './YangzhaiSynthesis'
import YangzhaiPerspectives from './YangzhaiPerspectives'
import YangzhaiConsistencyAudit from './YangzhaiConsistencyAudit'
import NarrationPanel from '../../components/NarrationPanel'

// 八卦方位（后天八卦 / 八方）
const GUA8 = [
  { gua: '坎', dir: '北',   group: '东四' },
  { gua: '艮', dir: '东北', group: '西四' },
  { gua: '震', dir: '东',   group: '东四' },
  { gua: '巽', dir: '东南', group: '东四' },
  { gua: '离', dir: '南',   group: '东四' },
  { gua: '坤', dir: '西南', group: '西四' },
  { gua: '兑', dir: '西',   group: '西四' },
  { gua: '乾', dir: '西北', group: '西四' },
]

const STAR_COLOR = {
  生气: '#27ae60', 天医: '#2980b9', 延年: '#16a085', 伏位: '#7f8c8d',
  祸害: '#e67e22', 六煞: '#9b59b6', 五鬼: '#c0392b', 绝命: '#8b0000',
}
const GRADE_COLOR = {
  上吉之宅: '#27ae60', 次吉之宅: '#16a085', 平常之宅: '#d4a040',
  大凶之宅: '#8b0000', 凶宅: '#c0392b',
}

// 二十四山（壬子癸 丑艮寅 …）→ 卦 / 三元龙
const SHAN_SEQ = [
  ['壬','坎','地'],['子','坎','天'],['癸','坎','人'],['丑','艮','地'],['艮','艮','天'],['寅','艮','人'],
  ['甲','震','地'],['卯','震','天'],['乙','震','人'],['辰','巽','地'],['巽','巽','天'],['巳','巽','人'],
  ['丙','离','地'],['午','离','天'],['丁','离','人'],['未','坤','地'],['坤','坤','天'],['申','坤','人'],
  ['庚','兑','地'],['酉','兑','天'],['辛','兑','人'],['戌','乾','地'],['乾','乾','天'],['亥','乾','人'],
]
const SHAN24 = SHAN_SEQ.map(s => s[0])
const SHAN_GUA = Object.fromEntries(SHAN_SEQ.map(s => [s[0], s[1]]))
const SHAN_YUAN = Object.fromEntries(SHAN_SEQ.map(s => [s[0], s[2]]))

// 六事（门主灶之外）：净者宜吉方、秽者宜凶方
const LIUSHI_ITEMS = [
  { key: '路',   tip: '来路·引气', prefers: '吉' },
  { key: '井',   tip: '水财·属水', prefers: '吉' },
  { key: '厕',   tip: '秽污·压凶', prefers: '凶' },
  { key: '碓磨', tip: '动器·压凶', prefers: '凶' },
  { key: '畜栏', tip: '秽臊·压凶', prefers: '凶' },
]

function GuaPicker({ label, value, onChange, hint }) {
  return (
    <div style={{ marginBottom: '0.7rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
        <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{label}</span>
        <span style={{ fontSize: '0.62rem', color: 'var(--text-faint)' }}>{hint}</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px' }}>
        {GUA8.map(g => (
          <button key={g.gua} onClick={() => onChange(g.gua)}
            style={{
              padding: '6px 2px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
              border: value === g.gua ? '1.5px solid var(--accent)' : '1px solid var(--border)',
              background: value === g.gua ? 'rgba(212,160,64,0.12)' : 'var(--bg-subtle)',
              color: value === g.gua ? 'var(--accent)' : 'var(--text-secondary)',
              fontSize: '0.7rem', lineHeight: 1.3,
              fontWeight: value === g.gua ? 700 : 400,
            }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.9rem' }}>{g.gua}</div>
            <div style={{ fontSize: '0.56rem', color: g.group === '东四' ? '#27ae60' : '#c0392b' }}>
              {g.dir}·{g.group}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}



export default function YangzhaiSanyaoPanel() {
  const [men, setMen] = useState('坎')
  const [zhu, setZhu] = useState('巽')
  const [zao, setZao] = useState('震')
  const [zaoFacing, setZaoFacing] = useState('')
  const [floor, setFloor] = useState('')
  const [jin, setJin] = useState('')
  const [birthYear, setBirthYear] = useState('')
  const [gender, setGender] = useState('male')
  const [analysisYear, setAnalysisYear] = useState(new Date().getFullYear())  // 流年方位辅参
  const [analysisMonth, setAnalysisMonth] = useState(new Date().getMonth() + 1)  // 流月方位辅参
  const [liushi, setLiushi] = useState({})   // { 井:'巽', 厕:'艮', ... }
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [showShare, setShowShare] = useState(false)

  const run = async () => {
    setLoading(true); setErr('')
    try {
      const body = { men, zhu, zao }
      if (analysisYear) body.analysis_year = analysisYear
      if (analysisMonth) body.analysis_month = analysisMonth
      if (zaoFacing) body.zao_facing = zaoFacing
      if (floor) body.floor = parseInt(floor)
      if (jin) body.jin = parseInt(jin)
      if (birthYear && parseInt(birthYear) > 1900) {
        body.birth_year = parseInt(birthYear)
        body.gender = gender
      }
      const ls = Object.fromEntries(Object.entries(liushi).filter(([, v]) => v))
      if (Object.keys(ls).length) body.liushi = ls
      const r = await fengshuiApi.yangzhaiSanyao(body)
      setResult(r.data || r)
    } catch (e) {
      setErr('排盘失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="card">
        <div className="card-title">《阳宅三要》· 门主灶</div>
        <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)',
          fontFamily: 'var(--font-serif)', marginBottom: '0.8rem', lineHeight: 1.5 }}>
          清·赵九峰：「看阳宅之法，先看大门，次看主房，后看灶。」
          以大门定东西四宅，大游年翻卦推门→主、主→灶之吉凶。
        </div>
        <GuaPicker label="① 大门" value={men} onChange={(g)=>{setMen(g)}} hint="纳气之口·定宅" />
        {/* 精确门向（二十四山，可选，覆盖上方八卦门） */}
        <div style={{ display:'flex', alignItems:'center', gap:'0.5rem', margin:'-0.4rem 0 0.7rem' }}>
          <span style={{ fontSize:'0.64rem', color:'var(--text-faint)' }}>精确门向(廿四山)：</span>
          <select value={SHAN24.includes(men)?men:''} onChange={e=>e.target.value&&setMen(e.target.value)}
            style={{ flex:1, fontSize:'0.7rem', padding:'3px 6px', borderRadius:'var(--r-sm)',
              border:'1px solid var(--border)', background:'var(--bg-subtle)', color:'var(--text-secondary)' }}>
            <option value="">— 用八卦门 —</option>
            {SHAN24.map(s => <option key={s} value={s}>{s}山（{SHAN_GUA[s]}·{SHAN_YUAN[s]}元）</option>)}
          </select>
        </div>
        <GuaPicker label="② 主房" value={zhu} onChange={setZhu} hint="一家之主所居" />
        <GuaPicker label="③ 灶位" value={zao} onChange={setZao} hint="火门·养命之源" />
        {/* 灶口向（可选） */}
        <div style={{ marginBottom: '0.7rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>④ 灶口向 <span style={{fontSize:'0.6rem',color:'var(--text-faint)'}}>（可选）</span></span>
            <span style={{ fontSize: '0.62rem', color: 'var(--text-faint)' }}>纳气之向·宜向吉方</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '4px' }}>
            <button onClick={() => setZaoFacing('')}
              style={{ padding: '6px 2px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
                border: zaoFacing === '' ? '1.5px solid var(--accent)' : '1px solid var(--border)',
                background: zaoFacing === '' ? 'rgba(212,160,64,0.12)' : 'var(--bg-subtle)',
                color: zaoFacing === '' ? 'var(--accent)' : 'var(--text-faint)',
                fontSize: '0.68rem' }}>不设</button>
            {GUA8.map(g => (
              <button key={g.gua} onClick={() => setZaoFacing(g.gua)}
                style={{ padding: '6px 2px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
                  border: zaoFacing === g.gua ? '1.5px solid var(--accent)' : '1px solid var(--border)',
                  background: zaoFacing === g.gua ? 'rgba(212,160,64,0.12)' : 'var(--bg-subtle)',
                  color: zaoFacing === g.gua ? 'var(--accent)' : 'var(--text-secondary)',
                  fontSize: '0.72rem', fontFamily: 'var(--font-display)' }}>{g.gua}</button>
            ))}
          </div>
        </div>
        {/* 楼层 / 进数（可选） */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.6rem' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>楼层（论层数五行）</div>
            <input type="number" min="1" value={floor} onChange={e => setFloor(e.target.value)}
              placeholder="如 6" style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>进数（穿宫九星）</div>
            <input type="number" min="1" max="9" value={jin} onChange={e => setJin(e.target.value)}
              placeholder="如 3" style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }} />
          </div>
        </div>
        {/* 主人命卦（人宅相配 — 八宅明镜命根，可选） */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.6rem', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>主人生年（断命卦·人宅相配）</div>
            <input type="number" min="1900" max="2100" value={birthYear} onChange={e => setBirthYear(e.target.value)}
              placeholder="如 1990" style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>性别</div>
            <select value={gender} onChange={e => setGender(e.target.value)}
              style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }}>
              <option value="male">男（乾造）</option>
              <option value="female">女（坤造）</option>
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>分析流年（方位辅参）</div>
            <input type="number" min="1864" max="2100" value={analysisYear}
              onChange={e => setAnalysisYear(Number(e.target.value))}
              title="门主灶为静、不随年变；此年决定流年文昌/财位/五黄/病符/太岁等方位（宅静时动）"
              style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.66rem', color: 'var(--text-faint)', marginBottom: '0.2rem' }}>分析流月</div>
            <input type="number" min="1" max="12" value={analysisMonth}
              onChange={e => setAnalysisMonth(Number(e.target.value))}
              title="流月紫白叠流年，精确到该月之文昌/财位/五黄/病符方"
              style={{ width: '100%', padding: '5px 8px', fontSize: '0.74rem',
                borderRadius: 'var(--r-sm)', border: '1px solid var(--border)', background: 'var(--bg-subtle)' }} />
          </div>
        </div>
        {/* 六事安置（可选）：路·井·厕·碓磨·畜栏 */}
        <div style={{ marginBottom: '0.6rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              ⑤ 六事安置 <span style={{ fontSize: '0.6rem', color: 'var(--text-faint)' }}>（可选）</span>
            </span>
            <span style={{ fontSize: '0.62rem', color: 'var(--text-faint)' }}>净居吉方·秽镇凶方</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {LIUSHI_ITEMS.map(it => (
              <div key={it.key} style={{ display: 'grid', gridTemplateColumns: '72px 1fr',
                gap: '0.45rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)' }}>
                  {it.key}
                  <span style={{ fontSize: '0.54rem', marginLeft: '3px',
                    color: it.prefers === '吉' ? '#27ae60' : '#c0392b' }}>{it.tip}</span>
                </span>
                <select value={liushi[it.key] || ''}
                  onChange={e => setLiushi(prev => ({ ...prev, [it.key]: e.target.value }))}
                  style={{ width: '100%', fontSize: '0.7rem', padding: '3px 6px',
                    borderRadius: 'var(--r-sm)', border: '1px solid var(--border)',
                    background: 'var(--bg-subtle)', color: 'var(--text-secondary)' }}>
                  <option value="">— 不设 —</option>
                  {GUA8.map(g => <option key={g.gua} value={g.gua}>{g.gua}（{g.dir}）</option>)}
                  <option value="中宫">中宫（忌）</option>
                </select>
              </div>
            ))}
          </div>
        </div>
        <button className="btn-primary" onClick={run} disabled={loading}
          style={{ width: '100%', marginTop: '0.4rem' }}>
          {loading ? '排盘中…' : '断 三 要'}
        </button>
        {err && <div style={{ color: '#c0392b', fontSize: '0.72rem', marginTop: '0.4rem' }}>{err}</div>}
      </div>

      {result && result.success && (
        <>
          <div style={{ display:'flex', justifyContent:'flex-end' }}>
            <button className="btn btn-sm" onClick={() => setShowShare(true)} title="生成分享图">🖼 分享图</button>
          </div>
          {/* 总断 */}
          {result?.master_synthesis?.available && (() => {
            const QC = { 吉:'#27ae60', 中:'var(--accent)', 凶:'#c0392b' }
            const ms = result.master_synthesis
            const pc = QC[ms.overall_quality] || 'var(--accent)'
            return (
              <div className="card card-glow" style={{ borderTop:`4px solid ${pc}`, marginBottom:'1rem' }}>
                <div className="card-title">综合宅论 · 总汇合参</div>
                <div style={{ fontFamily:'var(--font-serif)', fontSize:'var(--text-md)', fontWeight:600,
                  color:pc, marginBottom:'0.5rem' }}>
                  {ms.house_type} · {ms.grade} · 综评<span style={{ color:pc }}>{ms.overall_quality}</span>
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
                <NarrationPanel ms={ms} fullData={result} module="yangzhai" />
              </div>
            )
          })()}
          <YangzhaiOverview data={result} />
          <YangzhaiSynthesis data={result} />
          <YangzhaiPerspectives data={result} />
          <YangzhaiConsistencyAudit data={result} />
          <div className="card" style={{
            borderLeft: `4px solid ${GRADE_COLOR[result.grade] || 'var(--accent)'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              marginBottom: '0.5rem' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-faint)' }}>{result.house_type}</span>
                <div style={{ fontSize: '1.15rem', fontWeight: 800,
                  color: GRADE_COLOR[result.grade] || 'var(--accent)',
                  fontFamily: 'var(--font-display)' }}>{result.grade}</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, lineHeight: 1,
                  color: GRADE_COLOR[result.grade] || 'var(--accent)' }}>{result.score}</div>
                <div style={{ fontSize: '0.58rem', color: 'var(--text-faint)' }}>综合评分</div>
              </div>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.6 }}>{result.verdict}</div>
            {result.door_detail && result.door_detail.jian_note && (
              <div style={{ marginTop: '0.4rem', fontSize: '0.66rem', color: '#e67e22',
                fontFamily: 'var(--font-serif)', lineHeight: 1.5 }}>
                ⚠ {result.door_detail.jian_note}
              </div>
            )}
          </div>

          {/* 八宅总论 */}
          {result.house_overview && result.house_overview.name && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.5rem' }}>
                <div className="card-title" style={{ marginBottom: 0 }}>
                  {result.house_overview.name}·总论
                </div>
                <span style={{ fontSize: '0.64rem', color: 'var(--text-faint)',
                  fontFamily: 'var(--font-serif)' }}>
                  {result.house_overview.facing} · 属{result.house_overview.wuxing} · 主{result.house_overview.lord}
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.65, marginBottom: '0.5rem' }}>
                {result.house_overview.desc}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                <span style={{ fontSize: '0.64rem', color: 'var(--text-faint)' }}>三吉方：</span>
                {(result.house_overview.best || []).map((b, i) => (
                  <span key={i} style={{ fontSize: '0.64rem', padding: '1px 6px',
                    background: 'rgba(39,174,96,0.1)', color: '#27ae60',
                    border: '1px solid #27ae6033', borderRadius: '3px' }}>{b}</span>
                ))}
              </div>
            </div>
          )}

          {/* 门→主→灶 生成链（三宫卦象 + 三要关系 + 纯杂判定 合一） */}
          <div className="card">
            <YangzhaiChainPlate result={result} />
          </div>

          {/* 门主局详断 —— 《阳宅三要》64局断语库 */}
          {result.menzhu_ju && result.menzhu_ju.ming && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.55rem' }}>
                <div className="card-title" style={{ marginBottom: 0 }}>门主局详断</div>
                <span style={{ fontSize: '0.62rem', color: 'var(--text-faint)',
                  fontFamily: 'var(--font-serif)' }}>{result.menzhu_ju.wuxing}·{result.menzhu_ju.level}</span>
              </div>
              <div style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--accent)',
                fontFamily: 'var(--font-display)', marginBottom: '0.5rem' }}>
                {result.menzhu_ju.ming}
              </div>
              {[
                ['综合', result.menzhu_ju.zong, '#d4a040'],
                ['人丁', result.menzhu_ju.ding, '#27ae60'],
                ['财禄', result.menzhu_ju.cai, '#2980b9'],
                ['功名·健康', result.menzhu_ju.gongjian, '#16a085'],
                ['应何人', result.menzhu_ju.yingren, '#9b59b6'],
              ].map(([k, v, c]) => (
                <div key={k} style={{ display: 'grid', gridTemplateColumns: '58px 1fr',
                  gap: '0.5rem', marginBottom: '0.35rem', alignItems: 'start' }}>
                  <span style={{ fontSize: '0.66rem', fontWeight: 600, color: c,
                    fontFamily: 'var(--font-serif)', paddingTop: '1px' }}>{k}</span>
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-serif)', lineHeight: 1.6 }}>{v}</span>
                </div>
              ))}
            </div>
          )}

          {/* 灶配断 */}
          {result.zao_ju && result.zao_ju.desc && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                marginBottom: '0.5rem' }}>
                <div className="card-title" style={{ marginBottom: 0 }}>灶位详断</div>
                <span style={{ fontSize: '0.66rem', padding: '1px 8px', borderRadius: '3px',
                  background: result.zao_ju.quality.includes('凶') ? 'rgba(192,57,43,0.12)' : 'rgba(39,174,96,0.12)',
                  color: result.zao_ju.quality.includes('凶') ? '#c0392b' : '#27ae60',
                  fontWeight: 700 }}>{result.zao_ju.quality}</span>
              </div>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.65 }}>
                {result.zao_ju.desc}
              </div>
            </div>
          )}

          {/* 整局成文断（512局） */}
          {result.full_ju && result.full_ju.full_text && (
            <div className="card" style={{ borderLeft: '4px solid var(--accent)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.5rem' }}>
                <div className="card-title" style={{ marginBottom: 0 }}>{result.full_ju.ju_name}</div>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent)',
                  fontFamily: 'var(--font-display)' }}>{result.full_ju.ju_grade}</span>
              </div>
              <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.75, textAlign: 'justify' }}>
                {result.full_ju.full_text}
              </div>
            </div>
          )}

          {/* 楼层五行 */}
          {result.floor && result.floor.success && (
            <div className="card">
              <div className="card-title">论层数 · 楼层五行</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.7rem', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent)',
                  fontFamily: 'var(--font-display)' }}>{result.floor.floor}层</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  属{result.floor.floor_wuxing}　{result.floor.relation}　
                  <strong style={{ color: result.floor.quality === '吉' ? '#27ae60' :
                    result.floor.quality === '凶' ? '#c0392b' : 'var(--text-muted)' }}>
                    {result.floor.quality}</strong>
                </span>
              </div>
              {result.floor_guide && (
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)', lineHeight: 1.6 }}>
                  {result.floor_guide.desc}
                </div>
              )}
            </div>
          )}

          {/* 穿宫九星 */}
          {result.chuangong && result.chuangong.success && (
            <div className="card">
              <div className="card-title">穿宫九星 · 进深高低</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {result.chuangong.rows.map((r, i) => (
                  <div key={i} style={{ display: 'grid', gridTemplateColumns: '44px 56px 1fr',
                    gap: '0.5rem', alignItems: 'center', padding: '0.3rem 0.5rem',
                    background: r.is_auspicious ? 'rgba(39,174,96,0.07)' : 'rgba(192,57,43,0.07)',
                    borderLeft: `2px solid ${r.is_auspicious ? '#27ae60' : '#c0392b'}`,
                    borderRadius: 'var(--r-sm)', fontSize: '0.72rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>第{r.jin}进</span>
                    <span style={{ fontWeight: 700, color: r.is_auspicious ? '#27ae60' : '#c0392b' }}>{r.star}</span>
                    <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)' }}>
                      {r.is_auspicious ? '宜高大宽敞·受旺气' : '宜低矮窄小·压凶气'}
                    </span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: '0.4rem', fontSize: '0.62rem', color: 'var(--text-faint)',
                fontFamily: 'var(--font-serif)', fontStyle: 'italic' }}>{result.chuangong.note}</div>
            </div>
          )}

          {/* 六事安置断 —— 《阳宅十书·论六事》 */}
          {result.liushi && result.liushi.success && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                marginBottom: '0.5rem' }}>
                <div className="card-title" style={{ marginBottom: 0 }}>六事安置断</div>
                <span style={{ fontSize: '0.7rem', fontWeight: 700,
                  color: result.liushi.bad_count > result.liushi.good_count ? '#c0392b' : '#27ae60',
                  fontFamily: 'var(--font-display)' }}>{result.liushi.grade}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {result.liushi.items.filter(it => it.success).map((it, i) => {
                  const ji = it.is_auspicious
                  const col = ji ? '#27ae60' : '#c0392b'
                  return (
                    <div key={i} style={{ display: 'grid', gridTemplateColumns: '88px 1fr',
                      gap: '0.5rem', alignItems: 'start', padding: '0.35rem 0.5rem',
                      background: `${col}0d`, borderLeft: `2px solid ${col}`, borderRadius: 'var(--r-sm)' }}>
                      <div>
                        <span style={{ fontSize: '0.74rem', fontWeight: 700,
                          color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)' }}>{it.item}</span>
                        <span style={{ fontSize: '0.6rem', marginLeft: '3px', color: 'var(--text-faint)' }}>
                          {it.place === '中宫' ? '中宫' : `${it.place}·${it.direction || ''}`}
                        </span>
                        {it.younian && (
                          <div style={{ fontSize: '0.58rem', color: STAR_COLOR[it.younian] || '#888',
                            fontWeight: 700 }}>{it.younian}</div>
                        )}
                      </div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)',
                        fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>{it.judgment}</span>
                    </div>
                  )
                })}
              </div>
              {result.liushi.interaction_warnings && result.liushi.interaction_warnings.length > 0 && (
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {result.liushi.interaction_warnings.map((w, i) => (
                    <div key={i} style={{ fontSize: '0.66rem', color: '#e67e22',
                      fontFamily: 'var(--font-serif)', lineHeight: 1.45 }}>⚠ {w}</div>
                  ))}
                </div>
              )}
              <div style={{ marginTop: '0.5rem', fontSize: '0.72rem', color: 'var(--text-muted)',
                fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>{result.liushi.summary}</div>
              {result.liushi.general && (
                <div style={{ marginTop: '0.4rem', padding: '0.4rem 0.6rem',
                  background: 'rgba(212,160,64,0.05)', borderRadius: 'var(--r-sm)',
                  fontSize: '0.62rem', color: 'var(--text-faint)',
                  fontFamily: 'var(--font-serif)', fontStyle: 'italic', lineHeight: 1.5 }}>
                  《阳宅十书·论六事》：{result.liushi.general.principle}
                </div>
              )}
            </div>
          )}

          {/* 调整建议 */}
          <div className="card">
            <div className="card-title">调整建议</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {result.advice.map((a, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.4rem',
                  fontSize: '0.74rem', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)', lineHeight: 1.55 }}>
                  <span style={{ color: 'var(--accent)' }}>·</span>
                  <span>{a}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: '0.6rem', padding: '0.4rem 0.6rem',
              background: 'rgba(212,160,64,0.05)', borderRadius: 'var(--r-sm)',
              fontSize: '0.62rem', color: 'var(--text-faint)',
              fontFamily: 'var(--font-serif)', fontStyle: 'italic', lineHeight: 1.5 }}>
              《阳宅三要》：门主灶三者，门为君、主为臣、灶为佐。东四宅门主灶俱要落东四卦位，
              西四宅俱要落西四卦位；纯则吉，杂则凶。灶乃养命之源，尤忌坐绝命、五鬼。
            </div>
          </div>
        </>
      )}
      {showShare && <ShareImage data={result} module="yangzhai" onClose={() => setShowShare(false)} />}
    </div>
  )
}
