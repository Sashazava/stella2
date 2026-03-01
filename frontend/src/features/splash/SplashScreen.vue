<template>
  <div class="splash-screen">
    <div class="splash-content">
      <div class="splash-logo">
        <Star :size="56" :stroke-width="1.5" class="splash-star" />
        <span class="splash-brand">Stella</span>
      </div>
      <p class="splash-slogan">Найдёшь всё, что нужно!</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Star } from 'lucide-vue-next'

const router = useRouter()

const SPLASH_KEY = 'stella_splash_shown'
const SPLASH_DURATION = 3000

onMounted(() => {
  if (sessionStorage.getItem(SPLASH_KEY)) {
    router.push('/catalog')
    return
  }

  sessionStorage.setItem(SPLASH_KEY, '1')

  setTimeout(() => {
    router.push('/catalog')
  }, SPLASH_DURATION)
})
</script>

<style scoped>
.splash-screen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    160deg,
    var(--tg-theme-bg-color, #17212b) 0%,
    color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 8%) 50%,
    var(--tg-theme-bg-color, #17212b) 100%
  );
  overflow: hidden;
}

.splash-screen::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(
    ellipse 60% 50% at 50% 45%,
    color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%),
    transparent
  );
  pointer-events: none;
}

.splash-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.splash-logo {
  display: flex;
  align-items: center;
  gap: 14px;
  animation: splash-fade-scale 0.6s ease-out both;
}

.splash-star {
  color: var(--tg-theme-button-color, #5288c1);
  filter: drop-shadow(0 0 20px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 60%));
}

.splash-brand {
  font-size: 48px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--tg-theme-text-color, #f5f5f5);
}

.splash-slogan {
  margin: 0;
  font-size: 16px;
  font-weight: 400;
  color: var(--tg-theme-hint-color, #708499);
  animation: splash-fade-in 0.6s ease-out 0.5s both;
}

@keyframes splash-fade-scale {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes splash-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
