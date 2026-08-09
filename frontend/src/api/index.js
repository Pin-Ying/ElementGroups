import axios from 'axios'

// 直接寫在 <img src> 等非 axios 場合使用的 API base。
// production 由 Render 注入 VITE_API_URL 指向後端服務；沒設定時退回同源 /api。
export const apiBase = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

export function getElements() {
  return api.get('/elements')
}

export function getGroups(groupType) {
  return api.post('/groups', { groupType })
}

export function getElementDetail(symbol) {
  return api.get(`/elements/${symbol}`)
}

export function getElementAbility(symbol) {
  return api.get(`/elements/${symbol}/ability`)
}

export function login(email, password) {
  return api.post('/auth/login', { email, password })
}

export function logout() {
  return api.post('/auth/logout')
}

export function getAuthStatus() {
  return api.get('/auth/status')
}

export function createDb() {
  return api.post('/admin/create-db')
}

export function updateDb() {
  return api.post('/admin/update-db')
}

export function getStoryData() {
  return api.get('/admin/story')
}

export function updateStory(formData) {
  return api.post('/admin/story', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function backfillImgData() {
  return api.post('/admin/backfill-img-data')
}

export function getDefaultImgInfo() {
  return api.get('/admin/default-img')
}

export function getAiStatus() {
  return api.get('/ai/status')
}

export function suggestStory(payload) {
  return api.post('/admin/story-suggest', payload)
}

export function getElementsCompletion() {
  return api.get('/elements/completion')
}

export function rebuildCompletion() {
  return api.post('/admin/rebuild-completion')
}

export function getCreatorLinks() {
  return api.get('/creator-links')
}

export function getAdminCreatorLinks() {
  return api.get('/admin/creator-links')
}

export function updateCreatorLinks(data) {
  return api.post('/admin/creator-links', data)
}

export function updateDefaultImg(formData) {
  return api.post('/admin/default-img', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export default api
