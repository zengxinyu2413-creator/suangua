/**
 * ClassicalCompendiumPanel.jsx — 典籍精读专区
 *
 * 展示 10 大命理学典籍的深度内容：
 *   - 历史背景
 *   - 核心思想
 *   - 主要章节（含原文 + 释义）
 *   - 核心名句
 *   - 学习路径
 *   - 现代价值
 */
import React, { useState, useEffect } from 'react'

const getApiBase = () => {
  try {
    return JSON.parse(localStorage.getItem('bagua-settings') || '{}')?.state?.apiBaseUrl ?? ''
  } catch {
    return ''
  }
}

export default function ClassicalCompendiumPanel() {
  const [list, setList] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    fetch(getApiBase() + '/api/v1/knowledge/compendium/list')
      .then(r => r.json())
      .then(j => setList(j.data || []))
      .catch(e => console.error(e))
  }, [])
  
  const openBook = async (id) => {
    setSelectedId(id)
    setLoading(true)
    try {
      const r = await fetch(getApiBase() + '/api/v1/knowledge/compendium/' + id)
      const j = await r.json()
      setDetail(j.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div style={{ padding: '1rem 0' }}>
      <div style={{ marginBottom: '1.2rem' }}>
        <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent)',
          fontFamily: 'var(--font-serif)', marginBottom: '0.3rem' }}>
          📚 典籍精读
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-serif)', lineHeight: 1.65 }}>
          十大命理学典籍的深度精读，每本含历史背景、核心思想、章节原文释义、经典名句、学习路径。
          点击任一典籍卡片进入详细内容。
        </div>
      </div>
      
      {/* 典籍卡片列表 */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.85rem',
        marginBottom: '1.5rem',
      }}>
        {list.map(b => (
          <div key={b.id}
            onClick={() => openBook(b.id)}
            style={{
              padding: '0.85rem 1rem',
              background: selectedId === b.id ? `${b.color}22` : 'var(--bg-raised)',
              border: `1.5px solid ${selectedId === b.id ? b.color : 'var(--border)'}`,
              borderRadius: 'var(--r-md)',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.45rem' }}>
              <div style={{
                width: 38, height: 38, borderRadius: 'var(--r-sm)',
                background: b.color, color: '#fff',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-display)',
                flexShrink: 0,
              }}>{b.icon}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: b.color, fontFamily: 'var(--font-serif)' }}>
                  《{b.title}》
                </div>
                <div style={{ fontSize: '0.62rem', color: 'var(--text-faint)', marginTop: '1px' }}>
                  {b.dynasty.split('（')[0]}
                </div>
              </div>
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              {b.author}
            </div>
            <div style={{
              fontSize: '0.65rem', color: b.color, fontWeight: 600,
              padding: '2px 6px', background: `${b.color}11`,
              border: `1px solid ${b.color}44`, borderRadius: '3px',
              display: 'inline-block', marginBottom: '0.35rem',
            }}>
              {b.category}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-faint)', lineHeight: 1.5, fontFamily: 'var(--font-serif)' }}>
              {b.summary}
            </div>
          </div>
        ))}
      </div>
      
      {/* 详细内容 */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
          <div className="spinner" /><p style={{ marginTop: '0.5rem' }}>加载典籍内容…</p>
        </div>
      )}
      
      {!loading && detail && (
        <CompendiumDetail data={detail} />
      )}
    </div>
  )
}

