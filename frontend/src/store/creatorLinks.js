import { reactive } from 'vue'
import { getCreatorLinks } from '../api'

// footer 與 /links 頁面共用，避免各自打一次 API
const state = reactive({
  links: [],
  description: '',
  avatar_shape: 'circle',
  loaded: false
})

function apply(data) {
  state.links = data.links || []
  state.description = data.description || ''
  state.avatar_shape = data.avatar_shape || 'circle'
  state.loaded = true
}

export async function ensureCreatorLinks() {
  if (state.loaded) return
  try {
    const res = await getCreatorLinks()
    apply(res.data)
  } catch (e) {
    console.error('Failed to load creator links:', e)
    // 不標記 loaded，讓之後的呼叫可以重試
  }
}

// Admin 存檔後讓 footer / links 頁立即反映
export function setCreatorLinks(data) {
  apply(data || {})
}

export const creatorLinksState = state
