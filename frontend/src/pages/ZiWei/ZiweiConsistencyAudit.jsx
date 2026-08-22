/*
 * ZiweiConsistencyAudit — 命盘一致性审核
 * 上层：确定性引擎检出的跨模块矛盾/张力（始终显示，按轻重着色）。
 * 下层：AI 审定意见（按需调用，明标「AI 辅助·不作准」，与确定性断语区分）。
 */
import React from 'react'
import AiInterpretPanel from '../../components/UI/AiInterpretPanel'

const SEV = {
  矛盾: { color: '#c0392b', bg: 'rgba(192,57,43,0.08)', icon: '⚠' },
  注意: { color: '#d4880a', bg: 'rgba(212,136,10,0.08)', icon: '◐' },
  提示: { color: 'var(--text-muted)', bg: 'var(--bg-raised)', icon: '·' },
}

export default function ZiweiConsistencyAudit({ data }) {
  const ca = data?.consistency_audit
  if (!ca || !ca.available) return null
  const s = ca.summary || {}
  const headColor = s.矛盾 > 0 ? '#c0392b' : s.注意 > 0 ? '#d4880a' : '#27ae60'

  return (
    <div className="card" style={{ borderLeft: `3px solid ${headColor}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
        flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.5rem' }}>
        <div className="card-title" style={{ margin: 0 }}>命盘一致性审核</div>
        <span style={{ display: 'flex', gap: '0.5rem', fontSize: 'var(--text-2xs)' }}>
          {s.矛盾 > 0 && <span style={{ color: SEV.矛盾.color }}>矛盾 {s.矛盾}</span>}
          {s.注意 > 0 && <span style={{ color: SEV.注意.color }}>注意 {s.注意}</span>}
          {s.提示 > 0 && <span style={{ color: 'var(--text-muted)' }}>提示 {s.提示}</span>}
          {ca.clean && <span style={{ color: '#27ae60' }}>✓ 协调一致</span>}
        </span>
      </div>

      <div style={{ fontSize: 'var(--text-sm)', color: headColor, fontFamily: 'var(--font-serif)',
        marginBottom: ca.findings?.length ? '0.6rem' : 0 }}>
        {ca.verdict}
      </div>

      {ca.findings?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
          {ca.findings.map((f, i) => {
            const sev = SEV[f.severity] || SEV.提示
            return (
              <div key={i} style={{ padding: '0.5rem 0.7rem', background: sev.bg,
                borderLeft: `2px solid ${sev.color}` }}>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'baseline', flexWrap: 'wrap' }}>
                  <span style={{ color: sev.color, fontWeight: 700, fontSize: 'var(--text-sm)',
                    fontFamily: 'var(--font-serif)' }}>{sev.icon} {f.title}</span>
                  <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)' }}>
                    〔{(f.modules || []).join(' × ')}〕
                  </span>
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)', lineHeight: 1.7, marginTop: '0.2rem' }}>{f.detail}</div>
                {f.suggestion && (
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)',
                    fontFamily: 'var(--font-serif)', lineHeight: 1.65, marginTop: '0.25rem',
                    paddingTop: '0.25rem', borderTop: '1px dashed var(--border)' }}>
                    论法：{f.suggestion}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {(s.矛盾 > 0 || s.注意 > 0 || s.提示 > 0) && (
        <div style={{ marginTop: '0.7rem' }}>
          <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-faint)', marginBottom: '0.3rem' }}>
            以下为 AI 辅助审定意见——对上述发现作取舍解释，仅供参考、不覆盖确定性断语
          </div>
          <AiInterpretPanel module="ziwei_audit" data={data} extraContext="命盘一致性审定" />
        </div>
      )}
    </div>
  )
}