function CompendiumDetail({ data }) {
  const color = data.color || '#8a6f4a'
  return (
    <div style={{
      padding: '1.2rem 1.4rem', background: 'var(--bg-raised)',
      borderRadius: 'var(--r-md)', border: `2px solid ${color}55`,
      marginTop: '1rem',
    }}>
      {/* 标题 */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', marginBottom: '1.2rem',
        paddingBottom: '0.85rem', borderBottom: `1px solid ${color}33` }}>
        <div style={{
          width: 60, height: 60, borderRadius: 'var(--r-md)',
          background: color, color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1.8rem', fontWeight: 700, fontFamily: 'var(--font-display)',
          flexShrink: 0,
        }}>{data.icon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color, fontFamily: 'var(--font-serif)' }}>
            《{data.title}》
          </div>
          {data.alt_title && data.alt_title !== data.title && (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              又名《{data.alt_title}》
            </div>
          )}
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.45rem',
            fontFamily: 'var(--font-serif)', lineHeight: 1.7 }}>
            <span style={{ color: 'var(--text-muted)' }}>作者：</span>{data.author}<br/>
            <span style={{ color: 'var(--text-muted)' }}>朝代：</span>{data.dynasty}<br/>
            <span style={{ color: 'var(--text-muted)' }}>规模：</span>{data.volume}<br/>
            <span style={{ color: 'var(--text-muted)' }}>类别：</span>
            <span style={{ color, fontWeight: 600 }}>{data.category}</span>
          </div>
        </div>
      </div>
      
      {/* 历史背景 */}
      <Section title="📜 历史背景" color={color}>
        <p style={{ fontFamily: 'var(--font-serif)', fontSize: '0.86rem',
          color: 'var(--text-secondary)', lineHeight: 1.95, whiteSpace: 'pre-line' }}>
          {data.historical_background}
        </p>
      </Section>
      
      {/* 核心思想 */}
      {data.core_philosophy && (
        <Section title="🧭 核心思想" color={color}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {data.core_philosophy.map((p, i) => (
              <div key={i} style={{
                padding: '0.55rem 0.75rem', background: `${color}0a`,
                borderLeft: `3px solid ${color}`,
                borderRadius: 'var(--r-sm)',
                fontSize: '0.82rem', fontFamily: 'var(--font-serif)',
                color: 'var(--text-secondary)', lineHeight: 1.75,
              }}>
                <MarkdownBold text={p} color={color} />
              </div>
            ))}
          </div>
        </Section>
      )}
      
      {/* 主要章节 */}
      {data.key_chapters && data.key_chapters.length > 0 && (
        <Section title="📖 主要章节精解" color={color}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {data.key_chapters.map((ch, i) => (
              <div key={i} style={{
                padding: '0.85rem 1rem', background: 'var(--bg-subtle)',
                border: `1px solid ${color}33`, borderRadius: 'var(--r-md)',
              }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color,
                  fontFamily: 'var(--font-serif)', marginBottom: '0.5rem' }}>
                  {ch.name}
                </div>
                {ch.text && (
                  <div style={{
                    padding: '0.55rem 0.85rem', marginBottom: '0.55rem',
                    background: `${color}15`,
                    borderLeft: `3px solid ${color}`,
                    fontFamily: 'var(--font-serif)', fontSize: '0.88rem',
                    color: 'var(--accent)', fontStyle: 'italic', lineHeight: 1.85,
                  }}>
                    「{ch.text}」
                  </div>
                )}
                <p style={{
                  fontFamily: 'var(--font-serif)', fontSize: '0.82rem',
                  color: 'var(--text-secondary)', lineHeight: 1.92, whiteSpace: 'pre-line',
                }}>
                  <MarkdownBold text={ch.explanation} color={color} />
                </p>
              </div>
            ))}
          </div>
        </Section>
      )}
      
      {/* 核心名句 */}
      {data.key_aphorisms && data.key_aphorisms.length > 0 && (
        <Section title="💎 经典名句" color={color}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
            {data.key_aphorisms.map((a, i) => (
              <div key={i} style={{
                padding: '0.65rem 0.85rem',
                background: `linear-gradient(90deg, ${color}0f, transparent)`,
                borderLeft: `2px solid ${color}`,
                borderRadius: 'var(--r-sm)',
              }}>
                <div style={{
                  fontFamily: 'var(--font-serif)', fontSize: '0.92rem',
                  color: color, fontStyle: 'italic', lineHeight: 1.78,
                  marginBottom: '0.3rem', fontWeight: 600,
                }}>
                  「{a.text}」
                </div>
                <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)',
                  fontFamily: 'var(--font-serif)', marginBottom: '0.25rem' }}>
                  ── {a.source}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)', lineHeight: 1.75 }}>
                  {a.explanation}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
      
      {/* 学习路径 */}
      {data.study_path && data.study_path.length > 0 && (
        <Section title="🎓 学习路径" color={color}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {data.study_path.map((step, i) => (
              <div key={i} style={{
                display: 'flex', gap: '0.6rem', alignItems: 'flex-start',
                padding: '0.5rem 0.75rem', background: 'var(--bg-subtle)',
                borderRadius: 'var(--r-sm)',
              }}>
                <div style={{
                  width: 24, height: 24, borderRadius: '50%',
                  background: color, color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.7rem', fontWeight: 700, flexShrink: 0,
                }}>{i + 1}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)',
                  fontFamily: 'var(--font-serif)', lineHeight: 1.7, paddingTop: '2px' }}>
                  <MarkdownBold text={step} color={color} />
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
      
      {/* 现代价值 */}
      {data.modern_relevance && (
        <Section title="🌟 现代价值" color={color}>
          <div style={{
            padding: '0.85rem 1rem',
            background: `linear-gradient(135deg, ${color}15, ${color}05)`,
            border: `1px solid ${color}55`,
            borderRadius: 'var(--r-md)',
            fontFamily: 'var(--font-serif)', fontSize: '0.85rem',
            color: 'var(--text-secondary)', lineHeight: 1.9, whiteSpace: 'pre-line',
          }}>
            {data.modern_relevance}
          </div>
        </Section>
      )}
    </div>
  )
}

function Section({ title, color, children }) {
  return (
    <div style={{ marginBottom: '1.4rem' }}>
      <div style={{
        fontSize: '0.95rem', fontWeight: 700, color, fontFamily: 'var(--font-serif)',
        marginBottom: '0.6rem', paddingBottom: '0.3rem',
        borderBottom: `1px dashed ${color}55`,
      }}>
        {title}
      </div>
      {children}
    </div>
  )
}

/**
 * 渲染含 **粗体** 标记的文本（Markdown 简化版）
 */
function MarkdownBold({ text, color }) {
  if (!text) return null
  // 分割 **xxx** 部分
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return (
    <>
      {parts.map((p, i) => {
        if (p.startsWith('**') && p.endsWith('**')) {
          return (
            <strong key={i} style={{ color, fontWeight: 700 }}>
              {p.slice(2, -2)}
            </strong>
          )
        }
        return <span key={i}>{p}</span>
      })}
    </>
  )
}
