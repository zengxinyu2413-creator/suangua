/**
 * LiuyaoYingqiCalendar.jsx — 应期日历
 *
 * 根据用神状态自动推算未来 60 天哪些是应期日：
 *   - 用神冲日（旺相不动时应期）
 *   - 用神合日（动时应期）
 *   - 出空日（空亡时）
 *   - 冲墓日（入墓时）
 *
 * 用"日历热图"方式展示，让用户一眼看出关键日子
 */
import React from 'react'

// 六十甲子
const TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
const DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
const CHONG = { 子:'午', 丑:'未', 寅:'申', 卯:'酉', 辰:'戌', 巳:'亥',
                午:'子', 未:'丑', 申:'寅', 酉:'卯', 戌:'辰', 亥:'巳' }
const HE_LIU = { 子:'丑', 丑:'子', 寅:'亥', 亥:'寅', 卯:'戌', 戌:'卯',
                 辰:'酉', 酉:'辰', 巳:'申', 申:'巳', 午:'未', 未:'午' }
// 三合（六亲所合的另两支）
const SANHE_PAIR = {
  子: ['申','辰'], 申: ['子','辰'], 辰: ['申','子'],
  丑: ['巳','酉'], 巳: ['酉','丑'], 酉: ['巳','丑'],
  寅: ['午','戌'], 午: ['寅','戌'], 戌: ['寅','午'],
  卯: ['亥','未'], 亥: ['卯','未'], 未: ['亥','卯'],
}
// 五行墓库
const MU_KU = { 木:'未', 火:'戌', 土:'辰', 金:'丑', 水:'辰' }

/**
 * 从今天起，生成未来 N 天的干支
 */
function genDays(startGan, startZhi, n = 60) {
  const ganIdx = TIANGAN.indexOf(startGan)
  const zhiIdx = DIZHI.indexOf(startZhi)
  if (ganIdx < 0 || zhiIdx < 0) return []
  const days = []
  for (let i = 0; i < n; i++) {
    const g = TIANGAN[(ganIdx + i) % 10]
    const z = DIZHI[(zhiIdx + i) % 12]
    days.push({ index: i, gan: g, zhi: z, ganzhi: g + z })
  }
  return days
}

/**
 * 判断某日是否应期日，及类型
 */
function getYingqiType(day, yongBranch, yongElement, yongStrength, isKong, isChanging, kongList) {
  const reasons = []
  const z = day.zhi
  
  // 1. 出空日（用神空亡，出空之日）
  if (isKong && !kongList.includes(z) && z === yongBranch) {
    reasons.push({ type: '出空填实', color: '#e67e22', desc: `${z}日填实空亡` })
  }
  // 2. 冲空日（旬空可冲空起爻）
  if (isKong && CHONG[yongBranch] === z) {
    reasons.push({ type: '冲空', color: '#e67e22', desc: `${z}日冲空起爻` })
  }
  // 3. 冲用神日（用神旺相不动时应期）
  if (!isKong && !isChanging && CHONG[yongBranch] === z && ['旺','相'].includes(yongStrength)) {
    reasons.push({ type: '冲动应期', color: '#3498db', desc: `${z}日冲动用神` })
  }
  // 4. 合用神日（用神发动时应期）
  if (!isKong && isChanging && HE_LIU[yongBranch] === z) {
    reasons.push({ type: '合日应期', color: '#27ae60', desc: `${z}日合住用神` })
  }
  // 5. 三合用神日（半三合 → 全三合）
  if (!isKong && SANHE_PAIR[yongBranch]?.includes(z)) {
    reasons.push({ type: '三合', color: '#9b59b6', desc: `${z}日与${yongBranch}三合` })
  }
  // 6. 用神生扶日（衰弱时应期）
  // (需要根据五行算，简化处理)
  
  // 7. 同位（用神本支日，旺空可填实）
  if (!isKong && z === yongBranch && ['旺','相'].includes(yongStrength)) {
    reasons.push({ type: '本气日', color: '#16a085', desc: `${z}日用神本气` })
  }
  
  return reasons
}

