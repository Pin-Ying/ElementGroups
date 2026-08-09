<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <!-- Login Form -->
    <div v-if="!authState.loggedIn" class="admin-box">
      <p class="title">LOGIN</p>
      <div class="box" id="login-box">
        <form @submit.prevent="handleLogin">
          <label class="label">Email</label>
          <input class="input" type="text" v-model="email" placeholder="Email" required />
          <label class="label">Password</label>
          <input class="input" type="password" v-model="password" placeholder="Password" required />
          <div class="form-actions">
            <button class="button" type="submit">Login</button>
            <button class="button secondary" type="button" @click="email = ''; password = ''">Reset</button>
          </div>
        </form>
        <p v-if="msg" class="msg error-msg">{{ msg }}</p>
      </div>
    </div>

    <!-- Admin Panel -->
    <div v-if="authState.loggedIn" class="admin-box">
      <div class="admin-header">
        <p class="title">ADMIN</p>
        <button class="button secondary" @click="handleLogout">Logout</button>
      </div>

      <!-- Tab switcher -->
      <div class="group-type-button" style="margin-bottom: 24px">
        <button class="button" :class="{ active: adminTab === 'main' }" @click="adminTab = 'main'">管理</button>
        <button class="button" :class="{ active: adminTab === 'maintenance' }" @click="adminTab = 'maintenance'">維護工具</button>
      </div>

      <!-- ── 管理 Tab ── -->
      <template v-if="adminTab === 'main'">

        <!-- Default Image -->
        <div class="box">
          <p class="title is-4">DEFAULT IMAGE</p>
          <p class="desc">元素尚未上傳圖片時顯示的預設圖片</p>
          <img v-if="defaultImgData" :src="defaultImgData" class="img-preview" alt="Default" />
          <p v-else class="placeholder-text">尚未設定</p>
          <form @submit.prevent="handleUpdateDefaultImg">
            <input class="input" type="file" accept=".jpg" ref="defaultImgInput" required @change="onDefaultImgFileChange" />
            <div v-if="defaultImgPreviewUrl" class="preview-new">
              <p class="preview-label">新圖片預覽（尚未儲存）</p>
              <img :src="defaultImgPreviewUrl" class="img-preview" alt="New default preview" />
            </div>
            <button class="button" type="submit" :disabled="defaultImgSaving">
              {{ defaultImgSaving ? 'Uploading…' : 'Upload' }}
            </button>
          </form>
        </div>

        <!-- Creator Links -->
        <div class="box">
          <p class="title is-4">CREATOR LINKS</p>
          <p class="desc">
            設定要對外顯示的社群連結，數量不限。<br>
            儲存後會出現在每一頁最下方的頁尾，以及 /links 頁面；網址留空的項目會被忽略。
          </p>

          <form @submit.prevent="handleUpdateCreatorLinks">
            <div v-if="!creatorLinks.length" class="placeholder-text">
              尚未新增任何連結，點下方「＋ 新增連結」開始。
            </div>

            <div v-for="(link, i) in creatorLinks" :key="i" class="link-row">
              <div class="link-row-fields">
                <select class="select link-platform" v-model="link.platform" @change="onPlatformChange(link)">
                  <option v-for="p in platforms" :key="p.key" :value="p.key">{{ p.label }}</option>
                </select>
                <input
                  class="input link-label"
                  type="text"
                  v-model="link.label"
                  placeholder="顯示名稱"
                />
                <input
                  class="input link-url"
                  type="url"
                  v-model="link.url"
                  :placeholder="platformInfo(link.platform).placeholder"
                />
              </div>
              <div class="link-row-actions">
                <button class="icon-button" type="button" title="上移" :disabled="i === 0" @click="moveLink(i, -1)">↑</button>
                <button class="icon-button" type="button" title="下移" :disabled="i === creatorLinks.length - 1" @click="moveLink(i, 1)">↓</button>
                <button class="icon-button danger" type="button" title="刪除" @click="removeLink(i)">✕</button>
              </div>
            </div>

            <div class="link-actions">
              <button class="button secondary" type="button" @click="addLink">＋ 新增連結</button>
              <button class="button" type="submit" :disabled="creatorLinksSaving">
                {{ creatorLinksSaving ? 'Saving…' : 'Save' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Update Story -->
        <div class="box">
          <p class="title is-4">UPDATE STORY</p>
          <p class="desc">
            編輯單一元素的故事內容與代表圖片。<br>
            選擇元素後，Story 的文字會顯示在前台該元素的介紹頁（/stroy/{{ selectedSymbol || 'Symbol' }}），
            上傳圖片則會<strong>直接覆蓋</strong>該元素目前的圖片。<br>
            下拉選單的 ✓ 表示已寫故事、📷 表示已上傳圖片。
          </p>

          <div class="progress-summary">
            <span>已寫故事 <strong>{{ storyProgress }}</strong> / {{ elements.length }}</span>
            <span class="progress-divider">·</span>
            <span>已上圖 <strong>{{ imageProgress }}</strong> / {{ elements.length }}</span>
          </div>

          <form @submit.prevent="handleUpdateStory">
            <label class="label">Element</label>
            <select v-model="selectedSymbol" class="select" @change="onSymbolChange">
              <option v-for="opt in elementOptions" :key="opt.symbol" :value="opt.symbol">{{ opt.label }}</option>
            </select>

            <div v-if="selectedSymbol" class="current-img-wrap">
              <p class="preview-label">目前圖片</p>
              <img
                :src="currentElementImgSrc"
                class="img-preview"
                alt=""
                @error="e => e.target.style.display='none'"
              />
            </div>

            <label class="label">Story</label>
            <textarea
              class="textarea"
              v-model="storyText"
              rows="6"
              placeholder="Write the story…"
            ></textarea>

            <label class="label">Image (.jpg)</label>
            <input class="input" type="file" accept=".jpg" ref="imageInput" @change="onImageFileChange" />
            <div v-if="newImagePreviewUrl" class="preview-new">
              <p class="preview-label">新圖片預覽（尚未儲存）</p>
              <img :src="newImagePreviewUrl" class="img-preview" alt="New image preview" />
            </div>

            <button class="button" type="submit" :disabled="loading">Submit</button>
          </form>
        </div>

      </template>

      <!-- ── 維護工具 Tab ── -->
      <template v-if="adminTab === 'maintenance'">

        <div class="box maintenance-box">
          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">Create DB</p>
              <p class="desc">確認 Firestore 資料表是否存在（Firebase 模式下無實際作用，可忽略）</p>
            </div>
            <button class="button" @click="handleCreateDb">執行</button>
          </div>

          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">Update DB</p>
              <p class="desc">將週期表基礎資料（118 個元素屬性）上傳至 Firebase Realtime DB。<br>若資料已存在則略過，初始佈署後執行一次即可。</p>
            </div>
            <button class="button" @click="handleUpdateDb">執行</button>
          </div>

          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">Backfill img_data</p>
              <p class="desc">掃描所有元素，將只有 Firebase Storage URL（img）但沒有 base64（img_data）的圖片補齊。<br>用於批次補全舊資料，正常情況下上傳圖片時已自動處理。</p>
            </div>
            <button class="button" @click="handleBackfill">執行</button>
          </div>

          <div class="maintenance-item">
            <div class="maintenance-info">
              <p class="maintenance-title">重建完成度摘要</p>
              <p class="desc">重新掃描所有元素，更新首頁用來標示「已上傳圖片／已寫故事」的摘要資料。<br>正常情況下儲存故事時已自動同步，只有直接從 Firebase 後台改過資料才需要執行。</p>
            </div>
            <button class="button" @click="handleRebuildCompletion">執行</button>
          </div>

          <p v-if="adminMsg" class="msg" :class="adminMsgType">{{ adminMsg }}</p>
        </div>

      </template>
    </div>
  </div>
</template>

<script>
import { createDb, updateDb, getStoryData, updateStory, backfillImgData, getDefaultImgInfo, updateDefaultImg, getAdminCreatorLinks, updateCreatorLinks, rebuildCompletion, apiBase } from '../api'
import { authState, login, logout } from '../store/auth'
import { showToast } from '../store/toast'
import { setCreatorLinks } from '../store/creatorLinks'
import { PLATFORMS, platformInfo } from '../utils/socialPlatforms'
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { LoadingSpinner },
  data() {
    return {
      authState,
      adminTab: 'main',
      loading: false,
      email: '',
      password: '',
      msg: '',
      adminMsg: '',
      adminMsgType: '',
      elements: [],
      storyDatas: {},
      imageDatas: {},
      hasImageMap: {},
      selectedSymbol: '',
      storyText: '',
      defaultImgData: '',
      defaultImgSaving: false,
      newImagePreviewUrl: '',
      defaultImgPreviewUrl: '',
      creatorLinks: [],
      creatorLinksSaving: false,
      platforms: PLATFORMS
    }
  },
  computed: {
    currentElementImgSrc() {
      if (!this.selectedSymbol) return ''
      return apiBase + '/elements/' + this.selectedSymbol + '/img'
    },
    // #5：每個元素標示故事/圖片完成度，讓 admin 一眼看出還有哪些沒補
    elementOptions() {
      return this.elements.map(sym => {
        const hasStory = !!(this.storyDatas[sym] || '').trim()
        const hasImage = !!this.hasImageMap[sym]
        const marks = (hasStory ? ' ✓' : '') + (hasImage ? ' 📷' : '')
        return { symbol: sym, hasStory, hasImage, label: sym + marks }
      })
    },
    storyProgress() {
      return this.elementOptions.filter(o => o.hasStory).length
    },
    imageProgress() {
      return this.elementOptions.filter(o => o.hasImage).length
    }
  },
  async mounted() {
    if (this.authState.loggedIn) {
      await Promise.all([this.loadStoryData(), this.loadDefaultImg(), this.loadCreatorLinks()])
    }
  },
  beforeUnmount() {
    this.revokeImagePreview()
    this.revokeDefaultImgPreview()
  },
  methods: {
    onImageFileChange(e) {
      this.revokeImagePreview()
      const file = e.target.files[0]
      if (file) this.newImagePreviewUrl = URL.createObjectURL(file)
    },
    revokeImagePreview() {
      if (this.newImagePreviewUrl) {
        URL.revokeObjectURL(this.newImagePreviewUrl)
        this.newImagePreviewUrl = ''
      }
    },
    onDefaultImgFileChange(e) {
      this.revokeDefaultImgPreview()
      const file = e.target.files[0]
      if (file) this.defaultImgPreviewUrl = URL.createObjectURL(file)
    },
    revokeDefaultImgPreview() {
      if (this.defaultImgPreviewUrl) {
        URL.revokeObjectURL(this.defaultImgPreviewUrl)
        this.defaultImgPreviewUrl = ''
      }
    },
    async handleLogin() {
      this.loading = true
      this.msg = ''
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          await Promise.all([this.loadStoryData(), this.loadDefaultImg(), this.loadCreatorLinks()])
        } else {
          this.msg = result.message || 'Login failed'
        }
      } catch (e) {
        this.msg = e.response?.data?.message || 'Login failed'
      } finally {
        this.loading = false
      }
    },
    async handleLogout() {
      this.loading = true
      try {
        await logout()
      } catch (e) {
        console.error('Logout failed:', e)
      } finally {
        this.loading = false
      }
    },
    async handleCreateDb() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await createDb()
        this.adminMsg = res.data.message
        this.adminMsgType = 'success-msg'
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.loading = false
      }
    },
    async handleBackfill() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await backfillImgData()
        this.adminMsg = res.data.message
        this.adminMsgType = 'success-msg'
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.loading = false
      }
    },
    async handleRebuildCompletion() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await rebuildCompletion()
        this.adminMsg = res.data.message
        this.adminMsgType = 'success-msg'
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.loading = false
      }
    },
    async handleUpdateDb() {
      this.loading = true
      this.adminMsg = ''
      try {
        const res = await updateDb()
        this.adminMsg = res.data.message
        this.adminMsgType = 'success-msg'
        await this.loadStoryData()
      } catch (e) {
        this.adminMsg = e.response?.data?.message || 'Error!'
        this.adminMsgType = 'error-msg'
      } finally {
        this.loading = false
      }
    },
    async loadDefaultImg() {
      try {
        const res = await getDefaultImgInfo()
        this.defaultImgData = res.data.img_data || ''
      } catch (e) {
        console.error('Failed to load default image:', e)
      }
    },
    async handleUpdateDefaultImg() {
      const imageFile = this.$refs.defaultImgInput?.files[0]
      if (!imageFile) return
      const formData = new FormData()
      formData.append('image', imageFile)
      this.defaultImgSaving = true
      try {
        const res = await updateDefaultImg(formData)
        showToast(res.data.message, 'success')
        await this.loadDefaultImg()
        this.$refs.defaultImgInput.value = ''
        this.revokeDefaultImgPreview()
      } catch (e) {
        showToast(e.response?.data?.message || 'Upload failed', 'error')
      } finally {
        this.defaultImgSaving = false
      }
    },
    platformInfo,
    addLink() {
      const used = new Set(this.creatorLinks.map(l => l.platform))
      const next = PLATFORMS.find(p => !used.has(p.key)) || PLATFORMS[0]
      this.creatorLinks.push({ platform: next.key, label: next.label, url: '' })
    },
    removeLink(i) {
      this.creatorLinks.splice(i, 1)
    },
    moveLink(i, delta) {
      const target = i + delta
      if (target < 0 || target >= this.creatorLinks.length) return
      const [item] = this.creatorLinks.splice(i, 1)
      this.creatorLinks.splice(target, 0, item)
    },
    onPlatformChange(link) {
      // 顯示名稱還是預設值時，跟著平台一起換；使用者自訂過就不動它
      const isDefaultLabel = PLATFORMS.some(p => p.label === link.label)
      if (!link.label || isDefaultLabel) link.label = platformInfo(link.platform).label
    },
    async loadCreatorLinks() {
      try {
        const res = await getAdminCreatorLinks()
        this.creatorLinks = (res.data.links || []).map(l => ({
          platform: l.platform || 'website',
          label: l.label || '',
          url: l.url || ''
        }))
      } catch (e) {
        console.error('Failed to load creator links:', e)
      }
    },
    async handleUpdateCreatorLinks() {
      const links = this.creatorLinks
        .filter(l => (l.url || '').trim())
        .map(l => ({
          platform: l.platform,
          label: (l.label || '').trim() || platformInfo(l.platform).label,
          url: l.url.trim()
        }))
      this.creatorLinksSaving = true
      try {
        const res = await updateCreatorLinks({ links })
        showToast(res.data.message || 'Saved!', 'success')
        // 讓頁尾與 /links 立刻反映這次儲存的結果
        setCreatorLinks(links)
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.creatorLinksSaving = false
      }
    },
    async loadStoryData() {
      try {
        const res = await getStoryData()
        this.elements = res.data.elements || []
        this.storyDatas = res.data.storyDatas || {}
        this.imageDatas = res.data.imageDatas || {}
        this.hasImageMap = res.data.hasImage || {}
        if (this.elements.length > 0) {
          this.selectedSymbol = this.elements[0]
          this.storyText = this.storyDatas[this.selectedSymbol] || ''
        } else {
          showToast('元素清單為空，請先執行 Update DB', 'warning')
        }
      } catch (e) {
        console.error('Failed to load story data:', e)
        showToast('無法載入元素清單：' + (e.message || 'Network error'), 'error')
      }
    },
    onSymbolChange() {
      this.storyText = this.storyDatas[this.selectedSymbol] || ''
      this.revokeImagePreview()
      if (this.$refs.imageInput) this.$refs.imageInput.value = ''
    },
    async handleUpdateStory() {
      const formData = new FormData()
      formData.append('symbol', this.selectedSymbol)
      formData.append('stroy', this.storyText)
      const imageFile = this.$refs.imageInput?.files[0]
      if (imageFile) formData.append('image', imageFile)
      this.loading = true
      try {
        const res = await updateStory(formData)
        showToast(res.data.message || 'Saved!', 'success')
        this.storyDatas[this.selectedSymbol] = this.storyText
        // 讓下拉選單的完成度標記立即反映這次儲存的結果
        if (imageFile) this.hasImageMap[this.selectedSymbol] = true
        if (this.$refs.imageInput) this.$refs.imageInput.value = ''
        this.revokeImagePreview()
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.admin-box {
  text-align: center;
  padding: 20px;
  max-width: 720px;
  margin: 0 auto;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 4px;
}

.box {
  background: rgba(20, 5, 35, 0.5);
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 8px;
  padding: 24px 28px;
  margin-bottom: 20px;
  text-align: left;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.desc {
  font-size: 13px;
  opacity: 0.55;
  margin: 2px 0 14px;
  line-height: 1.5;
}

/* ── Creator links 動態列 ── */
.link-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(228, 251, 255, 0.07);
}

.link-row:last-of-type {
  border-bottom: none;
}

.link-row-fields {
  flex: 1;
  display: grid;
  grid-template-columns: 130px 150px 1fr;
  gap: 8px;
  min-width: 0;
}

.link-row-fields .input,
.link-row-fields .select {
  margin: 0;
}

.link-row-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  padding-top: 2px;
}

.icon-button {
  width: 28px;
  height: 30px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 5px;
  background: rgba(228, 251, 255, 0.05);
  color: rgba(228, 251, 255, 0.7);
  cursor: pointer;
  font-size: 13px;
  line-height: 1;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.icon-button:hover:not(:disabled) {
  background: rgba(228, 251, 255, 0.15);
  border-color: rgba(228, 251, 255, 0.45);
  color: #e4fbff;
}

.icon-button:disabled {
  opacity: 0.25;
  cursor: not-allowed;
}

.icon-button.danger:hover:not(:disabled) {
  background: rgba(255, 107, 107, 0.18);
  border-color: rgba(255, 107, 107, 0.6);
  color: #ff6b6b;
}

.link-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 14px;
}

@media (max-width: 700px) {
  .link-row-fields {
    grid-template-columns: 1fr;
  }
}

.progress-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  opacity: 0.75;
  margin: 0 0 14px;
  padding: 8px 12px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 6px;
  background: rgba(228, 251, 255, 0.04);
}

