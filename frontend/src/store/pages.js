import { reactive } from 'vue'
import { getPages } from '../api'
import { metaText } from './pageMeta'
import { BUILTIN_PAGES } from '../utils/builtinPages'

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
//
// 標題刻意不在這裡另外寫一份：molecules / particles 取自 pageMeta 的頁面
// 標題，guide / links 取自內建頁面。否則同一個頁面會有兩個名字，改了一邊
// 另一邊就對不上——頁面標題已經是 Elementary Particles，頁尾卻還是
// 「基本粒子」。用 getter 而非常數，pageMeta 晚一步載入時也會跟著更新。
// 位置同理：molecules / particles 沒有 Markdown 內容、不會進 _pages，
// 導覽位置改由 pageMeta 決定，站長才有主導權。guide / links 在後台轉成
// 可編輯頁面之前先用預設位置，轉換後完全依 _pages 的設定。
const BUILTIN_NAV = [
  {
    slug: 'molecules',
    to: '/molecules',
    label: () => metaText('molecules', 'title'),
    position: () => metaText('molecules', 'nav_position'),
    order: () => Number(metaText('molecules', 'nav_order')) || 0
  },
  {
    slug: 'particles',
    to: '/particles',
    label: () => metaText('particles', 'title'),
    position: () => metaText('particles', 'nav_position'),
    order: () => Number(metaText('particles', 'nav_order')) || 0
  },
  {
    slug: 'watermark',
    to: '/watermark',
    label: () => metaText('watermark', 'title'),
    position: () => metaText('watermark', 'nav_position'),
    order: () => Number(metaText('watermark', 'nav_order')) || 0
  },
  { slug: 'guide', to: '/guide', label: () => BUILTIN_PAGES.guide.title, position: () => 'footer', order: () => 0 },
  { slug: 'links', to: '/links', label: () => BUILTIN_PAGES.links.title, position: () => 'footer', order: () => 0 }
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
        items.push({ to: b.to, label: page.title, draft: !page.published, order: page.nav_order || 0 })
      }
    } else if (b.position() === position) {
      items.push({ to: b.to, label: b.label(), draft: false, order: b.order() })
    }
  }

  const builtinSlugs = new Set(BUILTIN_NAV.map(b => b.slug))
  for (const p of state.pages) {
    if (p.nav_position !== position || builtinSlugs.has(p.slug)) continue
    items.push({ to: `/p/${p.slug}`, label: p.title, draft: !p.published, order: p.nav_order || 0 })
  }

  return items.sort((a, b) => a.order - b.order)
}

export const pagesState = state
