<template>
  <div class="profile-page">
    <!-- Avatar Section -->
    <div class="profile-hero">
      <div class="hero-glow" />
      <div class="avatar-wrapper">
        <div class="avatar-ring">
          <div class="avatar" :style="avatarStyle">
            <User v-if="!avatarSrc" :size="36" :stroke-width="1.5" />
          </div>
        </div>
        <button class="avatar-change-btn" @click="triggerFilePicker">
          <Camera :size="14" :stroke-width="2" />
          <span>Изменить фото</span>
        </button>
        <input
          ref="fileInputRef"
          type="file"
          accept="image/*"
          class="file-input-hidden"
          @change="handleAvatarChange"
        />
      </div>
      <div class="profile-name-display">
        <span class="display-name">{{ displayName }}</span>
        <span v-if="profile?.username" class="display-username">@{{ profile.username }}</span>
      </div>
    </div>

    <!-- Info Section -->
    <div class="profile-card">
      <div class="card-header">
        <span class="card-title">Личные данные</span>
        <button v-if="!isEditing" class="edit-trigger" @click="startEditing">
          <Edit :size="16" :stroke-width="2" />
          <span>Редактировать</span>
        </button>
      </div>

      <div class="fields-grid">
        <div class="field-row">
          <div class="field-icon">
            <User :size="18" :stroke-width="1.8" />
          </div>
          <div class="field-body">
            <label class="field-label">Имя</label>
            <input
              v-if="isEditing"
              v-model="form.first_name"
              type="text"
              class="field-input"
              placeholder="Введите имя"
            />
            <span v-else class="field-value">{{ profile?.first_name || '—' }}</span>
          </div>
        </div>

        <div class="field-row">
          <div class="field-icon">
            <User :size="18" :stroke-width="1.8" />
          </div>
          <div class="field-body">
            <label class="field-label">Фамилия</label>
            <input
              v-if="isEditing"
              v-model="form.last_name"
              type="text"
              class="field-input"
              placeholder="Введите фамилию"
            />
            <span v-else class="field-value">{{ profile?.last_name || '—' }}</span>
          </div>
        </div>

        <div class="field-row">
          <div class="field-icon">
            <Phone :size="18" :stroke-width="1.8" />
          </div>
          <div class="field-body">
            <label class="field-label">Телефон</label>
            <input
              v-if="isEditing"
              v-model="form.phone"
              type="tel"
              class="field-input"
              placeholder="+7 (999) 000-00-00"
            />
            <span v-else class="field-value">{{ profile?.phone || '—' }}</span>
          </div>
        </div>

        <div class="field-row">
          <div class="field-icon">
            <MapPin :size="18" :stroke-width="1.8" />
          </div>
          <div class="field-body">
            <label class="field-label">Город</label>
            <div v-if="isEditing" class="city-input-group">
              <input
                v-model="form.city"
                type="text"
                class="field-input"
                placeholder="Введите город"
              />
              <button
                class="gps-btn"
                :class="{ detecting: isDetectingCity }"
                :disabled="isDetectingCity"
                @click="detectCity"
              >
                <MapPin :size="14" :stroke-width="2.2" />
              </button>
            </div>
            <span v-else class="field-value">{{ profile?.city || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- Save / Cancel Actions -->
      <div v-if="isEditing" class="card-actions">
        <button class="btn-cancel" @click="cancelEditing">Отмена</button>
        <button class="btn-save" :disabled="isSaving || !isFormValid" @click="saveProfile">
          <span v-if="isSaving" class="spinner" />
          <span v-else>Сохранить</span>
        </button>
      </div>

      <!-- Success Toast -->
      <Transition name="toast">
        <div v-if="showSuccess" class="success-toast">
          <Check :size="16" :stroke-width="2.5" />
          <span>Профиль обновлён</span>
        </div>
      </Transition>
    </div>

    <!-- My Listings Link -->
    <router-link to="/my-listings" class="profile-link">
      <div class="link-content">
        <span class="link-text">Мои объявления</span>
      </div>
      <ChevronRight :size="20" :stroke-width="2" />
    </router-link>

    <!-- App Info -->
    <div class="app-info">
      <span class="app-info-text">Stella v0.1.0</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { User, Phone, MapPin, Camera, ChevronRight, Edit, Check } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import * as usersApi from '@/api/users'
import type { UserUpdate } from '@/types'

const userStore = useUserStore()
const profile = computed(() => userStore.profile)

const isEditing = ref(false)
const isSaving = ref(false)
const isDetectingCity = ref(false)
const showSuccess = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const form = reactive<UserUpdate>({
  first_name: '',
  last_name: '',
  phone: '',
  city: '',
})

const displayName = computed(() => {
  const p = profile.value
  if (!p) return ''
  return [p.first_name, p.last_name].filter(Boolean).join(' ')
})

const avatarSrc = computed(() => profile.value?.avatar_url || null)

const avatarStyle = computed(() => {
  if (avatarSrc.value) {
    return { backgroundImage: `url(${avatarSrc.value})` }
  }
  return {}
})

const isFormValid = computed(() => {
  return !!(form.first_name?.trim() && form.phone?.trim() && form.city?.trim())
})

function startEditing(): void {
  const p = profile.value
  if (p) {
    form.first_name = p.first_name || ''
    form.last_name = p.last_name || ''
    form.phone = p.phone || ''
    form.city = p.city || ''
  }
  isEditing.value = true
}

function cancelEditing(): void {
  isEditing.value = false
}

async function saveProfile(): Promise<void> {
  isSaving.value = true
  try {
    const data: UserUpdate = {
      first_name: form.first_name,
      last_name: form.last_name,
      phone: form.phone,
      city: form.city,
    }
    await userStore.updateProfile(data)
    isEditing.value = false
    showSuccess.value = true
    setTimeout(() => {
      showSuccess.value = false
    }, 2500)
  } finally {
    isSaving.value = false
  }
}

async function detectCity(): Promise<void> {
  isDetectingCity.value = true
  try {
    await new Promise<void>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          try {
            const { latitude, longitude } = pos.coords
            const resp = await fetch(
              `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`,
            )
            const data: Record<string, Record<string, string>> = await resp.json()
            form.city =
              data.address?.city || data.address?.town || data.address?.village || ''
            resolve()
          } catch {
            reject(new Error('Geocoding failed'))
          }
        },
        () => reject(new Error('Geolocation denied')),
        { timeout: 10000 },
      )
    })
  } finally {
    isDetectingCity.value = false
  }
}

