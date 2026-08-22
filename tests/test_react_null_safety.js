/**
 * Frontend test: 空值渲染安全（AST 精确版）
 * 防止「紫微界面打不开」那类 null 崩溃复发。
 * 对 useState(null) 可空变量，在「未被该变量守护」处直接成员访问 → 首次渲染 result=null 崩溃。
 * 安全：{result && result.x} / {result ? result.x : y} / result?.x / 函数内 if(!result)return。
 */
const fs = require('fs')
const path = require('path')
const babel = (() => {
  for (const p of ['@babel/core', '/tmp/node_modules/@babel/core',
                   path.resolve(__dirname, '../node_modules/@babel/core')]) {
    try { return require(p) } catch (e) { /* try next */ }
  }
  console.error('跳过：未找到 @babel/core（前端空值守护需要）')
  process.exit(0)
})()
const PAGES_DIR = path.resolve(__dirname, '../frontend/src/pages')

function walk(dir) {
  let out = []
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) out = out.concat(walk(p))
    else if (e.name.endsWith('.jsx') || e.name.endsWith('.js')) out.push(p)
  }
  return out
}
function rootIdentName(node) {
  let cur = node
  while (cur && (cur.type === 'MemberExpression' || cur.type === 'OptionalMemberExpression' ||
                 cur.type === 'CallExpression' || cur.type === 'OptionalCallExpression')) {
    cur = cur.object || cur.callee
  }
  return cur && cur.type === 'Identifier' ? cur.name : null
}
function testsVar(node, v) {
  if (!node) return false
  if (node.type === 'Identifier') return node.name === v
  if (node.type === 'MemberExpression' || node.type === 'OptionalMemberExpression') return rootIdentName(node) === v
  if (node.type === 'OptionalCallExpression' || node.type === 'CallExpression') return testsVar(node.callee, v)
  // 守护表达式可含比较/逻辑/取反：zejiResult?.x?.length > 0、!result、a && result?.x
  if (node.type === 'BinaryExpression') return testsVar(node.left, v) || testsVar(node.right, v)
  if (node.type === 'LogicalExpression') return testsVar(node.left, v) || testsVar(node.right, v)
  if (node.type === 'UnaryExpression') return testsVar(node.argument, v)
  return false
}

