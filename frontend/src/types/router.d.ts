import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    requiresTelegram?: boolean
    requiresRegistration?: boolean
  }
}
