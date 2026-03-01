import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { init, initData, isTMA, viewport, themeParams, backButton } from '@telegram-apps/sdk-vue'
import App from './App.vue'
import { router } from './router'
import './assets/main.css'

async function bootstrap() {
  console.log('[BOOT] 1/9 bootstrap() started')

  // Dev mode: mock Telegram environment to prevent init() crash outside Telegram
  if (import.meta.env.DEV) {
    console.log('[BOOT] DEV mode detected, checking TMA...')
    const { setupDevMock } = await import('./lib/telegram-mock')
    try {
      const isTma = await isTMA('complete')
      if (!isTma) {
        console.log('[BOOT] Not in TMA, applying dev mock')
        setupDevMock()
      }
    } catch {
      console.log('[BOOT] isTMA check failed, applying dev mock')
      setupDevMock()
    }
  }

  console.log('[BOOT] 2/9 calling init()')
  try {
    init()
    console.log('[BOOT] 2/9 init() OK')
  } catch (e) {
    console.error('[BOOT] 2/9 init() FAILED:', e)
  }

  // Restore Telegram init data (user info, auth) from launch params
  try {
    initData.restore()
    console.log('[BOOT] 2.5/9 initData.restore() OK, raw:', initData.raw() ? initData.raw()!.substring(0, 80) + '...' : 'EMPTY')
  } catch (e) {
    console.error('[BOOT] 2.5/9 initData.restore() FAILED:', e)
  }

  // Mount SDK UI components with availability guards
  try {
    console.log('[BOOT] 3/9 viewport.mount.isAvailable():', viewport.mount.isAvailable())
    if (viewport.mount.isAvailable()) {
      await viewport.mount()
      console.log('[BOOT] 3/9 viewport.mount() OK')
      viewport.bindCssVars()
      console.log('[BOOT] 3/9 viewport.bindCssVars() OK')
      if (viewport.expand.isAvailable()) viewport.expand()
    }
  } catch (e) {
    console.error('[BOOT] 3/9 viewport FAILED:', e)
  }

  try {
    console.log('[BOOT] 4/9 themeParams.mount.isAvailable():', themeParams.mount.isAvailable())
    if (themeParams.mount.isAvailable()) {
      await themeParams.mount()
      console.log('[BOOT] 4/9 themeParams.mount() OK')
      themeParams.bindCssVars()
      console.log('[BOOT] 4/9 themeParams.bindCssVars() OK')
    }
  } catch (e) {
    console.error('[BOOT] 4/9 themeParams FAILED:', e)
  }

  try {
    console.log('[BOOT] 5/9 backButton.mount.isAvailable():', backButton.mount.isAvailable())
    if (backButton.mount.isAvailable()) {
      backButton.mount()
      console.log('[BOOT] 5/9 backButton.mount() OK')
    }
  } catch (e) {
    console.error('[BOOT] 5/9 backButton FAILED:', e)
  }

  console.log('[BOOT] 6/9 createApp()')
  const app = createApp(App)

  // Global error handler — catch any unhandled Vue errors
  app.config.errorHandler = (err, instance, info) => {
    console.error('[VUE ERROR]', info, err)
  }

  console.log('[BOOT] 7/9 use(pinia)')
  app.use(createPinia())
  console.log('[BOOT] 8/9 use(router)')
  app.use(router)

  // Router error handler
  router.onError((err) => {
    console.error('[ROUTER ERROR]', err)
  })

  console.log('[BOOT] 9/9 mounting #app')
  app.mount('#app')
  console.log('[BOOT] ✅ App mounted successfully')
  console.log('[BOOT] Current URL:', window.location.href)

bootstrap().catch(e => console.error('[BOOT] ❌ bootstrap() FATAL:', e))