// 把 ISO 日期格式化为 "6月30日 周二"
const WEEK = ['周日','周一','周二','周三','周四','周五','周六']
function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso + (iso.length <= 10 ? 'T00:00:00' : ''))
  if (isNaN(d)) return iso
  return `${d.getMonth() + 1}月${d.getDate()}日 ${WEEK[d.getDay()]}`
}

/**
 * 后端精确应期卡片 —— 优先展示古法精算结论（用神状态 → 候选地支 → 具体公历日）
 */
function BackendYingqiCard({ yq }) {
  if (!yq || !yq.available) return null
  const primary = yq.primary
  const cands = (yq.candidates || []).filter(c => (c.dates || []).length > 0)

  return (
    <div style={{ marginBottom: '0.85rem' }}>
      {/* 最可能应期 —— 主结论 */}
      {primary && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.7rem',
          padding: '0.6rem 0.8rem', marginBottom: '0.55rem',
          background: `linear-gradient(135deg, ${primary.color}1a, ${primary.color}08)`,
          border: `1px solid ${primary.color}55`,
          borderLeft: `3px solid ${primary.color}`,
          borderRadius: 'var(--r-sm)',
        }}>
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            minWidth: 62, padding: '0.2rem 0.4rem',
            background: `${primary.color}1a`, borderRadius: 'var(--r-sm)',
          }}>
            <span style={{ fontSize:'var(--text-lg)', fontWeight: 800, lineHeight: 1.1,
              color: primary.color, fontFamily: 'var(--font-display)' }}>
              {primary.ganzhi}
            </span>
            <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
              {primary.scope === '月' ? '应月' : `第${primary.days_ahead}日`}
            </span>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span style={{ fontSize:'var(--text-sm)', fontWeight: 700, color: 'var(--text-primary)' }}>
                最可能应期 · {fmtDate(primary.date)}
              </span>
              <span style={{
                fontSize:'var(--text-2xs)', padding: '1px 6px', borderRadius: '2px',
                background: `${primary.color}22`, color: primary.color,
                border: `1px solid ${primary.color}55`,
              }}>{primary.type}</span>
            </div>
            <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-secondary)',
              fontFamily: 'var(--font-serif)', lineHeight: 1.5, marginTop: '2px' }}>
              {primary.principle}
              <span style={{ color: 'var(--text-faint)' }}> —{primary.classic}</span>
            </div>
          </div>
        </div>
      )}

      {/* 用神状态 + 缓急 */}
      <div style={{
        display: 'flex', flexWrap: 'wrap', gap: '0.4rem 0.7rem', alignItems: 'center',
        fontSize:'var(--text-2xs)', color: 'var(--text-muted)',
        fontFamily: 'var(--font-serif)', marginBottom: '0.5rem',
      }}>
        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{yq.state_summary}</span>
        {yq.tempo && <span style={{ color: 'var(--text-faint)' }}>· {yq.tempo}</span>}
      </div>

      {/* 候选应期列表（精确公历日） */}
      {cands.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.28rem' }}>
          {cands.slice(0, 6).map((c, i) => {
            const d0 = c.dates[0]
            const more = c.dates[1]
            return (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '54px 1fr auto',
                gap: '0.5rem', alignItems: 'center',
                padding: '0.3rem 0.55rem',
                background: `${c.color}0d`,
                borderLeft: `2px solid ${c.color}`,
                borderRadius: 'var(--r-sm)', fontSize:'var(--text-xs)',
              }}>
                <span style={{ color: c.color, fontFamily: 'var(--font-display)',
                  fontWeight: 700 }}>{d0.ganzhi}{d0.scope}</span>
                <span style={{ color: 'var(--text-secondary)', overflow: 'hidden',
                  textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  <span style={{
                    display: 'inline-block', marginRight: '0.4rem', padding: '0 5px',
                    fontSize:'var(--text-2xs)', background: `${c.color}1a`, color: c.color,
                    border: `1px solid ${c.color}44`, borderRadius: '2px',
                  }}>{c.type}</span>
                  {fmtDate(d0.date)}
                  {more && <span style={{ color: 'var(--text-faint)' }}>
                    （次：{fmtDate(more.date)}）</span>}
                </span>
                <span style={{ color: 'var(--text-faint)', fontSize:'var(--text-2xs)',
                  whiteSpace: 'nowrap' }}>
                  {d0.scope === '月' ? '应月' : `${d0.days_ahead}日后`}
                </span>
              </div>
            )
          })}
        </div>
      )}

      <div style={{
        marginTop: '0.55rem', paddingTop: '0.45rem',
        borderTop: '1px dashed var(--border)',
        fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
        fontFamily: 'var(--font-serif)', fontStyle: 'italic',
      }}>
        以下为未来 60 天应期热图（辅助参考）
      </div>
    </div>
  )
}

