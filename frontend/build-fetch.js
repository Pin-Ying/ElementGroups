// Build 期間向後端取資料的共用邏輯：重試，以及失敗時要吵。
//
// 背景（issue #45）：三個 vite plugin（seo / sitemap / prerender）都會在 build
// 階段打一次後端拿資料。Render 免費方案的後端會休眠，冷啟動要 30〜60 秒，
// build 時它若正在睡，那支請求就 timeout。
//
// 原本三支各自寫了一份 fetchJson，全都是 catch 後 return null，而 plugin 收到
// null 就 console.warn 一行然後 return——**build 的 exit code 仍然是 0**。
// 於是 118 個元素頁的預渲染整批被略過、對爬蟲全站是同一份空殼，Google Search
// Console 回報 129 頁「已找到但未建立索引」，而且這個狀況存在多久都不會有人
// 發現。sitemap 之所以還有東西，只是因為它有靜態元素清單當後備。
//
// 這裡做兩件事：
//
// 1. **重試**。冷啟動失敗第一次本來就是常態，隔十幾秒再試才是正常做法。
//    實測（後端休眠狀態下 build）：三支請求第一次全部逾時 45 秒，第二次全部
//    成功。第一批請求同時扛下喚醒後端的角色，後面的 plugin 打到的就是已經
//    醒著的後端——實際順序是 sitemap（generateBundle）先，接著 seo
//    （transformIndexHtml），最後 prerender（writeBundle）。
// 2. **requireBuildData()**。在 Render 上取不到資料就讓 build 直接失敗，
//    「SEO 靜默壞掉」因此變成「部署失敗」，至少會被看見。本機與 CI 不受影響
//    ——CI 刻意走 fallback 路徑，確認退路沒被改壞
//    （見 .github/workflows/build-check.yml）。

const DEFAULT_TIMEOUT = 45000
const DEFAULT_ATTEMPTS = 3
const DEFAULT_RETRY_DELAY = 15000

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

// 在 Render 上一律為開，不必靠任何設定——`RENDER` 是 Render 自己注入的預設
// 環境變數（值恆為 `true`），build 階段就有。
//
// 為什麼不只用 render.yaml 的 buildCommand 帶 PRERENDER_REQUIRED=1：那假設了
// render.yaml 真的被套用。實測發現不能假設——把 rewrite 規則加進 render.yaml
// 之後線上完全沒有變化（見 docs/verification/issue45-prerender.txt）。若這個
// 服務不是由 Blueprint 管理、或 Blueprint 的 Auto Sync 被關掉，render.yaml
// 就是一份沒人讀的檔案，而防線放在沒人讀的檔案裡等於沒有防線。
//
// `PRERENDER_REQUIRED` 保留為明確覆寫，兩個方向都能蓋過自動判斷：
//   留空       → 跟著 RENDER 走（Render 上開、本機與 CI 關）
//   1 / true   → 強制開，本機要驗證失敗路徑時用
//   0 / false  → 強制關，**逃生門**：後端真的掛了又非得先把前端部署出去時
// 這是專案既有的慣例（見 PASSWORD_LOGIN_ENABLED：留空＝連動，明確設值＝逃生門）。
export function requireBuildData() {
  const explicit = (process.env.PRERENDER_REQUIRED || '').trim().toLowerCase()
  if (explicit === '0' || explicit === 'false') return false
  if (explicit !== '') return true
  return Boolean(process.env.RENDER)
}

// 「沒設定 API 網址」和「設定了但打不通」是兩件事：前者是本機與 CI 的正常
// 路徑，後者才是 issue #45 那個會靜默上線的故障。分開判斷，才不會為了抓
// 後者把本機 build 的輸出洗成一整片警告。
export function configProblem(apiBase) {
  if (!apiBase) return 'VITE_API_URL 未設定'
  if (!/^https?:\/\//.test(apiBase)) return `VITE_API_URL 不是絕對網址（${apiBase}）`
  return null
}

export async function fetchJson(apiBase, urlPath, options = {}) {
  const {
    label = urlPath,
    timeout = DEFAULT_TIMEOUT,
    attempts = DEFAULT_ATTEMPTS,
    retryDelay = DEFAULT_RETRY_DELAY
  } = options

  if (configProblem(apiBase)) return null

  const url = `${apiBase.replace(/\/$/, '')}${urlPath}`
  let lastError = ''

  for (let attempt = 1; attempt <= attempts; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeout)
    try {
      const res = await fetch(url, { signal: controller.signal })
      if (res.ok) {
        if (attempt > 1) console.log(`[build-fetch] ${label} 第 ${attempt} 次嘗試成功`)
        return await res.json()
      }
      lastError = `HTTP ${res.status}`
    } catch (err) {
      // AbortError 的 message 是 "This operation was aborted"，看不出是逾時
      lastError = err?.name === 'AbortError' ? `逾時 ${timeout}ms` : (err?.message || String(err))
    } finally {
      clearTimeout(timer)
    }

    if (attempt < attempts) {
      console.warn(
        `[build-fetch] ${label} 第 ${attempt}/${attempts} 次失敗（${lastError}），` +
        `${Math.round(retryDelay / 1000)} 秒後重試`
      )
      await sleep(retryDelay)
    } else {
      console.warn(`[build-fetch] ${label} ${attempts} 次都失敗（${lastError}）`)
    }
  }

  return null
}

export const RETRY_ATTEMPTS = DEFAULT_ATTEMPTS

// 缺了 build 需要的資料時的統一處置。
//
// required 模式一律丟例外——用 throw 而不是 process.exit，vite 會把它當成
// build 失敗、印出來源位置，exit code 非 0，Render 的部署因此停在這裡，而不是
// 把一份對爬蟲空白的站台送上線。
//
// 非 required 模式：soft（設定本來就沒給）印一行就好，否則印醒目區塊——這種
// 情況是「設定齊全卻拿不到資料」，也就是真正的故障。
export function reportMissing(label, { reason, impact, fix, soft = false } = {}) {
  const required = requireBuildData()

  if (soft && !required) {
    console.warn(`${label} ${reason}，略過`)
    return
  }

  // 講清楚是「誰」讓 build 停下來的，否則看 log 的人會去翻沒設過的
  // PRERENDER_REQUIRED
  const trigger = process.env.RENDER && !(process.env.PRERENDER_REQUIRED || '').trim()
    ? '在 Render 上取不到資料一律中止 build（由 RENDER 環境變數判定）'
    : '已設定 PRERENDER_REQUIRED，中止 build'

  const lines = [
    `${label} 取不到 build 需要的資料`,
    '',
    `原因：${reason}`,
    `影響：${impact}`,
    ...(fix ? ['', `處理：${fix}`] : []),
    ...(required
      ? ['', `${trigger}。若非得先部署，設 PRERENDER_REQUIRED=0 可暫時放行。`]
      : ['', '這不是 Render 環境，build 繼續——但產出會缺這部分。'])
  ]

  const border = '='.repeat(76)
  const block = ['', border, ...lines.map(line => (line ? `  ${line}` : '')), border, ''].join('\n')

  if (required) {
    console.error(block)
    throw new Error(`${label} 取不到 build 需要的資料——${trigger}`)
  }
  console.warn(block)
}
