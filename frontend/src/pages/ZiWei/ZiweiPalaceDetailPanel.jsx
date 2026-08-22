/**
 * ZiweiPalaceDetailPanel.jsx
 * ============================
 * 完整的宫位详情面板 — 用户点击某宫后看到全部命理细节。
 *
 * 信息分区（命理师阅盘的标准顺序）：
 *   ① 宫位标识：宫名、宫干支、对宫名、命/身宫标记、大限/长生
 *   ② 星耀：主星（亮度+生年四化高亮）/ 辅星 / 煞星 / 调候星
 *   ③ 宫干飞化：本宫宫干起 4 化，分三类显示（离心/向心/普通飞宫）
 *      含关键语象标签：质能变 / 双忌叠加 / 禄解忌 / 禄忌交战 / 忌冲
 *   ④ 他宫飞入：哪些宫飞入本宫
 *   ⑤ 三方四正：本宫的命财官迁三方，对宫主星
 *
 * 数据来源：
 *   - palace 字段：iztro 排盘的宫位完整数据
 *   - insights.feihua_by_palace[idx]：Z-2 飞星派引擎每宫飞化记录
 *   - allPalaces：全 12 宫数据（用于三方四正查找）
 */
import React from 'react'

// 与 PalaceCell 一致的亮度色
const BRIGHT_COLOR = {
  '庙': '#c8a04a', '旺': '#f39c12', '得': '#3498db',
  '利': '#27ae60', '平': '#7f8c8d', '不': '#e67e22', '陷': '#e74c3c',
}

// 化象色（禄绿 权金 科蓝 忌红）
const HUA_COLOR = {
  '化禄': '#27ae60', '化权': '#c8a04a',
  '化科': '#3498db', '化忌': '#e74c3c',
}

// 飞化类型色（按强度）
const FH_TYPE_COLOR = {
  '离心自化': '#e67e22',
  '向心自化': '#9b59b6',
  '普通飞宫': '#3498db',
  '未排到':   '#95a5a6',
}

// 六煞、六吉（用于分类辅星）
const SIX_SHA = new Set(['擎羊', '陀罗', '火星', '铃星', '地空', '地劫'])
const SIX_JI  = new Set(['左辅', '右弼', '文昌', '文曲', '天魁', '天钺'])

// ─────────────────────────────────────────────────────────
// 工具
// ─────────────────────────────────────────────────────────
function classifyStars(allStars) {
  const sha = [], ji = [], lucun = [], tianma = [], other = []
  for (const s of (allStars || [])) {
    const nm = s.name
    if (SIX_SHA.has(nm))      sha.push(s)
    else if (SIX_JI.has(nm))  ji.push(s)
    else if (nm === '禄存')   lucun.push(s)
    else if (nm === '天马')   tianma.push(s)
    else other.push(s)
  }
  return { sha, ji, lucun, tianma, other }
}

// 三方四正 index：[本, +4, +8, +6 对宫]
function getSfszIndices(soulIdx) {
  return {
    self:    soulIdx,
    cai:     (soulIdx + 4) % 12,   // 财帛
    guan:    (soulIdx + 8) % 12,   // 官禄
    qian:    (soulIdx + 6) % 12,   // 迁移
  }
}

