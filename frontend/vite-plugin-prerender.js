// Build 時為每個元素頁輸出一份自己的靜態 HTML。
//
// 問題：這是 SPA，所有網址共用同一份 index.html。Google 會執行 JS 所以
// 看得到 utils/seo.js 設定的標題與描述，但 Bing、Facebook、LINE 的爬蟲
// 不執行 JS——它們抓 /stroy/O 和 /stroy/Fe 拿到的是一模一樣的空殼。
//
// 做法：把打包好的 index.html 複製 118 份到 stroy/{Symbol}/index.html，
// 每份只換掉 head 裡的 title、description、og/twitter 與 JSON-LD。body
// 完全不動，載入的還是同一份 JS，所以使用者看到的行為沒有任何差別。
//
// 這是安全的加法：如果靜態主機沒有把 /stroy/O 對應到這個檔案，就會落回
// 原本的 /* → /index.html 重寫，也就是今天的行為，不會壞掉，只是少了
// 這層 SEO 好處。
//
// 真正的預渲染（把 Vue 跑起來輸出完整 DOM）需要 headless browser，對這個
// 專案的收益主要在 meta 而不是內文，先不引進那個相依。

import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'

import { fetchJson, configProblem, reportMissing, RETRY_ATTEMPTS } from './build-fetch.js'

function escapeAttr(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function describe(el) {
  if (el.excerpt) return `${el.Name}（${el.Symbol}）：${el.excerpt}`

  const facts = [
    el.AtomicNumber ? `原子序 ${el.AtomicNumber}` : '',
    el.AtomicMass ? `原子量 ${el.AtomicMass}` : '',
    el.GroupBlock,
    el.StandardState ? `常溫下為${el.StandardState}` : ''
  ].filter(Boolean).join('、')

  return `${el.Name}（${el.Symbol}）：${facts}。`
}

// 換掉 head 裡的 SEO 標籤。既有的 og/twitter 是 vite-plugin-seo 用全站
// 文案寫進去的，要先拿掉，否則同一個屬性會出現兩次
function withElementMeta(html, { title, description, canonical, image, jsonLd }) {
  const tags = [
    `<link rel="canonical" href="${escapeAttr(canonical)}" />`,
    `<meta property="og:type" content="article" />`,
    `<meta property="og:title" content="${escapeAttr(title)}" />`,
    `<meta property="og:description" content="${escapeAttr(description)}" />`,
    `<meta property="og:url" content="${escapeAttr(canonical)}" />`,
    image ? `<meta property="og:image" content="${escapeAttr(image)}" />` : '',
    `<meta name="twitter:card" content="summary_large_image" />`,
    `<meta name="twitter:title" content="${escapeAttr(title)}" />`,
    `<meta name="twitter:description" content="${escapeAttr(description)}" />`,
    image ? `<meta name="twitter:image" content="${escapeAttr(image)}" />` : '',
    `<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>`
  ].filter(Boolean).join('\n    ')

  // 用 [\s\S] 而不是 . ——後台的網站描述可以有換行，`.` 不跨行會讓這些
  // 移除全部失效，結果 head 裡同時留著全站與元素兩份 description
  return html
    .replace(/<title>[\s\S]*?<\/title>/, `<title>${escapeAttr(title)}</title>`)
    .replace(/\s*<meta name="description" content="[\s\S]*?" \/>/, '')
    .replace(/\s*<meta (?:property="og:|name="twitter:)[\s\S]*?\/>/g, '')
    .replace(
      '</head>',
      `  <meta name="description" content="${escapeAttr(description)}" />\n    ${tags}\n  </head>`
    )
}

export default function prerenderPlugin() {
  return {
    name: 'prerender-element-pages',
    apply: 'build',
    async writeBundle(options, bundle) {
      const apiBase = process.env.VITE_API_URL
      const siteUrl = (process.env.VITE_SITE_URL || '').replace(/\/$/, '')

      const index = bundle['index.html']
      if (!index) return

      if (!siteUrl) {
        reportMissing('[prerender]', {
          reason: '未設定 VITE_SITE_URL',
          impact: '不預渲染元素頁；canonical 與 og:url 需要絕對網址才寫得出來',
          soft: true
        })
        return
      }

      const [data, settings] = await Promise.all([
        // /elements/seo 要並行讀 118 筆，後端冷啟動時會慢；build 只跑一次，
        // 等久一點也比整批預渲染靜悄悄被跳過好
        fetchJson(apiBase, '/elements/seo', { label: '元素 SEO 資料' }),
        fetchJson(apiBase, '/site-settings', { label: '網站設定' })
      ])
      const siteTitle = (settings?.title || '').trim() || 'Element Groups'
      const elements = data?.elements || []
      if (!elements.length) {
        const issue = configProblem(apiBase)
        reportMissing('[prerender]', {
          reason: issue || `${apiBase}/elements/seo 重試 ${RETRY_ATTEMPTS} 次` +
            `都沒有回應，或回傳空清單（實際拿到 ${elements.length} 筆）`,
          impact: '118 個元素頁對不執行 JS 的爬蟲是同一份空殼——同樣的標題、' +
            '同樣的描述、沒有結構化資料。Google 會判定內容重複而不建立索引',
          fix: '確認後端服務活著；免費方案的休眠請靠 buildCommand 的預熱請求。' +
            '若元素資料是空的，先跑 POST /api/admin/update-db',
          soft: Boolean(issue)
        })
        return
      }

      const html = index.source
      const outDir = options.dir
      const imgBase = apiBase.replace(/\/$/, '')
      let withStory = 0

      await Promise.all(elements.map(async el => {
        const canonical = `${siteUrl}/stroy/${el.Symbol}`
        const description = describe(el)
        const image = `${imgBase}/elements/${el.Symbol}/img`
        if (el.excerpt) withStory++

        const page = withElementMeta(html, {
          title: `${el.Name} ${el.Symbol}｜${siteTitle}`,
          description,
          canonical,
          image,
          jsonLd: {
            '@context': 'https://schema.org',
            '@type': 'ChemicalSubstance',
            name: el.Name || el.Symbol,
            alternateName: el.Symbol,
            identifier: String(el.AtomicNumber || ''),
            description,
            url: canonical,
            image,
            ...(el.AtomicMass ? { molecularWeight: String(el.AtomicMass) } : {})
          }
        })

        const dir = path.join(outDir, 'stroy', el.Symbol)
        await mkdir(dir, { recursive: true })
        await writeFile(path.join(dir, 'index.html'), page)
      }))

      console.log(`[prerender] 已輸出 ${elements.length} 個元素頁（其中 ${withStory} 個帶有故事開頭）`)
    }
  }
}