export default function LiuyaoYingqiCalendar({ data }) {
  if (!data) return null
  
  const ta = data.topic_analysis || {}
  const yaos = data.yaos || []
  const yq = data.yingqi || {}   // 后端精确应期
  const yongShenName = ta.yong_shen_name
  const dayGan = data.day_gan || '甲'
  const dayZhi = data.day_zhi || '子'
  const kongList = data.kong_wang_branches || []
  
  // 找用神爻
  let yongYao = null
  if (yongShenName && yongShenName !== '世爻' && yongShenName !== '应爻') {
    yongYao = yaos.find(y => y.liu_qin === yongShenName)
  } else if (yongShenName === '世爻') {
    yongYao = yaos.find(y => y.is_world)
  } else if (yongShenName === '应爻') {
    yongYao = yaos.find(y => y.is_application)
  }
  
  // 前端热图依赖用神爻；若取不到但后端已精算，则只渲染后端精确卡片
  if (!yongYao) {
    if (yq.available) {
      return (
        <div className="card" style={{ padding: '0.85rem 1rem' }}>
          <div className="card-title" style={{ marginBottom: '0.6rem' }}>应期精算</div>
          <BackendYingqiCard yq={{ ...yq }} />
          <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
            fontFamily: 'var(--font-serif)', fontStyle: 'italic', textAlign: 'center' }}>
            {yq.verdict}
          </div>
        </div>
      )
    }
    return null
  }
  
  const yongBranch = yongYao.branch
  const yongElement = yongYao.element
  const yongStrength = yongYao.strength?.label
  const isKong = yongYao.kong_wang
  const isChanging = yongYao.is_changing
  
  // 生成 60 天
  const days = genDays(dayGan, dayZhi, 60)
  
  // 分析每天
  const annotated = days.map(d => ({
    ...d,
    yingqi: getYingqiType(d, yongBranch, yongElement, yongStrength, isKong, isChanging, kongList),
  }))
  
  // 提取关键应期日（前 10 个）
  const keyDays = annotated.filter(d => d.yingqi.length > 0).slice(0, 10)
  
  return (
    <div className="card" style={{ padding: '0.85rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <div className="card-title" style={{ marginBottom: 0 }}>应期日历 · 未来 60 天</div>
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontFamily: 'var(--font-serif)' }}>
          用神 {yongShenName}爻 {yongBranch} · {yongStrength}
          {isKong && <span style={{ color: '#e74c3c' }}> · 空</span>}
          {isChanging && <span style={{ color: '#d4a040' }}> · 动</span>}
        </div>
      </div>

      {/* 后端精确应期（优先展示） */}
      <BackendYingqiCard yq={yq} />

      {/* 60 天热图 */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(15, 1fr)', gap: '2px',
        marginBottom: '0.7rem',
      }}>
        {annotated.map((d, i) => {
          const intensity = d.yingqi.length
          const mainColor = d.yingqi[0]?.color || null
          return (
            <div key={i}
              title={`${i+1}日后 · ${d.ganzhi}${d.yingqi.length > 0 ? '\n' + d.yingqi.map(y => y.type + '：' + y.desc).join('\n') : ''}`}
              style={{
                aspectRatio: '1',
                background: mainColor ? `${mainColor}${intensity >= 2 ? 'cc' : '88'}` : 'var(--bg-subtle)',
                border: mainColor ? `1px solid ${mainColor}` : '1px solid var(--border)',
                borderRadius: '3px',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize:'var(--text-2xs)',
                fontFamily: 'var(--font-display)',
                color: mainColor ? '#fff' : 'var(--text-faint)',
                cursor: mainColor ? 'pointer' : 'default',
                fontWeight: mainColor ? 700 : 400,
              }}>
              {d.zhi}
            </div>
          )
        })}
      </div>
      
      {/* 关键应期列表 */}
      {keyDays.length > 0 ? (
        <div>
          <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '0.35rem', fontFamily: 'var(--font-serif)' }}>
            关键应期（最近 {keyDays.length} 个）：
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {keyDays.map((d, i) => (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '50px 70px 1fr',
                gap: '0.5rem', padding: '0.35rem 0.55rem',
                background: `${d.yingqi[0].color}11`,
                borderLeft: `3px solid ${d.yingqi[0].color}`,
                borderRadius: 'var(--r-sm)',
                fontSize:'var(--text-xs)',
              }}>
                <span style={{ color: 'var(--text-muted)' }}>
                  第{d.index + 1}日
                </span>
                <span style={{ color: d.yingqi[0].color, fontFamily: 'var(--font-display)', fontWeight: 700 }}>
                  {d.ganzhi}日
                </span>
                <span style={{ color: 'var(--text-secondary)' }}>
                  {d.yingqi.map(y => (
                    <span key={y.type} style={{
                      display: 'inline-block', marginRight: '0.4rem',
                      padding: '1px 5px', fontSize:'var(--text-2xs)',
                      background: `${y.color}22`, color: y.color,
                      border: `1px solid ${y.color}55`, borderRadius: '2px',
                    }}>
                      {y.type}
                    </span>
                  ))}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-faint)', fontFamily: 'var(--font-serif)', textAlign: 'center', padding: '0.5rem' }}>
          未来 60 天内无明显应期日，事态可能拖延或需长期等待
        </div>
      )}
      
      {/* 图例 */}
      <div style={{
        display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center',
        fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginTop: '0.6rem',
        padding: '0.3rem', background: 'var(--bg-subtle)', borderRadius: 'var(--r-sm)',
      }}>
        <span><span style={{ color: '#3498db', fontWeight: 700 }}>■</span> 冲动</span>
        <span><span style={{ color: '#27ae60', fontWeight: 700 }}>■</span> 合日</span>
        <span><span style={{ color: '#9b59b6', fontWeight: 700 }}>■</span> 三合</span>
        <span><span style={{ color: '#e67e22', fontWeight: 700 }}>■</span> 出空/冲空</span>
        <span><span style={{ color: '#16a085', fontWeight: 700 }}>■</span> 本气</span>
      </div>
      
      <div style={{
        marginTop: '0.5rem', padding: '0.35rem 0.6rem',
        background: 'rgba(212,160,64,0.04)', borderRadius: 'var(--r-sm)',
        fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
        fontFamily: 'var(--font-serif)', fontStyle: 'italic', lineHeight: 1.5,
      }}>
        《卜筮正宗》：用神旺相，逢冲之日动而应；用神发动，逢合之日合而应；
        用神空亡，待出空之日方应；用神入墓，须冲墓库之日。
      </div>
    </div>
  )
}
