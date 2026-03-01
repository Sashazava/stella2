<template>
  <div class="listing-card" @click="$emit('click')">
    <div class="listing-card__image">
      <img
        v-if="listing.photos.length > 0"
        :src="listing.photos[0].url"
        :alt="listing.title"
        class="listing-card__photo"
        loading="lazy"
      />
      <div v-else class="listing-card__placeholder">
        <ImageOff :size="28" :stroke-width="1.5" />
      </div>
    </div>

    <div class="listing-card__body">
      <p class="listing-card__title">{{ listing.title }}</p>
      <span class="listing-card__price">{{ formatPrice(listing.price) }}</span>
      <span v-if="listing.city" class="listing-card__city">
        <MapPin :size="12" :stroke-width="2" />
        {{ listing.city }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Listing } from '@/types'
import { MapPin, ImageOff } from 'lucide-vue-next'

defineProps<{
  listing: Listing
}>()

defineEmits<{
  click: []
}>()

function formatPrice(price: number | string): string {
  return new Intl.NumberFormat('ru-RU').format(Number(price)) + ' ₽'
}
</script>

<style scoped>
.listing-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-card);
  background: var(--tg-theme-secondary-bg-color, #232e3c);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  -webkit-tap-highlight-color: transparent;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.04) inset;
}

.listing-card:active {
  transform: scale(0.97);
}

.listing-card__image {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  background: color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #000 15%);
  overflow: hidden;
}

.listing-card__photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.listing-card__placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.4;
}

.listing-card__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px 12px;
}

.listing-card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.35;
  color: var(--tg-theme-text-color, #f5f5f5);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.listing-card__price {
  font-size: 16px;
  font-weight: 700;
  color: var(--tg-theme-text-color, #f5f5f5);
  letter-spacing: -0.01em;
}

.listing-card__city {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: var(--tg-theme-hint-color, #708499);
  margin-top: 2px;
}
</style>
