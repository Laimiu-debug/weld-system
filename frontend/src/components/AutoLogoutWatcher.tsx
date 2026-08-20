import { useEffect, useRef } from 'react'
import { message } from 'antd'
import { useAuthStore } from '@/store/authStore'
import { usePreferencesStore } from '@/store/preferencesStore'

const ACTIVITY_EVENTS: Array<keyof WindowEventMap> = [
  'mousemove',
  'mousedown',
  'keydown',
  'touchstart',
  'scroll',
]

/** Applies auto-logout based on security preferences. */
export default function AutoLogoutWatcher() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const logout = useAuthStore((s) => s.logout)
  const autoLogout = usePreferencesStore((s) => s.preferences.autoLogout)
  const autoLogoutMinutes = usePreferencesStore((s) => s.preferences.autoLogoutMinutes)
  const sessionTimeout = usePreferencesStore((s) => s.preferences.sessionTimeout)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    const enabled = isAuthenticated && (autoLogout || sessionTimeout)
    if (!enabled) {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
      return
    }

    const minutes = Math.max(5, autoLogoutMinutes || 30)
    const ms = minutes * 60 * 1000

    const schedule = () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current)
      }
      timerRef.current = window.setTimeout(async () => {
        message.warning(`已超过 ${minutes} 分钟无操作，已自动退出登录`)
        await logout()
      }, ms)
    }

    schedule()
    ACTIVITY_EVENTS.forEach((eventName) => {
      window.addEventListener(eventName, schedule, { passive: true })
    })

    return () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current)
      }
      ACTIVITY_EVENTS.forEach((eventName) => {
        window.removeEventListener(eventName, schedule)
      })
    }
  }, [isAuthenticated, autoLogout, sessionTimeout, autoLogoutMinutes, logout])

  return null
}
