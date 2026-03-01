<template>
  <div class="catalog-page">
    <!-- Top bar -->
    <header class="catalog-header">
      <div class="catalog-header__city">
        <MapPin :size="16" :stroke-width="2" />
        <span>{{ cityLabel }}</span>
      </div>
      <h1 class="catalog-header__title">Stella</h1>
    </header>

    <!-- Registration banner for unregistered users -->
    <div v-if="!userStore.isRegistered" class="catalog-banner">
      <p class="catalog-banner__text">
        📍 Укажите город, чтобы видеть товары рядом
      </p>
      <router-link to="/register" class="catalog-banner__button">
        Зарегистрироваться
      </router-link>
    </div>

    <!-- Category filter -->
    <CategoryFilter
      :categories="catalogStore.categories"
      :selected-id="catalogStore.selectedCategory"
      @select="onCategorySelect"
    />

    <!-- Listings grid -->
    <div v-if="allListings.length > 0" class="catalog-grid">
      <ListingCard
        v-for="item in allListings"
        :key="item.id"
        :listing="item"
        class="catalog-grid__item"
        @click="goToListing(item.id)"
      />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!catalogStore.loading"
      class="catalog-empty"
    >
      <PackageOpen :size="48" :stroke-width="1.2" class="catalog-empty__icon" />
      <p class="catalog-empty__text">Пока нет объявлений</p>
    </div>

    <!-- Loading state -->
    <div v-if="catalogStore.loading" class="catalog-loading">
      <div class="catalog-spinner" />
    </div>

    <!-- Load more -->
    <div
      v-if="canLoadMore && !catalogStore.loading"
      class="catalog-loadmore"
    >
      <button class="catalog-loadmore__button" @click="loadMore">
        Загрузить ещё
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { MapPin, PackageOpen } from 'lucide-vue-next'
import { useCatalogStore } from '@/stores/catalog'
import { useUserStore } from '@/stores/user'
import type { Listing } from '@/types'
import CategoryFilter from './CategoryFilter.vue'
import ListingCard from './ListingCard.vue'

const router = useRouter()
const catalogStore = useCatalogStore()
const userStore = useUserStore()

const allListings = ref<Listing[]>([])

const cityLabel = computed(() => {
  return userStore.profile?.city || 'Все города'
})

const canLoadMore = computed(() => {
  return catalogStore.currentPage < catalogStore.totalPages && allListings.value.length > 0
})

onMounted(async () => {
  await Promise.all([
    catalogStore.loadCategories(),
    catalogStore.loadListings(),
  ])
  allListings.value = [...catalogStore.listings]
})

// Sync store listings into local accumulated list after each load
watch(
  () => catalogStore.listings,
  (newListings) => {
    if (catalogStore.currentPage === 1) {
      allListings.value = [...newListings]
    } else {
      // Deduplicate when appending
      const existingIds = new Set(allListings.value.map(l => l.id))
      const fresh = newListings.filter(l => !existingIds.has(l.id))
      allListings.value = [...allListings.value, ...fresh]
    }
  },
)

async function onCategorySelect(categoryId: string | null) {
  allListings.value = []
  await catalogStore.loadListings({
    category: categoryId ?? undefined,
    page: 1,
  })
}

async function loadMore() {
  await catalogStore.loadListings({
    page: catalogStore.currentPage + 1,
  })
}

function goToListing(id: string) {
  router.push('/catalog/' + id)
}
</script>

<style scoped>
.catalog-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--tg-theme-bg-color, #17212b);
  padding-bottom: 24px;
}

/* ---- Header ---- */
.catalog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
}

.catalog-header__city {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 500;
  color: var(--tg-theme-hint-color, #708499);
}

.catalog-header__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--tg-theme-text-color, #f5f5f5);
}

/* ---- Banner ---- */
.catalog-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 16px 12px;
  padding: 12px 14px;
  border-radius: var(--radius-card);
  background: color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 85%);
  border: 1px solid color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 70%);
}

.catalog-banner__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: var(--tg-theme-text-color, #f5f5f5);
  flex: 1;
}

.catalog-banner__button {
  flex-shrink: 0;
  padding: 8px 14px;
  border-radius: var(--radius-button);
  background: var(--tg-theme-button-color, #5288c1);
  color: var(--tg-theme-button-text-color, #fff);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: opacity 0.15s ease;
}

.catalog-banner__button:active {
  opacity: 0.8;
}

/* ---- Grid ---- */
.catalog-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 4px 16px 0;
}

.catalog-grid__item {
  animation: card-enter 0.35s ease both;
}

.catalog-grid__item:nth-child(1) { animation-delay: 0.03s; }
.catalog-grid__item:nth-child(2) { animation-delay: 0.06s; }
.catalog-grid__item:nth-child(3) { animation-delay: 0.09s; }
.catalog-grid__item:nth-child(4) { animation-delay: 0.12s; }
.catalog-grid__item:nth-child(5) { animation-delay: 0.15s; }
.catalog-grid__item:nth-child(6) { animation-delay: 0.18s; }

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ---- Empty state ---- */
.catalog-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 64px 16px;
  flex: 1;
}

.catalog-empty__icon {
  color: var(--tg-theme-hint-color, #708499);
  opacity: 0.35;
}

.catalog-empty__text {
  margin: 0;
  font-size: 15px;
  color: var(--tg-theme-hint-color, #708499);
}

/* ---- Loading ---- */
.catalog-loading {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.catalog-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid color-mix(in srgb, var(--tg-theme-button-color, #5288c1), transparent 70%);
  border-top-color: var(--tg-theme-button-color, #5288c1);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ---- Load more ---- */
.catalog-loadmore {
  display: flex;
  justify-content: center;
  padding: 20px 16px 0;
}

.catalog-loadmore__button {
  padding: 12px 32px;
  border: none;
  border-radius: var(--radius-button);
  background: var(--tg-theme-secondary-bg-color, #232e3c);
  color: var(--tg-theme-button-color, #5288c1);
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.catalog-loadmore__button:active {
  transform: scale(0.97);
  opacity: 0.8;
}
</style>
