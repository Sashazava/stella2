import type { UserPublic } from './user'
import type { Category } from './category'

export type ListingStatus = 'pending' | 'approved' | 'rejected'

export interface ListingPhoto {
  id: string
  url: string
  position: number
}

export interface Listing {
  id: string
  title: string
  description: string
  price: number
  currency: string
  status: ListingStatus
  city?: string
  category?: Category
  seller?: UserPublic
  photos: ListingPhoto[]
  created_at: string
  updated_at: string
}

export interface ListingCreate {
  title: string
  description: string
  price: number
  currency?: string
  category_id?: string
}

export interface ListingUpdate {
  title?: string
  description?: string
  price?: number
  currency?: string
  category_id?: string
}

export interface PhotoUploadResponse {
  upload_url: string
  object_key: string
  position: number
}

export interface PhotoConfirm {
  object_key: string
  position: number
}
