// 每頁的 SEO 標籤。
//
// 這是 SPA，所有頁面共用同一份 index.html，build 時只能注入一組全站文案
// （見 vite-plugin-seo.js）。這裡負責在路由切換後把標題、描述、canonical
// 與結構化資料改成該頁自己的內容。
//
// 會執行 JS 的爬蟲（Google）看得到這裡的結果；不執行 JS 的（Facebook、
// LINE、Bing）只看得到 build 時注入的那一組，那部分要靠預渲染解決。
//
// 所有由這裡產生的標籤都掛上 data-seo，切頁時先清掉再重建，
// 免得上一頁的描述殘留到下一頁。

const MANAGED = 'data-seo'

// 網站設定是非同步載入的，回來得比頁面資料晚時會把頁面自己的標題與描述
// 蓋掉。這個旗標讓 siteSettings 知道目前這頁已經有自己的 SEO，不要再覆寫。
let claimed = false

export function hasPageSeo() {
  return claimed
}

function upsert(selector, create) {
  let el = document.head.querySelector(selector)
  if (!el) {
    el = create()
    el.setAttribute(MANAGED, '')
    document.head.appendChild(el)
  }
  return el
}

function setMeta(attr, key, content) {
  const selector = `meta[${attr}="${key}"]`
  if (!content) {
    const existing = document.head.querySelector(`${selector}[${MANAGED}]`)
    if (existing) existing.remove()
    return
  }
  const el = upsert(selector, () => {
    const meta = document.createElement('meta')
    meta.setAttribute(attr, key)
    return meta
  })
  el.setAttribute('content', content)
}

function setCanonical(href) {
  if (!href) return
  const el = upsert('link[rel="canonical"]', () => {
    const link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    return link
  })
  el.setAttribute('href', href)
}

function setJsonLd(data) {
  const existing = document.head.querySelector(`script[type="application/ld+json"][${MANAGED}]`)
  if (existing) existing.remove()
  if (!data) return

  const script = document.createElement('script')
  script.type = 'application/ld+json'
  script.setAttribute(MANAGED, '')
  script.textContent = JSON.stringify(data)
  document.head.appendChild(script)
}

// 描述太長會被搜尋結果截斷，切在句子邊界比硬切好看
export function truncate(text, max = 155) {
  const clean = String(text || '').replace(/\s+/g, ' ').trim()
  if (clean.length <= max) return clean
  const cut = clean.slice(0, max)
  const stop = Math.max(cut.lastIndexOf('。'), cut.lastIndexOf('，'), cut.lastIndexOf(' '))
  return (stop > max * 0.6 ? cut.slice(0, stop) : cut).trim() + '…'
}

// Markdown 頁面沒有另外寫描述，就把內文開頭剝成純文字來用
export function markdownExcerpt(md, max = 155) {
  const text = String(md || '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[*_`>|#-]/g, ' ')
  return truncate(text, max)
}

export function absoluteUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  return window.location.origin + (path.startsWith('/') ? path : `/${path}`)
}

/**
 * 設定目前這一頁的 SEO 標籤。
 *
 * @param {object} opts
 * @param {string} opts.title       完整標題（呼叫端自己組好站名）
 * @param {string} opts.description 該頁描述
 * @param {string} opts.path        canonical 路徑，預設是目前網址
 * @param {string} opts.image       分享預覽圖網址
 * @param {object} opts.jsonLd      結構化資料，不需要就不用給
 * @param {boolean} opts.noindex    後台之類不該被收錄的頁面
 */
export function setPageSeo({ title, description, path, image, jsonLd, noindex } = {}) {
  claimed = true
  if (title) document.title = title

  const canonical = absoluteUrl(path || window.location.pathname)
  const desc = truncate(description)

  setMeta('name', 'description', desc)
  setCanonical(canonical)

  setMeta('property', 'og:type', 'website')
  setMeta('property', 'og:title', title)
  setMeta('property', 'og:description', desc)
  setMeta('property', 'og:url', canonical)
  setMeta('property', 'og:image', image)

  setMeta('name', 'twitter:card', image ? 'summary_large_image' : 'summary')
  setMeta('name', 'twitter:title', title)
  setMeta('name', 'twitter:description', desc)
  setMeta('name', 'twitter:image', image)

  setMeta('name', 'robots', noindex ? 'noindex, nofollow' : '')

  setJsonLd(jsonLd)
}

/** 元素頁的結構化資料。 */
export function elementJsonLd(el, { url, image, description }) {
  return {
    '@context': 'https://schema.org',
    '@type': 'ChemicalSubstance',
    name: el.Name || el.Symbol,
    alternateName: el.Symbol,
    identifier: String(el.AtomicNumber || ''),
    description,
    url,
    ...(image ? { image } : {}),
    ...(el.AtomicMass ? { molecularWeight: String(el.AtomicMass) } : {})
  }
}

/** 分子頁的結構化資料。 */
export function moleculeJsonLd(mol, { url, image, description }) {
  return {
    '@context': 'https://schema.org',
    '@type': 'MolecularEntity',
    name: mol.name || mol.formula,
    ...(mol.formula ? { molecularFormula: mol.formula } : {}),
    description,
    url,
    ...(image ? { image } : {})
  }
}
