<template>
  <div class="category-filter" ref="scrollContainer">
    <button
      class="category-chip"
      :class="{ 'category-chip--active': selectedId === null }"
      @click="$emit('select', null)"
    >
      <span class="category-chip__label">Все</span>
    </button>
    <button
      v-for="cat in categories"
      :key="cat.id"
      class="category-chip"
      :class="{ 'category-chip--active': selectedId === cat.id }"
      @click="$emit('select', cat.id)"
    >
      <span v-if="cat.icon" class="category-chip__icon">{{ cat.icon }}</span>
      <span class="category-chip__label">{{ cat.name }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Category } from '@/types'

defineProps<{
  categories: Category[]
  selectedId: string | null
}>()

defineEmits<{
  select: [id: string | null]
}>()
</script>

<style scoped>
.category-filter {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 0 16px 12px;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.category-filter::-webkit-scrollbar {
  display: none;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-button);
  background: var(--tg-theme-secondary-bg-color, #232e3c);
  color: var(--tg-theme-hint-color, #708499);
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
}

.category-chip:active {
  transform: scale(0.96);
}

.category-chip--active {
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
}

.category-chip__icon {
  font-size: 15px;
  line-height: 1;
}

.category-chip__label {
  line-height: 1;
}
</style>
