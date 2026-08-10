import { reactive } from 'vue'
import { getPageMeta } from '../api'
import { fieldDefault } from '../utils/pageMeta'

// 內建頁面文案的覆寫值（issue #20）。一次抓全部、全站共用；
// 沒有覆寫的欄位由 metaText() 退回 utils/pageMeta.js 的預設值。
const state = reactive({
  meta: {},
  loaded: false
})

export const pageMetaState = state

export async function ensurePageMeta() {
  if (state.loaded) return
  try {
    const res = await getPageMeta()
    state.meta = res.data.meta || {}
    state.loaded = true
  } catch (e) {
    console.error('Failed to load page meta:', e)
  }
}

// Admin 存檔後重新抓，讓前台立即反映
export async function refreshPageMeta() {
  state.loaded = false
  await ensurePageMeta()
}

export function metaText(key, field) {
  return state.meta[key]?.[field] || fieldDefault(key, field)
}
