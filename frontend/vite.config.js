import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { mockPlugin } from './mock/vite-mock.js'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const useMock = env.VITE_USE_MOCK === 'true'
  const apiTarget = env.VITE_API_BASE || 'http://localhost:8080'

  return {
    plugins: [vue(), ...(useMock ? [mockPlugin()] : [])],
    server: {
      port: 5173,
      ...(useMock
        ? {}
        : {
            proxy: {
              '/api': { target: apiTarget, changeOrigin: true }
            }
          })
    }
  }
})