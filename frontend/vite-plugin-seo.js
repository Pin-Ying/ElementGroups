// Build 時把後台設定的網站文案寫進 index.html。
//
// 這是 SPA，meta tag 由 JS 在載入後設定；但搜尋引擎與社群分享的爬蟲
// 多半不執行 JS（Facebook / LINE / Twitter 完全不執行），只會讀原始
// HTML，於是抓到的永遠是 build 時寫死的預設文案。
//
// 這裡用 transformIndexHtml 在打包階段注入，不會改到原始的 index.html。
// 代價：後台改完文案要重新部署一次，爬蟲才看得到新的內容（使用者端
// 仍然是即時生效，因為 JS 會再覆寫一次）。

import { fetchJson, configProblem, reportMissing, RETRY_ATTEMPTS } from './build-fetch.js'

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

export default function seoPlugin() {
  return {
    name: 'inject-seo',
    apply: 'build',
    async transformIndexHtml(html) {
      const apiBase = process.env.VITE_API_URL
      const siteUrl = (process.env.VITE_SITE_URL || '').replace(/\/$/, '')

      const settings = await fetchJson(apiBase, '/site-settings', { label: '網站設定' })
      if (!settings) {
        const issue = configProblem(apiBase)
        reportMissing('[inject-seo]', {
          reason: issue || `${apiBase}/site-settings 重試 ${RETRY_ATTEMPTS} 次都沒有回應`,
          impact: 'index.html 用的是程式內建預設文案，不是後台設定的內容',
          fix: '確認後端服務活著；免費方案的休眠請靠 buildCommand 的預熱請求',
          soft: Boolean(issue)
        })
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

      // 同樣用 [\s\S]：後台文案可以有換行，`.` 不跨行會讓置換靜默失效
      return html
        .replace(/<title>[\s\S]*?<\/title>/, `<title>${escapeAttr(title)}</title>`)
        .replace(
          /<meta name="description" content="[\s\S]*?" \/>/,
          `<meta name="description" content="${escapeAttr(description)}" />`
        )
        .replace('</head>', `  ${tags}\n  </head>`)
    }
  }
}
