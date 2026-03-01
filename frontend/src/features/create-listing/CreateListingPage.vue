<template>
  <div class="create-page">
    <h1 class="create-page__title">Новое объявление</h1>

    <!-- Photo Upload -->
    <section class="create-page__section" style="animation-delay: 0s">
      <label class="form-label">
        <Camera :size="15" :stroke-width="2" />
        Фотографии
      </label>
      <PhotoUploadGrid v-model="photos" />
      <p v-if="submitted && photos.length === 0" class="form-error">
        Добавьте хотя бы одно фото
      </p>
    </section>

    <!-- Title -->
    <section class="create-page__section" style="animation-delay: 0.04s">
      <div class="form-label-row">
        <label class="form-label" for="listing-title">Название</label>
        <span
          class="form-counter"
          :class="{ 'form-counter--warn': title.length > 80 }"
        >
          {{ title.length }}/100
        </span>
      </div>
      <input
        id="listing-title"
        v-model="title"
        type="text"
        class="form-input"
        :class="{ 'form-input--error': submitted && !title.trim() }"
        maxlength="100"
        placeholder="Что продаёте?"
      />
    </section>

    <!-- Description -->
    <section class="create-page__section" style="animation-delay: 0.08s">
      <div class="form-label-row">
        <label class="form-label" for="listing-desc">Описание</label>
        <span
          class="form-counter"
          :class="{ 'form-counter--warn': description.length > 1800 }"
        >
          {{ description.length }}/2000
        </span>
      </div>
      <textarea
        id="listing-desc"
        ref="descRef"
        v-model="description"
        class="form-input form-textarea"
        :class="{ 'form-input--error': submitted && !description.trim() }"
        maxlength="2000"
        placeholder="Опишите товар подробнее"
        rows="4"
        @input="autoGrow"
      />
    </section>

    <!-- Price -->
    <section class="create-page__section" style="animation-delay: 0.12s">
      <label class="form-label" for="listing-price">Цена</label>
      <div class="form-input-wrap">
        <input
          id="listing-price"
          v-model="price"
          type="number"
          class="form-input form-input--price"
          :class="{ 'form-input--error': submitted && !isPriceValid }"
          min="1"
          step="1"
          inputmode="numeric"
          placeholder="0"
        />
        <span class="form-suffix">₽</span>
      </div>
    </section>

    <!-- Category -->
    <section class="create-page__section" style="animation-delay: 0.16s">
      <label class="form-label">Категория</label>
      <CategorySelector
        :categories="catalogStore.categories"
        v-model="selectedCategory"
      />
    </section>

    <!-- Error banner -->
    <Transition name="banner">
      <div v-if="submitError" class="create-page__error">
        {{ submitError }}
      </div>
    </Transition>

    <!-- Submit -->
    <div class="create-page__submit">
      <p v-if="uploadStep" class="create-page__progress">{{ uploadStep }}</p>
      <button
        type="button"
        class="submit-btn"
        :disabled="submitting"
        @click="handleSubmit"
      >
        <span v-if="submitting" class="submit-spinner" />
        <span v-else>Опубликовать</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Camera } from 'lucide-vue-next'
import { useListingStore } from '@/stores/listing'
import { useCatalogStore } from '@/stores/catalog'
import * as listingsApi from '@/api/listings'
import PhotoUploadGrid from './PhotoUploadGrid.vue'
import type { PhotoItem } from './PhotoUploadGrid.vue'
import { compressImage } from './PhotoUploadGrid.vue'
import CategorySelector from './CategorySelector.vue'

const router = useRouter()
const listingStore = useListingStore()
const catalogStore = useCatalogStore()

// Form state
const photos = ref<PhotoItem[]>([])
const title = ref('')
const description = ref('')
const price = ref('')
const selectedCategory = ref<string | null>(null)
const descRef = ref<HTMLTextAreaElement | null>(null)

// Submit state
const submitting = ref(false)
const submitError = ref('')
const uploadStep = ref('')
const submitted = ref(false)

// Validation
const isPriceValid = computed(() => {
  const n = parseFloat(price.value)
  return !isNaN(n) && n > 0
})

const isValid = computed(() => {
  return (
    photos.value.length > 0 &&
    title.value.trim().length > 0 &&
    title.value.length <= 100 &&
    description.value.trim().length > 0 &&
    description.value.length <= 2000 &&
    isPriceValid.value
  )
})

