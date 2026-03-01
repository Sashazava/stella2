<template>
  <div class="upload-grid">
    <div
      v-for="(slot, idx) in displaySlots"
      :key="idx"
      class="upload-slot"
      :class="{
        'upload-slot--hero': idx === 0,
        'upload-slot--filled': !!slot,
      }"
    >
      <template v-if="slot">
        <img :src="slot.preview" :alt="`Фото ${idx + 1}`" class="upload-img" />
        <button type="button" class="upload-remove" @click="remove(idx)">
          <X :size="14" :stroke-width="2.5" />
        </button>
        <span v-if="idx === 0" class="upload-badge">Обложка</span>
      </template>
      <button v-else type="button" class="upload-add" @click="pickFile">
        <Camera v-if="idx === 0" :size="28" :stroke-width="1.6" />
        <Plus v-else :size="22" :stroke-width="2" />
      </button>
    </div>

    <input
      ref="inputRef"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      multiple
      class="upload-input-hidden"
      @change="onPick"
    />
  </div>
</template>

<script lang="ts">
export interface PhotoItem {
  file: File
  preview: string
}

export async function compressImage(file: File): Promise<Blob> {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas')
    const img = new Image()
    img.onload = () => {
      const maxWidth = 1200
      const scale = Math.min(1, maxWidth / img.width)
      canvas.width = img.width * scale
      canvas.height = img.height * scale
      canvas.getContext('2d')!.drawImage(img, 0, 0, canvas.width, canvas.height)
      canvas.toBlob((blob) => resolve(blob!), 'image/jpeg', 0.8)
    }
    img.src = URL.createObjectURL(file)
  })
}
</script>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Camera, Plus, X } from 'lucide-vue-next'

const MAX_PHOTOS = 5

const props = defineProps<{
  modelValue: PhotoItem[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: PhotoItem[]]
}>()

const inputRef = ref<HTMLInputElement | null>(null)

const displaySlots = computed(() => {
  const slots: (PhotoItem | null)[] = []
  for (let i = 0; i < MAX_PHOTOS; i++) {
    slots.push(props.modelValue[i] ?? null)
  }
  return slots
})

function pickFile() {
  inputRef.value?.click()
}

function onPick(e: Event) {
  const el = e.target as HTMLInputElement
  if (!el.files?.length) return

  const remaining = MAX_PHOTOS - props.modelValue.length
  if (remaining <= 0) return

  const items: PhotoItem[] = Array.from(el.files)
    .slice(0, remaining)
    .map((f) => ({ file: f, preview: URL.createObjectURL(f) }))

  emit('update:modelValue', [...props.modelValue, ...items])
  el.value = ''
}

function remove(index: number) {
  const item = props.modelValue[index]
  if (item) URL.revokeObjectURL(item.preview)
  emit(
    'update:modelValue',
    props.modelValue.filter((_, i) => i !== index),
  )
}
</script>

<style scoped>
.upload-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.upload-slot {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  background: color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 6%);
  border: 1px solid color-mix(in srgb, var(--tg-theme-bg-color, #17212b), #fff 10%);
  animation: slot-enter 0.3s ease both;
}

.upload-slot--hero {
  grid-column: span 2;
  grid-row: span 2;
  aspect-ratio: auto;
}

.upload-slot:not(.upload-slot--filled) {
  border: 2px dashed color-mix(in srgb, var(--tg-theme-hint-color, #708499), transparent 50%);
  background: transparent;
}

.upload-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.upload-remove {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.upload-remove:active {
  transform: scale(0.9);
  background: rgba(220, 38, 38, 0.8);
}

.upload-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(4px);
  color: #fff;
}

.upload-add {
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  color: var(--tg-theme-hint-color, #708499);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
}

.upload-add:active {
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 90%);
  color: var(--tg-theme-button-color, #5288c1);
}

.upload-input-hidden {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

@keyframes slot-enter {
  from {
    opacity: 0;
    transform: scale(0.92);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
