<template>
  <div class="listing-page">
    <!-- Loading skeleton -->
    <div v-if="loading" class="listing-loading">
      <div class="skeleton skeleton-carousel" />
      <div class="skeleton-body">
        <div class="skeleton skeleton-title" />
        <div class="skeleton skeleton-price" />
        <div class="skeleton-row">
          <div class="skeleton skeleton-chip" />
          <div class="skeleton skeleton-chip" />
        </div>
        <div class="skeleton skeleton-text" />
        <div class="skeleton skeleton-text" />
        <div class="skeleton skeleton-text-short" />
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="listing-error">
      <p class="listing-error-text">{{ error }}</p>
    </div>

    <!-- Content -->
    <template v-else-if="listing">
      <PhotoCarousel :photos="listing.photos" />

      <div class="listing-body">
        <!-- Header: title + owner status badge -->
        <div class="listing-header">
          <h1 class="listing-title">{{ listing.title }}</h1>
          <span
            v-if="isOwner"
            class="status-badge"
            :class="`status-badge--${listing.status}`"
          >
            {{ statusLabel }}
          </span>
        </div>

        <!-- Price -->
        <p class="listing-price">{{ formattedPrice }}</p>

        <!-- Meta chips -->
        <div class="listing-meta">
          <div v-if="listing.category" class="listing-chip">
            <Tag :size="14" :stroke-width="2" />
            <span>{{ listing.category.name }}</span>
          </div>
          <div v-if="listing.city" class="listing-chip">
            <MapPin :size="14" :stroke-width="2" />
            <span>{{ listing.city }}</span>
          </div>
        </div>

        <!-- Description -->
        <div class="listing-section">
          <h2 class="section-title">Описание</h2>
          <p class="listing-description">{{ listing.description }}</p>
        </div>

        <!-- Seller -->
        <div v-if="listing.seller" class="seller-card">
          <div class="seller-avatar">
            <img
              v-if="listing.seller.avatar_url"
              :src="listing.seller.avatar_url"
              :alt="sellerName"
              class="seller-avatar-img"
            />
            <span v-else class="seller-avatar-initial">
              {{ sellerInitial }}
            </span>
          </div>
          <div class="seller-info">
            <span class="seller-name">{{ sellerName }}</span>
            <span class="seller-since">{{ memberSince }}</span>
          </div>
        </div>

        <!-- Bottom spacer for fixed contact button -->
        <div class="listing-bottom-spacer" />
      </div>

      <!-- Contact button (hidden for own listings) -->
      <SellerContactButton
        v-if="listing.seller && !isOwner"
        :seller="listing.seller"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { MapPin, Tag } from 'lucide-vue-next'
import { useListingStore } from '@/stores/listing'
import { useUserStore } from '@/stores/user'
import PhotoCarousel from './PhotoCarousel.vue'
import SellerContactButton from './SellerContactButton.vue'

const route = useRoute()
const listingStore = useListingStore()
const userStore = useUserStore()

const { currentListing: listing, loading, error } = storeToRefs(listingStore)

const isOwner = computed(() => {
  if (!listing.value?.seller || !userStore.profile) return false
  return listing.value.seller.telegram_id === userStore.profile.telegram_id
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    pending: 'На модерации',
    approved: 'Одобрено',
    rejected: 'Отклонено',
  }
  return labels[listing.value?.status ?? ''] ?? listing.value?.status
})

const formattedPrice = computed(() => {
  if (!listing.value) return ''
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: listing.value.currency || 'UZS',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(listing.value.price)
})

const sellerName = computed(() => {
  if (!listing.value?.seller) return ''
  const s = listing.value.seller
  return [s.first_name, s.last_name].filter(Boolean).join(' ')
})

const sellerInitial = computed(() =>
  sellerName.value.charAt(0).toUpperCase(),
)

const memberSince = computed(() => {
  if (!listing.value?.seller?.created_at) return ''
  const date = new Date(listing.value.seller.created_at)
  return `Участник с ${date.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}`
})

onMounted(() => {
  const id = route.params.id as string
  listingStore.fetchListing(id)
})
</script>

<style scoped>
/* ===== Page ===== */
.listing-page {
  min-height: 100vh;
  background: var(--tg-theme-bg-color, #17212b);
}

/* ===== Loading skeleton ===== */
.listing-loading {
  animation: fade-in 0.3s ease both;
}

.skeleton {
  background: linear-gradient(
    110deg,
    var(--tg-theme-secondary-bg-color, #232e3c) 30%,
    color-mix(in srgb, var(--tg-theme-secondary-bg-color, #232e3c), #fff 6%) 50%,
    var(--tg-theme-secondary-bg-color, #232e3c) 70%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 8px;
}

.skeleton-carousel {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 0;
}

.skeleton-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-title {
  height: 26px;
  width: 75%;
}

.skeleton-price {
  height: 32px;
  width: 40%;
}

.skeleton-row {
  display: flex;
  gap: 8px;
}

.skeleton-chip {
  height: 28px;
  width: 90px;
}

.skeleton-text {
  height: 16px;
  width: 100%;
}

.skeleton-text-short {
  height: 16px;
  width: 60%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ===== Error ===== */
.listing-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  padding: 24px;
}

.listing-error-text {
  color: var(--tg-theme-hint-color, #708499);
  font-size: 15px;
  text-align: center;
  margin: 0;
}

/* ===== Body ===== */
.listing-body {
  padding: 16px;
  animation: fade-in 0.35s ease both;
}

/* ===== Header ===== */
.listing-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 6px;
}

.listing-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.25;
  color: var(--tg-theme-text-color, #f5f5f5);
  flex: 1;
}

/* ===== Status badge ===== */
.status-badge {
  flex-shrink: 0;
  margin-top: 3px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge--pending {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.14);
}

.status-badge--approved {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.14);
}

.status-badge--rejected {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.14);
}

/* ===== Price ===== */
.listing-price {
  margin: 0 0 14px;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--tg-theme-button-color, #5288c1);
}

/* ===== Meta chips ===== */
.listing-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.listing-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 13px;
  color: var(--tg-theme-hint-color, #708499);
  background: var(--tg-theme-secondary-bg-color, #232e3c);
}

/* ===== Description ===== */
.listing-section {
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--tg-theme-text-color, #f5f5f5);
}

.listing-description {
  margin: 0;
  font-size: 15px;
  line-height: 1.55;
  color: color-mix(in srgb, var(--tg-theme-text-color, #f5f5f5), transparent 15%);
  white-space: pre-line;
}

/* ===== Seller card ===== */
.seller-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: var(--radius-card, 12px);
  background: var(--tg-theme-secondary-bg-color, #232e3c);
}

.seller-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 75%);
}

.seller-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.seller-avatar-initial {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 18px;
  font-weight: 700;
  color: var(--tg-theme-button-color, #5288c1);
}

.seller-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.seller-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--tg-theme-text-color, #f5f5f5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.seller-since {
  font-size: 13px;
  color: var(--tg-theme-hint-color, #708499);
}

/* ===== Bottom spacer ===== */
.listing-bottom-spacer {
  height: calc(80px + env(safe-area-inset-bottom));
}

/* ===== Animations ===== */
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
