import { computed } from 'vue'
import {
  initData,
  themeParams as sdkThemeParams,
  useSignal,
} from '@telegram-apps/sdk-vue'

/**
 * Composable that exposes reactive Telegram SDK state.
 *
 * Must be called inside a Vue component setup (uses `onBeforeUnmount` internally).
 */
export function useTelegram() {
  // Reactive refs backed by SDK signals
  const user = useSignal(initData.user)
  const initDataRaw = useSignal(initData.raw)
  const isDark = useSignal(sdkThemeParams.isDark)
  const themeParams = useSignal(sdkThemeParams.state)

  // Derived reactive state
  const isReady = computed(() => user.value !== undefined)
  const colorScheme = computed<'dark' | 'light'>(() =>
    isDark.value ? 'dark' : 'light',
  )

  return {
    /** Telegram user from init data (undefined until init data is available) */
    user,
    /** Raw init data query string */
    initDataRaw,
    /** True when user data has been loaded from Telegram init data */
    isReady,
    /** 'dark' or 'light' based on Telegram theme background color */
    colorScheme,
    /** Full theme parameters object from Telegram */
    themeParams,
  }
}
