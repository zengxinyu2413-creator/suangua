import { create } from 'zustand'
import { useSettingsStore } from './settingsStore'

const STORAGE_KEY = 'bagua_auth'

function loadAuth() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) } catch { return null }
}

function saveAuth(data) {
  if (data) localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  else localStorage.removeItem(STORAGE_KEY)
}

async function api(path, body = null, token = null) {
  const { apiBaseUrl } = useSettingsStore.getState()
  const opts = { method: body ? 'POST' : 'GET', headers: { 'Content-Type': 'application/json' } }
  if (token) opts.headers['X-User-Token'] = token
  if (body) opts.body = JSON.stringify(body)
  const res = await fetch(`${apiBaseUrl}/api/v1/user${path}`, opts)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '请求失败')
  return data.data
}

export const useAuthStore = create((set, get) => ({
  user: loadAuth(),
  loading: false,

  register: async (username, password, displayName) => {
    set({ loading: true })
    try {
      const user = await api('/register', { username, password, display_name: displayName })
      saveAuth(user)
      set({ user, loading: false })
      return { success: true }
    } catch (e) {
      set({ loading: false })
      return { success: false, error: e.message }
    }
  },

  login: async (username, password) => {
    set({ loading: true })
    try {
      const user = await api('/login', { username, password })
      saveAuth(user)
      set({ user, loading: false })
      return { success: true }
    } catch (e) {
      set({ loading: false })
      return { success: false, error: e.message }
    }
  },

  logout: () => { saveAuth(null); set({ user: null }) },

  saveChart: async (module, title, summary, birthInfo, chartData, notes) => {
    const { user } = get()
    if (!user?.token) return { success: false, error: '未登录' }
    return await api('/charts', { module, title, summary, birth_info: birthInfo, chart_data: chartData, notes }, user.token)
  },

  listCharts: async (module) => {
    const { user } = get()
    if (!user?.token) return []
    return await api(`/charts${module ? '?module=' + module : ''}`, null, user.token)
  },

  updateNotes: async (chartId, notes) => {
    const { user } = get()
    if (!user?.token) return
    const { apiBaseUrl } = useSettingsStore.getState()
    await fetch(`${apiBaseUrl}/api/v1/user/charts/${chartId}/notes`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-User-Token': user.token },
      body: JSON.stringify({ notes })
    })
  },

  deleteChart: async (chartId) => {
    const { user } = get()
    if (!user?.token) return
    const { apiBaseUrl } = useSettingsStore.getState()
    await fetch(`${apiBaseUrl}/api/v1/user/charts/${chartId}`, {
      method: 'DELETE', headers: { 'X-User-Token': user.token }
    })
  },
}))
