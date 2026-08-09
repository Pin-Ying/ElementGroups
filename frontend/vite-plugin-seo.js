// Build 時把後台設定的網站文案寫進 index.html。
//
// 這是 SPA，meta tag 由 JS 在載入後設定；但搜尋引擎與社群分享的爬蟲
// 多半不執行 JS（Facebook / LINE / Twitter 完全不執行），只會讀原始
// HTML，於是抓到的永遠是 build 時寫死的預設文案。
//
// 這裡用 transformIndexHtml 在打包階段注入，不會改到原始的 index.html。
// 代價：後台改完文案要重新部署一次，爬蟲才看得到新的內容（使用者端
// 仍然是即時生效，因為 JS 會再覆寫一次）。

const FETCH_TIMEOUT = 8000

const FALLBACK = {
  title: 'Element Groups',
  description: 'Explore the periodic table — group elements by chemical properties, valence shell, and more.'
}

function escapeAttr(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

async function fetchSettings(apiBase) {
  if (!apiBase || !/^https?:\/\//.test(apiBase)) return null
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT)
  try {
    const res = await fetch(`${apiBase.replace(/\/$/, '')}/site-settings`, {
      signal: controller.signal
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export default function seoPlugin() {
  return {
    name: 'inject-seo',
    apply: 'build',
    async transformIndexHtml(html) {
      const apiBase = process.env.VITE_API_URL
      const siteUrl = (process.env.VITE_SITE_URL || '').replace(/\/$/, '')

      const settings = await fetchSettings(apiBase)
      if (!settings) {
        // 後端休眠或尚未部署時不要讓 build 失敗，沿用預設文案
        console.warn('[inject-seo] 取不到網站設定，使用預設文案')
      }

      const title = (settings?.title || '').trim() || FALLBACK.title
      const description = (settings?.description || '').trim() || FALLBACK.description
      // 分享預覽圖：後台設了背景圖就用它，否則退回元素預設圖
      const image = settings?.bg_image
        ? `${siteUrl}/api/elements/default-img`
        : apiBase
          ? `${apiBase.replace(/\/$/, '')}/elements/default-img`
          : ''

      const tags = [
        `<meta property="og:type" content="website" />`,
        `<meta property="og:title" content="${escapeAttr(title)}" />`,
        `<meta property="og:description" content="${escapeAttr(description)}" />`,
        siteUrl ? `<meta property="og:url" content="${escapeAttr(siteUrl)}" />` : '',
        image ? `<meta property="og:image" content="${escapeAttr(image)}" />` : '',
        `<meta name="twitter:card" content="summary_large_image" />`,
        `<meta name="twitter:title" content="${escapeAttr(title)}" />`,
        `<meta name="twitter:description" content="${escapeAttr(description)}" />`,
        image ? `<meta name="twitter:image" content="${escapeAttr(image)}" />` : ''
      ].filter(Boolean).join('\n    ')

      return html
        .replace(/<title>.*?<\/title>/, `<title>${escapeAttr(title)}</title>`)
        .replace(
          /<meta name="description" content=".*?" \/>/,
          `<meta name="description" content="${escapeAttr(description)}" />`
        )
        .replace('</head>', `  ${tags}\n  </head>`)
    }
  }
}
