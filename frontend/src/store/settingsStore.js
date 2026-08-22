/**
 * store/settingsStore.js
 * Global application state using Zustand.
 * Persisted to localStorage automatically.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useSettingsStore = create(
  persist(
    (set, get) => ({
      // API — empty string = same-origin relative requests ("/api/v1/...").
      // Works automatically in three scenarios without any manual config:
      //   1. Local dev:      vite proxy forwards /api & /health to the backend
      //   2. Single-port prod: FastAPI serves the built frontend + API together
      //   3. Reverse-proxied cloud: frontend and API share the public domain
      // Only override this (in 设置) if the API truly lives on a different origin.
      apiBaseUrl: '',

      // LLM configuration
      llmProvider: 'anthropic',   // 'anthropic' | 'deepseek' | 'openai' | 'moonshot' | 'gemini'
      llmKey: '',                  // API key — stored in persisted store
      llmBaseUrl: '',              // override base URL (empty = use provider default)
      llmModel: 'claude-sonnet-4-6',  // model name
      llmStyle: 'anthropic',            // api style: anthropic | openai | gemini
      llmCustomName: '',                // display name for custom provider

      // Theme
      theme: 'light',
      accentColor: 'red',

      // Locale / defaults
      defaultGender: 'male',

      // Display
      compactMode: false,
      animationsEnabled: true,

      // Actions
      setApiBaseUrl:    (url) => set({ apiBaseUrl: url.replace(/\/$/, '') }),
      setLlmProvider:   (p)   => set({ llmProvider: p }),
      setLlmKey:        (k)   => set({ llmKey: k }),
      setLlmBaseUrl:    (u)   => set({ llmBaseUrl: u }),
      setLlmModel:      (m)   => set({ llmModel: m }),
      setLlmStyle:      (v)   => set({ llmStyle: v }),
      setLlmCustomName: (n)   => set({ llmCustomName: n }),
      setTheme:         (t)   => set({ theme: t }),
      setAccentColor:   (c)   => set({ accentColor: c }),
      setDefaultGender: (g)   => set({ defaultGender: g }),
      setCompactMode:   (v)   => set({ compactMode: v }),
      setAnimationsEnabled: (v) => set({ animationsEnabled: v }),
      resetAll: () => set({
        apiBaseUrl: '',
        llmProvider: 'anthropic', llmKey: '', llmBaseUrl: '', llmModel: 'claude-sonnet-4-6', llmStyle: 'anthropic', llmCustomName: '',
        theme: 'light', accentColor: 'red',
        defaultGender: 'male', compactMode: false, animationsEnabled: true,
      }),
    }),
    { name: 'bagua-settings' }
  )
);

// ── Notification store (transient, not persisted) ─────────
export const useNotifyStore = create((set) => ({
  notifications: [],
  notify: (message, type = 'info') => {
    const id = Date.now();
    set((s) => ({ notifications: [...s.notifications, { id, message, type }] }));
    setTimeout(() => {
      set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) }));
    }, 4000);
  },
}));
