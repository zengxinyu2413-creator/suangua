import BirthFillBar from '../../components/UI/BirthFillBar'
import React, { useState, useRef, useEffect } from 'react'
import BirthForm from '../../components/UI/BirthForm'
import { useSettingsStore, useNotifyStore } from '../../store/settingsStore'
import './AgentPage.css'

const QUICK_PROMPTS = [
  '今年整体运势如何？',
  '我适合什么行业？',
  '如何提升财运？',
  '感情发展前景？',
  '健康方面需要注意什么？',
  '事业何时有突破？',
  '子女运如何？',
  '近期有贵人吗？',
]

export default function AgentPage() {
  const { apiBaseUrl, llmProvider, llmKey, llmBaseUrl, llmModel, llmStyle } = useSettingsStore()
  const PROVIDER_DEFAULTS = { anthropic:'claude-sonnet-4-6', deepseek:'deepseek-chat', openai:'gpt-4o', moonshot:'moonshot-v1-8k', gemini:'gemini-2.0-flash' }
  const PROVIDER_STYLES    = { anthropic:'anthropic', deepseek:'openai', openai:'openai', moonshot:'openai', gemini:'gemini' }
  const effectiveStyle = llmStyle || PROVIDER_STYLES[llmProvider] || 'openai'
  const effectiveModel = llmModel || PROVIDER_DEFAULTS[llmProvider] || 'claude-sonnet-4-6'
  const { notify } = useNotifyStore()

  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [streaming, setStreaming] = useState(false)
  const [birth, setBirth]       = useState({
    year:1990, month:5, day:22, hour:8, minute:0, gender:'male',
    is_lunar:true, is_leap_month:false, province:null, city:null,
  })
  const bottomRef = useRef(null)
  const abortRef  = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:'smooth' }) }, [messages])

  const sendMessage = async () => {
    if (streaming) return
    const q = question.trim() || '请综合解读我的命盘'
    setMessages(p => [...p, { role:'user', content: q, ts:Date.now() }])
    setQuestion('')

    if (!llmKey.trim()) {
      setMessages(p => [...p, { role:'assistant', ts:Date.now(),
        content:'⚠️ 请先在【设置】页面配置 API Key 才能使用 AI 顾问功能。', error:true }])
      return
    }

    setStreaming(true)
    setMessages(p => [...p, { role:'assistant', content:'', ts:Date.now() }])
    try {
      abortRef.current = new AbortController()
      const body = {
        question: q,
        session_history: messages.slice(-10).map(m => ({ role:m.role, content:m.content })),
        context: {
          birth: {
            year: birth.year, month: birth.month, day: birth.day,
            hour: birth.hour, gender: birth.gender === 'male' ? '男' : '女'
          }
        }
      }
      const resp = await fetch(`${apiBaseUrl}/api/v1/agent/consult`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-LLM-Key': llmKey.trim(),
          'X-LLM-Provider': llmProvider || 'anthropic',
          'X-LLM-Base-Url': llmBaseUrl.trim() || '',
          'X-LLM-Model': effectiveModel,
          'X-LLM-Style': effectiveStyle,
        },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
      })
      if (!resp.ok) {
        const e = await resp.json().catch(() => ({ detail:'请求失败' }))
        throw new Error(e.detail || `HTTP ${resp.status}`)
      }
      const reader = resp.body.getReader(); const decoder = new TextDecoder(); let buf = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream:true })
        const lines = buf.split('\n'); buf = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') continue
          try {
            const chunk = JSON.parse(raw)
            if (chunk.text) {
              setMessages(p => {
                const copy = [...p]; const last = copy[copy.length - 1]
                if (last && last.role === 'assistant') last.content += chunk.text
                return copy
              })
            }
          } catch {}
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        setMessages(p => {
          const copy = [...p]; const last = copy[copy.length - 1]
          if (last?.role === 'assistant' && !last.content) last.content = '⚠️ ' + e.message
          last.error = true
          return copy
        })
      }
    } finally { setStreaming(false); abortRef.current = null }
  }

  const stopStream = () => { abortRef.current?.abort(); setStreaming(false) }
  const clearChat  = () => { setMessages([]); notify('对话已清空', 'info') }

  return (
    <div className="page agent-page">
      <div className="page-header">
        <div>
          <div className="page-title">AI 命理顾问</div>
          <div className="page-subtitle">输入生辰 · 自动排盘 · 结合《穷通宝鉴》《滴天髓》《子平真诠》深度解答</div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={clearChat}>清空对话</button>
      </div>

      <div className="agent-layout">
        {/* ─── LEFT SIDEBAR ─── */}
        <aside className="agent-sidebar">
          <div className="agent-sidebar-section">
            <div className="agent-sidebar-label">生辰信息</div>
            <div style={{ fontSize:'var(--text-xs)', color:'var(--text-muted)', marginBottom:6, lineHeight:1.6 }}>
              填写后提问，系统自动排算八字命盘并结合古籍解答
            </div>
            <BirthFillBar currentValues={birth} onFill={setBirth} />
            <BirthForm values={birth} onChange={setBirth} />
          </div>

          <div className="agent-sidebar-section">
            <div className="agent-sidebar-label">快速提问</div>
            <div className="agent-quick-prompts">
              {QUICK_PROMPTS.map(p => (
                <button key={p} className="agent-quick-btn"
                  onClick={() => setQuestion(p)}>
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="agent-sidebar-section" style={{ fontSize:'var(--text-xs)', color:'var(--text-faint)', lineHeight:1.7 }}>
            <div className="agent-sidebar-label">使用说明</div>
            <p>本顾问自动排算八字命盘（四柱·用神·大运），结合穷通宝鉴调候、滴天髓日干论、子平真诠格局分析，由 AI 综合给出专业解答。</p>
            <p style={{ marginTop:4 }}>如需详细的六爻占卜、奇门遁甲、风水分析，请使用对应的专业模块。</p>
          </div>
        </aside>

        {/* ─── MAIN CHAT AREA ─── */}
        <div className="agent-main">
          <div className="agent-messages">
            {messages.length === 0 && (
              <div className="agent-empty">
                <div className="agent-empty-icon">🔮</div>
                <div className="agent-empty-title">AI 命理顾问</div>
                <div className="agent-empty-hint">
                  填写左侧生辰信息，在下方输入问题开始咨询
                </div>
                <div className="agent-flow-hint">
                  <span className="agent-flow-step">① 填写生辰</span>
                  <span className="agent-flow-arrow">→</span>
                  <span className="agent-flow-step">② 输入问题</span>
                  <span className="agent-flow-arrow">→</span>
                  <span className="agent-flow-step">③ 自动排盘+AI解答</span>
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg}
                isLast={i===messages.length-1} streaming={streaming} />
            ))}
            <div ref={bottomRef}/>
          </div>

          <div className="agent-input-wrap">
            <textarea className="agent-input" value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => { if (e.key==='Enter' && (e.ctrlKey||e.metaKey)) sendMessage() }}
              placeholder="输入命理问题… （Ctrl+Enter 发送）"
              rows={2} />
            {streaming
              ? <button className="agent-send-btn stop" onClick={stopStream}>⏹<span>停止</span></button>
              : <button className="agent-send-btn" onClick={sendMessage}>
                  ✨<span>发送</span>
                </button>
            }
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Message Bubble ── */
function MessageBubble({ msg, isLast, streaming }) {
  const isUser   = msg.role === 'user'
  const isSystem = msg.role === 'system'
  const isStreaming = isLast && !isUser && !isSystem && streaming

  if (isSystem) return (
    <div className="agent-system-msg">
      <span className="agent-system-dot"/>
      {msg.content}
    </div>
  )

  return (
    <div className={`agent-msg ${isUser?'user':'ai'} ${msg.error?'error':''}`}>
      {!isUser && <div className="agent-avatar">🔮</div>}
      <div className="agent-bubble">
        {msg.content || (isStreaming ? <span className="agent-thinking">正在排盘并分析…</span> : '')}
        {isStreaming && <span className="agent-cursor">▊</span>}
      </div>
    </div>
  )
}