// ─────────────────────────────────────────────────────────
// ① 头部 — 宫名 + 干支 + 对宫 + 大限/流年宫名（Z-7）
// ─────────────────────────────────────────────────────────
function PalaceHeader({ palace, allPalaces, decadeLabel, annualLabel }) {
  const oppIdx = (palace.index + 6) % 12
  const oppPalace = (allPalaces || []).find(p => p.index === oppIdx)
  return (
    <div style={{
      marginBottom: '0.55rem', paddingBottom: '0.4rem',
      borderBottom: '1px solid var(--border)',
    }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.65rem', flexWrap: 'wrap' }}>
          <span style={{
            fontSize:'var(--text-xl)', fontWeight: 700,
            color: palace.is_soul ? 'var(--jade)' :
                   palace.is_body ? 'var(--cyan-b, #3498db)' :
                   'var(--text-primary)',
            fontFamily: 'var(--font-display)',
          }}>{palace.name}</span>
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)' }}>
            {palace.heavenly_stem}{palace.earthly_branch}
          </span>
          {palace.is_soul && <span style={{
            padding: '1px 6px', fontSize:'var(--text-2xs)', fontWeight: 700,
            color: 'var(--jade)', border: '1px solid var(--jade)',
          }}>命宫</span>}
          {palace.is_body && <span style={{
            padding: '1px 6px', fontSize:'var(--text-2xs)', fontWeight: 700,
            color: 'var(--cyan-b, #3498db)', border: '1px solid var(--cyan-b, #3498db)',
          }}>身宫</span>}
        </div>
        {oppPalace && (
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-faint)' }}>
            对宫 → {oppPalace.name}
          </div>
        )}
      </div>
      {/* Z-7: 大限/流年宫名徽章 */}
      {(decadeLabel || annualLabel) && (
        <div style={{ display: 'flex', gap: '6px', marginTop: '4px', flexWrap: 'wrap' }}>
          {decadeLabel && (
            <span style={{
              padding: '1px 7px', fontSize:'var(--text-2xs)', fontWeight: 600,
              color: '#9b59b6', background: 'rgba(155,89,182,0.08)',
              border: '1px solid rgba(155,89,182,0.35)',
            }}>{decadeLabel.name}</span>
          )}
          {annualLabel && (
            <span style={{
              padding: '1px 7px', fontSize:'var(--text-2xs)', fontWeight: 600,
              color: '#d35400', background: 'rgba(211,84,0,0.06)',
              border: '1px solid rgba(211,84,0,0.35)',
            }}>{annualLabel.name}</span>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// ② 星耀分区
// ─────────────────────────────────────────────────────────
function StarsSection({ palace }) {
  const majors = palace.major_stars || []
  const all_minor = palace.minor_stars || []
  const adj = palace.adj_stars || []
  const { sha, ji, lucun, tianma, other: otherMinor } = classifyStars(all_minor)

  return (
    <div style={{ marginBottom: '0.7rem' }}>
      {/* 主星 */}
      <div style={{ marginBottom: '0.45rem' }}>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
          主星
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
          {majors.length > 0 ? majors.map((s, i) => (
            <span key={i} style={{
              padding: '3px 9px', borderRadius: 0,
              background: 'var(--accent-bg)',
              color: BRIGHT_COLOR[s.brightness] || 'var(--accent)',
              border: `1px solid ${BRIGHT_COLOR[s.brightness] || 'var(--accent-dim)'}`,
              fontSize: 'var(--text-sm)', fontWeight: 700,
              display: 'inline-flex', alignItems: 'center', gap: '3px',
            }}>
              {s.name}
              {s.brightness && <span style={{ fontSize:'var(--text-2xs)' }}>({s.brightness})</span>}
              {s.mutagen && (
                <span style={{
                  marginLeft: '2px', padding: '0 3px',
                  fontSize:'var(--text-2xs)', fontWeight: 700,
                  background: HUA_COLOR[`化${s.mutagen}`] || 'var(--text-muted)',
                  color: '#fff',
                }}>化{s.mutagen}</span>
              )}
            </span>
          )) : (
            <span style={{ color: 'var(--text-faint)', fontSize: 'var(--text-sm)' }}>空宫（借对宫论）</span>
          )}
        </div>
      </div>

      {/* 星曜入宫详断（14主星×12宫库） */}
      {(palace.star_interpretations || []).length > 0 && (
        <div style={{ marginBottom: '0.55rem' }}>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
            星曜入{palace.name}·详断
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {palace.star_interpretations.map((si, i) => (
              <div key={i} style={{
                padding: '6px 9px', background: 'var(--bg-subtle)',
                borderLeft: '3px solid var(--accent)', borderRadius: 0,
              }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px',
                  flexWrap: 'wrap', marginBottom: '2px' }}>
                  <strong style={{ color: 'var(--accent)', fontSize: 'var(--text-sm)' }}>
                    {si.star}{si.brightness && `（${si.brightness}）`}
                  </strong>
                  <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
                    {si.info?.type} · {si.info?.zhu}
                  </span>
                  {si.brightness_tone && (
                    <span style={{ fontSize:'var(--text-2xs)', padding: '0 5px',
                      background: si.brightness_tone.includes('吉') ? 'rgba(39,174,96,0.12)' :
                        si.brightness_tone.includes('凶') ? 'rgba(192,57,43,0.12)' : 'var(--accent-bg)',
                      color: si.brightness_tone.includes('吉') ? '#27ae60' :
                        si.brightness_tone.includes('凶') ? '#c0392b' : 'var(--text-muted)',
                      borderRadius: '2px' }}>{si.brightness_tone}</span>
                  )}
                </div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)', lineHeight: 1.6 }}>{si.duan}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 双星组合断 */}
      {palace.palace_full?.double_star?.ming && (
        <div style={{ marginBottom: '0.55rem', padding: '7px 10px',
          background: 'rgba(212,160,64,0.08)', borderLeft: '3px solid var(--accent)' }}>
          <div style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--accent)',
            marginBottom: '2px', fontFamily: 'var(--font-display)' }}>
            ◇ {palace.palace_full.double_star.ming}
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)',
            fontFamily: 'var(--font-serif)', lineHeight: 1.65 }}>
            {palace.palace_full.double_star.duan}
          </div>
        </div>
      )}

      {/* 辅煞星效应 */}
      {(palace.palace_full?.aux || []).length > 0 && (
        <div style={{ marginBottom: '0.55rem' }}>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
            辅煞星·入{palace.name}效应
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {palace.palace_full.aux.map((a, i) => {
              const isJi = a.lei.includes('吉') || a.lei.includes('财') || a.lei === '动星'
              return (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '52px 1fr',
                  gap: '6px', alignItems: 'baseline', fontSize: 'var(--text-sm)' }}>
                  <span style={{ fontWeight: 700, fontSize:'var(--text-xs)',
                    color: isJi ? 'var(--jade)' : '#c0392b' }}>{a.star}</span>
                  <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)',
                    lineHeight: 1.55 }}>{a.effect}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 吉星 / 煞星 分类显示 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
        {/* 吉星 + 禄马 */}
        <div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '3px' }}>
            吉星 / 禄马
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
            {[...ji, ...lucun, ...tianma].map((s, i) => (
              <span key={i} style={{
                fontSize:'var(--text-2xs)', color: 'var(--jade)',
                background: 'rgba(74,122,90,0.08)',
                padding: '1px 5px', borderRadius: 0,
                display: 'inline-flex', alignItems: 'center', gap: '2px',
              }}>
                {s.name}
                {s.mutagen && (
                  <span style={{
                    padding: '0 2px',
                    background: HUA_COLOR[`化${s.mutagen}`] || 'var(--text-muted)',
                    color: '#fff', fontSize:'var(--text-2xs)',
                  }}>{s.mutagen}</span>
                )}
              </span>
            ))}
            {ji.length + lucun.length + tianma.length === 0 && (
              <span style={{ color: 'var(--text-faint)', fontSize:'var(--text-2xs)' }}>—</span>
            )}
          </div>
        </div>

        {/* 煞星 */}
        <div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '3px' }}>
            煞星
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
            {sha.map((s, i) => (
              <span key={i} style={{
                fontSize:'var(--text-2xs)', color: '#e74c3c',
                background: 'rgba(231,76,60,0.08)',
                padding: '1px 5px', borderRadius: 0,
              }}>
                {s.name}
              </span>
            ))}
            {sha.length === 0 && (
              <span style={{ color: 'var(--text-faint)', fontSize:'var(--text-2xs)' }}>—</span>
            )}
          </div>
        </div>
      </div>

      {/* 其他辅星 + 调候 */}
      {(otherMinor.length > 0 || adj.length > 0) && (
        <div style={{ marginTop: '0.4rem' }}>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '3px' }}>
            其他辅星 / 调候
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
            {[...otherMinor, ...adj].slice(0, 12).map((s, i) => (
              <span key={i} style={{
                fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
                background: 'var(--bg-subtle)',
                padding: '1px 4px', borderRadius: 0,
              }}>{s.name}</span>
            ))}
            {otherMinor.length + adj.length > 12 && (
              <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
                +{otherMinor.length + adj.length - 12}
              </span>
            )}
          </div>
        </div>
      )}

      {/* 大限 + 长生十二 */}
      <div style={{
        display: 'flex', gap: '1rem', marginTop: '0.5rem',
        paddingTop: '0.35rem', borderTop: '1px dashed var(--border)',
        fontSize: 'var(--text-xs)', color: 'var(--text-muted)',
      }}>
        {palace.decadal_range?.length === 2 && (
          <span>大限：{palace.decadal_range[0]}–{palace.decadal_range[1]}岁</span>
        )}
        {palace.changsheng12 && <span>长生：{palace.changsheng12}</span>}
        {palace.boshi12 && <span>博士：{palace.boshi12}</span>}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// ③ 宫干飞化（来自 insights.feihua_by_palace）
