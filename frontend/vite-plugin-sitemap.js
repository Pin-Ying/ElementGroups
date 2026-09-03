// Build 時產生 sitemap.xml 與 robots.txt。
//
// 為什麼在 build 產生而不是做成後端端點：
//
// 1. sitemap 必須跟網站在同一個網域，後端是另一個服務，網址不同
// 2. Render 的 static site 把 /* 重寫到 index.html，只有實際存在的檔案
//    才會被優先送出——所以 sitemap.xml 得是 dist 裡的真檔案
// 3. 後端在免費方案會休眠，爬蟲來抓 sitemap 時不該等它冷啟動
//
// 代價是新增分子或頁面後要重新部署，sitemap 才會更新。元素固定 118 個
// 不受影響，而後台改文案本來就要重新部署爬蟲才看得到（見 vite-plugin-seo.js）。

import { ELEMENT_SYMBOLS } from './src/data/elementSymbols.js'
import { fetchJson, configProblem, reportMissing, RETRY_ATTEMPTS } from './build-fetch.js'

function escapeXml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

// sitemap 的 lastmod 要 W3C datetime；後台存的是 ISO 字串，取日期就夠
function toLastmod(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : date.toISOString().slice(0, 10)
}

function urlEntry({ loc, lastmod, changefreq, priority }) {
  return [
    '  <url>',
    `    <loc>${escapeXml(loc)}</loc>`,
    lastmod ? `    <lastmod>${lastmod}</lastmod>` : '',
    changefreq ? `    <changefreq>${changefreq}</changefreq>` : '',
    priority ? `    <priority>${priority}</priority>` : '',
    '  </url>'
  ].filter(Boolean).join('\n')
}

export default function sitemapPlugin() {
  return {
    name: 'emit-sitemap',
    apply: 'build',
    async generateBundle() {
      const apiBase = process.env.VITE_API_URL
      const siteUrl = (process.env.VITE_SITE_URL || '').replace(/\/$/, '')

      if (!siteUrl) {
        // sitemap 與 robots 的 Sitemap 指令都需要絕對網址，沒有站台網址
        // 就產不出有效的檔案；本機 build 走這條路很正常，required 模式下
        // 則是缺環境變數的部署設定錯誤，要擋下來
        reportMissing('[emit-sitemap]', {
          reason: '未設定 VITE_SITE_URL',
          impact: '不產生 sitemap.xml 與 robots.txt，搜尋引擎沒有網址清單可抓',
          soft: true
        })
        return
      }

      const [completion, molecules, pages] = await Promise.all([
        fetchJson(apiBase, '/elements/completion', { label: '元素完成度' }),
        fetchJson(apiBase, '/molecules', { label: '分子清單' }),
        fetchJson(apiBase, '/pages', { label: '附加頁面' })
      ])

      // 檢查放在組 entries 之前：required 模式要在產出任何檔案以前就中止，
      // 不要送出一份「筆數看起來正常、其實少了分子頁與 lastmod」的 sitemap。
      // 只有 null（請求失敗）算缺資料，空清單是合法的——站上本來就可能還
      // 沒有分子或附加頁面
      const issue = configProblem(apiBase)
      const missing = [
        [completion, '元素完成度', '元素頁全部沒有 lastmod，爬蟲看不出哪些頁面更新過'],
        [molecules, '分子清單', 'sitemap 不含任何分子頁，/molecule/:slug 從來沒被提交給 Google'],
        [pages, '附加頁面', 'sitemap 不含後台建立的自訂頁 /p/:slug']
      ].filter(([data]) => !data)

      if (missing.length) {
        reportMissing('[emit-sitemap]', {
          reason: issue || `${missing.map(([, name]) => name).join('、')}` +
            `重試 ${RETRY_ATTEMPTS} 次都沒有回應（${apiBase}）`,
          impact: missing.map(([, , effect]) => effect).join('；'),
          fix: '確認後端服務活著；免費方案的休眠請靠 buildCommand 的預熱請求',
          soft: Boolean(issue)
        })
      }

      const done = completion?.completion || {}
      const entries = []

      entries.push(urlEntry({
        loc: `${siteUrl}/`,
        changefreq: 'weekly',
        priority: '1.0'
      }))

      // 元素頁是全站的主要內容。有原創故事的權重高一些，那才是真正
      // 有獨特內容、值得排在前面的頁面
      for (const el of ELEMENT_SYMBOLS) {
        const info = done[el.Symbol] || {}
        entries.push(urlEntry({
          loc: `${siteUrl}/story/${el.Symbol}`,
          lastmod: toLastmod(info.updated_at),
          changefreq: 'monthly',
          priority: info.story ? '0.8' : '0.5'
        }))
      }

      for (const path of ['/molecules', '/particles', '/guide', '/links']) {
        entries.push(urlEntry({
          loc: `${siteUrl}${path}`,
          changefreq: 'monthly',
          priority: '0.6'
        }))
      }

      // 未登入時 API 本來就只回傳已發布的，草稿不會進 sitemap
      for (const m of molecules?.molecules || []) {
        if (!m.published) continue
        entries.push(urlEntry({
          loc: `${siteUrl}/molecule/${m.slug}`,
          lastmod: toLastmod(m.updated_at),
          changefreq: 'monthly',
          priority: '0.7'
        }))
      }

      for (const p of pages?.pages || []) {
        if (!p.published) continue
        entries.push(urlEntry({
          loc: `${siteUrl}/p/${p.slug}`,
          changefreq: 'monthly',
          priority: '0.5'
        }))
      }

      this.emitFile({
        type: 'asset',
        fileName: 'sitemap.xml',
        source: [
          '<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
          entries.join('\n'),
          '</urlset>',
          ''
        ].join('\n')
      })

      this.emitFile({
        type: 'asset',
        fileName: 'robots.txt',
        source: [
          'User-agent: *',
          'Allow: /',
          // 後台沒有值得收錄的內容，也不希望出現在搜尋結果
          'Disallow: /admin',
          '',
          `Sitemap: ${siteUrl}/sitemap.xml`,
          ''
        ].join('\n')
      })

      // 把驗收要看的三個數字直接印在 build log 裡。issue #45 的症狀正是
      // 「123 筆看起來很正常，但 lastmod 0 個、分子頁 0 個」——只印總筆數
      // 看不出資料其實沒拿到
      const lastmods = entries.filter(entry => entry.includes('<lastmod>')).length
      const moleculeUrls = entries.filter(entry => entry.includes('/molecule/')).length
      console.log(
        `[emit-sitemap] 已產生 sitemap.xml（${entries.length} 筆，` +
        `其中 lastmod ${lastmods} 個、分子頁 ${moleculeUrls} 個）與 robots.txt`
      )
    }
  }
}
