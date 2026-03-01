<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { User as UserIcon, Phone, MapPin, Camera } from 'lucide-vue-next'
import RegistrationStep from './RegistrationStep.vue'
import { useTelegramStore } from '@/stores/telegram'
import { useUserStore } from '@/stores/user'
import { getAvatarUploadUrl } from '@/api/users'

const router = useRouter()
const telegramStore = useTelegramStore()
const userStore = useUserStore()

// --- State ---
const step = ref(1)
const direction = ref<'left' | 'right'>('left')
const isSubmitting = ref(false)
const isLocating = ref(false)
const gpsError = ref(false)
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | undefined>()
const fileInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  first_name: '',
  last_name: '',
  phone: '',
  city: '',
  latitude: undefined as number | undefined,
  longitude: undefined as number | undefined,
})

// --- Pre-fill from Telegram ---
onMounted(() => {
  if (telegramStore.user) {
    form.first_name = telegramStore.user.firstName || ''
    form.last_name = telegramStore.user.lastName || ''
    avatarPreview.value = telegramStore.user.photoUrl
  }
})

// --- Step config ---
const stepIcons = [UserIcon, Phone, MapPin, Camera] as const
const stepTitles = ['Как вас зовут?', 'Номер телефона', 'Ваш город', 'Фото профиля']
const stepSubtitles = [
  'Введите ваше имя',
  'Для связи с покупателями',
  'Чтобы показывать товары рядом',
  'Чтобы вас узнавали',
]

const currentIcon = computed(() => stepIcons[step.value - 1])
const currentTitle = computed(() => stepTitles[step.value - 1])
const currentSubtitle = computed(() => stepSubtitles[step.value - 1])

// --- Validation ---
const canProceed = computed(() => {
  switch (step.value) {
    case 1:
      return form.first_name.trim().length > 0
    case 2:
      return form.phone.trim().length > 0
    case 3:
      return form.city.trim().length > 0
    case 4:
      return true
    default:
      return false
  }
})

// --- Navigation ---
function goNext() {
  if (step.value < 4) {
    direction.value = 'left'
    step.value++
  } else {
    submit()
  }
}

function goBack() {
  if (step.value > 1) {
    direction.value = 'right'
    step.value--
  }
}

