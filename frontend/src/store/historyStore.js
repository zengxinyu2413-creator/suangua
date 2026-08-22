/**
 * store/historyStore.js
 * =====================
 * 断事笔记 + 排盘历史 — localStorage persistence
 */
import { create } from 'zustand'

const STORAGE_KEY = 'bagua_history'
const MAX_RECORDS = 100

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch { return [] }
}

function saveHistory(records) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(records.slice(0, MAX_RECORDS)))
  } catch {}
}

export const useHistoryStore = create((set, get) => ({
  records: loadHistory(),

  addRecord: (record) => {
    const r = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2,6),
      ts: new Date().toISOString(),
      ...record,
      notes: '',
    }
    const updated = [r, ...get().records].slice(0, MAX_RECORDS)
    saveHistory(updated)
    set({ records: updated })
    return r.id
  },

  updateNote: (id, notes) => {
    const updated = get().records.map(r => r.id === id ? { ...r, notes } : r)
    saveHistory(updated)
    set({ records: updated })
  },

  deleteRecord: (id) => {
    const updated = get().records.filter(r => r.id !== id)
    saveHistory(updated)
    set({ records: updated })
  },

  clearAll: () => {
    saveHistory([])
    set({ records: [] })
  },
}))
