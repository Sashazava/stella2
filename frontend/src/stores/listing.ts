import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Listing, ListingCreate } from '@/types'
import * as listingsApi from '@/api/listings'

export const useListingStore = defineStore('listing', () => {
  const currentListing = ref<Listing | null>(null)
  const myListings = ref<Listing[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchListing(id: string) {
    loading.value = true
    error.value = null
    try {
      currentListing.value = await listingsApi.getListing(id)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch listing'
    } finally {
      loading.value = false
    }
  }

  async function createListing(data: ListingCreate) {
    loading.value = true
    error.value = null
    try {
      const listing = await listingsApi.createListing(data)
      myListings.value.push(listing)
      return listing
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create listing'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMyListings() {
    loading.value = true
    error.value = null
    try {
      myListings.value = await listingsApi.getMyListings()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch my listings'
    } finally {
      loading.value = false
    }
  }

  return { currentListing, myListings, loading, error, fetchListing, createListing, fetchMyListings }
})
