import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserRegistration, UserUpdate } from '@/types'
import * as usersApi from '@/api/users'

export const useUserStore = defineStore('user', () => {
  const profile = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isRegistered = computed(() => profile.value?.is_registered ?? false)

  async function fetchProfile() {
    isLoading.value = true
    error.value = null
    try {
      profile.value = await usersApi.getProfile()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch profile'
    } finally {
      isLoading.value = false
    }
  }

  async function register(data: UserRegistration) {
    isLoading.value = true
    error.value = null
    try {
      profile.value = await usersApi.register(data)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to register'
    } finally {
      isLoading.value = false
    }
  }

  async function updateProfile(data: UserUpdate) {
    isLoading.value = true
    error.value = null
    try {
      profile.value = await usersApi.updateProfile(data)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update profile'
    } finally {
      isLoading.value = false
    }
  }

  return { profile, isLoading, error, isRegistered, fetchProfile, register, updateProfile }
})
