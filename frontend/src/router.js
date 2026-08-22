/**
 * router.js —— 轻量 URL 路由（History API，无需 react-router）。
 *
 * active/showSettings ↔ URL 路径互相映射，支持深链接 / 前进后退 / 收藏分享。
 * 纯函数，便于单测与复用。
 */

// 可路由的模块 slug（与 App.jsx 的 PAGE_MAP 键一致）
export const ROUTE_SLUGS = [
  'agent', 'bazi', 'ziwei', 'dayun', 'qimen', 'liuyao',
  'fengshui', 'knowledge', 'yijing', 'guardian',
];

/** 路径 → 状态。返回 null 表示「用默认」（如 '/' 或未知路径）。 */
export function parseRoute(pathname) {
  const slug = (pathname || '/').replace(/^\/+/, '').split('/')[0];
  if (slug === 'settings') return { active: null, settings: true };
  if (ROUTE_SLUGS.includes(slug)) return { active: slug, settings: false };
  return null;
}

/** 状态 → 路径。settings 优先；active 为空 → 根路径。 */
export function routeToPath(active, settings) {
  if (settings) return '/settings';
  if (!active) return '/';
  return '/' + active;
}
