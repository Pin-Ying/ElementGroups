import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import seo from './vite-plugin-seo.js'

export default defineConfig({
  plugins: [vue(), seo()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