// objName 是否被「函数参数」或「局部 const 声明/解构」遮蔽（即非本文件 useState 变量）
function shadowedByParam(memberPath, objName) {
  let cur = memberPath
  while (cur.parentPath) {
    const pn = cur.parentPath.node
    if (pn.type === 'FunctionDeclaration' || pn.type === 'FunctionExpression' || pn.type === 'ArrowFunctionExpression') {
      // 参数遮蔽
      for (const param of (pn.params || [])) {
        if (param.type === 'Identifier' && param.name === objName) return true
        if (param.type === 'ObjectPattern' && _objPatternBinds(param, objName)) return true
      }
      // 局部 const/let 声明遮蔽（如 const {data}=useApi() / const data=…），但排除顶层 useState(null) 本身
      let localBind = false
      cur.parentPath.traverse({ VariableDeclarator(vp) {
        const id = vp.node.id, init = vp.node.init
        const isUseStateNull = init && init.type === 'CallExpression' && init.callee && init.callee.name === 'useState'
        if (isUseStateNull) return   // useState 声明不算遮蔽（它就是可空源）
        if (id.type === 'Identifier' && id.name === objName) localBind = true
        if (id.type === 'ObjectPattern' && _objPatternBinds(id, objName)) localBind = true
      }})
      if (localBind) return true
    }
    cur = cur.parentPath
  }
  return false
}
function _objPatternBinds(pat, name) {
  for (const pr of (pat.properties || [])) {
    if ((pr.type === 'ObjectProperty' || pr.type === 'Property') && pr.value &&
        pr.value.type === 'Identifier' && pr.value.name === name) return true
  }
  return false
}
function _contains(node, target) {
  if (!node) return false
  if (node === target) return true
  for (const k of Object.keys(node)) {
    if (['loc','start','end','leadingComments','trailingComments','innerComments'].includes(k)) continue
    const val = node[k]
    if (Array.isArray(val)) { for (const c of val) if (c && typeof c.type === 'string' && _contains(c, target)) return true }
    else if (val && typeof val.type === 'string') { if (_contains(val, target)) return true }
  }
  return false
}
function _leftGuards(left, v) {
  if (!left) return false
  if (testsVar(left, v)) return true
  if (left.type === 'LogicalExpression') return _leftGuards(left.left, v) || testsVar(left.right, v)
  return false
}
function _testHasNegation(node, v) {
  if (!node) return false
  if (node.type === 'UnaryExpression' && node.operator === '!' &&
      node.argument.type === 'Identifier' && node.argument.name === v) return true
  // if (loading || !data) return — 递归进 || / && 找 !v
  if (node.type === 'LogicalExpression') return _testHasNegation(node.left, v) || _testHasNegation(node.right, v)
  return false
}
function _hasEarlyGuard(fnPath, v) {
  // 仅查函数「直接体」顶层的 if(!v)return（提前守护须在执行路径上），
  // 不下钻嵌套子函数（子回调里的 if(!v)return 不保护本函数渲染路径）。
  const body = fnPath.node.body
  if (!body || body.type !== 'BlockStatement') return false
  for (const stmt of body.body) {
    if (stmt.type === 'IfStatement' && _testHasNegation(stmt.test, v)) {
      const cons = stmt.consequent
      if (cons && (cons.type === 'ReturnStatement' ||
          (cons.type === 'BlockStatement' && cons.body.some(s => s.type === 'ReturnStatement')))) {
        return true
      }
    }
  }
  return false
}
function analyzeCode(code, label) {
  let ast
  // 解析失败返回 null（区别于「解析成功但 0 违规」的 []），供自检识别静默失效
  try { ast = babel.parseSync(code, { configFile: false, babelrc: false, parserOpts: { plugins: ['jsx'] } }) }
  catch (e) { console.error("解析失败 " + label + ": " + e.message); process.exitCode = 2; return null }
  const nullable = new Set()
  babel.traverse(ast, { VariableDeclarator(p) {
    const init = p.node.init
    if (init && init.type === 'CallExpression' && init.callee && init.callee.name === 'useState' &&
        (init.arguments.length === 0 || (init.arguments[0] && init.arguments[0].type === 'NullLiteral'))) {
      const id = p.node.id
      if (id.type === 'ArrayPattern' && id.elements[0] && id.elements[0].type === 'Identifier') nullable.add(id.elements[0].name)
    }
  }})
  if (!nullable.size) return []
  const violations = []
  babel.traverse(ast, { MemberExpression(p) {
    const objName = p.node.object.type === 'Identifier' ? p.node.object.name : null
    if (!objName || !nullable.has(objName)) return
    // 若该名在包裹函数参数中（prop/参数），则非本文件 useState 变量，父组件已守护，跳过
    if (shadowedByParam(p, objName)) return
    let safe = false, cur = p
    while (cur.parentPath) {
      const parent = cur.parentPath, pn = parent.node
      if (pn.type === 'LogicalExpression' && (pn.operator === '&&' || pn.operator === '??')) {
        if (_contains(pn.right, cur.node) && (testsVar(pn.left, objName) || _leftGuards(pn.left, objName))) { safe = true; break }
      }
      if (pn.type === 'ConditionalExpression' && testsVar(pn.test, objName)) {
        if (_contains(pn.consequent, cur.node) || _contains(pn.alternate, cur.node)) { safe = true; break }
      }
      // 正向 if 块守护：if (v) { …v.x… } —— 本节点在 consequent 块、test 正向测试 v
      if (pn.type === 'IfStatement' && testsVar(pn.test, objName) && !_testHasNegation(pn.test, objName)) {
        if (_contains(pn.consequent, cur.node)) { safe = true; break }
      }
      if (pn.type === 'FunctionDeclaration' || pn.type === 'FunctionExpression' || pn.type === 'ArrowFunctionExpression') {
        if (_hasEarlyGuard(parent, objName)) { safe = true; break }
      }
      cur = parent
    }
    if (!safe) violations.push({ var: objName, line: p.node.loc ? p.node.loc.start.line : '?', prop: (p.node.property && p.node.property.name) || '' })
  }})
  return violations
}
function analyzeFile(file) {
  const v = analyzeCode(fs.readFileSync(file, 'utf-8'), file)
  return v === null ? [] : v
}

// ── 守护自检 ──────────────────────────────────────────────
// 防止守护「静默失效」：若 babel 解析失效（如缺 preset）或判别逻辑回归，
// 守护会假装「0 违规 ✓」而实则什么都没查。每次运行先以已知样本验证守护本身。
const _SELF_BAD = "import {useState} from 'react'\n" +
  "export default function B(){ const [d,setD]=useState(null); return <div>{d.x}</div> }"
const _SELF_GOOD = "import {useState} from 'react'\n" +
  "export default function G(){ const [d,setD]=useState(null); return <div>{d?.x}</div> }"
const _sb = analyzeCode(_SELF_BAD, '<selfcheck-bad>')
const _sg = analyzeCode(_SELF_GOOD, '<selfcheck-good>')
if (_sb === null || _sg === null) {
  console.error('❌ 守护自检：解析失效（babel 不可用？），空值守护无法工作 —— 拒绝以「通过」收场')
  process.exit(2)
}
if (_sb.length < 1) {
  console.error('❌ 守护自检：未能抓到已知空值违规（d.x）—— 守护判别逻辑已失效！')
  process.exit(2)
}
if (_sg.length !== 0) {
  console.error('❌ 守护自检：误报安全写法（d?.x）—— 守护精确性已退化！')
  process.exit(2)
}
console.error('✓ 守护自检通过：能抓真违规、不冤枉安全写法')

let totalFiles = 0, bad = []
for (const f of walk(PAGES_DIR)) { const v = analyzeFile(f); totalFiles++; if (v.length) bad.push({ file: path.relative(PAGES_DIR, f), violations: v }) }
if (bad.length) {
  console.error('❌ 空值渲染安全：可空变量在守护外直接成员访问（首次渲染会崩）：')
  let n = 0
  for (const b of bad) for (const v of b.violations) { console.error(`   ${b.file}:${v.line}  ${v.var}.${v.prop}  → 应 ${v.var}?.${v.prop} 或置于 {${v.var} && …} 内`); n++ }
  console.error(`\n总计: ${n} 处真实违规`)
  process.exit(1)
} else { console.log(`总计: ${totalFiles} 文件 AST 检查，0 处守护外空值访问 ✓`) }
