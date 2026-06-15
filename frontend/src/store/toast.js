import { reactive } from 'vue'

const state = reactive({ toasts: [] })
let nextId = 0

export function showToast(message, type = 'info', duration = 3500) {
  const id = ++nextId
  state.toasts.push({ id, message, type })
  setTimeout(() => removeToast(id), duration)
}

export function removeToast(id) {
  const idx = state.toasts.findIndex(t => t.id === id)
  if (idx !== -1) state.toasts.splice(idx, 1)
}

export const toastState = state
