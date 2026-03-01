import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ListingCard from '@/features/catalog/ListingCard.vue'

const mockListing = {
  id: 'listing-1',
  title: 'Продам велосипед',
  description: 'Отличный велосипед',
  price: 5000,
  currency: 'RUB',
  status: 'approved' as const,
  city: 'Москва',
  category: { id: 'cat-1', name: 'Спорт', slug: 'sport', is_approved: true },
  seller: { id: 'user-1', telegram_id: 12345, first_name: 'Test', username: 'testuser' },
  photos: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('ListingCard', () => {
  it('renders listing title', () => {
    const wrapper = mount(ListingCard, {
      props: { listing: mockListing as any },
    })
    expect(wrapper.text()).toContain('Продам велосипед')
  })

  it('renders formatted price', () => {
    const wrapper = mount(ListingCard, {
      props: { listing: mockListing as any },
    })
    // Price 5000 formatted as Russian locale
    expect(wrapper.text()).toContain('₽')
  })

  it('renders city when provided', () => {
    const wrapper = mount(ListingCard, {
      props: { listing: mockListing as any },
    })
    expect(wrapper.text()).toContain('Москва')
  })

  it('shows placeholder when no photos', () => {
    const wrapper = mount(ListingCard, {
      props: { listing: { ...mockListing, photos: [] } as any },
    })
    // No img tag when photos is empty
    expect(wrapper.find('img').exists()).toBe(false)
  })

  it('shows photo when photos array has items', () => {
    const listingWithPhoto = {
      ...mockListing,
      photos: [{ id: 'p1', url: 'http://example.com/photo.jpg', position: 0 }],
    }
    const wrapper = mount(ListingCard, {
      props: { listing: listingWithPhoto as any },
    })
    expect(wrapper.find('img').exists()).toBe(true)
    expect(wrapper.find('img').attributes('src')).toBe('http://example.com/photo.jpg')
  })

  it('emits click event when clicked', async () => {
    const wrapper = mount(ListingCard, {
      props: { listing: mockListing as any },
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
