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

const FETCH_TIMEOUT = 8000

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

async function fetchJson(apiBase, path) {
  if (!apiBase || !/^https?:\/\//.test(apiBase)) return null
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT)
  try {
    const res = await fetch(`${apiBase.replace(/\/$/, '')}${path}`, { signal: controller.signal })
    return res.ok ? await res.json() : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
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
        // 就產不出有效的檔案；讓 build continue，但要講清楚為什麼沒有
        console.warn('[emit-sitemap] 未設定 VITE_SITE_URL，略過 sitemap.xml 與 robots.txt')
        return
      }

      const [completion, molecules, pages] = await Promise.all([
        fetchJson(apiBase, '/elements/completion'),
        fetchJson(apiBase, '/molecules'),
        fetchJson(apiBase, '/pages')
      ])

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
          loc: `${siteUrl}/stroy/${el.Symbol}`,
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

      if (!completion) console.warn('[emit-sitemap] 取不到元素完成度，sitemap 少了 lastmod')
      if (!molecules) console.warn('[emit-sitemap] 取不到分子清單，sitemap 不含分子頁')
      if (!pages) console.warn('[emit-sitemap] 取不到附加頁面，sitemap 不含自訂頁')

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

      console.log(`[emit-sitemap] 已產生 sitemap.xml（${entries.length} 筆）與 robots.txt`)
    }
  }
}