function triggerFilePicker(): void {
  fileInputRef.value?.click()
}

async function handleAvatarChange(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    // Compress image via canvas
    const compressed = await compressImage(file, 512, 0.8)

    // Get presigned upload URL
    const { upload_url, object_key } = await usersApi.getAvatarUploadUrl()

    // Upload to presigned URL
    await fetch(upload_url, {
      method: 'PUT',
      body: compressed,
      headers: { 'Content-Type': 'image/jpeg' },
    })

    // Build the public avatar URL from object_key
    const baseUrl = import.meta.env.VITE_STORAGE_URL || ''
    const avatarUrl = baseUrl ? `${baseUrl}/${object_key}` : object_key

    // Update profile with new avatar URL
    await userStore.updateProfile({ avatar_url: avatarUrl })

    showSuccess.value = true
    setTimeout(() => {
      showSuccess.value = false
    }, 2500)
  } finally {
    // Reset file input
    target.value = ''
  }
}

function compressImage(file: File, maxSize: number, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      const canvas = document.createElement('canvas')
      let w = img.width
      let h = img.height
      if (w > maxSize || h > maxSize) {
        const ratio = Math.min(maxSize / w, maxSize / h)
        w = Math.round(w * ratio)
        h = Math.round(h * ratio)
      }
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Canvas not supported'))
        return
      }
      ctx.drawImage(img, 0, 0, w, h)
      canvas.toBlob(
        (blob) => {
          if (blob) resolve(blob)
          else reject(new Error('Compression failed'))
        },
        'image/jpeg',
        quality,
      )
    }
    img.onerror = () => reject(new Error('Image load failed'))
    img.src = url
  })
}

