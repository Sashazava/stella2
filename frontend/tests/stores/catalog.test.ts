import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCatalogStore } from '@/stores/catalog'

vi.mock('@/api/listings', () => ({
  getListings: vi.fn(),
  getListing: vi.fn(),
  createListing: vi.fn(),
  getMyListings: vi.fn(),
}))

vi.mock('@/api/categories', () => ({
  getCategories: vi.fn(),
  proposeCategory: vi.fn(),
}))

import * as listingsApi from '@/api/listings'
import * as categoriesApi from '@/api/categories'

const mockCategory = { id: 'cat-1', name: 'Электроника', slug: 'elektronika', is_approved: true }

const mockListing = {
  id: 'listing-1',
  title: 'Ноутбук',
  description: 'Хороший ноутбук',
  price: 50000,
  currency: 'RUB',
  status: 'approved',
  city: 'Москва',
  category: mockCategory,
  seller: { id: 'user-1', telegram_id: 12345, first_name: 'Test', username: 'testuser' },
  photos: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const mockPaginatedResponse = {
  items: [mockListing],
  total: 1,
  page: 1,
  pages: 1,
  per_page: 20,
}

describe('useCatalogStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts with empty listings', () => {
    const store = useCatalogStore()
    expect(store.listings).toEqual([])
  })

  it('loadListings populates listings on success', async () => {
    vi.mocked(listingsApi.getListings).mockResolvedValue(mockPaginatedResponse as any)
    const store = useCatalogStore()
    await store.loadListings()
    expect(store.listings).toHaveLength(1)
    expect(store.listings[0].title).toBe('Ноутбук')
  })

  it('loadListings sets error on failure', async () => {
    vi.mocked(listingsApi.getListings).mockRejectedValue(new Error('API error'))
    const store = useCatalogStore()
    await store.loadListings()
    expect(store.error).toBe('API error')
    expect(store.listings).toEqual([])
  })

  it('loadCategories populates categories', async () => {
    vi.mocked(categoriesApi.getCategories).mockResolvedValue([mockCategory] as any)
    const store = useCatalogStore()
    await store.loadCategories()
    expect(store.categories).toHaveLength(1)
    expect(store.categories[0].name).toBe('Электроника')
  })

  it('loadListings with city filter sets selectedCity', async () => {
    vi.mocked(listingsApi.getListings).mockResolvedValue(mockPaginatedResponse as any)
    const store = useCatalogStore()
    await store.loadListings({ city: 'Казань' })
    expect(store.selectedCity).toBe('Казань')
  })

  it('loading is false after loadListings completes', async () => {
    vi.mocked(listingsApi.getListings).mockResolvedValue(mockPaginatedResponse as any)
    const store = useCatalogStore()
    await store.loadListings()
    expect(store.loading).toBe(false)
  })
})
