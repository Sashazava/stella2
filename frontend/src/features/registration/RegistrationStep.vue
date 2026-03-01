<script setup lang="ts">
defineProps<{
  currentStep: number
  totalSteps: number
  canProceed: boolean
  isLoading?: boolean
}>()

const emit = defineEmits<{
  next: []
  back: []
}>()
</script>

<template>
  <div class="reg-step">
    <!-- Progress dots -->
    <div class="dots">
      <span
        v-for="i in totalSteps"
        :key="i"
        class="dot"
        :class="{
          'dot--active': i === currentStep,
          'dot--done': i < currentStep,
        }"
      />
    </div>

    <!-- Scrollable content area -->
    <div class="content">
      <slot />
    </div>

    <!-- Pinned bottom actions -->
    <div class="actions">
      <button
        v-if="currentStep > 1"
        type="button"
        class="btn-back"
        @click="emit('back')"
      >
        Назад
      </button>
      <button
        type="button"
        class="btn-next"
        :class="{ 'btn-next--disabled': !canProceed || isLoading }"
        :disabled="!canProceed || isLoading"
        @click="emit('next')"
      >
        <span v-if="isLoading" class="spinner" />
        <span v-else>{{ currentStep === totalSteps ? 'Готово' : 'Далее' }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.reg-step {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--color-background);
  color: var(--color-text);
}

.dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 24px 8px;
}

.dot {
  height: 5px;
  width: 5px;
  border-radius: 999px;
  background: var(--color-hint);
  opacity: 0.2;
  transition: all 0.3s ease-out;
}

.dot--active {
  width: 28px;
  background: var(--color-primary);
  opacity: 1;
}

.dot--done {
  background: var(--color-primary);
  opacity: 0.55;
}

.content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.actions {
  flex-shrink: 0;
  display: flex;
  gap: 12px;
  padding: 12px 24px 32px;
}

.btn-back {
  height: 50px;
  padding: 0 20px;
  border-radius: var(--radius-button);
  background: var(--color-surface);
  color: var(--color-hint);
  font-weight: 500;
  font-size: 15px;
  border: none;
  cursor: pointer;
  transition: transform 0.1s;
}

.btn-back:active {
  transform: scale(0.97);
}

.btn-next {
  flex: 1;
  height: 50px;
  border-radius: var(--radius-button);
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.1s, opacity 0.2s;
}

.btn-next:active {
  transform: scale(0.98);
}

.btn-next--disabled {
  opacity: 0.4;
  pointer-events: none;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
