<template>
  <div class="cat-selector">
    <button
      type="button"
      class="cat-selector__trigger"
      :class="{ 'cat-selector__trigger--active': isOpen }"
      @click="toggleDropdown"
    >
      <div class="cat-selector__trigger-left">
        <Tag :size="16" :stroke-width="2" />
        <span v-if="selectedCategory" class="cat-selector__selected">
          {{ selectedCategory.name }}
        </span>
        <span v-else class="cat-selector__placeholder">Выберите категорию</span>
      </div>
      <ChevronDown
        :size="18"
        :stroke-width="2"
        class="cat-selector__chevron"
        :class="{ 'cat-selector__chevron--open': isOpen }"
      />
    </button>

    <!-- Backdrop -->
    <div v-if="isOpen" class="cat-selector__backdrop" @click="closeDropdown" />

    <!-- Dropdown -->
    <Transition name="dropdown">
      <div v-if="isOpen" class="cat-selector__dropdown">
        <div class="cat-selector__list">
          <button
            v-for="cat in allCategories"
            :key="cat.id"
            type="button"
            class="cat-selector__option"
            :class="{ 'cat-selector__option--selected': modelValue === cat.id }"
            @click="selectCategory(cat.id)"
          >
            <span class="cat-selector__option-name">{{ cat.name }}</span>
            <div
              v-if="modelValue === cat.id"
              class="cat-selector__option-check"
            />
          </button>

          <!-- Divider -->
          <div class="cat-selector__divider" />

          <!-- Propose new category -->
          <div v-if="!showPropose" class="cat-selector__propose-trigger">
            <button
              type="button"
              class="cat-selector__option cat-selector__option--propose"
              @click="startPropose"
            >
              <Plus :size="16" :stroke-width="2" />
              <span class="cat-selector__option-name">Предложить категорию</span>
            </button>
          </div>

          <div v-else class="cat-selector__propose-form">
            <input
              ref="proposeInputRef"
              v-model="proposeInput"
              type="text"
              class="cat-selector__propose-input"
              placeholder="Название категории"
              maxlength="50"
              @keyup.enter="submitPropose"
            />
            <button
              type="button"
              class="cat-selector__propose-btn"
              :disabled="!proposeInput.trim() || proposing"
              @click="submitPropose"
            >
              <span v-if="proposing" class="cat-selector__spinner" />
              <span v-else>Отправить</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { Tag, ChevronDown, Plus } from 'lucide-vue-next'
import type { Category } from '@/types'
import * as categoriesApi from '@/api/categories'

const props = defineProps<{
  categories: Category[]
  modelValue: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

const isOpen = ref(false)
const showPropose = ref(false)
const proposeInput = ref('')
const proposing = ref(false)
const proposeInputRef = ref<HTMLInputElement | null>(null)
const localCategories = ref<Category[]>([])

const allCategories = computed(() => {
  const ids = new Set(props.categories.map((c) => c.id))
  const unique = localCategories.value.filter((c) => !ids.has(c.id))
  return [...props.categories, ...unique]
})

const selectedCategory = computed(() => {
  if (!props.modelValue) return undefined
  return allCategories.value.find((c) => c.id === props.modelValue)
})

function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (!isOpen.value) {
    showPropose.value = false
    proposeInput.value = ''
  }
}

function closeDropdown() {
  isOpen.value = false
  showPropose.value = false
  proposeInput.value = ''
}

function selectCategory(id: string) {
  emit('update:modelValue', id === props.modelValue ? null : id)
  isOpen.value = false
  showPropose.value = false
}

async function startPropose() {
  showPropose.value = true
  await nextTick()
  proposeInputRef.value?.focus()
}

async function submitPropose() {
  const name = proposeInput.value.trim()
  if (!name || proposing.value) return

  proposing.value = true
  try {
    const category = await categoriesApi.proposeCategory({ name })
    localCategories.value.push(category)
    emit('update:modelValue', category.id)
    proposeInput.value = ''
    showPropose.value = false
    isOpen.value = false
  } catch {
    // Silently fail — user can retry
  } finally {
    proposing.value = false
  }
}
</script>

<style scoped>
.cat-selector {
  position: relative;
}

.cat-selector__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 14px 16px;
  border: 1.5px solid color-mix(in srgb, var(--tg-theme-hint-color, #708499), transparent 75%);
  border-radius: 12px;
  background: color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #fff 3%);
  color: var(--tg-theme-text-color, #f5f5f5);
  font-size: 15px;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.cat-selector__trigger--active {
  border-color: var(--tg-theme-button-color, #5288c1);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%);
}

.cat-selector__trigger-left {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--tg-theme-button-color, #5288c1);
}

.cat-selector__selected {
  color: var(--tg-theme-text-color, #f5f5f5);
  font-weight: 500;
}

.cat-selector__placeholder {
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.7;
}

.cat-selector__chevron {
  color: var(--tg-theme-hint-color, #708499);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.cat-selector__chevron--open {
  transform: rotate(180deg);
}

/* Backdrop */
.cat-selector__backdrop {
  position: fixed;
  inset: 0;
  z-index: 19;
}

/* Dropdown */
.cat-selector__dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 20;
  border-radius: 14px;
  background: color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #fff 6%);
  border: 1px solid color-mix(in srgb, var(--tg-theme-hint-color, #708499), transparent 80%);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 2px 8px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.cat-selector__list {
  max-height: 260px;
  overflow-y: auto;
  padding: 6px;
}

.cat-selector__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--tg-theme-text-color, #f5f5f5);
  font-size: 15px;
  cursor: pointer;
  transition: background 0.15s ease;
  text-align: left;
}

.cat-selector__option:active {
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%);
}

.cat-selector__option--selected {
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 88%);
  font-weight: 500;
}

.cat-selector__option--selected .cat-selector__option-name {
  color: var(--tg-theme-button-color, #5288c1);
}

.cat-selector__option-name {
  flex: 1;
}

.cat-selector__option-check {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--tg-theme-button-color, #5288c1);
  box-shadow: 0 0 6px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 40%);
}

.cat-selector__option--propose {
  color: var(--tg-theme-button-color, #5288c1);
  font-weight: 500;
  font-size: 14px;
}

.cat-selector__divider {
  height: 1px;
  margin: 4px 10px;
  background: color-mix(in srgb, var(--tg-theme-hint-color, #708499), transparent 80%);
}

/* Propose form */
.cat-selector__propose-form {
  display: flex;
  gap: 8px;
  padding: 8px 10px 10px;
}

.cat-selector__propose-input {
  flex: 1;
  padding: 10px 12px;
  border: 1.5px solid color-mix(in srgb, var(--tg-theme-hint-color, #708499), transparent 75%);
  border-radius: 10px;
  background: color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #fff 3%);
  color: var(--tg-theme-text-color, #f5f5f5);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease;
}

.cat-selector__propose-input::placeholder {
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.6;
}

.cat-selector__propose-input:focus {
  border-color: var(--tg-theme-button-color, #5288c1);
}

.cat-selector__propose-btn {
  flex-shrink: 0;
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.cat-selector__propose-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.cat-selector__propose-btn:not(:disabled):active {
  transform: scale(0.95);
}

.cat-selector__spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

/* Dropdown transition */
.dropdown-enter-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dropdown-leave-active {
  transition: all 0.15s ease-in;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
