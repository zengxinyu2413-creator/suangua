/**
 * shareCanvasKit.js — 分享图共享绘制工具
 * ==========================================
 * 与 frontend/src/styles/plates.css 的"留白盘式"设计语言保持一致：
 * 近白纸面 · 细线收边 · 印石章首 · 朱印定论 · 五行配色 · 衬线大字干支
 *
 * 所有分享图（八字/六爻/紫微/奇门/玄空/阳宅/择日）共用此工具，
 * 保证七个模块的分享图视觉统一、且与 app 内盘式一致。
 */

// ── 色板（与 plates.css .gv-plate 变量一致的字面值，因 canvas 无法读取 CSS 变量）──
export const INK = '#2a2720'
export const INK_2 = '#5c594f'
export const INK_3 = '#928e84'
export const INK_4 = '#c2bdb2'
export const VERMILION = '#cf3b2c'
export const PAPER = '#f8f7f3'
export const HAIR = 'rgba(34,32,26,0.12)'
export const HAIR_2 = 'rgba(34,32,26,0.20)'

export const WX = { 木: '#2f8f63', 火: '#cf5132', 土: '#c1953a', 金: '#8a8475', 水: '#3a7ab5' }

// 印石配色（与项目既有 STONES 命名体系一致）
export const SEALS = {
  tianhuang: { bg: '#d8ab3c', ink: '#473205' }, // 八字·择日
  furong:    { bg: '#e8b0c0', ink: '#5a1e30' }, // 六爻
  jixue:     { bg: '#c83028', ink: '#fff0e6' }, // 紫微
  qingtian:  { bg: '#88b0a0', ink: '#1a3a2e' }, // 奇门
  balin:     { bg: '#a890c0', ink: '#281840' }, // 玄空·阳宅
  zhusha:    { bg: '#c83828', ink: '#fff0e0' }, // 每日守护
}

const SERIF = '"Noto Serif SC", serif'
const SANS = '"Noto Sans SC", sans-serif'
const MONO = '"JetBrains Mono", monospace'

/** 初始化 2x 高清 canvas，返回 ctx。W/H 为逻辑像素尺寸。 */
export function initCanvas(canvas, W, H) {
  canvas.width = W * 2
  canvas.height = H * 2
  canvas.style.width = W + 'px'
  canvas.style.height = H + 'px'
  const ctx = canvas.getContext('2d')
  ctx.scale(2, 2)
  ctx.fillStyle = PAPER
  ctx.fillRect(0, 0, W, H)
  return ctx
}

/** 章首：印石方章 + 标题 + 副标题（模块识别区）。返回下一行 y 坐标。 */
export function drawHeader(ctx, { x, y, W, seal, glyph, title, subtitle }) {
  const s = SEALS[seal] || SEALS.tianhuang
  // 印石方章
  ctx.fillStyle = s.bg
  ctx.fillRect(x, y, 34, 34)
  ctx.strokeStyle = 'rgba(255,255,255,0.35)'
  ctx.lineWidth = 0.5
  ctx.strokeRect(x + 3, y + 3, 28, 28)
  ctx.fillStyle = s.ink
  ctx.font = `600 17px ${SERIF}`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(glyph, x + 17, y + 18)
  ctx.textBaseline = 'alphabetic'
  ctx.textAlign = 'left'

  // 标题
  ctx.fillStyle = INK
  ctx.font = `700 19px ${SERIF}`
  ctx.fillText(title, x + 46, y + 20)
  ctx.fillStyle = INK_3
  ctx.font = `11px ${SANS}`
  ctx.fillText(subtitle || '', x + 46, y + 36)

  // 右上角平台印
  ctx.fillStyle = VERMILION
  ctx.font = `600 11px ${SERIF}`
  ctx.textAlign = 'right'
  ctx.fillText('中国术数平台', x + W, y + 12)
  ctx.fillStyle = INK_4
  ctx.font = `9px ${MONO}`
  ctx.fillText('CHINESE METAPHYSICS', x + W, y + 24)
  ctx.textAlign = 'left'

  return y + 50
}

/** 细线分隔（发丝线，非粗描边）。 */
export function drawHairline(ctx, x, y, w, strong = false) {
  ctx.fillStyle = strong ? HAIR_2 : HAIR
  ctx.fillRect(x, y, w, 1)
}

