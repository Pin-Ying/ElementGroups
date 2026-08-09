import { reactive } from 'vue'
import { getCreatorLinks } from '../api'

// footer 與 /links 頁面共用，避免各自打一次 API
const state = reactive({
  links: [],
  loaded: false
})

export async function ensureCreatorLinks() {
  if (state.loaded) return
  try {
    const res = await getCreatorLinks()
    state.links = res.data.links || []
    state.loaded = true
  } catch (e) {
    console.error('Failed to load creator links:', e)
    // 不標記 loaded，讓之後的呼叫可以重試
  }
}

// Admin 存檔後讓 footer / links 頁立即反映
export function setCreatorLinks(links) {
  state.links = links || []
  state.loaded = true
}

export const creatorLinksState = state
