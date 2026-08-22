/**
 * a11y.js —— 无障碍辅助。
 *
 * clickable(handler)：把一个「可点击的 div」变得键盘可达。
 * 展开后注入 role="button" + tabIndex=0 + onClick + onKeyDown(Enter/Space)，
 * 使键盘用户也能聚焦并触发，符合 WAI-ARIA 对非语义元素的最低要求。
 *
 * 用法： <div {...clickable(() => toggle(id))} className="...">…</div>
 *
 * 注：能用原生 <button> 时优先用 button；本 helper 用于已大量内联样式、
 * 改 button 会影响视觉的既有 div，做最小侵入式的无障碍补强。
 */
export function clickable(handler, { label } = {}) {
  return {
    onClick: handler,
    onKeyDown: (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        handler(e)
      }
    },
    role: 'button',
    tabIndex: 0,
    ...(label ? { 'aria-label': label } : {}),
  }
}
