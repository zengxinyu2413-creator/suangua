/**
 * ZiweiSchoolPanel.jsx — 紫微派别专属解读面板
 *
 * 三派各有不同的命理学方法论，每派的解读重点不同：
 *
 *   三合派（紫云/正统）：看主星组合 + 三方四正格局 + 煞星会照
 *   飞星派（钦天/河洛）：看宫干飞化 + 自化 + 飞化网络的吉凶交战
 *   四化派（钦天四化）：看生年四化落宫 + 来因宫 + 命迁财官的禀赋
 *
 * 这个组件不重复任何已有信息，只呈现"该派别独有的解读"。
 */
import React from 'react'

// ──────────────────────────────────────────────────────
// 三合派面板：主星组合 + 三方四正格局 + 煞星会照分析
// ──────────────────────────────────────────────────────
function SanhePanel({ palaces, insights, soulIdx }) {
  if (!palaces || palaces.length < 12) return null

  const soul   = palaces[soulIdx] || palaces.find(p => p.is_soul) || palaces[1]
  const wealth = palaces[(soulIdx + 8) % 12]   // 财帛宫
  const career = palaces[(soulIdx + 4) % 12]   // 官禄宫
  const migrate = palaces[(soulIdx + 6) % 12]  // 迁移宫
  const four = [
    { label: '命宫', p: soul,   color: '#c0392b' },
    { label: '财帛', p: wealth, color: '#27ae60' },
    { label: '官禄', p: career, color: '#2980b9' },
    { label: '迁移', p: migrate, color: '#8e44ad' },
  ]

  // 判断煞星会照（六煞：火铃羊陀空劫）
  const SHA_STARS = ['火星','铃星','擎羊','陀罗','地空','地劫']
  const shaInSanfang = []
  for (const { label, p } of four) {
    const shas = (p.minor_stars || []).filter(s => SHA_STARS.includes(s.name))
    if (shas.length > 0) {
      shaInSanfang.push({ palace: label, stars: shas.map(s => s.name) })
    }
  }

  // 主星组合（关键看命宫）
  const soulMajors = (soul.major_stars || []).map(s => `${s.name}(${s.brightness || '?'})`)

  return (
    <div className="card" style={{ padding: '0.85rem 1rem', borderLeft: '3px solid #f39c12' }}>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: '#d35400', marginBottom: '0.5rem' }}>
        三合派解读 · 三方四正格局分析
      </div>

      {/* 主星组合 */}
      <div style={{ marginBottom: '0.6rem', fontSize: 'var(--text-sm)', lineHeight: 1.6 }}>
        <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '2px' }}>命宫主星组合</div>
        <div>
          <strong style={{ color: '#c0392b' }}>{soulMajors.length > 0 ? soulMajors.join(' + ') : '空宫'}</strong>
          <span style={{ color: 'var(--text-faint)', marginLeft: '8px' }}>
            {soulMajors.length === 0 ? '空宫借对宫看' :
             soulMajors.length === 2 ? '双主同宫，论格局须合参' : '单一主星，本宫主导明确'}
          </span>
        </div>
      </div>

      {/* 三方四正 4 宫 */}
      <div style={{ marginBottom: '0.6rem' }}>
        <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
          三方四正（命/财/官/迁 — 三合派核心格局观察点）
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
          {four.map(({ label, p, color }) => (
            <div key={label} style={{
              padding: '6px 7px',
              border: `1px solid ${color}33`,
              background: `${color}06`,
              fontSize:'var(--text-2xs)',
              lineHeight: 1.4,
            }}>
              <div style={{ color, fontWeight: 700 }}>{label}（{p.heavenly_stem}{p.earthly_branch}）</div>
              <div style={{ color: 'var(--text-primary)', marginTop: '2px' }}>
                {(p.major_stars || []).length > 0
                  ? (p.major_stars).map(s => s.name).join('·')
                  : <span style={{ color: 'var(--text-faint)' }}>空宫</span>}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 经典格局（来自后端 patterns） */}
      {insights?.patterns && (insights.patterns.good?.length > 0 || insights.patterns.bad?.length > 0) && (
        <div style={{ marginBottom: '0.6rem' }}>
          <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
            经典格局（三合派核心评断依据）
          </div>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {(insights.patterns.good || []).map((g, i) => (
              <span key={`g-${i}`} style={{
                fontSize:'var(--text-xs)', padding: '3px 8px',
                background: 'rgba(39,174,96,0.1)', color: '#27ae60',
                border: '1px solid #27ae60', fontWeight: 600,
              }}>{g.name}</span>
            ))}
            {(insights.patterns.bad || []).map((g, i) => (
              <span key={`b-${i}`} style={{
                fontSize:'var(--text-xs)', padding: '3px 8px',
                background: 'rgba(231,76,60,0.1)', color: '#e74c3c',
                border: '1px solid #e74c3c', fontWeight: 600,
              }}>{g.name}</span>
            ))}
          </div>
        </div>
      )}

      {/* 煞星会照分析 */}
      <div>
        <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
          煞星会照（六煞星：火铃羊陀空劫，三合派论凶之关键）
        </div>
        {shaInSanfang.length === 0 ? (
          <div style={{ fontSize:'var(--text-xs)', color: '#27ae60' }}>
            ✓ 三方四正无煞星会照，格局清纯
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {shaInSanfang.map((s, i) => (
              <div key={i} style={{ fontSize:'var(--text-xs)', color: '#8e44ad' }}>
                ⚠ {s.palace}宫见 {s.stars.join('、')}
                <span style={{ color: 'var(--text-faint)', marginLeft: '6px' }}>
                  {s.stars.length >= 2 ? '双煞冲撞，需化解' : '单煞，可论增气或减分'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────
// 飞星派面板：宫干飞化路径 + 自化分析
// ──────────────────────────────────────────────────────
function FeixingPanel({ insights, feihuaChains }) {
  const summary = insights?.feihua_summary
  if (!summary && !feihuaChains?.available) return null
  const safeSummary = summary || {}

  // 自化宫位（离心 + 向心）
  const selfOutPalaces = safeSummary.self_out_palaces || []
  const selfInPalaces  = safeSummary.self_in_palaces || []

  // 质能变（生年化 + 自化 同宫位）— 飞星派最强语象
  const qcList = safeSummary.quality_changes || []

  // 禄忌交战
  const luJiWar = safeSummary.lu_ji_war || []

  // 命宫飞入
  const soulIncoming = safeSummary.soul_incoming || []

  // 双忌叠加 + 命宫被冲
  const doubleJi = safeSummary.double_ji || []
  const soulChong = safeSummary.soul_chong || []

  return (
    <div className="card" style={{ padding: '0.85rem 1rem', borderLeft: '3px solid #9b59b6' }}>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: '#7d3c98', marginBottom: '0.5rem' }}>
        飞星派解读 · 宫干四化网络与自化
      </div>

      {/* 自化分析 */}
      <div style={{ marginBottom: '0.6rem' }}>
        <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
          自化（飞星派最重要的命理结构）
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div style={{ padding: '6px 8px', background: 'rgba(231,76,60,0.05)',
            border: '1px solid rgba(231,76,60,0.3)' }}>
            <div style={{ fontSize:'var(--text-2xs)', color: '#c0392b', fontWeight: 600 }}>
              离心自化（{selfOutPalaces.length} 宫）
            </div>
            <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
              本宫干使本宫星化：能量喷散、本宫之事过度操作
            </div>
            {selfOutPalaces.length > 0 && (
              <div style={{ fontSize:'var(--text-xs)', marginTop: '4px', color: 'var(--text-primary)' }}>
                {selfOutPalaces.map(p => p.palace || p).join('、')}
              </div>
            )}
          </div>
          <div style={{ padding: '6px 8px', background: 'rgba(52,152,219,0.05)',
            border: '1px solid rgba(52,152,219,0.3)' }}>
            <div style={{ fontSize:'var(--text-2xs)', color: '#2980b9', fontWeight: 600 }}>
              向心自化（{selfInPalaces.length} 宫）
            </div>
            <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
              对宫干使本宫星化：能量内收、来自对宫的影响
            </div>
            {selfInPalaces.length > 0 && (
              <div style={{ fontSize:'var(--text-xs)', marginTop: '4px', color: 'var(--text-primary)' }}>
                {selfInPalaces.map(p => p.palace || p).join('、')}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 质能变（飞星派最强语象） */}
      {qcList.length > 0 && (
        <div style={{ marginBottom: '0.6rem' }}>
          <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
            质能变（生年四化 + 自化同宫 — 事必发生）
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {qcList.map((q, i) => (
              <div key={i} style={{
                fontSize:'var(--text-xs)', color: 'var(--text-primary)',
                padding: '3px 7px',
                background: 'rgba(243,156,18,0.06)',
                borderLeft: '2px solid #f39c12',
              }}>
                ◆ <strong>{q.palace}</strong>：{q.star} {q.hua}（{q.fh_type}）
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 禄忌交战 */}
      {luJiWar.length > 0 && (
        <div style={{ marginBottom: '0.6rem' }}>
          <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
            禄忌交战（化忌入本命化禄宫 — 虚禄财损）
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            {luJiWar.map((w, i) => (
              <div key={i} style={{ fontSize:'var(--text-xs)', color: '#e74c3c' }}>
                ⚠ {w.from} 化忌{w.star} → {w.to}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 命宫飞入 */}
      {soulIncoming.length > 0 && (
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
            命宫飞入（{soulIncoming.length} 条 — 一生格局之根）
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '3px' }}>
            {soulIncoming.slice(0, 8).map((i, idx) => (
              <div key={idx} style={{ fontSize:'var(--text-2xs)', color: 'var(--text-secondary)' }}>
                · {i.from} {i.hua}{i.star} → 命
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 飞化链路 · 多步串联 */}
      {feihuaChains?.available && (
        <div style={{ marginTop: '0.7rem', paddingTop: '0.6rem', borderTop: '1px dashed var(--border)' }}>
          <div style={{ color: '#7d3c98', fontSize:'var(--text-xs)', fontWeight: 700, marginBottom: '6px' }}>
            飞化链路 · 多步串联（飞星派网络）
          </div>
          {feihuaChains.birth_chain?.map((b, i) => (
            <div key={'b'+i} style={{ fontSize:'var(--text-2xs)', color: '#c0392b', lineHeight: 1.7,
              fontFamily: 'var(--font-serif)', marginBottom: '3px' }}>◆ {b.desc}</div>
          ))}
          {feihuaChains.ji_chains?.slice(0,2).map((c, i) => (
            <div key={'j'+i} style={{ fontSize:'var(--text-2xs)', color: 'var(--text-secondary)', lineHeight: 1.7,
              fontFamily: 'var(--font-serif)', marginBottom: '3px' }}>
              <span style={{ color:'#c0392b' }}>忌</span> {c.names.join(' → ')}{c.is_cycle?' ⟳':''}
            </div>
          ))}
          {feihuaChains.lu_chains?.slice(0,1).map((c, i) => (
            <div key={'l'+i} style={{ fontSize:'var(--text-2xs)', color: 'var(--text-secondary)', lineHeight: 1.7,
              fontFamily: 'var(--font-serif)', marginBottom: '3px' }}>
              <span style={{ color:'#27ae60' }}>禄</span> {c.names.join(' → ')}
            </div>
          ))}
          {feihuaChains.mutual?.filter(m => m.nature !== '中').slice(0,3).map((m, i) => (
            <div key={'m'+i} style={{ fontSize:'var(--text-2xs)',
              color: m.nature==='吉'?'#27ae60':'#c0392b', lineHeight: 1.7,
              fontFamily: 'var(--font-serif)', marginBottom: '3px' }}>⇄ {m.desc}</div>
          ))}
          {feihuaChains.focus?.slice(0,1).map((f, i) => (
            <div key={'f'+i} style={{ fontSize:'var(--text-2xs)', color: 'var(--accent)', lineHeight: 1.7,
              fontFamily: 'var(--font-serif)', marginTop: '3px' }}>◈ {f.desc}</div>
          ))}
        </div>
      )}
    </div>
  )
}

// ──────────────────────────────────────────────────────
// 四化派面板：生年四化禄权科忌落宫
// ──────────────────────────────────────────────────────
function SihuaPanel({ palaces, soulIdx, baziOverlay, birthSihua }) {
  if (!palaces || palaces.length < 12) return null

  // 找出含生年四化的星（main_stars 中 mutagen 字段）
  const sihuaMap = { '禄': null, '权': null, '科': null, '忌': null }
  for (const p of palaces) {
    for (const s of (p.major_stars || [])) {
      if (s.mutagen && sihuaMap.hasOwnProperty(s.mutagen)) {
        sihuaMap[s.mutagen] = { star: s.name, palace: p.name, palaceIdx: p.index,
                                stem: p.heavenly_stem, branch: p.earthly_branch }
      }
    }
    // 也看辅星（左辅右弼文昌文曲可能含化禄/权/科/忌）
    for (const s of (p.minor_stars || [])) {
      if (s.mutagen && sihuaMap.hasOwnProperty(s.mutagen) && !sihuaMap[s.mutagen]) {
        sihuaMap[s.mutagen] = { star: s.name, palace: p.name, palaceIdx: p.index,
                                stem: p.heavenly_stem, branch: p.earthly_branch }
      }
    }
  }

  // 来因宫：四化派理论 — 生年天干所在宫位
  const yearStem = baziOverlay?.sizhu_jieqi?.year?.[0]
  let laiyinPalace = null
  if (yearStem) {
    for (const p of palaces) {
      if (p.heavenly_stem === yearStem) {
        laiyinPalace = p
        break
      }
    }
  }

  // 四化派核心解读：12 宫位关键性
  const PALACE_MEANING = {
    '命宫':   '本人禀赋',  '兄弟宫': '兄弟手足',  '夫妻宫': '配偶感情',
    '子女宫': '子女创意',  '财帛宫': '财运现金',  '疾厄宫': '健康身体',
    '迁移宫': '外出际遇',  '交友宫': '朋友合伙',  '官禄宫': '事业地位',
    '田宅宫': '家宅产业',  '福德宫': '精神享受',  '父母宫': '父母长辈',
  }

  const HUA_INFO = {
    '禄': { color: '#27ae60', label: '化禄', desc: '此宫为先天财气与福气所在' },
    '权': { color: '#f39c12', label: '化权', desc: '此宫为先天主导力与才能所在' },
    '科': { color: '#2980b9', label: '化科', desc: '此宫为先天贵人名声所在' },
    '忌': { color: '#e74c3c', label: '化忌', desc: '此宫为先天执念与功课所在' },
  }

  return (
    <div className="card" style={{ padding: '0.85rem 1rem', borderLeft: '3px solid #e74c3c' }}>
      <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: '#c0392b', marginBottom: '0.5rem' }}>
        四化派解读 · 生年四化（先天禀赋）
      </div>
      <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-muted)', marginBottom: '0.6rem', lineHeight: 1.5 }}>
        四化派核心理论：出生年天干所触发的禄权科忌，落入哪四个宫位，
        即决定了一个人**与生俱来的运势重心**。这四宫不会因大限流年而改变。
      </div>

      {/* 4 化落宫 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px', marginBottom: '0.6rem' }}>
        {Object.entries(HUA_INFO).map(([hua, info]) => {
          const data = sihuaMap[hua]
          return (
            <div key={hua} style={{
              padding: '7px 7px',
              border: `2px solid ${info.color}`,
              background: `${info.color}0a`,
              textAlign: 'center',
            }}>
              <div style={{ fontSize:'var(--text-xs)', fontWeight: 700, color: info.color }}>
                {info.label}
              </div>
              {data ? (
                <>
                  <div style={{ fontSize:'var(--text-sm)', fontWeight: 700, color: 'var(--text-primary)', marginTop: '3px' }}>
                    {data.star}
                  </div>
                  <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    入{data.palace}
                  </div>
                  <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginTop: '1px' }}>
                    {PALACE_MEANING[data.palace]}
                  </div>
                </>
              ) : (
                <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginTop: '6px' }}>—</div>
              )}
            </div>
          )
        })}
      </div>

      {/* 解读：4 化所代表的人生主线 */}
      <div style={{ marginBottom: '0.6rem' }}>
        <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
          先天命运重心（四化派论命主线）
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {Object.entries(HUA_INFO).map(([hua, info]) => {
            const data = sihuaMap[hua]
            if (!data) return null
            return (
              <div key={hua} style={{ fontSize:'var(--text-xs)', lineHeight: 1.5,
                paddingLeft: '8px', borderLeft: `2px solid ${info.color}` }}>
                <strong style={{ color: info.color }}>{info.label}入{data.palace}</strong>
                <span style={{ color: 'var(--text-muted)' }}> — {info.desc.replace('此宫', PALACE_MEANING[data.palace])}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* 来因宫 */}
      {laiyinPalace && (
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
            来因宫（四化派钦天理论 — 生年天干所在宫位，是命主因果之源）
          </div>
          <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-primary)',
            padding: '4px 8px', background: 'rgba(155,89,182,0.05)',
            borderLeft: '2px solid #9b59b6' }}>
            <strong>{yearStem}</strong> 干坐 <strong>{laiyinPalace.name}</strong>
            <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>
              ← 命主此生因果起于「{PALACE_MEANING[laiyinPalace.name] || laiyinPalace.name}」
            </span>
          </div>
        </div>
      )}

      {/* 禄忌格局（飞星派重象，来自后端 birth_sihua） */}
      {birthSihua?.lu_ji_geju && (
        <div>
          <div style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)', marginBottom: '4px' }}>
            禄忌格局（生年禄忌之牵系 — 飞星派论福祸相依之象）
          </div>
          <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-primary)',
            padding: '4px 8px', background: 'rgba(212,160,64,0.06)',
            borderLeft: '2px solid var(--accent)', lineHeight: 1.7,
            fontFamily: 'var(--font-serif)' }}>
            {birthSihua.lu_ji_geju}
          </div>
        </div>
      )}
    </div>
  )
}

// ──────────────────────────────────────────────────────
// 总入口
// ──────────────────────────────────────────────────────
export default function ZiweiSchoolPanel({ school, palaces, insights, soulIdx, baziOverlay, birthSihua, feihuaChains }) {
  if (school === 'sanhe') {
    return <SanhePanel palaces={palaces} insights={insights} soulIdx={soulIdx} />
  } else if (school === 'feixing') {
    return <FeixingPanel insights={insights} feihuaChains={feihuaChains} />
  } else if (school === 'sihua') {
    return <SihuaPanel palaces={palaces} soulIdx={soulIdx} baziOverlay={baziOverlay} birthSihua={birthSihua} />
  }
  return null
}
