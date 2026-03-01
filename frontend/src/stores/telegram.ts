import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { initData } from '@telegram-apps/sdk-vue'
import type { User as TelegramUser } from '@telegram-apps/sdk-vue'

export const useTelegramStore = defineStore('telegram', () => {
  const initDataRaw = ref<string | undefined>(undefined)
  const user = ref<TelegramUser | undefined>(undefined)
  const isReady = ref(false)

  const isAuthenticated = computed(() => !!initDataRaw.value && !!user.value)

  function initialize() {
    initDataRaw.value = initData.raw()
    user.value = initData.user()
    isReady.value = true
  }

  return { initDataRaw, user, isReady, isAuthenticated, initialize }
})
