import React, { useRef, useEffect, useState } from 'react'
import { initCanvas } from '../../utils/shareCanvasKit'
import { RENDERERS } from '../../utils/shareRenderers'

const SIZE = { bazi: [640, 560], liuyao: [640, 520], ziwei: [640, 520], qimen: [640, 460],
  xuankong: [640, 440], yangzhai: [640, 460], date: [640, 480] }

const FILE_PREFIX = { bazi: '命盘', liuyao: '卦象', ziwei: '紫微', qimen: '奇门',
  xuankong: '玄空', yangzhai: '阳宅', date: '择日' }

// 各模块判断"是否有数据可分享"的最小必要字段
const HAS_DATA = {
  bazi: d => !!d?.day_master,
  liuyao: d => !!d?.original,
  ziwei: d => !!d?.soul_palace || !!d?.palaces,
  qimen: d => !!d?.palaces?.length,
  xuankong: d => !!d?.combined,
  yangzhai: d => !!d?.men,
  date: d => !!(d?.best_days?.length || d?.auspicious_days?.length),
}

export default function ShareImage({ data, module = 'bazi', onClose }) {
  const canvasRef = useRef(null)
  const [ready, setReady] = useState(false)

  const renderer = RENDERERS[module]
  const hasData = HAS_DATA[module]?.(data)

  useEffect(() => {
    if (!canvasRef.current || !data || !renderer || !hasData) return
    const [W, H] = SIZE[module] || [640, 480]
    const ctx = initCanvas(canvasRef.current, W, H)
    try {
      renderer(ctx, data, W, H)
      setReady(true)
    } catch (e) {
      // 静默失败保护：某一模块字段缺失不应白屏崩溃，仅不生成分享图
      console.error('ShareImage render failed:', module, e)
    }
  }, [data, module])

  const download = () => {
    const link = document.createElement('a')
    link.download = `${FILE_PREFIX[module] || '排盘'}_${Date.now()}.png`
    link.href = canvasRef.current.toDataURL('image/png')
    link.click()
  }

  if (!hasData) return null

  return (
    <div style={{ position:'fixed', inset:0, zIndex:9999, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', flexDirection:'column', gap:12 }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <canvas ref={canvasRef} style={{ maxWidth:'90vw', maxHeight:'80vh', border:'1px solid rgba(255,255,255,0.2)' }} />
      <div style={{ display:'flex', gap:8 }}>
        <button onClick={download} disabled={!ready} style={{ padding:'8px 20px', background:'var(--accent)', color:'#fff', border:'none', fontSize:13, fontWeight:600, cursor: ready ? 'pointer' : 'default', opacity: ready ? 1 : 0.5 }}>
          ⬇ 下载图片
        </button>
        <button onClick={onClose} style={{ padding:'8px 20px', background:'rgba(255,255,255,0.15)', color:'#fff', border:'1px solid rgba(255,255,255,0.3)', fontSize:13, cursor:'pointer' }}>
          关闭
        </button>
      </div>
    </div>
  )
}
