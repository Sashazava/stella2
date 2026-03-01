import type { User, UserRegistration, UserUpdate, UserPublic, AvatarUploadResponse } from '@/types'
import apiClient from './client'

export async function getProfile(): Promise<User> {
  const { data } = await apiClient.get<User>('/users/profile')
  return data
}

export async function register(payload: UserRegistration): Promise<User> {
  const { data } = await apiClient.post<User>('/users/register', payload)
  return data
}

export async function updateProfile(payload: UserUpdate): Promise<User> {
  const { data } = await apiClient.patch<User>('/users/profile', payload)
  return data
}

export async function getAvatarUploadUrl(): Promise<AvatarUploadResponse> {
  const { data } = await apiClient.post<AvatarUploadResponse>('/users/avatar')
  return data
}

export async function getPublicProfile(telegramId: number): Promise<UserPublic> {
  const { data } = await apiClient.get<UserPublic>(`/users/${telegramId}/public`)
  return data
}
