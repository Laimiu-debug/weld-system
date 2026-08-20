import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import {
  DEFAULT_SYSTEM_PREFERENCES,
  UserSystemPreferences,
} from '@/types/preferences'
import { preferencesService } from '@/services/preferences'

interface PreferencesState {
  preferences: UserSystemPreferences
  loaded: boolean
  loading: boolean
  setPreferences: (preferences: Partial<UserSystemPreferences>) => void
  loadFromServer: () => Promise<void>
  saveToServer: (preferences?: UserSystemPreferences) => Promise<UserSystemPreferences>
  resetToDefault: () => UserSystemPreferences
  applyDomEffects: (preferences?: UserSystemPreferences) => void
}

function resolveTheme(theme: UserSystemPreferences['theme']): 'light' | 'dark' {
  if (theme === 'dark') return 'dark'
  if (theme === 'light') return 'light'
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

function applyDomEffects(preferences: UserSystemPreferences) {
  if (typeof document === 'undefined') return

  const resolved = resolveTheme(preferences.theme)
  document.documentElement.setAttribute('data-theme', resolved)
  document.documentElement.style.setProperty('--primary-color', preferences.primaryColor)
  document.body.classList.toggle('compact-mode', preferences.compactMode)

  if (preferences.desktopNotifications && 'Notification' in window) {
    if (Notification.permission === 'default') {
      void Notification.requestPermission()
    }
  }
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set, get) => ({
      preferences: DEFAULT_SYSTEM_PREFERENCES,
      loaded: false,
      loading: false,

      setPreferences: (partial) => {
        const next = { ...get().preferences, ...partial }
        set({ preferences: next })
        applyDomEffects(next)
      },

      loadFromServer: async () => {
        set({ loading: true })
        try {
          const remote = await preferencesService.getPreferences()
          set({ preferences: remote, loaded: true })
          applyDomEffects(remote)
        } catch (error) {
          console.error('加载系统设置失败:', error)
          applyDomEffects(get().preferences)
          set({ loaded: true })
        } finally {
          set({ loading: false })
        }
      },

      saveToServer: async (preferences) => {
        const payload = preferences || get().preferences
        const saved = await preferencesService.updatePreferences(payload)
        set({ preferences: saved, loaded: true })
        applyDomEffects(saved)
        return saved
      },

      resetToDefault: () => {
        const defaults = { ...DEFAULT_SYSTEM_PREFERENCES }
        set({ preferences: defaults })
        applyDomEffects(defaults)
        return defaults
      },

      applyDomEffects: (preferences) => {
        applyDomEffects(preferences || get().preferences)
      },
    }),
    {
      name: 'user-system-preferences',
      partialize: (state) => ({ preferences: state.preferences }),
      onRehydrateStorage: () => (state) => {
        if (state?.preferences) {
          applyDomEffects(state.preferences)
        }
      },
    }
  )
)

export { resolveTheme }