// --- GPS detection ---
async function detectLocation() {
  if (!navigator.geolocation) {
    gpsError.value = true
    return
  }

  isLocating.value = true
  gpsError.value = false

  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 10000,
      })
    })

    const { latitude, longitude } = position.coords
    form.latitude = latitude
    form.longitude = longitude

    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`,
      { headers: { 'Accept-Language': 'ru' } },
    )
    const data = await response.json()
    const city =
      data.address?.city ||
      data.address?.town ||
      data.address?.village ||
      data.address?.state ||
      ''
    form.city = city
  } catch {
    gpsError.value = true
  } finally {
    isLocating.value = false
  }
}

// --- Avatar ---
function openFilePicker() {
  fileInput.value?.click()
}

function onFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    avatarFile.value = file
    avatarPreview.value = URL.createObjectURL(file)
  }
}

// --- Submit ---
async function submit() {
  isSubmitting.value = true

  await userStore.register({
    first_name: form.first_name.trim(),
    last_name: form.last_name.trim() || undefined,
    phone: '+7' + form.phone.trim(),
    city: form.city.trim(),
    latitude: form.latitude,
    longitude: form.longitude,
  })

  if (userStore.error) {
    isSubmitting.value = false
    return
  }

  // Upload avatar if selected (non-critical)
  if (avatarFile.value) {
    try {
      const { upload_url } = await getAvatarUploadUrl()
      await fetch(upload_url, {
        method: 'PUT',
        body: avatarFile.value,
        headers: { 'Content-Type': avatarFile.value.type },
      })
    } catch {
      // Avatar upload failure is non-critical — user can update later
    }
  }

  isSubmitting.value = false
  await router.push('/catalog')
}

// --- Telegram BackButton: intercept router.back() on step > 1 ---
onBeforeRouteLeave(() => {
  if (step.value > 1) {
    goBack()
    return false
  }
})
</script>

<template>
  <RegistrationStep
    :current-step="step"
    :total-steps="4"
    :can-proceed="canProceed"
    :is-loading="isSubmitting"
    @next="goNext"
    @back="goBack"
  >
    <Transition :name="'slide-' + direction" mode="out-in">
      <div :key="step" class="px-6 pt-6">
        <!-- Step header -->
        <div class="step-header">
          <div class="step-icon-ring">
            <component :is="currentIcon" :size="28" class="step-icon" />
          </div>
          <h1 class="step-title">{{ currentTitle }}</h1>
          <p class="step-subtitle">{{ currentSubtitle }}</p>
        </div>

        <!-- Step 1: Name -->
        <div v-if="step === 1" class="fields">
          <input
            v-model="form.first_name"
            type="text"
            placeholder="Имя *"
            autocomplete="given-name"
            class="reg-input"
          />
          <input
            v-model="form.last_name"
            type="text"
            placeholder="Фамилия (необязательно)"
            autocomplete="family-name"
            class="reg-input"
          />
        </div>

        <!-- Step 2: Phone -->
        <div v-else-if="step === 2" class="fields">
          <div class="phone-row">
            <span class="phone-prefix">+7</span>
            <input
              v-model="form.phone"
              type="tel"
              placeholder="9XX XXX XX XX"
              autocomplete="tel-national"
              class="phone-input"
            />
          </div>
        </div>

        <!-- Step 3: City -->
        <div v-else-if="step === 3" class="fields">
          <button
            type="button"
            class="gps-btn"
            :disabled="isLocating"
            @click="detectLocation"
          >
            <span
              v-if="isLocating"
              class="gps-spinner"
            />
            <template v-else>
              <span class="gps-emoji">📍</span>
              <span>Определить автоматически</span>
            </template>
          </button>

          <p v-if="gpsError" class="gps-hint">
            Не удалось определить. Введите город вручную:
          </p>

          <input
            v-model="form.city"
            type="text"
            placeholder="Введите название города"
            class="reg-input"
          />
        </div>

        <!-- Step 4: Avatar -->
        <div v-else-if="step === 4" class="avatar-section">
          <div class="avatar-ring">
            <img
              v-if="avatarPreview"
              :src="avatarPreview"
              alt="Avatar"
              class="avatar-img"
            />
            <Camera v-else :size="40" class="avatar-placeholder" />
          </div>

          <button
            type="button"
            class="avatar-change-btn"
            @click="openFilePicker"
          >
            {{ avatarPreview ? 'Изменить фото' : 'Загрузить фото' }}
          </button>

          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            class="hidden-input"
            @change="onFileSelect"
          />

          <p class="avatar-hint">Необязательно — можно добавить позже</p>
        </div>

        <!-- Error message -->
        <p v-if="userStore.error && step === 4" class="error-msg">
          {{ userStore.error }}
        </p>
      </div>
    </Transition>
  </RegistrationStep>
</template>

<style scoped>
/* --- Step header --- */
.step-header {
  text-align: center;
  margin-bottom: 32px;
}

.step-icon-ring {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-primary);
  opacity: 0.12;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  position: relative;
}

/* Icon sits on top of the ring with full opacity */
.step-icon-ring::after {
  content: '';
}

.step-icon {
  color: var(--color-primary);
  /* Override parent opacity for the icon */
  position: relative;
  z-index: 1;
}

/* Fix: ring bg has opacity, icon should not */
.step-icon-ring {
  background: transparent;
}

.step-icon-ring::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--color-primary);
  opacity: 0.12;
}

.step-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--color-text);
}

.step-subtitle {
  font-size: 14px;
  color: var(--color-hint);
  margin: 0;
}

/* --- Fields --- */
.fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reg-input {
  width: 100%;
  height: 50px;
  padding: 0 16px;
  border-radius: var(--radius-card);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 16px;
  outline: none;
  border: 1.5px solid transparent;
  transition: border-color 0.2s ease;
  font-family: inherit;
}

.reg-input:focus {
  border-color: var(--color-primary);
}

.reg-input::placeholder {
  color: var(--color-hint);
  opacity: 0.5;
}

/* --- Phone --- */
.phone-row {
  display: flex;
  align-items: center;
  height: 50px;
  background: var(--color-surface);
  border-radius: var(--radius-card);
  border: 1.5px solid transparent;
  transition: border-color 0.2s ease;
  overflow: hidden;
}

.phone-row:focus-within {
  border-color: var(--color-primary);
}

.phone-prefix {
  padding-left: 16px;
  padding-right: 4px;
  color: var(--color-hint);
  font-size: 16px;
  font-weight: 500;
  user-select: none;
  flex-shrink: 0;
}

.phone-input {
  flex: 1;
  height: 100%;
  background: transparent;
  color: var(--color-text);
  font-size: 16px;
  outline: none;
  border: none;
  padding: 0 16px 0 8px;
  font-family: inherit;
}

.phone-input::placeholder {
  color: var(--color-hint);
  opacity: 0.5;
}

/* --- GPS --- */
.gps-btn {
  width: 100%;
  height: 50px;
  border-radius: var(--radius-card);
  background: transparent;
  border: 1.5px solid var(--color-primary);
  color: var(--color-primary);
  font-weight: 500;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background 0.15s, transform 0.1s;
}

.gps-btn:active {
  background: var(--color-primary);
  color: #fff;
  transform: scale(0.98);
}

.gps-btn:disabled {
  opacity: 0.6;
  pointer-events: none;
}

.gps-emoji {
  font-size: 18px;
}

.gps-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.gps-hint {
  font-size: 13px;
  text-align: center;
  color: var(--color-hint);
  margin: 0;
}

/* --- Avatar --- */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar-ring {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: var(--color-surface);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  color: var(--color-hint);
  opacity: 0.35;
}

.avatar-change-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 16px;
  transition: opacity 0.15s;
}

.avatar-change-btn:active {
  opacity: 0.7;
}

.avatar-hint {
  font-size: 13px;
  color: var(--color-hint);
  margin-top: 12px;
}

.hidden-input {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
}

/* --- Error --- */
.error-msg {
  color: #f87171;
  font-size: 13px;
  text-align: center;
  margin-top: 16px;
}

/* --- Slide transitions --- */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.22s ease-out;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(24px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-24px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-24px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(24px);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
