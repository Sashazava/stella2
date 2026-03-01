import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTelegramStore } from '@/stores/telegram'

describe('useTelegramStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts with isReady = false', () => {
    const store = useTelegramStore()
    expect(store.isReady).toBe(false)
  })

  it('isAuthenticated is false before initialize()', () => {
    const store = useTelegramStore()
    expect(store.isAuthenticated).toBe(false)
  })

  it('initialize() sets isReady to true', () => {
    const store = useTelegramStore()
    store.initialize()
    expect(store.isReady).toBe(true)
  })

  it('initialize() populates initDataRaw from SDK', () => {
    const store = useTelegramStore()
    store.initialize()
    // mock returns 'mock_init_data' from setup.ts
    expect(store.initDataRaw).toBe('mock_init_data')
  })

  it('isAuthenticated is true after initialize() with valid data', () => {
    const store = useTelegramStore()
    store.initialize()
    // Both initDataRaw and user are set by the mock
    expect(store.isAuthenticated).toBe(true)
  })
})
