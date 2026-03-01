export interface Category {
  id: string
  name: string
  slug: string
  icon?: string
  is_approved: boolean
}

export interface CategoryCreate {
  name: string
}
