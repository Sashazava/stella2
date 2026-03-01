import type {
  Listing, ListingCreate, ListingUpdate,
  PhotoUploadResponse, PhotoConfirm,
} from '@/types'
import type { PaginatedResponse } from '@/types'
import apiClient from './client'

export interface CatalogFilters {
  city?: string
  category_id?: string
  page?: number
  per_page?: number
  sort?: 'recent' | 'price_asc' | 'price_desc'
}

export async function getListings(filters?: CatalogFilters): Promise<PaginatedResponse<Listing>> {
  const { data } = await apiClient.get<PaginatedResponse<Listing>>('/catalog', { params: filters })
  return data
}

export async function getListing(id: string): Promise<Listing> {
  const { data } = await apiClient.get<Listing>(`/listings/${id}`)
  return data
}

export async function createListing(payload: ListingCreate): Promise<Listing> {
  const { data } = await apiClient.post<Listing>('/listings', payload)
  return data
}

export async function updateListing(id: string, payload: ListingUpdate): Promise<Listing> {
  const { data } = await apiClient.patch<Listing>(`/listings/${id}`, payload)
  return data
}

export async function deleteListing(id: string): Promise<void> {
  await apiClient.delete(`/listings/${id}`)
}

export async function getMyListings(): Promise<Listing[]> {
  const { data } = await apiClient.get<Listing[]>('/listings/my')
  return data
}

export async function getPhotoUploadUrl(listingId: string): Promise<PhotoUploadResponse> {
  const { data } = await apiClient.post<PhotoUploadResponse>(`/listings/${listingId}/photos/upload-url`)
  return data
}

export async function confirmPhotoUpload(listingId: string, payload: PhotoConfirm): Promise<void> {
  await apiClient.post(`/listings/${listingId}/photos`, payload)
}

export async function deletePhoto(listingId: string, photoId: string): Promise<void> {
  await apiClient.delete(`/listings/${listingId}/photos/${photoId}`)
}
