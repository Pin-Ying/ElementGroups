// build-fetch 的測試。
//
// 這個模組值得測，理由和 moleculeCategory 不同：它不是規則複雜，而是
// **它壞掉的時候沒有任何症狀**。issue #45 的整個問題就是「取不到資料時
// 靜默略過、build 照樣成功」，所以這裡要釘住的是失敗路徑本身：
//
//   - 重試真的會重試，不是只印個訊息
//   - required 模式真的丟例外（build 才會失敗）
//   - 非 required 模式真的不丟（本機與 CI 才 build 得起來）
//   - 「沒設定」與「打不通」要走不同的處置
//
// 前三點若被改壞，一般的 build 檢查看不出來——它們的表徵都是「build 成功」。

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fetchJson, configProblem, requireBuildData, reportMissing } from './build-fetch.js'

const API = 'https://backend.example.com/api'

// 讓重試不必真的等 15 秒
const NO_DELAY = { retryDelay: 0 }

const ok = body => ({ ok: true, json: async () => body })

// 兩個都要在測試裡自己控制：requireBuildData 同時看 PRERENDER_REQUIRED 與
// RENDER，留任何一個給環境決定，測試就會依執行環境給出不同結果
const ENV_KEYS = ['PRERENDER_REQUIRED', 'RENDER']
let originalEnv

beforeEach(() => {
  originalEnv = Object.fromEntries(ENV_KEYS.map(key => [key, process.env[key]]))
  for (const key of ENV_KEYS) delete process.env[key]
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.spyOn(console, 'log').mockImplementation(() => {})
})

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (originalEnv[key] === undefined) delete process.env[key]
    else process.env[key] = originalEnv[key]
  }
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('requireBuildData', () => {
  it('本機與 CI（兩個變數都沒有）為關', () => {
    expect(requireBuildData()).toBe(false)
  })

  // 這是防線真正生效的條件。放在 render.yaml 的 buildCommand 裡不算——
  // 那份檔案不保證被套用
  it('Render 上自動為開，不必任何設定', () => {
    process.env.RENDER = 'true'
    expect(requireBuildData()).toBe(true)
  })

  it('明確設 1 或 true 為開', () => {
    process.env.PRERENDER_REQUIRED = '1'
    expect(requireBuildData()).toBe(true)
    process.env.PRERENDER_REQUIRED = 'true'
    expect(requireBuildData()).toBe(true)
  })

  // 逃生門：後端真的掛了又非得先把前端部署出去時
  it('在 Render 上明確設 0 或 false 可以關掉', () => {
    process.env.RENDER = 'true'
    for (const value of ['0', 'false', 'FALSE']) {
      process.env.PRERENDER_REQUIRED = value
      expect(requireBuildData(), `PRERENDER_REQUIRED=${JSON.stringify(value)}`).toBe(false)
    }
  })

  // 非空字串都是 truthy，填 0 以為關掉卻其實開著會很難查
  it('空白字串視為沒設定，跟著 RENDER 走', () => {
    for (const value of ['  ', '']) {
      process.env.PRERENDER_REQUIRED = value
      expect(requireBuildData(), `無 RENDER，PRERENDER_REQUIRED=${JSON.stringify(value)}`).toBe(false)
      process.env.RENDER = 'true'
      expect(requireBuildData(), `有 RENDER，PRERENDER_REQUIRED=${JSON.stringify(value)}`).toBe(true)
      delete process.env.RENDER
    }
  })
})

describe('configProblem', () => {
  it('絕對網址沒有問題', () => {
    expect(configProblem(API)).toBeNull()
    expect(configProblem('http://localhost:8000/api')).toBeNull()
  })

  it('未設定與相對路徑都是設定問題', () => {
    expect(configProblem(undefined)).toMatch(/未設定/)
    expect(configProblem('')).toMatch(/未設定/)
    // production 的前端是 static site，相對 /api 會被 SPA fallback 吞掉
    expect(configProblem('/api')).toMatch(/絕對網址/)
  })
})

describe('fetchJson', () => {
  it('成功就直接回傳 JSON', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ok({ elements: [1, 2] })))
    await expect(fetchJson(API, '/elements/seo', NO_DELAY)).resolves.toEqual({ elements: [1, 2] })
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  // 這是 issue #45 的正解：後端冷啟動失敗第一次是常態
  it('第一次失敗會重試，第二次成功就回傳', async () => {
    const fetchMock = vi.fn()
      .mockRejectedValueOnce(Object.assign(new Error('aborted'), { name: 'AbortError' }))
      .mockResolvedValueOnce(ok({ ok: 1 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchJson(API, '/site-settings', NO_DELAY)).resolves.toEqual({ ok: 1 })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('HTTP 錯誤碼也要重試，不是只有連線失敗', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 500 })
      .mockResolvedValueOnce(ok({ ok: 1 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchJson(API, '/elements/seo', NO_DELAY)).resolves.toEqual({ ok: 1 })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('全部失敗後回傳 null，且嘗試次數用完', async () => {
    const fetchMock = vi.fn(async () => { throw new Error('fetch failed') })
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchJson(API, '/molecules', { ...NO_DELAY, attempts: 3 })).resolves.toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('沒有可用的 API 網址時完全不發請求', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchJson(undefined, '/molecules', NO_DELAY)).resolves.toBeNull()
    await expect(fetchJson('/api', '/molecules', NO_DELAY)).resolves.toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('reportMissing', () => {
  const detail = { reason: '後端沒有回應', impact: '元素頁沒有各自的 meta' }

  it('非 required 模式不丟例外，build 要能繼續', () => {
    expect(() => reportMissing('[prerender]', detail)).not.toThrow()
    expect(console.warn).toHaveBeenCalled()
  })

  // 不修這條，前面的重試哪天再失效還是不會有人知道
  it('required 模式丟例外，讓 build 失敗', () => {
    process.env.PRERENDER_REQUIRED = '1'
    expect(() => reportMissing('[prerender]', detail)).toThrow(/PRERENDER_REQUIRED/)
    expect(console.error).toHaveBeenCalled()
  })

  it('required 模式下連 soft 也要擋——那是缺環境變數的部署設定錯誤', () => {
    process.env.PRERENDER_REQUIRED = '1'
    expect(() => reportMissing('[emit-sitemap]', { ...detail, soft: true })).toThrow()
  })

  it('soft 在非 required 模式只印一行，不印醒目區塊', () => {
    reportMissing('[inject-seo]', { ...detail, soft: true })
    const printed = console.warn.mock.calls.map(args => args.join(' ')).join('\n')
    expect(printed).not.toMatch(/={10}/)
    expect(printed).toMatch(/略過/)
  })

  it('非 soft 在非 required 模式印醒目區塊，並說明 build 仍會繼續', () => {
    reportMissing('[prerender]', detail)
    const printed = console.warn.mock.calls.map(args => args.join(' ')).join('\n')
    expect(printed).toMatch(/={10}/)
    expect(printed).toContain('後端沒有回應')
    expect(printed).toContain('元素頁沒有各自的 meta')
    expect(printed).toMatch(/build 繼續/)
  })
})
