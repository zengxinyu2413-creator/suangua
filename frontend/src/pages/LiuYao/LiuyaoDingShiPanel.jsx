/**
 * LiuyaoDingShiPanel.jsx — 六爻·卦定式
 *
 * 选一卦（1-64）+ 性别，展示：
 *   ① 装卦定式（六爻纳甲地支/五行/六亲/世应）
 *   ② 世爻六亲持世断
 *   ③ 六爻六亲分类应事断（求财/婚姻/求官/考试/求子/失物/疾病/官讼…）
 */
import React, { useState, useEffect } from 'react'
import { liuyaoApi } from '../../api/client'

const QIN_COLOR = {
  父母: '#8e44ad', 兄弟: '#e67e22', 子孙: '#27ae60', 妻财: '#f1c40f', 官鬼: '#c0392b',
}
const ROLE_COLOR = {
  '★用神': '#c0392b', '○吉助': '#27ae60', '○吉护': '#16a085',
  '✕忌动': '#c0392b', '△慎': '#e67e22',
}
function qColor(q) {
  if (!q) return 'var(--text-muted)'
  if (q.startsWith('★') || q.startsWith('○')) return '#27ae60'
  if (q.startsWith('✕')) return '#c0392b'
  if (q.startsWith('△')) return '#e67e22'
  return 'var(--text-secondary)'
}

