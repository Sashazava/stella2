import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { defineComponent } from 'vue'
import { initData, backButton } from '@telegram-apps/sdk-vue'

// Lazy-loaded components
const SplashScreen = () => import('@/features/splash/SplashScreen.vue')

const CatalogPage = () => import('@/features/catalog/CatalogPage.vue')

const ListingDetailPage = () => import('@/features/listing/ListingDetailPage.vue')

const RegistrationPage = () => import('@/features/registration/RegistrationPage.vue')

const CreateListingPage = () => import('@/features/create-listing/CreateListingPage.vue')

const MyListingsPage = () => import('@/features/my-listings/MyListingsPage.vue')

const ProfilePage = () => import('@/features/profile/ProfilePage.vue')

const ErrorPage = defineComponent({
  template: '<div>ErrorPage - TODO</div>',
})

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'splash',
    component: SplashScreen,
  },
  {
    path: '/catalog',
    name: 'catalog',
    component: CatalogPage,
    meta: {
      requiresTelegram: true,
    },
  },
  {
    path: '/catalog/:id',
    name: 'listing-detail',
    component: ListingDetailPage,
    meta: {
      requiresTelegram: true,
    },
  },
  {
    path: '/register',
    name: 'register',
    component: RegistrationPage,
    meta: {
      requiresTelegram: true,
    },
  },
  {
    path: '/create-listing',
    name: 'create-listing',
    component: CreateListingPage,
    meta: {
      requiresTelegram: true,
      requiresRegistration: true,
    },
  },
  {
    path: '/my-listings',
    name: 'my-listings',
    component: MyListingsPage,
    meta: {
      requiresTelegram: true,
      requiresRegistration: true,
    },
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfilePage,
    meta: {
      requiresTelegram: true,
      requiresRegistration: true,
    },
  },
  {
    path: '/error',
    name: 'error',
    component: ErrorPage,
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  // Check Telegram requirement
  if (to.meta.requiresTelegram) {
    const raw = initData.raw()
    if (!raw) {
      next('/error')
      return
    }
  }

  // Check registration requirement
  if (to.meta.requiresRegistration) {
    try {
      // Dynamically import to avoid build-time dependency on user store
      const userStoreModule = await import('@/stores/user').catch(() => null)
      if (userStoreModule) {
        const userStore = userStoreModule.useUserStore()
        if (!userStore.isRegistered) {
          next('/register')
          return
        }
      } else {
        // Store not available yet, redirect to register
        next('/register')
        return
      }
    } catch (error) {
      // Store not initialized yet, redirect to register
      next('/register')
      return
    }
  }

  next()
})

// Manage Telegram BackButton
router.afterEach((to) => {
  const showBackButton = to.path !== '/' && to.path !== '/catalog'
  if (showBackButton) {
    backButton.show()
    backButton.onClick(() => {
      router.back()
    })
  } else {
    backButton.hide()
  }
})
