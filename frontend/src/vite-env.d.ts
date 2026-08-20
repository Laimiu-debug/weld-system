/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_SUBTITLE: string
  readonly VITE_ORG_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_ENABLE_MOCK_DATA: string
  readonly VITE_ENABLE_DEVTOOLS: string
  readonly VITE_SENTRY_DSN: string
  readonly VITE_GOOGLE_ANALYTICS_ID: string
  readonly VITE_STRIPE_PUBLISHABLE_KEY: string
  readonly VITE_MAX_FILE_SIZE: string
  readonly VITE_ALLOWED_FILE_TYPES: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}