// ─────────────────────────────────────────────────────────
function FeihuaSection({ feihuaRecord, palace }) {
  if (!feihuaRecord || !feihuaRecord.transformations?.length) {
    return (
      <div style={{ marginBottom: '0.65rem' }}>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
          宫干飞化（飞星派）
        </div>
        <div style={{ color: 'var(--text-faint)', fontSize: 'var(--text-sm)' }}>
          （此宫飞化数据未生成，可能因 insights 字段未启用）
        </div>
      </div>
    )
  }

  return (
    <div style={{ marginBottom: '0.65rem' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
        宫干飞化（飞星派）— 宫干 <strong style={{ color: 'var(--text-primary)' }}>{feihuaRecord.stem}</strong> 起 4 化
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {feihuaRecord.transformations.map((tr, i) => {
          const huaColor = HUA_COLOR[tr.hua_type] || 'var(--text-secondary)'
          const fhTypeColor = FH_TYPE_COLOR[tr.fh_type] || 'var(--text-muted)'

          // 收集语象标签
          const tags = []
          if (tr.is_quality_change) tags.push({ text: '⚠ 质能变', color: '#e74c3c' })
          if (tr.is_double_ji)      tags.push({ text: '⚠ 双忌叠加', color: '#e74c3c' })
          if (tr.is_lu_ji_war)      tags.push({ text: '⚠ 禄忌交战', color: '#e67e22' })
          if (tr.is_he_won_ji)      tags.push({ text: '✦ 禄解忌', color: '#27ae60' })
          if (tr.chong_palace)      tags.push({ text: `冲${tr.chong_palace}`, color: '#e74c3c' })

          return (
            <div key={i} style={{
              padding: '5px 8px',
              background: 'var(--bg-subtle)',
              borderLeft: `3px solid ${fhTypeColor}`,
              fontSize: 'var(--text-sm)', lineHeight: 1.5,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span style={{
                  padding: '0 5px', fontSize:'var(--text-2xs)', fontWeight: 700,
                  background: huaColor, color: '#fff',
                }}>{tr.hua_type}</span>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{tr.target_star || '?'}</span>
                <span style={{ color: 'var(--text-muted)', fontSize:'var(--text-xs)' }}>→</span>
                <span style={{ color: 'var(--text-primary)' }}>
                  {tr.target_palace_name || '未排到'}
                </span>
                <span style={{
                  padding: '0 5px', fontSize:'var(--text-2xs)', fontWeight: 600,
                  color: fhTypeColor, border: `1px solid ${fhTypeColor}`,
                }}>{tr.fh_type}</span>
                {tr.target_palace_name && tr.fh_type !== '未排到' && (
                  <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
                    ({tr.is_inner ? '我宫' : '他宫'})
                  </span>
                )}
                {tags.map((t, ti) => (
                  <span key={ti} style={{
                    padding: '0 5px', fontSize:'var(--text-2xs)', fontWeight: 600,
                    color: t.color, background: `${t.color}15`,
                    border: `1px solid ${t.color}50`,
                  }}>{t.text}</span>
                ))}
              </div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {tr.interpretation}
              </div>
            </div>
          )
        })}
      </div>

      {/* 统计行 */}
      <div style={{
        marginTop: '0.4rem', fontSize: 'var(--text-xs)', color: 'var(--text-muted)',
        display: 'flex', gap: '0.75rem',
      }}>
        <span>离心自化 {feihuaRecord.self_out_count}</span>
        <span>向心自化 {feihuaRecord.self_in_count}</span>
        <span>普通飞宫 {feihuaRecord.fly_out_count}</span>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// ④ 他宫飞入本宫
// ─────────────────────────────────────────────────────────
function IncomingSection({ feihuaRecord }) {
  if (!feihuaRecord || !feihuaRecord.incoming_list?.length) {
    return null
  }
  return (
    <div style={{ marginBottom: '0.65rem' }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
        他宫飞入本宫（{feihuaRecord.incoming_list.length} 条）
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
        {feihuaRecord.incoming_list.map((inc, i) => {
          const huaColor = HUA_COLOR[inc.hua_type] || 'var(--text-secondary)'
          return (
            <div key={i} style={{
              padding: '3px 7px', background: 'var(--bg-subtle)',
              display: 'flex', alignItems: 'center', gap: '5px', flexWrap: 'wrap',
              fontSize: 'var(--text-sm)',
            }}>
              <span style={{ color: 'var(--text-muted)' }}>{inc.from_palace}</span>
              <span style={{
                padding: '0 4px', fontSize:'var(--text-2xs)', fontWeight: 700,
                background: huaColor, color: '#fff',
              }}>{inc.hua_type}</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{inc.star}</span>
              <span style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)' }}>→ 本宫</span>
              {inc.fh_type && inc.fh_type !== '普通飞宫' && (
                <span style={{
                  padding: '0 4px', fontSize:'var(--text-2xs)',
                  color: FH_TYPE_COLOR[inc.fh_type] || 'var(--text-muted)',
                  border: `1px solid ${FH_TYPE_COLOR[inc.fh_type] || 'var(--text-muted)'}`,
                }}>{inc.fh_type}</span>
              )}
              {inc.chong_palace && (
                <span style={{ fontSize:'var(--text-2xs)', color: '#e74c3c' }}>·冲{inc.chong_palace}</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// ⑤ 三方四正
// ─────────────────────────────────────────────────────────
function SanfangSizhengSection({ palace, allPalaces }) {
  if (!allPalaces?.length) return null
  const idxs = getSfszIndices(palace.index)
  const get = (i) => allPalaces.find(p => p.index === i)
  const pCai = get(idxs.cai), pGuan = get(idxs.guan), pQian = get(idxs.qian)

  const renderOne = (p, label) => {
    if (!p) return null
    const majors = (p.major_stars || []).map(s => `${s.name}${s.brightness ? `(${s.brightness})` : ''}`).join(' / ') || '空宫'
    return (
      <div style={{ padding: '4px 7px', background: 'var(--bg-subtle)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>{label}</span>
          <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>{p.name}（{p.earthly_branch}）</span>
        </div>
        <div style={{
          fontSize: 'var(--text-sm)', color: 'var(--text-primary)',
          fontFamily: 'var(--font-serif)', marginTop: '1px',
        }}>{majors}</div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '4px' }}>
        本宫三方四正
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '5px' }}>
        {renderOne(pCai, '财帛位')}
        {renderOne(pGuan, '官禄位')}
        {renderOne(pQian, '迁移位（对宫）')}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// ⑥ 大限/流年飞化（layer='decade' 或 'triple' 时显示）
// ─────────────────────────────────────────────────────────
function OverlayFeihuaSection({ palace, overlayInsights, layer }) {
  if (!overlayInsights || layer === 'natal') return null

  const decade = overlayInsights.decade
  const annual = overlayInsights.annual
  const palaceIdxStr = String(palace.index)

  // 取本宫接收的大限/流年化象
  const decadeIncoming = decade?.by_target_idx?.[palaceIdxStr] || []
  const annualIncoming = annual?.by_target_idx?.[palaceIdxStr] || []

  // 都没有则不渲染
  if (decadeIncoming.length === 0 && annualIncoming.length === 0) {
    // 显示一条提示，让用户知道这层飞化没飞到本宫
    return (
      <div style={{
        marginBottom: '0.65rem', padding: '5px 8px',
        background: 'var(--bg-subtle)', border: '1px dashed var(--border)',
        fontSize: 'var(--text-xs)', color: 'var(--text-faint)',
      }}>
        {layer === 'decade' ? '大限' : '大限/流年'}飞化未落入本宫
        {decade?.palace_name && ` · 大限命宫在【${decade.palace_name}】（干 ${decade.stem}）`}
        {layer === 'triple' && annual?.year && ` · 流年${annual.year}干${annual.stem}`}
      </div>
    )
  }

  const renderHuaList = (list, layerLabel, meta) => {
    if (list.length === 0) return null
    return (
      <div style={{ marginBottom: '0.4rem' }}>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: '3px' }}>
          {layerLabel}飞入本宫（共 {list.length} 化）
          {meta && <span style={{ marginLeft: '6px', fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>{meta}</span>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          {list.map((tr, i) => {
            const huaColor = HUA_COLOR[tr.hua_type] || 'var(--text-secondary)'
            const tags = []
            if (tr.is_he_won_ji) tags.push({ text: '✦ 禄解忌', color: '#27ae60' })
            if (tr.is_lu_ji_war) tags.push({ text: '⚠ 禄忌交战', color: '#e67e22' })
            if (tr.is_double_ji) tags.push({ text: '⚠ 双忌叠加', color: '#e74c3c' })
            if (tr.chong_palace) tags.push({ text: `冲${tr.chong_palace}`, color: '#e74c3c' })
            return (
              <div key={i} style={{
                padding: '4px 7px', background: 'var(--bg-subtle)',
                borderLeft: `3px solid ${huaColor}`,
                fontSize: 'var(--text-sm)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '0 5px', fontSize:'var(--text-2xs)', fontWeight: 700,
                    background: huaColor, color: '#fff',
                  }}>{tr.hua_type}</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{tr.target_star}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize:'var(--text-2xs)' }}>→ 本宫</span>
                  {tr.fh_type && tr.fh_type !== '普通飞宫' && (
                    <span style={{
                      padding: '0 5px', fontSize:'var(--text-2xs)',
                      color: FH_TYPE_COLOR[tr.fh_type] || 'var(--text-muted)',
                      border: `1px solid ${FH_TYPE_COLOR[tr.fh_type] || 'var(--text-muted)'}`,
                    }}>{tr.fh_type}</span>
                  )}
                  {tags.map((t, ti) => (
                    <span key={ti} style={{
                      padding: '0 5px', fontSize:'var(--text-2xs)', fontWeight: 600,
                      color: t.color, background: `${t.color}15`,
                      border: `1px solid ${t.color}50`,
                    }}>{t.text}</span>
                  ))}
                </div>
                {tr.interpretation && (
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    {tr.interpretation}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div style={{
      marginBottom: '0.65rem',
      padding: '0.5rem 0.65rem',
      background: 'rgba(155, 89, 182, 0.04)',
      border: '1px solid rgba(155, 89, 182, 0.2)',
    }}>
      <div style={{
        fontSize: 'var(--text-xs)', fontWeight: 700, marginBottom: '5px',
        color: '#9b59b6',
      }}>
        ▾ 运程层飞化（{layer === 'decade' ? '大限层' : '大限+流年层'}）
      </div>
      {renderHuaList(decadeIncoming, '大限',
        decade?.palace_name ? `命宫@${decade.palace_name} 干${decade.stem}` : null)}
      {layer === 'triple' && renderHuaList(annualIncoming, `流年${annual?.year || ''}`,
        annual?.stem ? `干${annual.stem}` : null)}
    </div>
  )
}

// ─────────────────────────────────────────────────────────
// 主组件
// ─────────────────────────────────────────────────────────
export default function ZiweiPalaceDetailPanel({
  palace,
  allPalaces,
  feihuaByPalace,
  layer = 'natal',           // 'natal' | 'decade' | 'triple'
  overlayInsights = null,    // 大限/三盘 overlay 数据
}) {
  if (!palace) return null
  const feihuaRecord = feihuaByPalace ? feihuaByPalace[String(palace.index)] : null

  // Z-7: 提取当前宫的大限/流年宫名
  const decadeLayout = (layer === 'decade' || layer === 'triple')
    ? overlayInsights?.decade?.palaces_layout
    : null
  const annualLayout = (layer === 'triple')
    ? overlayInsights?.annual?.palaces_layout
    : null
  const decadeLabel = decadeLayout ? decadeLayout[palace.index] : null
  const annualLabel = annualLayout ? annualLayout[palace.index] : null

  return (
    <div className="card card-glow" style={{
      marginTop: '0.85rem',
      padding: '0.85rem 1rem',
    }}>
      <PalaceHeader
        palace={palace}
        allPalaces={allPalaces}
        decadeLabel={decadeLabel}
        annualLabel={annualLabel}
      />
      <StarsSection palace={palace} />
      <FeihuaSection feihuaRecord={feihuaRecord} palace={palace} />
      <IncomingSection feihuaRecord={feihuaRecord} />
      <OverlayFeihuaSection palace={palace} overlayInsights={overlayInsights} layer={layer} />
      <SanfangSizhengSection palace={palace} allPalaces={allPalaces} />
    </div>
  )
}