export default function LiuyaoDingShiPanel() {
  const [num, setNum] = useState(1)
  const [gender, setGender] = useState('male')
  const [data, setData] = useState(null)
  const [catalog, setCatalog] = useState([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    liuyaoApi.guaCatalog().then(d => setCatalog(d.data || d)).catch(() => {})
  }, [])

  const load = async (n, g) => {
    setLoading(true); setErr('')
    try {
      const r = await liuyaoApi.guaStatic(n, g)
      setData(r.data || r)
    } catch (e) {
      setErr('加载失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { load(num, gender) }, [num, gender])

  const zg = data?.zhuang_gua
  const cs = data?.chi_shi
  const ys = data?.yao_yingshi

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* 选卦 + 性别 */}
      <div className="card">
        <div className="card-title">卦定式 · 装卦 / 持世 / 应事</div>
        <div style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
          fontFamily: 'var(--font-serif)', marginBottom: '0.7rem', lineHeight: 1.5 }}>
          火珠林纳甲法：六爻应事不主周易爻辞，而主纳甲六亲之生克持值。下断由卦象定式生成，不依摇卦日辰。
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.6rem' }}>
          <span style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)' }}>选卦：</span>
          <select value={num} onChange={e => setNum(parseInt(e.target.value))}
            style={{ flex: 1, fontSize:'var(--text-xs)', padding: '4px 8px', borderRadius: 'var(--r-sm)',
              border: '1px solid var(--border)', background: 'var(--bg-subtle)', color: 'var(--text-secondary)' }}>
            {(catalog.length ? catalog : Array.from({ length: 64 }, (_, i) => ({ number: i + 1, name: '' }))).map(h => (
              <option key={h.number} value={h.number}>
                第{h.number}卦 {h.name}{h.world_liu_qin ? `（${h.world_liu_qin}持世）` : ''}
              </option>
            ))}
          </select>
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            {[['male', '男占'], ['female', '女占']].map(([g, lbl]) => (
              <button key={g} onClick={() => setGender(g)}
                style={{ padding: '4px 10px', borderRadius: 'var(--r-sm)', cursor: 'pointer', fontSize:'var(--text-xs)',
                  border: gender === g ? '1.5px solid var(--accent)' : '1px solid var(--border)',
                  background: gender === g ? 'rgba(212,160,64,0.12)' : 'var(--bg-subtle)',
                  color: gender === g ? 'var(--accent)' : 'var(--text-faint)' }}>{lbl}</button>
            ))}
          </div>
        </div>
        {err && <div style={{ color: '#c0392b', fontSize:'var(--text-xs)' }}>{err}</div>}
        {loading && <div style={{ color: 'var(--text-faint)', fontSize:'var(--text-xs)' }}>加载中…</div>}
      </div>

      {/* ① 装卦定式 */}
      {zg && zg.success && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
            <div className="card-title" style={{ marginBottom: 0 }}>{zg.gua_name}卦 · 装卦定式</div>
            <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', fontFamily: 'var(--font-serif)' }}>
              {zg.palace}宫·{zg.gua_type} · 世{zg.world_line}应{zg.application_line}
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column-reverse', gap: '3px' }}>
            {zg.rows.map(r => {
              const col = QIN_COLOR[r.liu_qin] || '#888'
              return (
                <div key={r.position} style={{ display: 'grid',
                  gridTemplateColumns: '40px 64px 1fr 40px', gap: '0.5rem', alignItems: 'center',
                  padding: '0.3rem 0.5rem', borderRadius: 'var(--r-sm)',
                  background: r.shi_ying ? 'rgba(212,160,64,0.08)' : 'var(--bg-subtle)',
                  border: r.shi_ying ? '1px solid rgba(212,160,64,0.3)' : '1px solid transparent' }}>
                  <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>{r.name}</span>
                  <span style={{ fontSize:'var(--text-xs)', fontWeight: 700, color: col, fontFamily: 'var(--font-serif)' }}>
                    {r.liu_qin}
                  </span>
                  <span style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)', fontFamily: 'var(--font-display)' }}>
                    {r.zhi}{r.wuxing}
                  </span>
                  <span style={{ fontSize:'var(--text-xs)', fontWeight: 800,
                    color: r.shi_ying === '世' ? 'var(--accent)' : r.shi_ying === '应' ? '#2980b9' : 'transparent' }}>
                    {r.shi_ying}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ② 持世断 */}
      {cs && cs.world_liu_qin && (
        <div className="card" style={{ borderLeft: `4px solid ${QIN_COLOR[cs.world_liu_qin] || 'var(--accent)'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
            <div className="card-title" style={{ marginBottom: 0 }}>世爻持世断</div>
            <span style={{ fontSize:'var(--text-xs)', fontWeight: 700, color: QIN_COLOR[cs.world_liu_qin],
              fontFamily: 'var(--font-display)' }}>{cs.world_liu_qin}持世</span>
          </div>
          {cs.kou_jue && (
            <div style={{ fontSize:'var(--text-xs)', color: 'var(--accent)', fontFamily: 'var(--font-serif)',
              lineHeight: 1.7, marginBottom: '0.4rem', fontStyle: 'italic' }}>「{cs.kou_jue}」</div>
          )}
          <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)',
            lineHeight: 1.65, marginBottom: '0.35rem' }}>{cs.jie_xi}</div>
          <div style={{ fontSize:'var(--text-xs)', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)',
            lineHeight: 1.55 }}>{cs.pos_note}</div>
        </div>
      )}

      {/* ③ 六爻分类应事断 */}
      {ys && ys.lines && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
            <div className="card-title" style={{ marginBottom: 0 }}>六爻 · 分类应事断</div>
            <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)' }}>
              {ys.gender === 'female' ? '女占' : '男占'} · 用神—元神—忌神—仇神—制忌
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column-reverse', gap: '0.5rem' }}>
            {ys.lines.map(ln => {
              const col = QIN_COLOR[ln.liu_qin] || '#888'
              return (
                <div key={ln.position} style={{ padding: '0.5rem 0.6rem', borderRadius: 'var(--r-sm)',
                  background: `${col}0d`, borderLeft: `3px solid ${col}` }}>
                  <div style={{ fontSize:'var(--text-xs)', fontWeight: 700, color: 'var(--text-secondary)',
                    fontFamily: 'var(--font-serif)', marginBottom: '0.3rem' }}>
                    {ln.name}　<span style={{ color: col }}>{ln.liu_qin}</span> {ln.zhi}{ln.wuxing}
                    {ln.shi_ying && <span style={{ color: 'var(--accent)', marginLeft: '4px' }}>·{ln.shi_ying}</span>}
                    <span style={{ fontSize:'var(--text-2xs)', color: 'var(--text-faint)', marginLeft: '6px', fontWeight: 400 }}>
                      {ln.liu_qin_meaning}
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                    {ln.topics.map((t, i) => (
                      <span key={i} title={t.desc}
                        style={{ fontSize:'var(--text-2xs)', padding: '1px 6px', borderRadius: '3px',
                          background: 'var(--bg-subtle)', border: `1px solid ${qColor(t.quality)}33`,
                          color: qColor(t.quality), cursor: 'help' }}>
                        {t.label}<b style={{ marginLeft: '2px' }}>{t.quality}</b>
                      </span>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
          <div style={{ marginTop: '0.5rem', fontSize:'var(--text-2xs)', color: 'var(--text-faint)',
            fontFamily: 'var(--font-serif)', fontStyle: 'italic', lineHeight: 1.5 }}>
            悬停标签可见详断。爻位自下而上（初→上）。应事吉凶由该爻六亲对各事用神之五神角色而定。
          </div>
        </div>
      )}
    </div>
  )
}
