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
// 2. **requireBuildData()**。設了 PRERENDER_REQUIRED 就讓 build 直接失敗，
//    「SEO 靜默壞掉」因此變成「部署失敗」，至少會被看見。render.yaml 的
//    buildCommand 有設，本機開發與 CI 沒設——CI 是刻意不設的，它要走
//    fallback 路徑確認退路沒被改壞（見 .github/workflows/build-check.yml）。

const DEFAULT_TIMEOUT = 45000
const DEFAULT_ATTEMPTS = 3
const DEFAULT_RETRY_DELAY = 15000

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms))

// 設了才算開，`0` 與 `false` 視為關——避免有人填 PRERENDER_REQUIRED=0
// 以為關掉了，實際上非空字串都是 truthy
export function requireBuildData() {
  const value = (process.env.PRERENDER_REQUIRED || '').trim().toLowerCase()
  return value !== '' && value !== '0' && value !== 'false'
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

  const lines = [
    `${label} 取不到 build 需要的資料`,
    '',
    `原因：${reason}`,
    `影響：${impact}`,
    ...(fix ? ['', `處理：${fix}`] : []),
    ...(required
      ? ['', '已設定 PRERENDER_REQUIRED，中止 build。']
      : ['', '未設定 PRERENDER_REQUIRED，build 繼續——但上線的產出會缺這部分。'])
  ]

  const border = '='.repeat(76)
  const block = ['', border, ...lines.map(line => (line ? `  ${line}` : '')), border, ''].join('\n')

  if (required) {
    console.error(block)
    throw new Error(`${label} 取不到資料，且已設定 PRERENDER_REQUIRED——中止 build`)
  }
  console.warn(block)
}
