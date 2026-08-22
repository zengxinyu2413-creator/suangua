import React, { useState, useEffect, lazy, Suspense } from 'react'
import { useSettingsStore } from './store/settingsStore'
import { useAuthStore } from './store/authStore'
import { useBirthStore } from './store/birthStore'
import { systemApi } from './api/client'
import TaijiBg from './components/TaijiBg'
import { MODULES, STONES, Mtn } from './components/UI/Shared'
import { useHistoryStore } from './store/historyStore'
import { AuthModal, UserMenu } from './components/UI/AuthModal'
import Notifications from './components/UI/Notifications'
import { parseRoute, routeToPath } from './router'
import { clickable } from './utils/a11y'

// 页面按需懒加载（code-splitting）：首屏只加载外壳，各页在首次进入时才拉取自身 chunk。
const BaziPage       = lazy(() => import('./pages/Bazi/BaziPage'))
const LiuYaoPage     = lazy(() => import('./pages/LiuYao/LiuYaoPage'))
const QiMenPage      = lazy(() => import('./pages/QiMen/QiMenPage'))
const FengShuiPage   = lazy(() => import('./pages/FengShui/FengShuiPage'))
const DateSelectPage = lazy(() => import('./pages/DateSelection/DateSelectPage'))
const ZiWeiPage      = lazy(() => import('./pages/ZiWei/ZiWeiPage'))
const KnowledgePage  = lazy(() => import('./pages/Knowledge/KnowledgePage'))
const AgentPage      = lazy(() => import('./pages/Agent/AgentPage'))
const YiJingPage     = lazy(() => import('./pages/YiJing/YiJingPage'))
const DailyGuardianPage = lazy(() => import('./pages/DailyGuardian/DailyGuardianPage'))
const SettingsPage   = lazy(() => import('./pages/Settings/SettingsPage'))

const PAGE_MAP = {
  agent:     AgentPage,
  bazi:      BaziPage,
  ziwei:     ZiWeiPage,
  dayun:     DateSelectPage,
  qimen:     QiMenPage,
  liuyao:    LiuYaoPage,
  fengshui:  FengShuiPage,
  knowledge: KnowledgePage,
  yijing:    YiJingPage,
  guardian:   DailyGuardianPage,
}

// 懒加载页面的加载占位
function PageFallback() {
  return (
    <div className="loading" style={{ padding: '60px 20px', textAlign: 'center' }}>
      <div className="spinner" />
      <p>加载中…</p>
    </div>
  )
}

