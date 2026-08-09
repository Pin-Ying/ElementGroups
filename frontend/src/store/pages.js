import { reactive } from 'vue'
import { getPages } from '../api'

// 導覽列用的頁面清單。只含標題與位置，內容進頁面時才抓。
const state = reactive({
  pages: [],
  loaded: false
})

export async function ensurePages() {
  if (state.loaded) return
  try {
    const res = await getPages()
    state.pages = res.data.pages || []
    state.loaded = true
  } catch (e) {
    console.error('Failed to load pages:', e)
    // 不標記 loaded，讓之後的呼叫可以重試
  }
}

// Admin 存檔後重新抓，讓導覽立即反映
export async function refreshPages() {
  state.loaded = false
  await ensurePages()
}

export function pagesFor(position) {
  return state.pages.filter(p => p.nav_position === position)
}

export const pagesState = state