onMounted(() => {
  if (!profile.value) {
    userStore.fetchProfile()
  }
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding: 0 0 32px;
  background: var(--tg-theme-bg-color, #17212b);
  color: var(--tg-theme-text-color, #f5f5f5);
}

/* ── Hero / Avatar ── */
.profile-hero {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px 28px;
  overflow: hidden;
}

.hero-glow {
  position: absolute;
  top: -60px;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(
    ellipse at center,
    color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 82%),
    transparent 70%
  );
  pointer-events: none;
  filter: blur(30px);
}

.avatar-wrapper {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-ring {
  padding: 3px;
  border-radius: 50%;
  background: linear-gradient(
    135deg,
    var(--tg-theme-button-color, #5288c1),
    color-mix(in srgb, var(--tg-theme-button-color, #5288c1), #fff 30%)
  );
  box-shadow:
    0 4px 24px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 70%),
    0 0 0 1px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%);
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 8%);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--tg-theme-hint-color, #708499);
  border: 2px solid var(--tg-theme-bg-color, #17212b);
}

.avatar-change-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  border-radius: 20px;
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%);
  color: var(--tg-theme-button-color, #5288c1);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease;
}

.avatar-change-btn:active {
  transform: scale(0.96);
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 75%);
}

.file-input-hidden {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.profile-name-display {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  margin-top: 16px;
}

.display-name {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--tg-theme-text-color, #f5f5f5);
}

.display-username {
  font-size: 14px;
  color: var(--tg-theme-hint-color, #708499);
}

/* ── Profile Card ── */
.profile-card {
  position: relative;
  margin: 0 16px;
  padding: 20px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 5%);
  border: 1px solid color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 10%);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--tg-theme-text-color, #f5f5f5);
  letter-spacing: 0.01em;
}

.edit-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: none;
  border-radius: 10px;
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 88%);
  color: var(--tg-theme-button-color, #5288c1);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.edit-trigger:active {
  transform: scale(0.96);
}

/* ── Fields ── */
.fields-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 8%);
}

.field-row:last-child {
  border-bottom: none;
}

.field-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 90%);
  color: var(--tg-theme-button-color, #5288c1);
  margin-top: 2px;
}

.field-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--tg-theme-hint-color, #708499);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-value {
  font-size: 15px;
  font-weight: 400;
  color: var(--tg-theme-text-color, #f5f5f5);
  line-height: 1.4;
}

.field-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 15%);
  border-radius: 10px;
  background: color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 3%);
  color: var(--tg-theme-text-color, #f5f5f5);
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.field-input::placeholder {
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.6;
}

.field-input:focus {
  border-color: var(--tg-theme-button-color, #5288c1);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%);
}

/* ── City GPS ── */
.city-input-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.city-input-group .field-input {
  flex: 1;
}

.gps-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 60%);
  border-radius: 10px;
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 88%);
  color: var(--tg-theme-button-color, #5288c1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.gps-btn:active {
  transform: scale(0.92);
}

.gps-btn.detecting {
  animation: pulse-gps 1s ease-in-out infinite;
}

@keyframes pulse-gps {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Actions ── */
.card-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 8%);
}

.btn-cancel {
  flex: 1;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 15%);
  border-radius: 12px;
  background: transparent;
  color: var(--tg-theme-hint-color, #708499);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:active {
  transform: scale(0.97);
  background: color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 5%);
}

.btn-save {
  flex: 1.5;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: none;
  border-radius: 12px;
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 60%);
}

.btn-save:active {
  transform: scale(0.97);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid color-mix(in srgb, var(--tg-theme-button-text-color, #fff), transparent 60%);
  border-top-color: var(--tg-theme-button-text-color, #fff);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Success Toast ── */
.success-toast {
  position: absolute;
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%) translateY(100%);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 24px;
  background: #22c55e;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  box-shadow: 0 8px 24px rgba(34, 197, 94, 0.3);
  z-index: 10;
}

.toast-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-leave-active {
  transition: all 0.25s ease-in;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(calc(100% + 12px)) scale(0.9);
}

/* ── Links ── */
.profile-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 20px 16px 0;
  padding: 16px 18px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 5%);
  border: 1px solid color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 10%);
  text-decoration: none;
  color: var(--tg-theme-text-color, #f5f5f5);
  transition: all 0.2s ease;
}

.profile-link:active {
  transform: scale(0.98);
  background: color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 8%);
}

.link-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.link-text {
  font-size: 15px;
  font-weight: 500;
}

.profile-link svg:last-child {
  color: var(--tg-theme-hint-color, #708499);
}

/* ── App Info ── */
.app-info {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding: 0 16px;
}

.app-info-text {
  font-size: 12px;
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.6;
  letter-spacing: 0.04em;
}
</style>