.progress-summary strong {
  color: #6ee76e;
  font-weight: 600;
}

.progress-divider {
  opacity: 0.35;
}

.placeholder-text {
  font-size: 13px;
  opacity: 0.4;
  margin: 8px 0;
}

.img-preview {
  max-width: 160px;
  max-height: 160px;
  border-radius: 6px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  display: block;
  margin: 10px 0;
}

.current-img-wrap {
  margin: 8px 0;
}

.preview-label {
  font-size: 12px;
  opacity: 0.5;
  margin: 4px 0 2px;
}

.preview-new {
  margin: 4px 0 10px;
}
.preview-new .img-preview {
  border-color: rgba(110, 231, 110, 0.5);
}

.textarea {
  width: 100%;
  min-height: 120px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(228,251,255,0.15);
  border-radius: 6px;
  color: rgba(228,251,255,0.9);
  padding: 8px 10px;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
  display: block;
  margin: 4px 0 10px;
}

.maintenance-box {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.maintenance-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(228, 251, 255, 0.07);
}

.maintenance-item:last-of-type {
  border-bottom: none;
}

.maintenance-info {
  flex: 1;
  text-align: left;
}

.maintenance-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
}

.msg {
  margin-top: 12px;
  font-size: 13px;
}

.success-msg { color: #6ee76e; }
.error-msg { color: #ff6b6b; }

input.input,
select.select {
  display: block;
  width: 100%;
  margin: 4px 0 10px;
  box-sizing: border-box;
}

button.button {
  margin: 4px 2px;
}

button.secondary {
  opacity: 0.6;
}

button.button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
