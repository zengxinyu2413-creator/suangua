/**
 * Frontend test: React hooks import 完整性检查
 *
 * 这个测试扫描 frontend/src/ 下所有 .jsx 文件，确保：
 *   1. 每个用到的 hook（useState/useEffect/useMemo/useRef/useCallback/useContext/useReducer/useLayoutEffect）
 *      都在 import 语句中声明（或通过 React.xxx 调用）
 *   2. 防止"用了 useEffect 但 import 里只有 useState"这种白屏 bug
 *
 * 起源：用户反馈紫微界面无法显示，定位到 ZiWeiPage.jsx Z-9 改动加了 useEffect
 * 但忘了在 import 里加，导致整个页面 ReferenceError 白屏。
 */
const fs = require('fs')
const path = require('path')

const PROJECT_ROOT = path.resolve(__dirname, '..')
const FRONTEND_SRC = path.join(PROJECT_ROOT, 'frontend/src')
const HOOKS = [
  'useState', 'useEffect', 'useMemo', 'useRef',
  'useCallback', 'useContext', 'useReducer', 'useLayoutEffect',
  'useImperativeHandle', 'useDebugValue',
]

function findJsxFiles(dir, out = []) {
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, item.name)
    if (item.isDirectory()) {
      if (item.name === 'node_modules' || item.name.startsWith('.')) continue
      findJsxFiles(full, out)
    } else if (item.name.endsWith('.jsx') || item.name.endsWith('.tsx')) {
      out.push(full)
    }
  }
  return out
}

let passed = 0, failed = 0
const failures = []

function checkContent(content, rel) {
  const fails = []
  // Find React import line（may span multiple lines）
  const importMatch = content.match(/import\s+(?:React(?:\s*,\s*)?)?({[^}]*}|\w+)?\s*(?:,\s*({[^}]*}))?\s+from\s+['"]react['"]/);
  let importedNames = new Set()
  if (importMatch) {
    const named = (importMatch[1] || '') + ' ' + (importMatch[2] || '')
    for (const m of named.matchAll(/\b(use\w+)\b/g)) {
      importedNames.add(m[1])
    }
  }

  for (const hook of HOOKS) {
    const re = new RegExp(`(?<![\\w.])${hook}\\s*\\(`, 'g')
    const calls = [...content.matchAll(re)]
    const bareCalls = calls.filter(m => {
      const startPos = m.index
      const lineStart = content.lastIndexOf('\n', startPos) + 1
      const lineSoFar = content.slice(lineStart, startPos)
      return !lineSoFar.endsWith('React.')
    })
    if (bareCalls.length > 0 && !importedNames.has(hook)) {
      fails.push(`${rel}: 使用了 ${hook}() 但 import 缺失`)
      return fails   // 保持原行为：每文件报首个缺失 hook
    }
  }
  return fails
}

function checkFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8')
  const rel = path.relative(PROJECT_ROOT, filePath)
  const fails = checkContent(content, rel)
  if (fails.length) {
    failed++
    for (const f of fails) { failures.push(f); console.log(`  ✗ ${f}`) }
  } else {
    passed++
  }
}

// ── 守护自检 ──────────────────────────────────────────────
// 防止守护「静默失效」：若正则失配或判别逻辑回归，守护会假装「全通过」而实则什么都没查。
const _SELF_BAD = "import { useState } from 'react'\n" +
  "export default function B(){ useEffect(() => {}, []); return null }"   // 用 useEffect 却未 import → 应报
const _SELF_GOOD = "import { useState } from 'react'\n" +
  "export default function G(){ const [x] = useState(0); return null }"   // import+use useState → 应过
if (checkContent(_SELF_BAD, '<selfcheck-bad>').length < 1) {
  console.error('❌ hooks 守护自检：未能抓到「用了 useEffect 却未 import」—— 守护判别逻辑已失效！')
  process.exit(2)
}
if (checkContent(_SELF_GOOD, '<selfcheck-good>').length !== 0) {
  console.error('❌ hooks 守护自检：误报合法的 import+使用 —— 守护精确性已退化！')
  process.exit(2)
}
console.error('✓ hooks 守护自检通过：能抓缺失 import、不冤枉合法用法')

console.log('='.repeat(70))
console.log('React hooks import 完整性检查')
console.log('='.repeat(70))

const files = findJsxFiles(FRONTEND_SRC)
if (files.length === 0) {
  console.error(`❌ hooks 守护自检：扫描路径无任何 jsx 文件（${FRONTEND_SRC}）—— 路径错误或目录为空，守护形同虚设`)
  process.exit(2)
}
console.log(`扫描 ${files.length} 个 jsx 文件...\n`)

for (const f of files) {
  checkFile(f)
}

console.log(`\n${'='.repeat(70)}`)
console.log(`总计: ${passed} 文件通过 / ${failed} 文件失败`)
console.log('='.repeat(70))

if (failed > 0) {
  console.log('\n详细失败：')
  for (const f of failures) console.log('  - ' + f)
  process.exit(1)
}
