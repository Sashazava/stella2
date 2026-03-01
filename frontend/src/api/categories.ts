import type { Category, CategoryCreate } from '@/types'
import apiClient from './client'

export async function getCategories(): Promise<Category[]> {
  const { data } = await apiClient.get<Category[]>('/categories')
  return data
}

export async function proposeCategory(payload: CategoryCreate): Promise<Category> {
  const { data } = await apiClient.post<Category>('/categories/propose', payload)
  return data
}
