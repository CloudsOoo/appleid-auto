/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_PREFIX: string
  readonly VITE_ENV: string
  readonly VITE_USE_MOCK: string
  readonly VITE_TOKEN_KEY: string
  readonly VITE_REFRESH_TOKEN_KEY: string
  readonly VITE_ENABLE_ROUTE_TRANSITION: string
  readonly VITE_ENABLE_PROGRESS: string
  readonly VITE_UPLOAD_SIZE_LIMIT: string
  readonly VITE_LOG_LEVEL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
