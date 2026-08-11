import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import seo from './vite-plugin-seo.js'
import sitemap from './vite-plugin-sitemap.js'
import prerender from './vite-plugin-prerender.js'

export default defineConfig({
  plugins: [vue(), seo(), sitemap(), prerender()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
