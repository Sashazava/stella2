export interface User {
  id: string
  telegram_id: number
  first_name: string
  last_name?: string
  username?: string
  phone?: string
  city?: string
  latitude?: number
  longitude?: number
  avatar_url?: string
  is_registered: boolean
  created_at: string
  updated_at: string
}

export interface UserRegistration {
  first_name: string
  last_name?: string
  phone: string
  city: string
  latitude?: number
  longitude?: number
}

export interface UserUpdate {
  first_name?: string
  last_name?: string
  phone?: string
  city?: string
  latitude?: number
  longitude?: number
  avatar_url?: string
}

export interface UserPublic {
  id: string
  telegram_id: number
  first_name: string
  last_name?: string
  username?: string
  city?: string
  avatar_url?: string
  created_at: string
}

export interface AvatarUploadResponse {
  upload_url: string
  object_key: string
}
