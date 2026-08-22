/**
 * StructuredAiOutput.jsx — Z-9 结构化 AI 解读渲染器
 * ====================================================
 *
 * 把 LLM 流式输出的结构化文本解析为可交互的分章节展示：
 *
 *   1. 解析 `## 第X步：标题` → 分章节（可折叠/展开）
 *   2. 解析 ` [依据：<section>·<item>]` → 渲染成可点击的"溯源标签"
 *   3. 解析 `**粗体**` → 加粗渲染
 *   4. 流式时显示光标
 *
 * 用法：
 *   <StructuredAiOutput text={streamingText} streaming={isStreaming} onCitationClick={fn} />
 */
import React, { useState, useMemo } from 'react'

// 章节标题正则：## 第X步：标题
const SECTION_RE = /^##\s+(第[一二三四五六七八九十]+步[：:][^\n]*)$/gm

// 引用标签正则：[依据：section·item]
const CITATION_RE = /\[依据[：:]\s*([^·\]]+)·([^\]]+)\]/g

// 粗体正则：**text**
const BOLD_RE = /\*\*([^*]+?)\*\*/g

// section name → 颜色映射
const SECTION_COLOR = {
  '主星亮度评级': '#c8a04a',
  '经典格局':     '#9b59b6',
  '飞星派飞化':   '#27ae60',
  '冲宫连锁':     '#e74c3c',
  '生年四化':     '#e67e22',
  '来因宫':       '#3498db',
  '三方四正':     '#7f8c8d',
  '大限盘':       '#9b59b6',
  '流年盘':       '#d35400',
}

// ─────────────────────────────────────────────────────────
// 解析阶段一：把全文按 `## 第X步：` 分割成 sections
// ─────────────────────────────────────────────────────────
function parseSections(text) {
  if (!text) return []

  // 找出所有标题的 (start, title) 对
  const titlePoints = []
  let m
  const re = /^##\s+(第[一二三四五六七八九十]+步[：:][^\n]*)$/gm
  while ((m = re.exec(text)) !== null) {
    titlePoints.push({ idx: m.index, title: m[1], headerEnd: re.lastIndex })
  }

  if (titlePoints.length === 0) {
    // 没有任何章节 — 整个就是一段（流式时常见，还没到第二步）
    return [{ title: null, body: text }]
  }

  const sections = []
  // 第一个标题之前的文字（如果有），作为前言
  if (titlePoints[0].idx > 0) {
    const preamble = text.slice(0, titlePoints[0].idx).trim()
    if (preamble) sections.push({ title: null, body: preamble })
  }

  for (let i = 0; i < titlePoints.length; i++) {
    const start = titlePoints[i].headerEnd
    const end = (i < titlePoints.length - 1) ? titlePoints[i + 1].idx : text.length
    sections.push({
      title: titlePoints[i].title,
      body: text.slice(start, end).trim(),
    })
  }
  return sections
}

// ─────────────────────────────────────────────────────────
// 解析阶段二：把单个 section body 渲染为 React nodes
// 处理：粗体、引用标签、换行
// ─────────────────────────────────────────────────────────
function renderBody(body, onCitationClick) {
  if (!body) return null
  const lines = body.split('\n')
  return lines.map((line, lineIdx) => (
    <div key={lineIdx} style={{ marginBottom: line.trim() ? '0.35rem' : 0 }}>
      {renderInline(line, onCitationClick)}
    </div>
  ))
}

