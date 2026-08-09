import { reactive } from 'vue'
import { getSiteSettings } from '../api'

// index.html 是 build 時的靜態檔案，改不到；這裡的預設值要和它一致，
// 當作 API 還沒回來或沒設定時的 fallback。
const DEFAULTS = {
  title: 'Element Groups',
  subtitle: 'Explore the components of the world.',
  description: 'Explore the periodic table — group elements by chemical properties, valence shell, and more.'
}

const state = reactive({
  ...DEFAULTS,
  bg_image: '',
  loaded: false
})

function applyToDocument() {
  document.title = state.title
  let meta = document.querySelector('meta[name="description"]')
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('name', 'description')
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', state.description)
}

export async function ensureSiteSettings() {
  if (state.loaded) return
  try {
    const res = await getSiteSettings()
    // 後台留空的欄位仍沿用預設文案，避免整個標題變空白
    state.title = res.data.title || DEFAULTS.title
    state.subtitle = res.data.subtitle || DEFAULTS.subtitle
    state.description = res.data.description || DEFAULTS.description
    state.bg_image = res.data.bg_image || ''
    state.loaded = true
  } catch (e) {
    console.error('Failed to load site settings:', e)
  }
  applyToDocument()
}

// Admin 存檔後立即反映，不用重新整理
export function setSiteSettings(data) {
  state.title = data.title || DEFAULTS.title
  state.subtitle = data.subtitle || DEFAULTS.subtitle
  state.description = data.description || DEFAULTS.description
  if (data.bg_image !== undefined) state.bg_image = data.bg_image
  state.loaded = true
  applyToDocument()
}

export const siteSettingsState = state
export const SITE_DEFAULTS = DEFAULTS
