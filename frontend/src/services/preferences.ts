import { apiService } from './api'
import {
  DEFAULT_SYSTEM_PREFERENCES,
  UserSystemPreferences,
} from '@/types/preferences'

export const preferencesService = {
  async getPreferences(): Promise<UserSystemPreferences> {
    const response = await apiService.get<UserSystemPreferences>('/users/me/preferences')
    return { ...DEFAULT_SYSTEM_PREFERENCES, ...(response.data || {}) }
  },

  async updatePreferences(
    preferences: UserSystemPreferences
  ): Promise<UserSystemPreferences> {
    const response = await apiService.put<UserSystemPreferences>(
      '/users/me/preferences',
      preferences
    )
    return { ...DEFAULT_SYSTEM_PREFERENCES, ...(response.data || preferences) }
  },
}