export default function App() {
  const { theme, accentColor, apiBaseUrl } = useSettingsStore()
  // 默认进入首页落地页（观天之道 · 模块印章矩阵），而非直接跳到某个模块页
  const [active, setActive] = useState(null)
  const [showSettings, setShowSettings] = useState(false)
  const [showAuth, setShowAuth] = useState(false)
  const [status, setStatus] = useState('checking')
  const { user, logout } = useAuthStore()
  const { loadFromServer: loadBirth } = useBirthStore()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document.documentElement.setAttribute('data-accent', accentColor)
  }, [theme, accentColor])

  useEffect(() => {
    let m = true
    const ck = async () => {
      try { const r = await systemApi.health(); if(m) setStatus(r.status==='ok'?'online':'offline') }
      catch { if(m) setStatus('offline') }
    }
    ck(); const id = setInterval(ck, 30000)
    return () => { m=false; clearInterval(id) }
  }, [apiBaseUrl])

  // Load saved birth info when user logs in
  useEffect(() => { if (user?.token) loadBirth() }, [user?.token])

  // ── URL 路由同步 ──────────────────────────────────────
  // ① 挂载时按当前 URL 设初始页（深链接 / 刷新可还原）
  useEffect(() => {
    const r = parseRoute(window.location.pathname)
    if (r) { setActive(r.active); setShowSettings(r.settings) }
    // 用 replaceState 规范化首个 URL（不新增历史项）
    window.history.replaceState({ active: r ? r.active : active, settings: r ? r.settings : false },
                                '', routeToPath(r ? r.active : active, r ? r.settings : false))
  }, [])

  // ② 前进/后退（popstate）→ 按 URL 还原状态
  useEffect(() => {
    const onPop = () => {
      const r = parseRoute(window.location.pathname)
      setActive(r ? r.active : null)
      setShowSettings(r ? r.settings : false)
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  // ③ active/showSettings 变化 → pushState 更新 URL（仅在与当前 URL 不同时）
  useEffect(() => {
    const desired = routeToPath(active, showSettings)
    if (window.location.pathname !== desired) {
      window.history.pushState({ active, settings: showSettings }, '', desired)
    }
  }, [active, showSettings])

  const toggle = id => { setShowSettings(false); setActive(prev => prev === id ? null : id) }
  const activeMod = active ? MODULES.find(m => m.id === active) : null
  const activeSt  = activeMod ? STONES[activeMod.stone] : null
  const PageComp  = active ? PAGE_MAP[active] : null

  return (
    <div style={{ position:'relative', minHeight:'100vh' }}>
      <TaijiBg />
      <Notifications />

      <div className="app-shell">
        {/* ═══ Seal Stone Header ═══ */}
        <header className="topnav" style={{ height:'auto', padding:'8px 16px', flexWrap:'wrap', gap:8 }}>
          {/* Brand — 墨绿玉印 · 圆角印章 */}
          <div {...clickable(() => { setShowSettings(false); setActive(null) }, { label: '返回首页' })}
            className="gv-focus-ring"
            style={{ display:'flex', alignItems:'center', gap:10, marginRight:12, paddingRight:14, borderRight:'1px solid var(--border)', flexShrink:0, cursor:'pointer' }}>
            <div className="gv-brand-seal" style={{
              width:36, height:36, position:'relative', borderRadius:8,
              background:'linear-gradient(140deg, #3d7a5c 0%, #2d6b52 45%, #1f5540 100%)',
              display:'flex', alignItems:'center', justifyContent:'center',
              boxShadow:'0 1px 4px rgba(31,85,64,0.28), inset 0 1px 1px rgba(255,255,255,0.22)',
              transition:'transform .18s cubic-bezier(0.4,0,0.2,1), box-shadow .18s',
            }}>
              <div style={{ position:'absolute', inset:3, borderRadius:5, border:'1px solid rgba(255,255,255,0.28)' }}/>
              <span style={{ fontSize:19, color:'#f4f9f6', fontWeight:400, fontFamily:'var(--font-serif)', lineHeight:1 }}>☯</span>
            </div>
            <div style={{ display:'flex', flexDirection:'column' }}>
              <span style={{ fontSize:15, fontWeight:700, fontFamily:'var(--font-serif)', color:'var(--text-primary)', letterSpacing:2, lineHeight:1.2 }}>中国术数平台</span>
              <span style={{ fontSize:9, color:'var(--text-faint)', fontFamily:'var(--font-mono)', letterSpacing:1 }}>CHINESE METAPHYSICS</span>
            </div>
          </div>

          {/* Seal matrix */}
          <div style={{ display:'flex', gap:4, flex:1, flexWrap:'wrap', justifyContent:'center', alignItems:'center' }}>
            {MODULES.map(m => {
              const st = STONES[m.stone]
              const isAct = active === m.id
              return (
                <div key={m.id} {...clickable(() => toggle(m.id), { label: m.name })} title={`${m.name} · ${st.name}`}
                  className="gv-focus-ring gv-seal-tile"
                  style={{
                    width:50, height:50, cursor:'pointer', position:'relative',
                    background:st.bg, overflow:'hidden', flexShrink:0,
                    boxShadow:isAct ? `0 2px 8px ${st.glow}, inset 0 1px 2px rgba(255,255,255,0.3)` : '0 1px 3px rgba(0,0,0,0.05), inset 0 1px 1px rgba(255,255,255,0.2)',
                    transform:isAct ? 'rotate(-2deg) scale(1.05)' : 'none',
                    transition:'all .18s cubic-bezier(0.4,0,0.2,1)',
                    '--seal-glow': st.glow,
                  }}>
                  <div style={{ position:'absolute', inset:0, opacity:0.4,
                    backgroundImage:`radial-gradient(ellipse at 20% 30%,${st.vein} 0%,transparent 50%),radial-gradient(ellipse at 50% 10%,rgba(255,255,255,0.15) 0%,transparent 30%)` }}/>
                  <div style={{ position:'absolute', inset:4, border:`1.5px solid ${st.ink}`, opacity:isAct?0.7:0.12, transition:'opacity .2s' }}/>
                  <div style={{ position:'absolute', inset:7, border:`0.5px solid ${st.ink}`, opacity:isAct?0.35:0.06, transition:'opacity .2s' }}/>
                  <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}>
                    <span style={{ fontSize:17, fontWeight:900, fontFamily:'var(--font-serif)', color:st.ink, opacity:isAct?1:0.28, lineHeight:1, transition:'opacity .2s' }}>{m.glyph}</span>
                    <span style={{ fontSize:9, color:st.ink, opacity:isAct?0.8:0.22, marginTop:1 }}>{m.name}</span>
                  </div>
                  {isAct && <>
                    <div style={{ position:'absolute', top:1, left:2, width:3, height:2, background:`${st.ink}30` }}/>
                    <div style={{ position:'absolute', bottom:2, right:1, width:2, height:2, background:`${st.ink}20`, transform:'rotate(15deg)' }}/>
                  </>}
                </div>
              )
            })}
          </div>

          {/* Right — user + settings */}
          <div style={{ display:'flex', alignItems:'center', gap:6, flexShrink:0, paddingLeft:12, borderLeft:'1px solid var(--border)' }}>
            <div style={{ width:6, height:6, flexShrink:0, background:status==='online'?'var(--jade)':status==='offline'?'var(--red-light)':'var(--cyan-b)', boxShadow:status==='online'?'0 0 4px rgba(74,122,90,0.5)':'none' }}/>
            {user ? (
              <UserMenu onLogout={logout} />
            ) : (
              <button onClick={() => setShowAuth(true)} title="登录/注册" aria-label="登录或注册"
                style={{ padding:'4px 10px', border:'1px solid var(--border)', background:'transparent', fontSize:11, color:'var(--text-muted)', cursor:'pointer', fontFamily:'var(--font-sans)' }}>
                登录
              </button>
            )}
            <button onClick={() => { setShowSettings(!showSettings); setActive(null) }} aria-label="设置"
              title="系统设置"
              style={{
                width:34, height:34, position:'relative',
                border:showSettings?'1px solid var(--accent-dim)':'1px solid var(--border)',
                background:showSettings?'var(--accent-bg)':'transparent',
                cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center',
                transition:'all .15s',
              }}>
              <span style={{ fontSize:16, color:showSettings?'var(--accent)':'var(--text-muted)', transition:'color .15s' }}>⚙</span>
              {showSettings && <div style={{ position:'absolute', inset:3, border:'0.5px solid var(--accent-dim)', opacity:0.4 }}/>}
            </button>
          </div>
        </header>

        {/* Auth modal */}
        {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

        {/* ═══ Main content ═══ */}
        <main className="main-area">
          {showSettings ? (
            <div className="page"><div className="page-body">
              <Suspense fallback={<PageFallback />}><SettingsPage /></Suspense>
            </div></div>
          ) : active && PageComp ? (
            <div style={{ animation:'fadeIn .2s ease' }}>
              <div style={{
                padding:'8px 24px', display:'flex', alignItems:'center', gap:10,
                borderBottom:'1px solid var(--border)', background:'var(--bg-subtle)',
              }}>
                {/* 模块印章 — 与顶部导航印章同一套设计语言 */}
                <div style={{
                  width:26, height:26, position:'relative', flexShrink:0,
                  background:activeSt.bg, overflow:'hidden',
                  boxShadow:`0 1px 3px ${activeSt.glow}, inset 0 1px 1px rgba(255,255,255,0.25)`,
                }}>
                  <div style={{ position:'absolute', inset:0, opacity:0.4,
                    backgroundImage:`radial-gradient(ellipse at 20% 30%,${activeSt.vein} 0%,transparent 50%),radial-gradient(ellipse at 50% 10%,rgba(255,255,255,0.15) 0%,transparent 30%)` }}/>
                  <div style={{ position:'absolute', inset:2.5, border:`1px solid ${activeSt.ink}`, opacity:0.55 }}/>
                  <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center' }}>
                    <span style={{ fontSize:13, fontWeight:900, fontFamily:'var(--font-serif)', color:activeSt.ink, lineHeight:1 }}>{activeMod.glyph}</span>
                  </div>
                </div>
                <span style={{ fontSize:14, fontWeight:700, fontFamily:'var(--font-serif)', color:'var(--text-primary)' }}>{activeMod.name}</span>
                <span style={{ fontSize:12, color:'var(--text-muted)' }}>{activeSt.name} · {activeMod.desc}</span>
                <span style={{ marginLeft:'auto', fontSize:28, fontWeight:900, fontFamily:'var(--font-serif)', color:activeSt.inkLight, lineHeight:1 }}>{activeMod.glyph}</span>
              </div>
              <Suspense fallback={<PageFallback />}><PageComp /></Suspense>
            </div>
          ) : (
            /* ═══ 首页：意境化落地页 ═══ */
            <div style={{ padding:'40px 20px 60px', maxWidth:880, margin:'0 auto' }}>
              {/* 诗句题头 */}
              <div style={{ textAlign:'center', marginBottom:40 }}>
                <div style={{ fontSize:11, color:'var(--text-faint)', fontFamily:'var(--font-mono)', letterSpacing:4, marginBottom:8 }}>CHINESE METAPHYSICS PLATFORM</div>
                <div style={{ fontSize:22, fontFamily:'var(--font-serif)', fontWeight:700, color:'var(--text-primary)', letterSpacing:6, lineHeight:1.6 }}>
                  观天之道，执天之行
                </div>
                <div style={{ fontSize:13, fontFamily:'var(--font-serif)', color:'var(--text-muted)', marginTop:6, lineHeight:1.8 }}>
                  穷理尽性以至于命 · 《易传·说卦》
                </div>
                {/* 墨线分隔 */}
                <div style={{ width:60, height:1, background:'var(--accent)', opacity:0.3, margin:'20px auto 0' }}/>
              </div>

              {/* 八大模块卡片 */}
              <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(180px, 1fr))', gap:12 }}>
                {MODULES.map(m => {
                  const st = STONES[m.stone]
                  return (
                    <div key={m.id} {...clickable(() => toggle(m.id), { label: m.name })}
                      className="gv-focus-ring"
                      style={{
                        cursor:'pointer', padding:'20px 16px', position:'relative',
                        borderLeft:'2px solid var(--border)', borderBottom:'1px solid var(--border)',
                        transition:'all .2s', background:'var(--surface)',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.borderLeftColor = st.ink; e.currentTarget.style.background = 'var(--bg-subtle)' }}
                      onMouseLeave={e => { e.currentTarget.style.borderLeftColor = 'var(--border)'; e.currentTarget.style.background = 'var(--surface)' }}
                    >
                      {/* 石材色带 */}
                      <div style={{ position:'absolute', top:0, right:0, width:40, height:3, background:st.bg, opacity:0.6 }}/>
                      {/* 印石纹理（与印章同一质感语言） */}
                      <div style={{ position:'absolute', inset:0, pointerEvents:'none', opacity:0.16,
                        backgroundImage:`radial-gradient(ellipse at 88% 8%,${st.vein} 0%,transparent 42%)` }}/>
                      {/* 大字 */}
                      <div style={{ fontSize:28, fontWeight:900, fontFamily:'var(--font-serif)', color:st.ink, opacity:0.15, lineHeight:1, marginBottom:8 }}>{m.glyph}</div>
                      {/* 标题 */}
                      <div style={{ fontSize:15, fontWeight:700, fontFamily:'var(--font-serif)', color:'var(--text-primary)', marginBottom:4 }}>{m.name}</div>
                      {/* 描述 */}
                      <div style={{ fontSize:11, color:'var(--text-muted)', lineHeight:1.5 }}>{m.desc}</div>
                      {/* 石材名 */}
                      <div style={{ fontSize:9, color:'var(--text-faint)', marginTop:8, fontFamily:'var(--font-mono)' }}>{st.name}</div>
                    </div>
                  )
                })}
              </div>

              {/* 最近排盘记录 */}
              {(() => {
                const { records } = useHistoryStore.getState()
                if (!records || records.length === 0) return null
                return (
                  <div style={{ marginTop:32 }}>
                    <div style={{ fontSize:11, color:'var(--text-faint)', fontFamily:'var(--font-mono)', letterSpacing:2, marginBottom:10, textAlign:'center' }}>
                      最近排盘记录
                    </div>
                    <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
                      {records.slice(0, 5).map(r => (
                        <div key={r.id} {...clickable(() => toggle(r.module || 'bazi'), { label: r.summary || '排盘记录' })}
                          className="gv-focus-ring"
                          style={{
                          display:'flex', alignItems:'center', gap:8,
                          padding:'8px 12px', borderLeft:'2px solid var(--border)',
                          background:'var(--surface)', fontSize:12, cursor:'pointer',
                          transition:'border-color .15s',
                        }}
                          onMouseEnter={e => e.currentTarget.style.borderLeftColor = 'var(--accent)'}
                          onMouseLeave={e => e.currentTarget.style.borderLeftColor = 'var(--border)'}
                        >
                          <span style={{ fontFamily:'var(--font-serif)', color:'var(--accent)', fontWeight:600, width:80, flexShrink:0 }}>
                            {r.pillars ? r.pillars.slice(0,8) : (MODULES.find(x => x.id === (r.module||'bazi'))?.name || '')}
                          </span>
                          <span style={{ color:'var(--text-secondary)', flex:1 }}>{r.summary || ''}</span>
                          <span style={{ fontSize:10, color:'var(--text-faint)', fontFamily:'var(--font-mono)' }}>{new Date(r.ts).toLocaleDateString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })()}

              {/* 底部点题 */}
              <div style={{ textAlign:'center', marginTop:40 }}>
                <div style={{ fontSize:11, color:'var(--text-faint)', fontFamily:'var(--font-serif)', lineHeight:1.8 }}>
                  善易者不占 · 善占者不卜 · 善卜者不言
                </div>
                <div style={{ display:'flex', justifyContent:'center', gap:16, marginTop:16 }}>
                  {['穷通宝鉴','滴天髓','子平真诠','增删卜易','紫微斗数全书'].map(t => (
                    <span key={t} style={{ fontSize:9, color:'var(--text-faint)', padding:'2px 6px', border:'1px solid var(--border)', fontFamily:'var(--font-serif)' }}>{t}</span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      <style>{`@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
        .gv-focus-ring:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
        .gv-seal-tile:hover{transform:translateY(-3px) rotate(-1deg) scale(1.06) !important;box-shadow:0 6px 16px var(--seal-glow, rgba(0,0,0,0.12)), inset 0 1px 2px rgba(255,255,255,0.35) !important;}
        .gv-seal-tile:active{transform:translateY(-1px) scale(1.02) !important;}
        .gv-brand-seal:hover{transform:rotate(-2deg) scale(1.05);box-shadow:0 4px 12px rgba(31,85,64,0.34), inset 0 1px 2px rgba(255,255,255,0.3);}`}</style>
    </div>
  )
}
