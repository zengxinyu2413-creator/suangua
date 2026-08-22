/**
 * exportChartPng.js — 紫微命盘导出 PNG 工具
 *
 * 用浏览器原生 SVG foreignObject 把 DOM 元素截图为 PNG，
 * 无需引入第三方库。
 *
 * 关键技巧：
 *   1. 把目标 DOM 序列化成 outerHTML
 *   2. 包在 SVG <foreignObject> 中
 *   3. 用 Blob URL 加载到 Image
 *   4. 在 Canvas 上画 Image，导出 dataURL
 */

/**
 * 把 DOM 元素导出为 PNG
 * @param {HTMLElement} element 要截图的 DOM 元素
 * @param {string} filename 下载文件名（不含 .png）
 * @param {object} options { scale: 2 (高清), background: '#fff' }
 */
export async function exportElementToPng(element, filename = 'ziwei-chart', options = {}) {
  if (!element) throw new Error('元素不存在')
  
  const { scale = 2, background = '#ffffff' } = options
  
  const rect = element.getBoundingClientRect()
  const width = Math.ceil(rect.width)
  const height = Math.ceil(rect.height)
  
  // 1. 复制 DOM 并内联所有 computed 样式
  const cloned = element.cloneNode(true)
  inlineStyles(element, cloned)
  
  // 2. 构造 SVG（用 foreignObject 包 DOM）
  const xmlSerializer = new XMLSerializer()
  const html = xmlSerializer.serializeToString(cloned)
  
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
      <rect width="100%" height="100%" fill="${background}"/>
      <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
          ${html}
        </div>
      </foreignObject>
    </svg>
  `.trim()
  
  // 3. SVG → Blob → Object URL
  const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = width * scale
      canvas.height = height * scale
      const ctx = canvas.getContext('2d')
      ctx.scale(scale, scale)
      ctx.fillStyle = background
      ctx.fillRect(0, 0, width, height)
      ctx.drawImage(img, 0, 0)
      
      canvas.toBlob(blob => {
        if (!blob) {
          reject(new Error('Canvas 转 Blob 失败'))
          URL.revokeObjectURL(url)
          return
        }
        // 触发下载
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `${filename}.png`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(a.href)
        URL.revokeObjectURL(url)
        resolve()
      }, 'image/png')
    }
    img.onerror = (e) => {
      URL.revokeObjectURL(url)
      reject(new Error('SVG 加载失败：' + (e?.message || '可能是 DOM 中有跨域资源')))
    }
    img.src = url
  })
}

/**
 * 把源元素的 computed style 内联到目标元素（递归）
 * 这是 foreignObject 渲染的关键 — SVG 不识别外部 CSS
 */
function inlineStyles(source, target) {
  const computed = window.getComputedStyle(source)
  let cssText = ''
  for (let i = 0; i < computed.length; i++) {
    const prop = computed[i]
    const val = computed.getPropertyValue(prop)
    if (val) cssText += `${prop}: ${val}; `
  }
  target.setAttribute('style', cssText)
  
  // 递归处理子元素
  const srcChildren = source.children
  const tgtChildren = target.children
  for (let i = 0; i < srcChildren.length && i < tgtChildren.length; i++) {
    inlineStyles(srcChildren[i], tgtChildren[i])
  }
}
