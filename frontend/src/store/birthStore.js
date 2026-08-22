import { create } from 'zustand'
import { useSettingsStore } from './settingsStore'
import { useAuthStore } from './authStore'

const STORAGE_KEY = 'bagua_birth'

function loadLocal() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) } catch { return null }
}

function saveLocal(data) {
  if (data) localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  else localStorage.removeItem(STORAGE_KEY)
}

const DEFAULT_BIRTH = {
  year: 1990, month: 5, day: 22, hour: 8, minute: 0,
  gender: 'male', is_lunar: true, is_leap_month: false,
  province: null, city: null,
}

export const useBirthStore = create((set, get) => ({
  birth: loadLocal() || null,  // null = not set yet
  loaded: false,

  // Load from server (call after login)
  loadFromServer: async () => {
    const { user } = useAuthStore.getState()
    if (!user?.token) return
    try {
      const { apiBaseUrl } = useSettingsStore.getState()
      const res = await fetch(`${apiBaseUrl}/api/v1/user/birth-info`, {
        headers: { 'X-User-Token': user.token }
      })
      const data = await res.json()
      if (data.success && data.data && Object.keys(data.data).length > 0) {
        set({ birth: data.data, loaded: true })
        saveLocal(data.data)
      } else {
        set({ loaded: true })
      }
    } catch {
      set({ loaded: true })
    }
  },

  // Save to server + local
  saveBirth: async (birthInfo) => {
    set({ birth: birthInfo })
    saveLocal(birthInfo)

    const { user } = useAuthStore.getState()
    if (!user?.token) return true  // save locally only
    try {
      const { apiBaseUrl } = useSettingsStore.getState()
      await fetch(`${apiBaseUrl}/api/v1/user/birth-info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Token': user.token },
        body: JSON.stringify(birthInfo),
      })
      return true
    } catch { return false }
  },

  // Clear
  clear: () => { set({ birth: null }); saveLocal(null) },

  // Helper: get birth or defaults
  getBirthOrDefault: () => get().birth || DEFAULT_BIRTH,
}))