// Auto-grow textarea
function autoGrow() {
  const el = descRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

// Submit flow
async function handleSubmit() {
  submitted.value = true
  submitError.value = ''

  if (!isValid.value) return

  submitting.value = true
  uploadStep.value = 'Создаём объявление…'

  try {
    // 1. Create listing
    const listing = await listingStore.createListing({
      title: title.value.trim(),
      description: description.value.trim(),
      price: parseFloat(price.value),
      currency: 'RUB',
      category_id: selectedCategory.value || undefined,
    })

    // 2. Upload photos
    for (let i = 0; i < photos.value.length; i++) {
      uploadStep.value = `Загрузка фото ${i + 1}/${photos.value.length}…`

      // Get presigned upload URL
      const { upload_url, object_key, position } =
        await listingsApi.getPhotoUploadUrl(listing.id)

      // Compress image
      const compressed = await compressImage(photos.value[i].file)

      // PUT to presigned URL
      await axios.put(upload_url, compressed, {
        headers: { 'Content-Type': 'image/jpeg' },
      })

      // Confirm upload
      await listingsApi.confirmPhotoUpload(listing.id, {
        object_key,
        position,
      })
    }

    // 3. Redirect
    router.push('/my-listings')
  } catch (err) {
    submitError.value =
      err instanceof Error ? err.message : 'Не удалось создать объявление'
  } finally {
    submitting.value = false
    uploadStep.value = ''
  }
}

// Load categories on mount
onMounted(() => {
  if (catalogStore.categories.length === 0) {
    catalogStore.loadCategories()
  }
})

// Cleanup preview URLs
onBeforeUnmount(() => {
  photos.value.forEach((p) => URL.revokeObjectURL(p.preview))
})
</script>

<style scoped>
.create-page {
  max-width: 480px;
  margin: 0 auto;
  padding: 20px 16px 100px;
}

.create-page__title {
  margin: 0 0 24px;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--tg-theme-text-color, #f5f5f5);
}

/* Sections with staggered entrance */
.create-page__section {
  margin-bottom: 20px;
  animation: section-enter 0.35s ease both;
}

@keyframes section-enter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Labels */
.form-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--tg-theme-hint-color, #708499);
}

.form-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

/* Character counter */
.form-counter {
  font-size: 12px;
  font-weight: 500;
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.7;
  transition: color 0.2s, opacity 0.2s;
}

.form-counter--warn {
  color: #f59e0b;
  opacity: 1;
}

/* Inputs */
.form-input {
  width: 100%;
  padding: 14px 16px;
  background: color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #fff 3%);
  border: 1.5px solid color-mix(in srgb, var(--tg-theme-hint-color, #708499), transparent 75%);
  border-radius: 12px;
  color: var(--tg-theme-text-color, #f5f5f5);
  font-size: 16px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input::placeholder {
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.6;
}

.form-input:focus {
  border-color: var(--tg-theme-button-color, #5288c1);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%);
}

.form-input--error {
  border-color: #ef4444;
}

.form-input--error:focus {
  box-shadow: 0 0 0 3px color-mix(in srgb, #ef4444, transparent 85%);
}

/* Textarea */
.form-textarea {
  min-height: 120px;
  resize: none;
  line-height: 1.5;
}

/* Price input wrapper */
.form-input-wrap {
  position: relative;
}

.form-input--price {
  padding-right: 40px;
  -moz-appearance: textfield;
}

.form-input--price::-webkit-inner-spin-button,
.form-input--price::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.form-suffix {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  font-weight: 600;
  color: var(--tg-theme-hint-color, #708499);
  pointer-events: none;
}

/* Validation error */
.form-error {
  margin: 8px 0 0;
  font-size: 13px;
  font-weight: 500;
  color: #ef4444;
}

/* Submit error banner */
.create-page__error {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: color-mix(in srgb, #ef4444, transparent 88%);
  border: 1px solid color-mix(in srgb, #ef4444, transparent 65%);
  border-radius: 12px;
  color: #fca5a5;
  font-size: 14px;
}

.banner-enter-active {
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.banner-leave-active {
  transition: all 0.2s ease-in;
}

.banner-enter-from,
.banner-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Submit area */
.create-page__submit {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom, 0px));
  background: linear-gradient(
    to top,
    var(--tg-theme-bg-color, #17212b) 70%,
    transparent
  );
}

.create-page__progress {
  margin: 0 0 8px;
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: var(--tg-theme-hint-color, #708499);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  padding: 16px;
  border: none;
  border-radius: 14px;
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
  font-size: 17px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* Spinner */
.submit-spinner {
  display: inline-block;
  width: 22px;
  height: 22px;
  border: 2.5px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
