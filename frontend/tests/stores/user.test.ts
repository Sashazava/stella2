import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'

// Mock the users API module
vi.mock('@/api/users', () => ({
  getProfile: vi.fn(),
  register: vi.fn(),
  updateProfile: vi.fn(),
  getAvatarUploadUrl: vi.fn(),
}))

import * as usersApi from '@/api/users'

const mockUser = {
  id: 'uuid-1',
  telegram_id: 12345,
  first_name: 'Test',
  last_name: 'User',
  username: 'testuser',
  phone: '+79001234567',
  city: 'Москва',
  avatar_url: null,
  is_registered: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts with profile = null', () => {
    const store = useUserStore()
    expect(store.profile).toBeNull()
  })

  it('isRegistered is false when profile is null', () => {
    const store = useUserStore()
    expect(store.isRegistered).toBe(false)
  })

  it('fetchProfile sets profile on success', async () => {
    vi.mocked(usersApi.getProfile).mockResolvedValue(mockUser as any)
    const store = useUserStore()
    await store.fetchProfile()
    expect(store.profile).toEqual(mockUser)
    expect(store.isLoading).toBe(false)
  })

  it('isRegistered is true when profile.is_registered = true', async () => {
    vi.mocked(usersApi.getProfile).mockResolvedValue(mockUser as any)
    const store = useUserStore()
    await store.fetchProfile()
    expect(store.isRegistered).toBe(true)
  })

  it('fetchProfile sets error on failure', async () => {
    vi.mocked(usersApi.getProfile).mockRejectedValue(new Error('Network error'))
    const store = useUserStore()
    await store.fetchProfile()
    expect(store.error).toBe('Network error')
    expect(store.profile).toBeNull()
  })

  it('register() sets profile on success', async () => {
    vi.mocked(usersApi.register).mockResolvedValue(mockUser as any)
    const store = useUserStore()
    await store.register({
      first_name: 'Test',
      phone: '+79001234567',
      city: 'Москва',
    })
    expect(store.profile).toEqual(mockUser)
  })

  it('updateProfile() updates profile on success', async () => {
    const updated = { ...mockUser, city: 'Казань' }
    vi.mocked(usersApi.updateProfile).mockResolvedValue(updated as any)
    const store = useUserStore()
    store.profile = mockUser as any
    await store.updateProfile({ city: 'Казань' })
    expect(store.profile?.city).toBe('Казань')
  })
})
