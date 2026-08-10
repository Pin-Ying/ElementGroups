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

// 內建頁面有自己的路由，且在後台轉成可編輯之前不會出現在 _pages 裡。
// 尚未轉換時沿用這裡的預設位置，轉換後就完全依後台設定。
const BUILTIN_NAV = [
  { slug: 'molecules', label: 'Molecule Groups', to: '/molecules', defaultPosition: 'footer' },
  { slug: 'guide', label: '元素說明書', to: '/guide', defaultPosition: 'footer' },
  { slug: 'links', label: 'Connect', to: '/links', defaultPosition: 'footer' }
]

/**
 * 取得某個導覽位置要顯示的項目。
 *
 * @param {'header'|'sidebar'|'footer'} position
 * @returns {{to: string, label: string, draft: boolean}[]}
 */
export function navItemsFor(position) {
  const items = []

  for (const b of BUILTIN_NAV) {
    const page = state.pages.find(p => p.slug === b.slug)
    if (page) {
      // 已轉成可編輯頁面：位置與標題都以後台設定為準
      if (page.nav_position === position) {
        items.push({ to: b.to, label: page.title, draft: !page.published })
      }
    } else if (b.defaultPosition === position) {
      items.push({ to: b.to, label: b.label, draft: false })
    }
  }

  const builtinSlugs = new Set(BUILTIN_NAV.map(b => b.slug))
  for (const p of state.pages) {
    if (p.nav_position !== position || builtinSlugs.has(p.slug)) continue
    items.push({ to: `/p/${p.slug}`, label: p.title, draft: !p.published })
  }

  return items
}

export const pagesState = state
