import React, { useEffect, useMemo } from 'react'
import { ConfigProvider, theme as antdTheme, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { usePreferencesStore, resolveTheme } from '@/store/preferencesStore'
import { useAuthStore } from '@/store/authStore'
import AutoLogoutWatcher from '@/components/AutoLogoutWatcher'

interface PreferencesProviderProps {
  children: React.ReactNode
}

const PreferencesProvider: React.FC<PreferencesProviderProps> = ({ children }) => {
  const preferences = usePreferencesStore((s) => s.preferences)
  const loadFromServer = usePreferencesStore((s) => s.loadFromServer)
  const applyDomEffects = usePreferencesStore((s) => s.applyDomEffects)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  useEffect(() => {
    applyDomEffects(preferences)
  }, [preferences, applyDomEffects])

  useEffect(() => {
    if (isAuthenticated) {
      void loadFromServer()
    }
  }, [isAuthenticated, loadFromServer])

  const resolvedTheme = resolveTheme(preferences.theme)

  const antdConfig = useMemo(
    () => ({
      locale: preferences.language.startsWith('zh') ? zhCN : enUS,
      theme: {
        algorithm:
          resolvedTheme === 'dark'
            ? antdTheme.darkAlgorithm
            : antdTheme.defaultAlgorithm,
        token: {
          colorPrimary: preferences.primaryColor || '#1F5EFF',
          colorLink: preferences.primaryColor || '#1F5EFF',
          borderRadius: preferences.compactMode ? 4 : 6,
          fontSize: preferences.compactMode ? 13 : 14,
          controlHeight: preferences.compactMode ? 28 : 32,
        },
      },
      getPopupContainer: () => document.body,
      virtual: true,
    }),
    [preferences.language, preferences.primaryColor, preferences.compactMode, resolvedTheme]
  )

  return (
    <ConfigProvider {...antdConfig}>
      <AntApp>
        <AutoLogoutWatcher />
        {children}
      </AntApp>
    </ConfigProvider>
  )
}

export default PreferencesProvider
