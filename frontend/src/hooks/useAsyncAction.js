/**
 * useAsyncAction —— 统一的异步请求状态封装。
 *
 * 抽取自八字页的成熟模式：loading 态 + 持久 error 态 + 成功/失败 toast。
 * 解决各页错误处理不一致（部分页只 toast、不在页面内持久显示错误）的问题。
 *
 * 用法：
 *   const { loading, error, run } = useAsyncAction()
 *   async function handleRun() {
 *     const data = await run(() => fengshuiApi.analysis(form), { successMsg: '分析完成' })
 *     if (data) setResult(data)
 *   }
 *   // 渲染： {error && <div className="error-box">⚠ {error}</div>}
 *
 * run 失败时返回 undefined（不抛出），并同时：① 置 error 态（页面内持久显示）
 * ② 弹 error toast。成功则返回结果数据，可选弹 success toast。
 */
import { useState, useCallback } from 'react'
import { useNotifyStore } from '../store/settingsStore'

export function useAsyncAction() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { notify } = useNotifyStore()

  const run = useCallback(async (asyncFn, { successMsg, errorPrefix } = {}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await asyncFn()
      if (successMsg) notify(successMsg, 'success')
      return data
    } catch (e) {
      const msg = (errorPrefix ? errorPrefix + '：' : '') + (e?.message || '请求失败')
      setError(msg)
      notify(msg, 'error')
      return undefined
    } finally {
      setLoading(false)
    }
  }, [notify])

  return { loading, error, setError, run }
}