function renderInline(text, onCitationClick) {
  if (!text) return null

  // 用一个 token 化方法：先找所有 citation 和 bold 的位置
  const tokens = []  // {type: 'text'|'bold'|'cite', start, end, content?}
  const allMatches = []

  let m
  const citeRe = /\[依据[：:]\s*([^·\]]+)·([^\]]+)\]/g
  while ((m = citeRe.exec(text)) !== null) {
    allMatches.push({ type: 'cite', start: m.index, end: citeRe.lastIndex, section: m[1].trim(), item: m[2].trim() })
  }
  const boldRe = /\*\*([^*]+?)\*\*/g
  while ((m = boldRe.exec(text)) !== null) {
    allMatches.push({ type: 'bold', start: m.index, end: boldRe.lastIndex, content: m[1] })
  }
  allMatches.sort((a, b) => a.start - b.start)

  // 去掉重叠（罕见）
  const cleaned = []
  let lastEnd = -1
  for (const mm of allMatches) {
    if (mm.start >= lastEnd) {
      cleaned.push(mm)
      lastEnd = mm.end
    }
  }

  const nodes = []
  let cursor = 0
  cleaned.forEach((mm, i) => {
    if (mm.start > cursor) {
      nodes.push(<span key={`t${i}`}>{text.slice(cursor, mm.start)}</span>)
    }
    if (mm.type === 'bold') {
      nodes.push(<strong key={`b${i}`} style={{ color: 'var(--text-primary)' }}>{mm.content}</strong>)
    } else if (mm.type === 'cite') {
      const color = SECTION_COLOR[mm.section] || '#7f8c8d'
      nodes.push(
        <span
          key={`c${i}`}
          onClick={() => onCitationClick?.(mm.section, mm.item)}
          style={{
            display: 'inline-block',
            margin: '0 3px',
            padding: '0 6px',
            fontSize: '0.7rem', fontWeight: 600,
            color, background: `${color}12`,
            border: `1px solid ${color}55`,
            borderRadius: 0,
            cursor: 'pointer',
            verticalAlign: 'baseline',
          }}
          title={`点击查看：${mm.section} → ${mm.item}`}
        >
          {mm.section}·{mm.item}
        </span>
      )
    }
    cursor = mm.end
  })
  if (cursor < text.length) {
    nodes.push(<span key="tail">{text.slice(cursor)}</span>)
  }
  return nodes
}

// ─────────────────────────────────────────────────────────
// 主组件
// ─────────────────────────────────────────────────────────
export default function StructuredAiOutput({ text, streaming, onCitationClick }) {
  const sections = useMemo(() => parseSections(text), [text])
  const [collapsedSet, setCollapsedSet] = useState(new Set())

  const toggle = (i) => {
    setCollapsedSet(prev => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i); else next.add(i)
      return next
    })
  }

  if (!text && !streaming) return null

  // 统计：有多少个识别到的引用
  const totalCites = (text.match(/\[依据[：:]/g) || []).length

  return (
    <div style={{
      padding: '1rem 1.25rem',
      maxHeight: '500px', overflowY: 'auto',
      fontSize: 'var(--text-base)', lineHeight: 1.85,
      color: 'var(--text-secondary)', fontFamily: 'var(--font-serif)',
    }}>
      {/* 顶部统计条 */}
      {totalCites > 0 && (
        <div style={{
          marginBottom: '0.75rem', paddingBottom: '0.4rem',
          borderBottom: '1px dashed var(--border)',
          fontSize: 'var(--text-xs)', color: 'var(--text-faint)',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          <span>结构化解读</span>
          <span style={{
            padding: '1px 6px',
            background: 'var(--accent-bg)', color: 'var(--accent)',
          }}>{sections.filter(s => s.title).length} 章节</span>
          <span style={{
            padding: '1px 6px',
            background: 'rgba(231,76,60,0.08)', color: '#e74c3c',
          }}>{totalCites} 处溯源</span>
          <span style={{ color: 'var(--text-faint)', marginLeft: 'auto' }}>
            点击溯源标签查看依据
          </span>
        </div>
      )}

      {/* 各 section */}
      {sections.map((section, i) => {
        const isCollapsed = collapsedSet.has(i)
        // 没有标题的（前言或纯流式）直接渲染
        if (!section.title) {
          return (
            <div key={i} style={{ marginBottom: '0.75rem' }}>
              {renderBody(section.body, onCitationClick)}
            </div>
          )
        }
        return (
          <div key={i} style={{ marginBottom: '0.85rem' }}>
            <div
              onClick={() => toggle(i)}
              style={{
                fontWeight: 700,
                fontSize: 'var(--text-base)',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                marginBottom: '0.45rem',
                paddingBottom: '0.25rem',
                borderBottom: '1px solid var(--accent-dim)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <span style={{ fontSize: '0.75rem', color: 'var(--accent)' }}>{isCollapsed ? '▶' : '▼'}</span>
              <span style={{ color: 'var(--accent)' }}>{section.title}</span>
            </div>
            {!isCollapsed && (
              <div style={{ paddingLeft: '0.6rem' }}>
                {renderBody(section.body, onCitationClick)}
              </div>
            )}
          </div>
        )
      })}

      {/* 流式光标 */}
      {streaming && (
        <span style={{
          display: 'inline-block', width: '2px', height: '1em',
          background: 'var(--accent)', marginLeft: '2px', verticalAlign: 'text-bottom',
          animation: 'blink-cursor 0.8s step-end infinite',
        }}>
          <style>{`@keyframes blink-cursor{0%,100%{opacity:1}50%{opacity:0}}`}</style>
        </span>
      )}
    </div>
  )
}
