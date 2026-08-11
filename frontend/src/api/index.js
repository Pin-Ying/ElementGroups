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

export function getMolecules(params = {}) {
  return api.get('/molecules', { params })
}

export function getMolecule(slug) {
  return api.get(`/molecules/${slug}`)
}

export function suggestPage(payload) {
  return api.post('/admin/page-suggest', payload)
}

export function getPageMeta() {
  return api.get('/page-meta')
}

export function savePageMeta(key, payload) {
  return api.post(`/admin/page-meta/${key}`, payload)
}

export function getParticles() {
  return api.get('/particles')
}

export function getAdminParticles() {
  return api.get('/admin/particles')
}

export function saveParticle(payload) {
  return api.post('/admin/particles', payload)
}

export function deleteParticle(slug) {
  return api.delete(`/admin/particles/${slug}`)
}

export function getElementGroups() {
  return api.get('/element-groups')
}

export function getElementGroup(key) {
  return api.get(`/element-groups/${key}`)
}

export function getAdminGroups() {
  return api.get('/admin/element-groups')
}

export function saveGroup(key, payload) {
  return api.post(`/admin/element-groups/${key}`, payload)
}

export function getAdminMolecules() {
  return api.get('/admin/molecules')
}

export function saveMolecule(payload) {
  return api.post('/admin/molecules', payload)
}

export function deleteMolecule(slug) {
  return api.delete(`/admin/molecules/${slug}`)
}

export function lookupMolecule(params) {
  return api.get('/admin/molecules/lookup', { params })
}

export function getPages() {
  return api.get('/pages')
}

export function getPage(slug) {
  return api.get(`/pages/${slug}`)
}

export function getAdminPages() {
  return api.get('/admin/pages')
}

export function savePage(payload) {
  return api.post('/admin/pages', payload)
}

export function deletePage(slug) {
  return api.delete(`/admin/pages/${slug}`)
}

export function getSiteSettings() {
  return api.get('/site-settings')
}

export function getAdminSiteSettings() {
  return api.get('/admin/site-settings')
}

export function updateSiteSettings(formData) {
  return api.post('/admin/site-settings', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getAiStatus() {
  return api.get('/ai/status')
}

export function suggestStory(payload) {
  return api.post('/admin/story-suggest', payload)
}

export function getRecentElements(limit = 8) {
  return api.get('/elements/recent', { params: { limit } })
}

export function getPopularElements(limit = 8) {
  return api.get('/elements/popular', { params: { limit } })
}

export function recordElementView(symbol) {
  return api.post(`/elements/${symbol}/view`)
}

export function getElementLayers(symbol) {
  return api.get(`/elements/${symbol}/layers`)
}

export function getAdminLayers(symbol) {
  return api.get(`/admin/elements/${symbol}/layers`)
}

export function updateLayers(symbol, payload) {
  return api.post(`/admin/elements/${symbol}/layers`, payload)
}

export function getElectronStyles() {
  return api.get('/admin/electron-styles')
}

export function saveElectronStyle(payload) {
  return api.post('/admin/electron-styles', payload)
}

export function setDefaultElectronStyle(id) {
  return api.post('/admin/electron-styles/default', { id })
}

export function deleteElectronStyle(id) {
  return api.delete(`/admin/electron-styles/${id}`)
}

export function migrateElectronStyles() {
  return api.post('/admin/electron-styles/migrate')
}

export function migrateGalleries() {
  return api.post('/admin/gallery/migrate')
}

export function getElectronMotion() {
  return api.get('/admin/electron-motion')
}

export function setElectronMotion(motion) {
  return api.post('/admin/electron-motion', { motion })
}

// ── 通用圖庫 ──
export function getLibraries() {
  return api.get('/admin/libraries')
}

export function saveLibrary(payload) {
  return api.post('/admin/libraries', payload)
}

export function deleteLibrary(id) {
  return api.delete(`/admin/libraries/${id}`)
}

export function getBindableTargets(bindType) {
  return api.get(`/admin/bindable/${bindType}`)
}

export function getElementGallery(symbol) {
  return api.get(`/elements/${symbol}/gallery`)
}

export function getAdminGallery(symbol) {
  return api.get(`/admin/elements/${symbol}/gallery`)
}

export function updateGallery(symbol, images) {
  return api.post(`/admin/elements/${symbol}/gallery`, { images })
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
