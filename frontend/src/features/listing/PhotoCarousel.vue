<template>
  <div class="carousel">
    <div
      v-if="sortedPhotos.length"
      ref="trackRef"
      class="carousel-track"
      @scroll="onScroll"
    >
      <div
        v-for="photo in sortedPhotos"
        :key="photo.url"
        class="carousel-slide"
      >
        <img
          :src="photo.url"
          :alt="`Photo ${photo.position + 1}`"
          class="carousel-image"
          loading="lazy"
        />
      </div>
    </div>

    <div v-else class="carousel-empty">
      <Camera :size="40" :stroke-width="1.2" />
      <span>Нет фотографий</span>
    </div>

    <div v-if="sortedPhotos.length > 1" class="carousel-dots">
      <button
        v-for="(_, index) in sortedPhotos"
        :key="index"
        class="carousel-dot"
        :class="{ 'carousel-dot--active': index === currentIndex }"
        :aria-label="`Photo ${index + 1}`"
        @click="scrollTo(index)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Camera } from 'lucide-vue-next'
import type { ListingPhoto } from '@/types'

const props = defineProps<{
  photos: ListingPhoto[]
}>()

const trackRef = ref<HTMLElement | null>(null)
const currentIndex = ref(0)

const sortedPhotos = computed(() =>
  [...props.photos].sort((a, b) => a.position - b.position),
)

function onScroll() {
  const track = trackRef.value
  if (!track) return
  const slideWidth = track.clientWidth
  if (slideWidth === 0) return
  currentIndex.value = Math.round(track.scrollLeft / slideWidth)
}

function scrollTo(index: number) {
  const track = trackRef.value
  if (!track) return
  track.scrollTo({
    left: index * track.clientWidth,
    behavior: 'smooth',
  })
}
</script>

<style scoped>
.carousel {
  position: relative;
  width: 100%;
  background: var(--tg-theme-secondary-bg-color, #232e3c);
}

.carousel-track {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.carousel-track::-webkit-scrollbar {
  display: none;
}

.carousel-slide {
  flex: 0 0 100%;
  scroll-snap-align: start;
  aspect-ratio: 4 / 3;
}

.carousel-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.carousel-empty {
  aspect-ratio: 4 / 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--tg-theme-hint-color, #708499);
  font-size: 14px;
}

.carousel-dots {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
  padding: 5px 10px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.carousel-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: none;
  padding: 0;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.4);
  transition: all 0.25s ease;
}

.carousel-dot--active {
  background: #fff;
  transform: scale(1.25);
}
</style>
