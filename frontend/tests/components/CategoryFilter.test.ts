import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CategoryFilter from '@/features/catalog/CategoryFilter.vue'

const mockCategories = [
  { id: 'cat-1', name: 'Электроника', slug: 'elektronika', is_approved: true },
  { id: 'cat-2', name: 'Одежда', slug: 'odezhda', is_approved: true },
  { id: 'cat-3', name: 'Спорт', slug: 'sport', is_approved: true },
]

describe('CategoryFilter', () => {
  it('renders "Все" chip always', () => {
    const wrapper = mount(CategoryFilter, {
      props: { categories: mockCategories, selectedId: null },
    })
    expect(wrapper.text()).toContain('Все')
  })

  it('renders all category names', () => {
    const wrapper = mount(CategoryFilter, {
      props: { categories: mockCategories, selectedId: null },
    })
    expect(wrapper.text()).toContain('Электроника')
    expect(wrapper.text()).toContain('Одежда')
    expect(wrapper.text()).toContain('Спорт')
  })

  it('marks "Все" as active when selectedId is null', () => {
    const wrapper = mount(CategoryFilter, {
      props: { categories: mockCategories, selectedId: null },
    })
    const allChip = wrapper.findAll('button')[0]
    expect(allChip.classes()).toContain('category-chip--active')
  })

  it('marks selected category chip as active', () => {
    const wrapper = mount(CategoryFilter, {
      props: { categories: mockCategories, selectedId: 'cat-2' },
    })
    const chips = wrapper.findAll('button')
    // chip at index 0 = "Все", index 1 = cat-1, index 2 = cat-2
    expect(chips[2].classes()).toContain('category-chip--active')
    expect(chips[0].classes()).not.toContain('category-chip--active')
  })

  it('emits select with null when "Все" is clicked', async () => {
    const wrapper = mount(CategoryFilter, {
      props: { categories: mockCategories, selectedId: 'cat-1' },
    })
    await wrapper.findAll('button')[0].trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual([null])
  })

  it('emits select with category id when chip is clicked', async () => {
    const wrapper = mount(CategoryFilter, {
      props: { categories: mockCategories, selectedId: null },
    })
    // Click the first category chip (index 1, after "Все")
    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual(['cat-1'])
  })

  it('renders correct number of chips (categories + 1 for Все)', () => {
    const wrapper = mount(CategoryFilter, {
      props: { categories: mockCategories, selectedId: null },
    })
    const chips = wrapper.findAll('button')
    expect(chips).toHaveLength(mockCategories.length + 1)
  })
})
