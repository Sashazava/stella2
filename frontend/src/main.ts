import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { init, isTMA, viewport, themeParams, backButton } from '@telegram-apps/sdk-vue'
import App from './App.vue'
import { router } from './router'
import './assets/main.css'

async function bootstrap() {
  // Dev mode: mock Telegram environment to prevent init() crash outside Telegram
  if (import.meta.env.DEV) {
    const { setupDevMock } = await import('./lib/telegram-mock')
    try {
      const isTma = await isTMA('complete')
      if (!isTma) {
        setupDevMock()
      }
    } catch {
      // isTMA check failed — not in Telegram, apply mock
      setupDevMock()
    }
  }

  init()

  // Mount SDK UI components with availability guards
  if (viewport.mount.isAvailable()) {
    await viewport.mount()
    viewport.bindCssVars()
    if (viewport.expand.isAvailable()) viewport.expand()
  }
  if (themeParams.mount.isAvailable()) {
    await themeParams.mount()
    themeParams.bindCssVars()
  }
  if (backButton.mount.isAvailable()) {
    backButton.mount()
  }

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.mount('#app')
}

bootstrap()