/** 干支大字（衬线体，按五行配色）。 */
export function drawGanZhiBig(ctx, x, y, gan, zhi, ganWx, zhiWx, size = 30) {
  ctx.textAlign = 'center'
  ctx.font = `700 ${size}px ${SERIF}`
  ctx.fillStyle = WX[ganWx] || INK
  ctx.fillText(gan, x, y)
  ctx.fillStyle = WX[zhiWx] || INK
  ctx.fillText(zhi, x, y + size + 4)
  ctx.textAlign = 'left'
}

/** 小字标签（灰色字距标注，caption 风格）。 */
export function drawCaption(ctx, x, y, text, opts = {}) {
  ctx.textAlign = opts.align || 'left'
  ctx.fillStyle = opts.color || INK_3
  ctx.font = `${opts.weight || 400} ${opts.size || 10}px ${opts.mono ? MONO : SANS}`
  ctx.fillText(text, x, y)
  ctx.textAlign = 'left'
}

/** 正文行（衬线体，用于断语文字，自动按宽度换行）。返回结束后的 y。 */
export function drawParagraph(ctx, x, y, text, maxWidth, opts = {}) {
  if (!text) return y
  const size = opts.size || 12
  const lineHeight = opts.lineHeight || size * 1.85
  const maxLines = opts.maxLines || 4
  ctx.fillStyle = opts.color || INK_2
  ctx.font = `${opts.weight || 400} ${size}px ${SERIF}`
  ctx.textAlign = 'left'

  const chars = String(text).split('')
  let line = ''
  let cy = y
  let lines = 0
  for (let i = 0; i < chars.length; i++) {
    const test = line + chars[i]
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, cy)
      line = chars[i]
      cy += lineHeight
      lines++
      if (lines >= maxLines - 1) {
        // 最后一行截断加省略号
        let rest = chars.slice(i).join('')
        while (ctx.measureText(line + rest + '…').width > maxWidth && rest.length > 0) {
          rest = rest.slice(0, -1)
        }
        ctx.fillText(line + rest + (rest.length < chars.slice(i).join('').length ? '…' : ''), x, cy)
        return cy + lineHeight
      }
    } else {
      line = test
    }
  }
  if (line) { ctx.fillText(line, x, cy); cy += lineHeight }
  return cy
}

/** 朱印定论：小方章，钤盖关键判语（命格/用神/评级），微旋转，双线印边。 */
export function drawZhuSeal(ctx, cx, cy, text, subLabel, size = 60) {
  ctx.save()
  ctx.translate(cx, cy)
  ctx.rotate(-3 * Math.PI / 180)
  ctx.fillStyle = '#fffdf8'
  ctx.strokeStyle = VERMILION
  ctx.lineWidth = 2
  ctx.fillRect(-size / 2, -size / 2, size, size)
  ctx.strokeRect(-size / 2, -size / 2, size, size)
  ctx.strokeStyle = 'rgba(207,59,44,0.3)'
  ctx.lineWidth = 0.5
  ctx.strokeRect(-size / 2 + 4, -size / 2 + 4, size - 8, size - 8)

  ctx.fillStyle = VERMILION
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  const fontSize = text.length > 2 ? 15 : 19
  ctx.font = `700 ${fontSize}px ${SERIF}`
  ctx.fillText(text, 0, -4)
  if (subLabel) {
    ctx.font = `9px ${SANS}`
    ctx.fillText(subLabel, 0, 14)
  }
  ctx.textBaseline = 'alphabetic'
  ctx.textAlign = 'left'
  ctx.restore()
}

/** 页脚：诗句 + 日期 + 模块名，全模块统一收尾。margin 默认 24（七系统渲染器边距），可传入调用方自身边距对齐。 */
export function drawFooter(ctx, W, H, moduleLabel, margin = 24) {
  drawHairline(ctx, margin, H - 46, W - margin * 2, true)
  ctx.textAlign = 'center'
  ctx.fillStyle = INK_3
  ctx.font = `11px ${SERIF}`
  ctx.fillText('观天之道，执天之行 · 穷理尽性以至于命', W / 2, H - 28)
  ctx.fillStyle = INK_4
  ctx.font = `9px ${SANS}`
  ctx.fillText(`${new Date().toLocaleDateString()} · 中国术数平台 · ${moduleLabel}`, W / 2, H - 14)
  ctx.textAlign = 'left'
}

export { SERIF, SANS, MONO }
