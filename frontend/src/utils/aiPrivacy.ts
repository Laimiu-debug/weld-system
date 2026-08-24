import type { UserSystemPreferences } from '@/types/preferences'

export const AI_DATA_OUTBOUND_NOTICE_VERSION = 'ai-data-outbound-v1'

export const aiDataOutboundNotice = (host?: string) =>
  `为执行 AI 结构化提取或图纸识别，所选文件的原文、页面图像、识别文本及相关元数据可能发送至${host ? `外部模型服务 ${host}` : '您选择或平台配置的外部模型服务'}。数据仅用于本次 AI 处理，请确认文件允许外发且已获得必要授权。`

export function hasPersistentAIDataAuthorization(
  preferences: UserSystemPreferences,
): boolean {
  return preferences.aiDataOutboundAuthorized
    && preferences.aiDataOutboundNoticeVersion === AI_DATA_OUTBOUND_NOTICE_VERSION
}
