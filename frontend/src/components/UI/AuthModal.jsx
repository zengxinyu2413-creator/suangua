import React, { useState } from 'react'
import { clickable } from '../../utils/a11y'
import { useAuthStore } from '../../store/authStore'

export function AuthModal({ onClose }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const { login, register, loading } = useAuthStore()

  const pwHasUpper = /[A-Z]/.test(password)
  const pwHasLower = /[a-z]/.test(password)
  const pwHasDigit = /[0-9]/.test(password)
  const pwLenOk = password.length >= 6
  const pwValid = pwHasUpper && pwHasLower && pwHasDigit && pwLenOk

  const submit = async () => {
    setError('')
    if (mode === 'register' && !pwValid) {
      setError('密码需至少6位，含大写+小写+数字')
      return
    }
    const result = mode === 'login'
      ? await login(username, password)
      : await register(username, password, displayName)
    if (result.success) onClose()
    else setError(result.error || '操作失败')
  }

  return (
    <div style={{ position:'fixed', inset:0, zIndex:9999, background:'rgba(0,0,0,0.35)', display:'flex', alignItems:'center', justifyContent:'center' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background:'var(--surface)', width:340, padding:'28px 24px', border:'1px solid var(--border)', position:'relative' }}>
        <button onClick={onClose} style={{ position:'absolute', top:8, right:12, border:'none', background:'none', fontSize:18, color:'var(--text-muted)', cursor:'pointer' }}>×</button>
        <div style={{ textAlign:'center', marginBottom:20 }}>
          <div style={{ fontSize:16, fontWeight:700, fontFamily:'var(--font-serif)', color:'var(--text-primary)', letterSpacing:2 }}>
            {mode === 'login' ? '登录' : '注册'}
          </div>
          <div style={{ fontSize:11, color:'var(--text-muted)', marginTop:4 }}>命盘云端保存 · 多设备同步</div>
        </div>

        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          <input placeholder="用户名（至少2位）" value={username} onChange={e => setUsername(e.target.value)}
            style={{ padding:'8px 12px', border:'1px solid var(--border)', background:'var(--bg-subtle)', fontSize:13, fontFamily:'var(--font-sans)' }} />
          <input placeholder="密码" type="password" value={password} onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()}
            style={{ padding:'8px 12px', border:'1px solid var(--border)', background:'var(--bg-subtle)', fontSize:13 }} />

          {/* Password strength hints (register only) */}
          {mode === 'register' && password.length > 0 && (
            <div style={{ display:'flex', gap:8, fontSize:10, lineHeight:1.4 }}>
              <span style={{ color: pwLenOk ? 'var(--accent)' : 'var(--text-faint)' }}>≥6位{pwLenOk?'✓':''}</span>
              <span style={{ color: pwHasUpper ? 'var(--accent)' : 'var(--text-faint)' }}>大写{pwHasUpper?'✓':''}</span>
              <span style={{ color: pwHasLower ? 'var(--accent)' : 'var(--text-faint)' }}>小写{pwHasLower?'✓':''}</span>
              <span style={{ color: pwHasDigit ? 'var(--accent)' : 'var(--text-faint)' }}>数字{pwHasDigit?'✓':''}</span>
            </div>
          )}

          {mode === 'register' && (
            <input placeholder="显示名称（可选）" value={displayName} onChange={e => setDisplayName(e.target.value)}
              style={{ padding:'8px 12px', border:'1px solid var(--border)', background:'var(--bg-subtle)', fontSize:13 }} />
          )}
          {error && <div style={{ fontSize:12, color:'var(--red-light, #c0392b)', padding:'4px 0' }}>{error}</div>}
          <button onClick={submit} disabled={loading || !username || !password || (mode==='register' && !pwValid)}
            style={{ padding:'9px', background: (mode==='register' && !pwValid) ? 'var(--text-faint)' : 'var(--accent)', color:'#fff', border:'none', fontSize:13, fontWeight:600, cursor:'pointer', fontFamily:'var(--font-serif)', letterSpacing:1 }}>
            {loading ? '处理中…' : mode === 'login' ? '登 录' : '注 册'}
          </button>
          <div style={{ textAlign:'center', fontSize:12, color:'var(--text-muted)' }}>
            {mode === 'login' ? (
              <span>没有账号？<a onClick={() => { setMode('register'); setError('') }} style={{ color:'var(--accent)', cursor:'pointer' }}>注册</a></span>
            ) : (
              <span>已有账号？<a onClick={() => { setMode('login'); setError('') }} style={{ color:'var(--accent)', cursor:'pointer' }}>登录</a></span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function UserMenu({ onLogout }) {
  const { user } = useAuthStore()
  const [open, setOpen] = useState(false)
  if (!user) return null
  return (
    <div style={{ position:'relative' }}>
      <button onClick={() => setOpen(!open)} title={user.display_name || user.username}
        style={{ width:28, height:28, background:'var(--accent)', color:'#fff', border:'none', fontSize:12, fontWeight:700, cursor:'pointer', fontFamily:'var(--font-serif)', display:'flex', alignItems:'center', justifyContent:'center' }}>
        {(user.display_name || user.username).slice(0, 1).toUpperCase()}
      </button>
      {open && (
        <div style={{ position:'absolute', top:34, right:0, background:'var(--surface)', border:'1px solid var(--border)', padding:'8px 0', minWidth:140, zIndex:100 }}>
          <div style={{ padding:'6px 14px', fontSize:12, color:'var(--text-primary)', fontWeight:600 }}>{user.display_name || user.username}</div>
          <div style={{ padding:'6px 14px', fontSize:11, color:'var(--text-muted)', borderBottom:'1px solid var(--border)', marginBottom:4 }}>@{user.username}</div>
          <div {...clickable(() => { setOpen(false); onLogout() })}
            style={{ padding:'6px 14px', fontSize:12, color:'var(--red-light, #c0392b)', cursor:'pointer' }}>退出登录</div>
        </div>
      )}
    </div>
  )
}
