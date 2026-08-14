import { reactive } from 'vue'

const state = reactive({ toasts: [] })
let nextId = 0

const DEFAULT_DURATION = 3500

// 錯誤訊息預設不自動消失（duration 0），留在畫面上讓人看完、複製下來除錯。
// 呼叫端仍可自己指定 duration 蓋掉這個預設。
export function showToast(message, type = 'info', duration = type === 'error' ? 0 : DEFAULT_DURATION) {
  const sticky = !(duration > 0)
  // 停留型的訊息會累積，同一句話重複噴就不再疊上去
  if (sticky && state.toasts.some(t => t.sticky && t.type === type && t.message === message)) return
  const id = ++nextId
  state.toasts.push({ id, message, type, sticky })
  if (!sticky) setTimeout(() => removeToast(id), duration)
}

export function removeToast(id) {
  const idx = state.toasts.findIndex(t => t.id === id)
  if (idx !== -1) state.toasts.splice(idx, 1)
}

export const toastState = state
