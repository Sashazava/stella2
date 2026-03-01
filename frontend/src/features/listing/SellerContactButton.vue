<template>
  <div class="contact-bar">
    <a
      :href="telegramLink"
      class="contact-button"
      @click="onTap"
    >
      <MessageCircle :size="20" :stroke-width="2" />
      <span>Написать продавцу</span>
    </a>
    <a
      v-if="seller.username"
      :href="`https://t.me/${seller.username}`"
      class="contact-fallback"
      @click="onTap"
    >
      @{{ seller.username }}
    </a>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { MessageCircle } from 'lucide-vue-next'
import { hapticFeedback } from '@telegram-apps/sdk-vue'

const props = defineProps<{
  seller: {
    telegram_id: number
    username?: string
  }
}>()

const telegramLink = computed(() =>
  `tg://user?id=${props.seller.telegram_id}`,
)

function onTap() {
  if (hapticFeedback.impactOccurred.isAvailable()) {
    hapticFeedback.impactOccurred('medium')
  }
}
</script>

<style scoped>
.contact-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: linear-gradient(
    to top,
    var(--tg-theme-bg-color, #17212b) 60%,
    color-mix(in srgb, var(--tg-theme-bg-color, #17212b), transparent 5%) 80%,
    transparent
  );
  z-index: 100;
}

.contact-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 48px;
  border-radius: var(--radius-button, 10px);
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.contact-button:active {
  opacity: 0.75;
}

.contact-fallback {
  font-size: 13px;
  color: var(--tg-theme-link-color, #5eaade);
  text-decoration: none;
  padding: 2px 0;
}

.contact-fallback:active {
  opacity: 0.6;
}
</style>
