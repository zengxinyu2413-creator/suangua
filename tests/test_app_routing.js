/**
 * 路由逻辑测试 —— 校验 src/router.js 的 URL ↔ 状态映射。
 *
 * 不依赖打包器：以正则从 ESM 源码抽出纯函数体后 eval（函数无外部依赖）。
 * 校验：各模块往返一致、settings 往返、未知路径回落默认、全 slug 可深链接。
 */
const fs = require('fs')
const path = require('path')

const SRC = fs.readFileSync(path.resolve(__dirname, '../frontend/src/router.js'), 'utf8')

// 将 ESM 源转成可 eval 的 CJS：去掉 export 关键字
const cjs = SRC.replace(/export\s+const/g, 'const').replace(/export\s+function/g, 'function')
const sandbox = {}
new Function('exports', cjs + '\nexports.ROUTE_SLUGS=ROUTE_SLUGS;exports.parseRoute=parseRoute;exports.routeToPath=routeToPath;')(sandbox)
const { ROUTE_SLUGS, parseRoute, routeToPath } = sandbox

let pass = 0, fail = 0
const check = (cond, msg) => { if (cond) pass++; else { fail++; console.log('  ✗ ' + msg) } }

// ① 各模块 state → path → state 往返一致
for (const slug of ROUTE_SLUGS) {
  const p = routeToPath(slug, false)
  const r = parseRoute(p)
  check(r && r.active === slug && !r.settings, `往返 ${slug} → ${p} → ${JSON.stringify(r)}`)
}
// ② settings 往返
check(routeToPath(null, true) === '/settings', 'settings → /settings')
check(parseRoute('/settings').settings === true, '/settings → settings')
// ③ 未知 / 根路径 → null（用默认）
check(parseRoute('/') === null, "'/' → null")
check(parseRoute('/nonsense') === null, "未知 → null")
// ④ 全 slug 可深链接
for (const slug of ROUTE_SLUGS) check(parseRoute('/' + slug) !== null, `深链接 /${slug}`)
// ⑤ active 为空 → 根路径
check(routeToPath(null, false) === '/', 'null → /')

console.log(`\n路由逻辑：${pass} 通过 / ${fail} 失败`)
if (fail > 0) process.exit(1)
