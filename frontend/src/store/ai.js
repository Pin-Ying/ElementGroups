// AI 協助的全站狀態（issue #26）。
//
// 額度是「每天、整站共用」的，不是每個編輯畫面各自一份。原本 AdminView 與
// StoryEditor 各存一份 {enabled, used, limit}、各打一次 /ai/status，結果是
// 在後台用掉一次額度，前台故事編輯視窗顯示的數字不會跟著動——同一個事實
// 有兩個來源。
//
// 收成這裡之後，掛 AI 的欄位不必再各自傳狀態進去，也不必接「用掉了」的
// 事件；AiAssist 直接讀寫這份。
import { reactive } from 'vue'
import { getAiStatus } from '../api'

const state = reactive({
  enabled: false,
  used: 0,
  limit: 0,
  loaded: false
})

let inflight = null

async function load() {
  try {
    const res = await getAiStatus()
    state.enabled = !!res.data.enabled
    state.used = res.data.used || 0
    state.limit = res.data.limit || 0
  } catch {
    // 沒設定 API key、或後端還沒支援，就當作停用，介面完全不出現
    state.enabled = false
  } finally {
    state.loaded = true
    inflight = null
  }
}

/**
 * 確保狀態已載入。可以重複呼叫：載過就直接回，同時有多個欄位開場一起問也
 * 只會發一次請求。
 */
export function ensureAiStatus() {
  if (state.loaded) return Promise.resolve()
  if (!inflight) inflight = load()
  return inflight
}

/** 每產生一次就回報最新用量，所有顯示額度的地方一起更新。 */
export function setAiUsage(used, limit) {
  if (typeof used === 'number') state.used = used
  if (typeof limit === 'number') state.limit = limit
}

export const aiState = state
