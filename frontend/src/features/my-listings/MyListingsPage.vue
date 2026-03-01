<template>
  <div class="my-listings-page">
    <header class="page-header">
      <h1 class="page-title">Мои объявления</h1>
    </header>

    <!-- Loading -->
    <div v-if="store.loading" class="loading-state">
      <div class="loading-spinner" />
    </div>

    <!-- Empty state -->
    <div v-else-if="store.myListings.length === 0" class="empty-state">
      <div class="empty-icon-wrap">
        <Package :size="48" :stroke-width="1.2" class="empty-icon" />
      </div>
      <p class="empty-text">У вас пока нет объявлений</p>
      <button class="create-btn" @click="goToCreate">
        <Plus :size="18" :stroke-width="2" />
        Создать объявление
      </button>
    </div>

    <!-- Listings -->
    <div v-else class="listings-list">
      <div
        v-for="listing in store.myListings"
        :key="listing.id"
        class="listing-card"
        @click="goToListing(listing.id)"
      >
        <div class="listing-photo">
          <img
            v-if="listing.photos.length > 0"
            :src="listing.photos[0].url"
            :alt="listing.title"
            class="photo-img"
          />
          <Package v-else :size="24" :stroke-width="1.5" class="photo-placeholder-icon" />
        </div>

        <div class="listing-info">
          <h3 class="listing-title">{{ listing.title }}</h3>
          <span class="listing-price">{{ formatPrice(listing.price, listing.currency) }}</span>
        </div>

        <div class="listing-end">
          <span :class="['status-badge', statusConfig[listing.status].class]">
            {{ statusConfig[listing.status].label }}
          </span>
          <ChevronRight :size="18" :stroke-width="1.5" class="chevron-icon" />
        </div>
      </div>
    </div>

    <!-- FAB -->
    <button class="fab" @click="onFabClick" aria-label="Создать объявление">
      <Plus :size="28" :stroke-width="2.5" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, ChevronRight, Package } from 'lucide-vue-next'
import { hapticFeedback } from '@telegram-apps/sdk-vue'
import { useListingStore } from '@/stores/listing'
import type { ListingStatus } from '@/types'

const router = useRouter()
const store = useListingStore()

const statusConfig: Record<ListingStatus, { label: string; class: string }> = {
  pending: { label: 'На проверке', class: 'badge-pending' },
  approved: { label: 'Опубликовано', class: 'badge-approved' },
  rejected: { label: 'Отклонено', class: 'badge-rejected' },
}

onMounted(() => {
  store.fetchMyListings()
})

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency || 'RUB',
    maximumFractionDigits: 0,
  }).format(price)
}

function goToListing(id: string) {
  router.push(`/catalog/${id}`)
}

function goToCreate() {
  router.push('/create-listing')
}

function onFabClick() {
  if (hapticFeedback.impactOccurred.isAvailable()) {
    hapticFeedback.impactOccurred('light')
  }
  router.push('/create-listing')
}
</script>

<style scoped>
.my-listings-page {
  min-height: 100vh;
  background: var(--tg-theme-bg-color, #17212b);
  padding-bottom: 100px;
}

/* Header */
.page-header {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 20px 16px 12px;
  background: var(--tg-theme-bg-color, #17212b);
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--tg-theme-text-color, #f5f5f5);
}

/* Loading */
.loading-state {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 2.5px solid color-mix(in srgb, var(--tg-theme-hint-color, #708499), transparent 70%);
  border-top-color: var(--tg-theme-button-color, #5288c1);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 32px;
  gap: 16px;
}

.empty-icon-wrap {
  width: 88px;
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 88%);
}

.empty-icon {
  color: var(--tg-theme-button-color, #5288c1);
  opacity: 0.7;
}

.empty-text {
  margin: 0;
  font-size: 16px;
  color: var(--tg-theme-hint-color, #708499);
  text-align: center;
}

.create-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: var(--radius-button, 10px);
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.create-btn:active {
  opacity: 0.75;
}

/* Listings list */
.listings-list {
  display: flex;
  flex-direction: column;
  padding: 0 16px;
  gap: 2px;
}

.listing-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-card, 12px);
  background: var(--tg-theme-secondary-bg-color, #232e3c);
  cursor: pointer;
  transition: background 0.15s;
}

.listing-card:active {
  background: color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #fff 5%);
}

/* Photo */
.listing-photo {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: 10px;
  overflow: hidden;
  background: color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #000 20%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder-icon {
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.5;
}

/* Info */
.listing-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.listing-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--tg-theme-text-color, #f5f5f5);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.listing-price {
  font-size: 14px;
  font-weight: 500;
  color: var(--tg-theme-button-color, #5288c1);
}

/* End column */
.listing-end {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.chevron-icon {
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.5;
}

/* Status badges */
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  line-height: 1.4;
}

.badge-pending {
  background: color-mix(in srgb, #eab308, transparent 82%);
  color: #facc15;
}

.badge-approved {
  background: color-mix(in srgb, #22c55e, transparent 82%);
  color: #4ade80;
}

.badge-rejected {
  background: color-mix(in srgb, #ef4444, transparent 82%);
  color: #f87171;
}

/* FAB */
.fab {
  position: fixed;
  bottom: 24px;
  right: 20px;
  z-index: 50;
  width: 56px;
  height: 56px;
  border: none;
  border-radius: 16px;
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow:
    0 4px 16px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 50%),
    0 1px 3px rgba(0, 0, 0, 0.3);
  transition: transform 0.15s, box-shadow 0.15s;
}

.fab:active {
  transform: scale(0.92);
  box-shadow:
    0 2px 8px color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 60%),
    0 1px 2px rgba(0, 0, 0, 0.3);
}
</style>
