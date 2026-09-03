// Build 時為每個元素頁輸出一份自己的靜態 HTML。
//
// 問題：這是 SPA，所有網址共用同一份 index.html。Google 會執行 JS 所以
// 看得到 utils/seo.js 設定的標題與描述，但 Bing、Facebook、LINE 的爬蟲
// 不執行 JS——它們抓 /story/O 和 /story/Fe 拿到的是一模一樣的空殼。
//
// 做法：把打包好的 index.html 複製 118 份到 story/{Symbol}/index.html，
// 每份換掉 head 裡的 title、description、og/twitter 與 JSON-LD，並在 body
// 尾端補一段 <noscript> 的元素索引。載入的還是同一份 JS，所以使用者看到的
// 行為沒有任何差別。
//
// 這是安全的加法：如果靜態主機沒有把 /story/O 對應到這個檔案，就會落回
// 原本的 /* → /index.html 重寫，也就是今天的行為，不會壞掉，只是少了
// 這層 SEO 好處。
//
// 真正的預渲染（把 Vue 跑起來輸出完整 DOM）需要 headless browser，對這個
// 專案的收益主要在 meta 而不是內文，先不引進那個相依。
//
// ── <noscript> 的元素索引（issue #47）──────────────────────────────
//
// 在此之前全站每一頁的 body 都只有 `<div id="app"></div>`，`<a>` 標籤數是 0
// ——連結全由 JS 產生。所以 sitemap 是唯一的非 JS 發現路徑，118 個元素頁
// 對爬蟲是孤島：sitemap 宣告「這些網址存在」，但沒有任何頁面宣告「它們重要」。
//
// 為什麼用 <noscript> 而不是放進 #app：放 #app 裡的連結訊號較強，但 Vue 掛載
// 前會閃出來——1.4MB 的 bundle，每個使用者每一頁都會看到 118 個連結閃一下，
// 那是實際的視覺退步。<noscript> 零 FOUC，也沒有被當成隱藏連結的風險，而真正
// 不執行 JS 的爬蟲（Bing / Facebook / LINE）照樣讀得到。
//
// index.html 也一起注入：`/molecules`、`/guide`、`/links`、`/particles` 都是吃
// 同一份空殼，所以那些頁面連帶也有了導覽（issue #47 的第三層順便解決）。

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

// 全站共用的其他頁面。跟元素頁一樣，在此之前它們之間也沒有任何靜態連結
const SITE_PAGES = [
  ['/', '首頁 週期表'],
  ['/molecules', '分子'],
  ['/particles', '基本粒子'],
  ['/guide', '元素說明書'],
  ['/links', '社群連結']
]

// 給不執行 JS 的爬蟲用的靜態索引。
//
// currentSymbol 傳入時排除自己——自我連結沒有意義，而且元素頁本來就有
// canonical 指向自己。
function noscriptNav(elements, currentSymbol) {
  const elementLinks = elements
    .filter(el => el.Symbol !== currentSymbol)
    .map(el => {
      const name = el.Name ? `${escapeAttr(el.Name)}（${escapeAttr(el.Symbol)}）` : escapeAttr(el.Symbol)
      return `<li><a href="/story/${encodeURIComponent(el.Symbol)}">${name}</a></li>`
    })
    .join('')

  const pageLinks = SITE_PAGES
    .filter(([href]) => !(currentSymbol === null && href === '/'))
    .map(([href, label]) => `<li><a href="${escapeAttr(href)}">${escapeAttr(label)}</a></li>`)
    .join('')

  return [
    '<noscript>',
    '<nav aria-label="站台索引">',
    `<h2>元素索引</h2><ul>${elementLinks}</ul>`,
    `<h2>其他頁面</h2><ul>${pageLinks}</ul>`,
    '</nav>',
    '</noscript>'
  ].join('')
}

// 注入到 body 尾端。**命中要斷言**——這是字串替換，錨點沒對上會靜默 no-op，
// 而症狀是「build 成功但爬蟲還是看不到連結」，正是 issue #45 那類看不見的失敗
function withNav(html, nav, label) {
  const out = html.replace('</body>', `    ${nav}\n  </body>`)
  if (out === html) {
    throw new Error(`[prerender] ${label} 找不到 </body>，無法注入 <noscript> 索引`)
  }
  return out
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
        const canonical = `${siteUrl}/story/${el.Symbol}`
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

        const dir = path.join(outDir, 'story', el.Symbol)
        await mkdir(dir, { recursive: true })
        await writeFile(
          path.join(dir, 'index.html'),
          withNav(page, noscriptNav(elements, el.Symbol), `/story/${el.Symbol}`)
        )
      }))

      // index.html 也要有索引，而且它比元素頁更重要：首頁是 Google 重抓最頻繁
      // 的頁面，從它出發才能發現全部元素頁。同時 /molecules、/guide、/links、
      // /particles 都是吃這份空殼，所以它們連帶也有了導覽。
      //
      // 這裡是直接覆寫 vite 已經寫出的 dist/index.html（writeBundle 在檔案落地
      // 之後才跑）。不改 bundle.source，因為上面 118 份是以它為母本複製的，
      // 改了會讓每個元素頁都夾帶一份「全部 118 個」的索引而不是排除自己那份。
      await writeFile(
        path.join(outDir, 'index.html'),
        withNav(html, noscriptNav(elements, null), 'index.html')
      )

      console.log(
        `[prerender] 已輸出 ${elements.length} 個元素頁（其中 ${withStory} 個帶有故事開頭）；` +
        'index.html 與各元素頁都注入了 <noscript> 站台索引'
      )
    }
  }
}
