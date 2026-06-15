import axios from 'axios'

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

export function updateDefaultImg(formData) {
  return api.post('/admin/default-img', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export default api
