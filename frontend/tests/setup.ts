/**
 * Global test setup — mocks Telegram SDK and Axios before every test.
 */
import { vi } from 'vitest'

// ---------------------------------------------------------------------------
// Mock @telegram-apps/sdk-vue — it requires a real Telegram environment
// ---------------------------------------------------------------------------
vi.mock('@telegram-apps/sdk-vue', () => ({
  initData: {
    raw: vi.fn(() => 'mock_init_data'),
    user: vi.fn(() => ({
      id: 12345,
      firstName: 'Test',
      lastName: undefined,
      username: 'testuser',
    })),
  },
  backButton: {
    show: vi.fn(),
    hide: vi.fn(),
    onClick: vi.fn(),
    mount: { isAvailable: vi.fn(() => false) },
  },
  viewport: {
    mount: { isAvailable: vi.fn(() => false) },
    expand: { isAvailable: vi.fn(() => false) },
    bindCssVars: vi.fn(),
  },
  themeParams: {
    mount: { isAvailable: vi.fn(() => false) },
    bindCssVars: vi.fn(),
  },
  useSignal: vi.fn((signal) => ({ value: signal() })),
  init: vi.fn(),
  mockTelegramEnv: vi.fn(),
}))

// ---------------------------------------------------------------------------
// Mock axios API client — prevent real HTTP calls
// ---------------------------------------------------------------------------
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))
