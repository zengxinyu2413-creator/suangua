import React, { useState } from 'react'
import { useBirthStore } from '../../store/birthStore'
import { useAuthStore } from '../../store/authStore'

/**
 * BirthFillBar — 一键填充 / 保存为默认 toolbar
 * Place above or inside BirthForm. 
 * Props:
 *   currentValues: current birth form values
 *   onFill: callback to set values when user clicks fill
 */
export default function BirthFillBar({ currentValues, onFill }) {
  const { birth, saveBirth } = useBirthStore()
  const { user } = useAuthStore()
  const [msg, setMsg] = useState('')

  const hasSaved = birth && birth.year

  const handleFill = () => {
    if (!birth) {
      setMsg('尚未保存生辰')
      setTimeout(() => setMsg(''), 2000)
      return
    }
    onFill(birth)
    setMsg('已填充')
    setTimeout(() => setMsg(''), 1500)
  }

  const handleSave = async () => {
    if (!currentValues?.year) return
    await saveBirth(currentValues)
    setMsg(user ? '已保存至账号' : '已保存至本地')
    setTimeout(() => setMsg(''), 2000)
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8,
      padding: '4px 0',
    }}>
      <button
        onClick={handleFill}
        disabled={!hasSaved}
        style={{
          padding: '3px 10px', fontSize: 11, fontFamily: 'var(--font-serif)',
          border: '1px solid var(--accent-dim)',
          background: hasSaved ? 'var(--accent-bg)' : 'var(--bg-subtle)',
          color: hasSaved ? 'var(--accent)' : 'var(--text-faint)',
          cursor: hasSaved ? 'pointer' : 'default',
          letterSpacing: 1,
        }}
      >
        一键填充
      </button>
      <button
        onClick={handleSave}
        style={{
          padding: '3px 10px', fontSize: 11, fontFamily: 'var(--font-serif)',
          border: '1px solid var(--border)',
          background: 'var(--bg-subtle)',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
        }}
      >
        保存为默认
      </button>
      {msg && (
        <span style={{ fontSize: 10, color: 'var(--accent)', fontFamily: 'var(--font-serif)' }}>
          {msg}
        </span>
      )}
      {hasSaved && (
        <span style={{ fontSize: 9, color: 'var(--text-faint)', marginLeft: 'auto' }}>
          {birth.year}/{birth.month}/{birth.day} {birth.gender === 'male' ? '男' : '女'}
        </span>
      )}
    </div>
  )
}
