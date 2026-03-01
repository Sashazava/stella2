import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Listing, Category } from '@/types'
import * as listingsApi from '@/api/listings'
import * as categoriesApi from '@/api/categories'

export const useCatalogStore = defineStore('catalog', () => {
  const listings = ref<Listing[]>([])
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentPage = ref(1)
  const totalPages = ref(1)
  const selectedCity = ref<string | null>(null)
  const selectedCategory = ref<string | null>(null)

  async function loadListings(filters?: { city?: string; category?: string; page?: number }) {
    loading.value = true
    error.value = null
    try {
      const response = await listingsApi.getListings({
        city: filters?.city || selectedCity.value || undefined,
        category_id: filters?.category || selectedCategory.value || undefined,
        page: filters?.page || currentPage.value,
      })
      listings.value = response.items
      currentPage.value = response.page
      totalPages.value = response.pages
      if (filters?.city !== undefined) {
        selectedCity.value = filters.city || null
      }
      if (filters?.category !== undefined) {
        selectedCategory.value = filters.category || null
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load listings'
    } finally {
      loading.value = false
    }
  }

  async function loadCategories() {
    loading.value = true
    error.value = null
    try {
      categories.value = await categoriesApi.getCategories()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load categories'
    } finally {
      loading.value = false
    }
  }

  return {
    listings,
    categories,
    loading,
    error,
    currentPage,
    totalPages,
    selectedCity,
    selectedCategory,
    loadListings,
    loadCategories,
  }
})
