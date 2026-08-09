<template>
  <div>
    <LoadingSpinner v-if="loading" />

    <!-- 圖片裁切：上傳任何圖片後先進這裡 -->
    <ImageCropper
      v-if="cropFile"
      :file="cropFile"
      @done="onCropDone"
      @skip="onCropSkip"
      @cancel="onCropCancel"
    />

    <!-- Login Form -->
    <div v-if="!authState.loggedIn" class="admin-box">
      <p class="title">LOGIN</p>
      <div class="box" id="login-box">
        <form @submit.prevent="handleLogin">
          <label class="label">Email</label>
          <input class="input" type="text" v-model="email" required />
          <label class="label">Password</label>
          <input class="input" type="password" v-model="password" required />
          <div class="form-actions">
            <button class="button" type="submit">Login</button>
            <button class="button secondary" type="button" @click="email = ''; password = ''">Reset</button>
          </div>
        </form>
        <p v-if="msg" class="msg error-msg">{{ msg }}</p>
      </div>
    </div>

    <!-- Admin Panel -->
    <div v-if="authState.loggedIn" class="admin-layout">
      <!-- 側邊導覽：功能區塊變多後改為一次只顯示一項，不必一路往下滑 -->
      <aside class="admin-nav">
        <p class="nav-title">ADMIN</p>
        <nav class="nav-list">
          <button
            v-for="s in SECTIONS"
            :key="s.key"
            class="nav-item"
            type="button"
            :class="{ active: section === s.key }"
            @click="setSection(s.key)"
          >
            <span class="nav-icon">{{ s.icon }}</span>
            <span class="nav-label">{{ s.label }}</span>
          </button>
        </nav>
        <button class="nav-item nav-logout" type="button" @click="handleLogout">
          <span class="nav-icon">→</span>
          <span class="nav-label">登出</span>
        </button>
      </aside>

      <div class="admin-content">
        <p class="content-title">{{ currentSection.label }}</p>

        <!-- Site Settings -->
        <div v-if="section === 'site'" class="box">
          <p class="title is-4">SITE SETTINGS</p>
          <p class="desc">
            網站層級的基本資料。標題與副標題會顯示在每一頁的左上角，
            描述用於搜尋引擎與分享連結時的摘要；留空則沿用系統預設文案。
          </p>
          <form @submit.prevent="handleUpdateSiteSettings">
            <label class="label">網站標題</label>
            <input class="input" type="text" v-model="siteForm.title" />

            <label class="label">副標題</label>
            <input class="input" type="text" v-model="siteForm.subtitle" />

            <label class="label">網站描述（SEO）</label>
            <textarea class="textarea site-desc" v-model="siteForm.description" rows="2"></textarea>

            <label class="label">首頁背景圖</label>
            <p class="field-hint">{{ uploadHint }}</p>
            <img v-if="siteBgCurrent && !siteBgPreviewUrl" :src="siteBgCurrent" class="img-preview bg-preview" alt="目前背景圖" />
            <p v-else-if="!siteBgCurrent && !siteBgPreviewUrl" class="placeholder-text">尚未設定，維持原本的漸層底色</p>
            <input class="input" type="file" accept="image/*" ref="siteBgInput" @change="onSiteBgFileChange" />
            <div v-if="siteBgPreviewUrl" class="preview-new">
              <p class="preview-label">新背景圖預覽（尚未儲存）</p>
              <img :src="siteBgPreviewUrl" class="img-preview bg-preview" alt="New background preview" />
              <p class="compress-info">{{ compressionSummary(siteBgInfo) }}</p>
            </div>

            <label class="label">元素圖鑑外框</label>
            <p class="field-hint">套用在元素頁代表圖外圍的框線樣式，會依該元素的顏色變化。</p>
            <div class="frame-picker">
              <button
                v-for="f in FRAME_STYLES"
                :key="f.key"
                class="frame-option"
                type="button"
                :class="{ active: siteForm.frame_style === f.key }"
                @click="siteForm.frame_style = f.key"
              >
                <PokedexFrame :style="f.key" color="E06633">
                  <span class="frame-sample">Fe</span>
                </PokedexFrame>
                <span class="frame-option-label">{{ f.label }}</span>
              </button>
            </div>

            <label class="label">自訂外框圖（PNG，需透明背景）</label>
            <p class="field-hint">上傳後會覆蓋上面選的內建款式，圖片會等比拉伸鋪滿代表圖範圍。</p>
            <img v-if="siteFrameCurrent && !siteFramePreviewUrl" :src="siteFrameCurrent" class="img-preview bg-preview" alt="目前外框圖" />
            <p v-else-if="!siteFrameCurrent && !siteFramePreviewUrl" class="placeholder-text">未使用自訂外框</p>
            <input class="input" type="file" accept="image/png" ref="siteFrameInput" @change="onSiteFrameFileChange" />
            <div v-if="siteFramePreviewUrl" class="preview-new">
              <p class="preview-label">新外框圖預覽（尚未儲存）</p>
              <img :src="siteFramePreviewUrl" class="img-preview bg-preview" alt="New frame preview" />
            </div>

            <div class="link-actions">
              <button class="button" type="submit" :disabled="siteSaving">
                {{ siteSaving ? 'Saving…' : 'Save' }}
              </button>
              <button
                v-if="siteBgCurrent"
                class="button secondary"
                type="button"
                :disabled="siteSaving"
                @click="handleClearSiteBg"
              >移除背景圖</button>
              <button
                v-if="siteFrameCurrent"
                class="button secondary"
                type="button"
                :disabled="siteSaving"
                @click="handleClearSiteFrame"
              >移除自訂外框</button>
            </div>
          </form>
        </div>

        <!-- Default Image -->
        <div v-if="section === 'default-img'" class="box">
          <p class="title is-4">DEFAULT IMAGE</p>
          <p class="desc">
            元素尚未上傳圖片時顯示的預設圖片。<br>
            {{ uploadHint }}
          </p>
          <img v-if="defaultImgData" :src="defaultImgData" class="img-preview" alt="Default" />
          <p v-else class="placeholder-text">尚未設定</p>
          <form @submit.prevent="handleUpdateDefaultImg">
            <input class="input" type="file" accept="image/*" ref="defaultImgInput" @change="onDefaultImgFileChange" />
            <div v-if="defaultImgPreviewUrl" class="preview-new">
              <p class="preview-label">新圖片預覽（尚未儲存）</p>
              <img :src="defaultImgPreviewUrl" class="img-preview" alt="New default preview" />
              <p class="compress-info">{{ compressionSummary(defaultImgInfo) }}</p>
            </div>
            <button class="button" type="submit" :disabled="defaultImgSaving || !defaultImgBlob">
              {{ defaultImgSaving ? 'Uploading…' : 'Upload' }}
            </button>
          </form>
        </div>

        <!-- Creator Links -->
        <div v-if="section === 'links'" class="box">
          <p class="title is-4">CREATOR LINKS</p>
          <p class="desc">
            設定要對外顯示的社群連結，數量不限。<br>
            儲存後會出現在每一頁最下方的頁尾，以及 /links 頁面；網址留空的項目會被忽略。
          </p>

          <form @submit.prevent="handleUpdateCreatorLinks">
            <div v-if="!creatorLinks.length" class="placeholder-text">
              尚未新增任何連結，點下方「＋ 新增連結」開始。
            </div>

            <div v-if="creatorLinks.length" class="link-head">
              <span>平台</span>
              <span>顯示名稱</span>
              <span>網址</span>
            </div>

            <div v-for="(link, i) in creatorLinks" :key="i" class="link-row">
              <div class="link-row-fields">
                <select class="select link-platform" v-model="link.platform" @change="onPlatformChange(link)" aria-label="平台">
                  <option v-for="p in platforms" :key="p.key" :value="p.key">{{ p.label }}</option>
                </select>
                <input
                  class="input link-label"
                  type="text"
                  v-model="link.label"
                  aria-label="顯示名稱"
                />
                <input
                  class="input link-url"
                  type="url"
                  v-model="link.url"
                  aria-label="網址"
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
        <div v-if="section === 'story'" class="box">
          <p class="title is-4">UPDATE STORY</p>
          <p class="desc">
            編輯單一元素的故事內容與代表圖片。<br>
            選擇元素後，Story 的文字會顯示在前台該元素的介紹頁（/stroy/{{ selectedSymbol || 'Symbol' }}），
            上傳圖片則會<strong>直接覆蓋</strong>該元素目前的圖片。<br>
            下拉選單的 ✓ 表示已寫故事、▣ 表示已上傳圖片。
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

            <div class="label-row">
              <label class="label">Story</label>
              <button
                v-if="ai.enabled"
                class="ai-toggle"
                type="button"
                :class="{ active: aiPanelOpen }"
                @click="aiPanelOpen = !aiPanelOpen"
              >✧ AI 協助</button>
            </div>
            <textarea
              class="textarea"
              v-model="storyText"
              rows="6"
              ></textarea>

            <!-- AI 故事協助（只有後端設定了 API key 才會出現） -->
            <div v-if="ai.enabled && aiPanelOpen" class="ai-panel">
              <p class="ai-hint">
                會自動帶入這個元素的週期表資料（原子序、分類、熔沸點等）
                <template v-if="storyText.trim()">，以及你目前已經寫的內容（AI 會延伸潤飾而不是整段重寫）</template>。
              </p>

              <label class="label ai-label">風格／方向（選填）</label>
              <input
                class="input"
                type="text"
                v-model="aiDirection"
              />

              <label class="label ai-label">補充參考資料（選填）</label>
              <textarea
                class="textarea ai-reference"
                v-model="aiReference"
                rows="3"
              ></textarea>

              <div class="ai-actions">
                <button class="button" type="button" :disabled="aiLoading" @click="handleSuggest">
                  {{ aiLoading ? '產生中…' : (aiSuggestion ? '重新產生' : '產生建議') }}
                </button>
                <span v-if="ai.limit > 0" class="ai-quota">今日已用 {{ ai.used }} / {{ ai.limit }}</span>
              </div>

              <div v-if="aiSuggestion" class="ai-result">
                <p class="preview-label">AI 建議（尚未套用）</p>
                <div class="ai-suggestion">{{ aiSuggestion }}</div>
                <div class="ai-actions">
                  <button class="button secondary" type="button" @click="applySuggestion('append')">附加到編輯框</button>
                  <button class="button secondary" type="button" @click="applySuggestion('replace')">直接覆蓋</button>
                  <button class="button secondary" type="button" @click="aiSuggestion = ''">捨棄</button>
                </div>
                <p class="ai-note">套用後仍需按下方 Submit 才會真正儲存。</p>
              </div>
            </div>

            <label class="label">Image</label>
            <p class="field-hint">{{ uploadHint }}</p>
            <input class="input" type="file" accept="image/*" ref="imageInput" @change="onImageFileChange" />

            <!-- 目前圖片與待上傳的新圖並排，方便直接對照 -->
            <div class="img-compare">
              <div v-if="selectedSymbol" class="img-slot">
                <p class="preview-label">目前圖片</p>
                <img
                  :src="currentElementImgSrc"
                  class="img-preview"
                  alt=""
                  @error="e => e.target.style.display='none'"
                />
              </div>
              <div v-if="newImagePreviewUrl" class="img-slot img-slot--new">
                <p class="preview-label">新圖片（尚未儲存）</p>
                <img :src="newImagePreviewUrl" class="img-preview" alt="New image preview" />
                <p class="compress-info">{{ compressionSummary(newImageInfo) }}</p>
              </div>
            </div>

            <button class="button" type="submit" :disabled="loading">Submit</button>
          </form>

          <!-- 其他樣貌（gallery） -->
          <div class="gallery-admin">
            <p class="label">其他樣貌</p>
            <p class="field-hint">
              代表圖以外的照片，會顯示在元素頁故事下方的獨立區塊，最多 {{ GALLERY_MAX }} 張。<br>
              比照昆蟲、鳥類圖鑑：同一個元素的不同型態或狀態（例如純金屬、氧化物、礦石）。
            </p>

            <div v-if="!galleryItems.length" class="placeholder-text">
              尚未加入其他樣貌。
            </div>

            <div v-else class="gallery-admin-grid">
              <div v-for="(item, i) in galleryItems" :key="i" class="gallery-admin-item">
                <img :src="item.img_data" alt="" />
                <input
                  class="input gallery-caption"
                  type="text"
                  v-model="item.caption"
                  aria-label="說明文字"
                />
                <div class="gallery-admin-actions">
                  <button class="icon-button" type="button" title="左移" :disabled="i === 0" @click="moveGalleryItem(i, -1)">←</button>
                  <button class="icon-button" type="button" title="右移" :disabled="i === galleryItems.length - 1" @click="moveGalleryItem(i, 1)">→</button>
                  <button class="icon-button danger" type="button" title="刪除" @click="removeGalleryItem(i)">✕</button>
                </div>
              </div>
            </div>

            <input
              class="input"
              type="file"
              accept="image/*"
              multiple
              ref="galleryInput"
              :disabled="galleryItems.length >= GALLERY_MAX"
              @change="onGalleryFileChange"
            />

            <div class="link-actions">
              <button class="button" type="button" :disabled="gallerySaving || !selectedSymbol" @click="handleSaveGallery">
                {{ gallerySaving ? 'Saving…' : '儲存其他樣貌' }}
              </button>
              <span class="ai-quota">{{ galleryItems.length }} / {{ GALLERY_MAX }} 張</span>
            </div>
          </div>
        </div>

        <!-- 維護工具 -->
        <div v-if="section === 'maintenance'" class="box maintenance-box">
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
      </div>
    </div>
  </div>
</template>

<script>
import { createDb, updateDb, getStoryData, updateStory, backfillImgData, getDefaultImgInfo, updateDefaultImg, getAdminCreatorLinks, updateCreatorLinks, rebuildCompletion, getAiStatus, suggestStory, getAdminSiteSettings, updateSiteSettings, getAdminGallery, updateGallery, apiBase } from '../api'
import { authState, login, logout } from '../store/auth'
import { showToast } from '../store/toast'
import { setCreatorLinks } from '../store/creatorLinks'
import { setSiteSettings, SITE_DEFAULTS } from '../store/siteSettings'
import { PLATFORMS, platformInfo } from '../utils/socialPlatforms'
import { compressImage, formatBytes, MAX_UPLOAD_BYTES, MAX_EDGE } from '../utils/imageCompress'
import PokedexFrame, { FRAME_STYLES } from '../components/PokedexFrame.vue'
import ImageCropper from '../components/ImageCropper.vue'

// 與後端 GALLERY_MAX 一致
const GALLERY_MAX = 6

// 後台功能區塊。一次只顯示一項，避免所有表單疊在同一頁要一路往下滑。
const SECTIONS = [
  { key: 'story', label: '元素故事', icon: '✎' },
  { key: 'site', label: '網站設定', icon: '⚙' },
  { key: 'default-img', label: '預設圖片', icon: '▣' },
  { key: 'links', label: '社群連結', icon: '⚯' },
  { key: 'maintenance', label: '維護工具', icon: '⚒' }
]
import LoadingSpinner from '../components/LoadingSpinner.vue'

export default {
  components: { LoadingSpinner, PokedexFrame, ImageCropper },
  data() {
    return {
      authState,
      SECTIONS,
      section: SECTIONS.some(s => s.key === localStorage.getItem('adminSection'))
        ? localStorage.getItem('adminSection')
        : 'story',
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
      newImageBlob: null,
      newImageInfo: null,
      defaultImgPreviewUrl: '',
      defaultImgBlob: null,
      defaultImgInfo: null,
      creatorLinks: [],
      creatorLinksSaving: false,
      platforms: PLATFORMS,
      FRAME_STYLES,
      GALLERY_MAX,
      cropFile: null,
      cropTarget: null,
      cropQueue: [],
      galleryItems: [],
      gallerySaving: false,
      siteForm: { title: '', subtitle: '', description: '', frame_style: 'classic' },
      siteDefaults: SITE_DEFAULTS,
      siteBgCurrent: '',
      siteBgPreviewUrl: '',
      siteFrameCurrent: '',
      siteFramePreviewUrl: '',
      siteFrameBlob: null,
      siteBgBlob: null,
      siteBgInfo: null,
      siteSaving: false,
      ai: { enabled: false, used: 0, limit: 0 },
      aiPanelOpen: false,
      aiDirection: '',
      aiReference: '',
      aiSuggestion: '',
      aiLoading: false
    }
  },
  computed: {
    currentSection() {
      return SECTIONS.find(s => s.key === this.section) || SECTIONS[0]
    },
    uploadHint() {
      return `上傳前會自動等比縮至長邊 ${MAX_EDGE}px 並轉為 JPEG，減少資料庫用量；超過 ${formatBytes(MAX_UPLOAD_BYTES)} 的檔案不接受。`
    },
    currentElementImgSrc() {
      if (!this.selectedSymbol) return ''
      return apiBase + '/elements/' + this.selectedSymbol + '/img'
    },
    // #5：每個元素標示故事/圖片完成度，讓 admin 一眼看出還有哪些沒補
    elementOptions() {
      return this.elements.map(sym => {
        const hasStory = !!(this.storyDatas[sym] || '').trim()
        const hasImage = !!this.hasImageMap[sym]
        // 用幾何符號而非 emoji：介面字型沒有 emoji 字符，會渲染成方框
        const marks = (hasStory ? ' ✓' : '') + (hasImage ? ' ▣' : '')
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
      await Promise.all([this.loadStoryData(), this.loadDefaultImg(), this.loadCreatorLinks(), this.loadAiStatus(), this.loadSiteSettings()])
    }
  },
  beforeUnmount() {
    this.revokeImagePreview()
    this.revokeDefaultImgPreview()
  },
  methods: {
    // ── 圖片裁切流程 ──
    // 三個 1:1 顯示的圖片（元素代表圖、預設圖、其他樣貌）上傳後先進裁切；
    // 首頁背景圖是全螢幕 cover，固定比例沒有意義，維持原本的壓縮流程
    openCropper(e, target) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      if (!file.type.startsWith('image/')) {
        showToast('請選擇圖片檔', 'error')
        return
      }
      this.cropTarget = target
      this.cropQueue = []
      this.cropFile = file
    },
    async onCropDone({ blob }) {
      // 裁切輸出已是 JPEG，再走一次壓縮確保尺寸與檔案大小一致
      const file = new File([blob], 'cropped.jpg', { type: 'image/jpeg' })
      await this.acceptCropped(file)
    },
    async onCropSkip() {
      await this.acceptCropped(this.cropFile)
    },
    onCropCancel() {
      this.nextCropOrClose()
    },
    async acceptCropped(file) {
      const target = this.cropTarget
      try {
        const result = await compressImage(file)
        if (target === 'story') {
          this.newImageBlob = result.blob
          this.newImageInfo = result
          this.newImagePreviewUrl = URL.createObjectURL(result.blob)
        } else if (target === 'default') {
          this.defaultImgBlob = result.blob
          this.defaultImgInfo = result
          this.defaultImgPreviewUrl = URL.createObjectURL(result.blob)
        } else if (target === 'gallery') {
          const img_data = await new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result)
            reader.onerror = reject
            reader.readAsDataURL(result.blob)
          })
          this.galleryItems.push({ img_data, caption: '' })
        }
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      } finally {
        this.nextCropOrClose()
      }
    },
    nextCropOrClose() {
      // gallery 多檔時逐張處理
      this.cropFile = this.cropQueue.length ? this.cropQueue.shift() : null
      if (!this.cropFile) this.cropTarget = null
    },
    onImageFileChange(e) {
      this.revokeImagePreview()
      this.openCropper(e, 'story')
    },
    revokeImagePreview() {
      if (this.newImagePreviewUrl) {
        URL.revokeObjectURL(this.newImagePreviewUrl)
        this.newImagePreviewUrl = ''
      }
      this.newImageBlob = null
      this.newImageInfo = null
    },
    onDefaultImgFileChange(e) {
      this.revokeDefaultImgPreview()
      this.openCropper(e, 'default')
    },
    revokeDefaultImgPreview() {
      if (this.defaultImgPreviewUrl) {
        URL.revokeObjectURL(this.defaultImgPreviewUrl)
        this.defaultImgPreviewUrl = ''
      }
      this.defaultImgBlob = null
      this.defaultImgInfo = null
    },
    compressionSummary(info) {
      if (!info) return ''
      const saved = info.originalSize - info.compressedSize
      const pct = info.originalSize ? Math.round((saved / info.originalSize) * 100) : 0
      const size = `${formatBytes(info.originalSize)} → ${formatBytes(info.compressedSize)}`
      const dims = info.resized ? `，已縮至 ${info.width}×${info.height}` : ''
      return saved > 0 ? `${size}（省下 ${pct}%）${dims}` : `${size}${dims}`
    },
    async handleLogin() {
      this.loading = true
      this.msg = ''
      try {
        const result = await login(this.email, this.password)
        if (result.ok) {
          await Promise.all([this.loadStoryData(), this.loadDefaultImg(), this.loadCreatorLinks(), this.loadAiStatus(), this.loadSiteSettings()])
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
    async loadGallery() {
      if (!this.selectedSymbol) { this.galleryItems = []; return }
      try {
        const res = await getAdminGallery(this.selectedSymbol)
        this.galleryItems = res.data.images || []
      } catch (e) {
        console.error('Failed to load gallery:', e)
        this.galleryItems = []
      }
    },
    onGalleryFileChange(e) {
      const files = [...e.target.files]
      e.target.value = ''
      if (!files.length) return

      const room = GALLERY_MAX - this.galleryItems.length
      if (files.length > room) {
        showToast(`最多再加 ${room} 張，只會處理前 ${room} 張`, 'warning')
      }
      // 多檔時逐張進裁切，處理完一張才換下一張
      this.cropQueue = files.slice(0, room)
      this.cropTarget = 'gallery'
      this.cropFile = this.cropQueue.shift() || null
    },
    moveGalleryItem(i, delta) {
      const target = i + delta
      if (target < 0 || target >= this.galleryItems.length) return
      const [item] = this.galleryItems.splice(i, 1)
      this.galleryItems.splice(target, 0, item)
    },
    removeGalleryItem(i) {
      this.galleryItems.splice(i, 1)
    },
    async handleSaveGallery() {
      this.gallerySaving = true
      try {
        const res = await updateGallery(this.selectedSymbol, this.galleryItems.map(it => ({
          img_data: it.img_data,
          caption: (it.caption || '').trim()
        })))
        showToast(res.data.message || 'Saved!', 'success')
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.gallerySaving = false
      }
    },
    async loadSiteSettings() {
      try {
        const res = await getAdminSiteSettings()
        this.siteForm = {
          title: res.data.title || '',
          subtitle: res.data.subtitle || '',
          description: res.data.description || '',
          frame_style: res.data.frame_style || 'classic'
        }
        this.siteBgCurrent = res.data.bg_image || ''
        this.siteFrameCurrent = res.data.frame_image || ''
      } catch (e) {
        console.error('Failed to load site settings:', e)
      }
    },
    async onSiteBgFileChange(e) {
      this.revokeSiteBgPreview()
      const file = e.target.files[0]
      if (!file) return
      try {
        const result = await compressImage(file)
        this.siteBgBlob = result.blob
        this.siteBgInfo = result
        this.siteBgPreviewUrl = URL.createObjectURL(result.blob)
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
        e.target.value = ''
      }
    },
    revokeSiteBgPreview() {
      if (this.siteBgPreviewUrl) {
        URL.revokeObjectURL(this.siteBgPreviewUrl)
        this.siteBgPreviewUrl = ''
      }
      this.siteBgBlob = null
      this.siteBgInfo = null
    },
    onSiteFrameFileChange(e) {
      this.revokeSiteFramePreview()
      const file = e.target.files[0]
      if (!file) return
      // 外框圖要保留透明背景，不能走 JPEG 壓縮，只擋過大的檔案
      if (file.size > MAX_UPLOAD_BYTES) {
        showToast(`外框圖 ${formatBytes(file.size)} 超過 ${formatBytes(MAX_UPLOAD_BYTES)} 上限`, 'error')
        e.target.value = ''
        return
      }
      this.siteFrameBlob = file
      this.siteFramePreviewUrl = URL.createObjectURL(file)
    },
    revokeSiteFramePreview() {
      if (this.siteFramePreviewUrl) {
        URL.revokeObjectURL(this.siteFramePreviewUrl)
        this.siteFramePreviewUrl = ''
      }
      this.siteFrameBlob = null
    },
    buildSiteFormData() {
      const formData = new FormData()
      formData.append('title', this.siteForm.title)
      formData.append('subtitle', this.siteForm.subtitle)
      formData.append('description', this.siteForm.description)
      formData.append('frame_style', this.siteForm.frame_style || 'classic')
      return formData
    },
    async handleClearSiteFrame() {
      const formData = this.buildSiteFormData()
      formData.append('clear_frame_image', '1')
      await this.saveSiteSettings(formData)
    },
    async saveSiteSettings(formData) {
      this.siteSaving = true
      try {
        const res = await updateSiteSettings(formData)
        showToast(res.data.message || 'Saved!', 'success')
        await this.loadSiteSettings()
        // 讓 header 與頁面標題立刻反映
        setSiteSettings({ ...this.siteForm, bg_image: this.siteBgCurrent, frame_image: this.siteFrameCurrent })
        if (this.$refs.siteBgInput) this.$refs.siteBgInput.value = ''
        if (this.$refs.siteFrameInput) this.$refs.siteFrameInput.value = ''
        this.revokeSiteBgPreview()
        this.revokeSiteFramePreview()
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.siteSaving = false
      }
    },
    async handleUpdateSiteSettings() {
      const formData = this.buildSiteFormData()
      if (this.siteBgBlob) formData.append('bg_image', this.siteBgBlob, 'bg.jpg')
      if (this.siteFrameBlob) formData.append('frame_image', this.siteFrameBlob, 'frame.png')
      await this.saveSiteSettings(formData)
    },
    async handleClearSiteBg() {
      const formData = this.buildSiteFormData()
      formData.append('clear_bg_image', '1')
      await this.saveSiteSettings(formData)
    },
    async loadAiStatus() {
      try {
        const res = await getAiStatus()
        this.ai = {
          enabled: !!res.data.enabled,
          used: res.data.used || 0,
          limit: res.data.limit || 0
        }
      } catch (e) {
        // 沒設定或後端還沒支援，就當作停用，介面完全不顯示
        this.ai = { enabled: false, used: 0, limit: 0 }
      }
    },
    async handleSuggest() {
      this.aiLoading = true
      try {
        const res = await suggestStory({
          symbol: this.selectedSymbol,
          draft: this.storyText,
          direction: this.aiDirection,
          reference: this.aiReference
        })
        this.aiSuggestion = res.data.suggestion || ''
        this.ai.used = res.data.used ?? this.ai.used
        this.ai.limit = res.data.limit ?? this.ai.limit
      } catch (e) {
        showToast(e.response?.data?.message || 'AI 產生失敗', 'error')
      } finally {
        this.aiLoading = false
      }
    },
    applySuggestion(mode) {
      if (!this.aiSuggestion) return
      if (mode === 'replace') {
        this.storyText = this.aiSuggestion
      } else {
        const current = this.storyText.trim()
        this.storyText = current ? current + '\n\n' + this.aiSuggestion : this.aiSuggestion
      }
      this.aiSuggestion = ''
      showToast('已套用到編輯框，記得按 Submit 儲存', 'success')
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
      if (!this.defaultImgBlob) return
      const formData = new FormData()
      formData.append('image', this.defaultImgBlob, '_default.jpg')
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
    setSection(key) {
      this.section = key
      localStorage.setItem('adminSection', key)
      this.adminMsg = ''
    },
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
          this.loadGallery()
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
      this.loadGallery()
      this.revokeImagePreview()
      if (this.$refs.imageInput) this.$refs.imageInput.value = ''
    },
    async handleUpdateStory() {
      const formData = new FormData()
      formData.append('symbol', this.selectedSymbol)
      formData.append('stroy', this.storyText)
      const imageBlob = this.newImageBlob
      if (imageBlob) formData.append('image', imageBlob, `${this.selectedSymbol}.jpg`)
      this.loading = true
      try {
        const res = await updateStory(formData)
        showToast(res.data.message || 'Saved!', 'success')
        this.storyDatas[this.selectedSymbol] = this.storyText
        // 讓下拉選單的完成度標記立即反映這次儲存的結果
        if (imageBlob) this.hasImageMap[this.selectedSymbol] = true
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

/* ── 後台版面：側邊導覽 + 內容區 ── */
.admin-layout {
  display: grid;
  grid-template-columns: 190px 1fr;
  gap: 20px;
  max-width: 1080px;
  margin: 0 auto;
  padding: 20px 18px 40px;
  align-items: start;
}

.admin-nav {
  position: sticky;
  top: 88px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 14px 10px;
  border: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 10px;
  background: rgba(20, 5, 35, 0.5);
}

.nav-title {
  font-size: 12px;
  letter-spacing: 0.2em;
  color: rgba(228, 251, 255, 0.35);
  margin: 0 0 10px;
  padding: 0 10px;
  text-align: left;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 11px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: rgba(228, 251, 255, 0.62);
  font-family: inherit;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: rgba(228, 251, 255, 0.07);
  color: rgba(228, 251, 255, 0.92);
}

.nav-item.active {
  background: rgba(228, 251, 255, 0.15);
  color: #e4fbff;
  font-weight: 600;
}

.nav-icon {
  width: 16px;
  text-align: center;
  opacity: 0.8;
  flex-shrink: 0;
}

.nav-logout {
  margin-top: 10px;
  padding-top: 13px;
  border-top: 1px solid rgba(228, 251, 255, 0.1);
  border-radius: 0 0 7px 7px;
  color: rgba(228, 251, 255, 0.4);
}

.nav-logout:hover {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
}

.admin-content {
  min-width: 0;
}

.content-title {
  font-size: 13px;
  letter-spacing: 0.16em;
  color: rgba(228, 251, 255, 0.4);
  margin: 0 0 10px;
  text-align: left;
}

.admin-content .box {
  margin-bottom: 0;
}

@media (max-width: 760px) {
  .admin-layout {
    grid-template-columns: 1fr;
    gap: 14px;
    padding: 14px 10px 32px;
  }

  .admin-nav {
    position: static;
    flex-direction: row;
    align-items: center;
    gap: 4px;
    overflow-x: auto;
    padding: 8px;
    scrollbar-width: none;
  }

  .admin-nav::-webkit-scrollbar { display: none; }

  .nav-title { display: none; }

  .nav-list {
    flex-direction: row;
    gap: 4px;
  }

  .nav-item {
    width: auto;
    white-space: nowrap;
    padding: 7px 12px;
    font-size: 13px;
  }

  .nav-logout {
    margin-top: 0;
    padding-top: 7px;
    border-top: none;
    border-left: 1px solid rgba(228, 251, 255, 0.1);
    border-radius: 7px;
    margin-left: 4px;
    padding-left: 12px;
  }
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
.link-head {
  display: grid;
  grid-template-columns: 130px 150px 1fr;
  gap: 8px;
  padding: 0 0 6px;
  margin-right: 100px;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(228, 251, 255, 0.4);
  border-bottom: 1px solid rgba(228, 251, 255, 0.1);
}

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
  /* 單欄排列時欄位標題對不上，改在列內用 aria-label 辨識 */
  .link-head {
    display: none;
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

.img-compare {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  margin: 10px 0 4px;
}

.img-slot {
  min-width: 0;
}

.img-slot--new .img-preview {
  border-color: rgba(110, 231, 110, 0.55);
}

.preview-label {
  font-size: 12px;
  opacity: 0.5;
  margin: 4px 0 2px;
}

.preview-new {
  margin: 4px 0 10px;
}

/* ── AI 故事協助 ── */
.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ai-toggle {
  padding: 3px 12px;
  font-size: 12px;
  border: 1px solid rgba(157, 140, 255, 0.45);
  border-radius: 999px;
  background: rgba(157, 140, 255, 0.1);
  color: rgba(210, 200, 255, 0.9);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.ai-toggle:hover,
.ai-toggle.active {
  background: rgba(157, 140, 255, 0.25);
  border-color: rgba(157, 140, 255, 0.8);
  color: #fff;
}

.ai-panel {
  margin: 4px 0 14px;
  padding: 14px 16px;
  border: 1px solid rgba(157, 140, 255, 0.28);
  border-radius: 8px;
  background: rgba(90, 70, 160, 0.12);
}

.ai-hint {
  font-size: 12px;
  opacity: 0.6;
  margin: 0 0 10px;
  line-height: 1.6;
}

.ai-label {
  font-size: 12px;
  opacity: 0.75;
}

.ai-reference {
  min-height: 60px;
}

.ai-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.ai-quota {
  font-size: 12px;
  opacity: 0.5;
}

.ai-result {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(228, 251, 255, 0.1);
}

.ai-suggestion {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.75;
  padding: 12px 14px;
  border-radius: 6px;
  background: rgba(3, 1, 12, 0.5);
  border: 1px solid rgba(228, 251, 255, 0.12);
  max-height: 320px;
  overflow-y: auto;
}

.ai-note {
  font-size: 12px;
  opacity: 0.5;
  margin: 8px 0 0;
}

.field-hint {
  font-size: 12px;
  opacity: 0.45;
  margin: 0 0 6px;
  line-height: 1.5;
}

.site-desc {
  min-height: 60px;
}

/* ── 其他樣貌管理 ── */
.gallery-admin {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(228, 251, 255, 0.1);
}

.gallery-admin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  margin: 10px 0 14px;
}

.gallery-admin-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(228, 251, 255, 0.12);
  border-radius: 8px;
  background: rgba(3, 1, 12, 0.4);
}

.gallery-admin-item img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 5px;
  border: none;
}

.gallery-caption {
  margin: 0;
  font-size: 12px;
  padding: 4px 7px;
}

.gallery-admin-actions {
  display: flex;
  gap: 4px;
  justify-content: center;
}

/* ── 圖鑑外框選擇 ── */
.frame-picker {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
  gap: 10px;
  margin: 4px 0 14px;
  max-width: 460px;
}

.frame-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 9px;
  border: 1px solid rgba(228, 251, 255, 0.14);
  border-radius: 8px;
  background: transparent;
  font-family: inherit;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.frame-option:hover {
  border-color: rgba(228, 251, 255, 0.4);
  background: rgba(228, 251, 255, 0.05);
}

.frame-option.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.1);
}

.frame-sample {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1 / 1;
  font-size: 20px;
  font-weight: 700;
  color: #E06633;
  background: rgba(60, 40, 75, 0.6);
}

.frame-option-label {
  font-size: 12px;
  color: rgba(228, 251, 255, 0.7);
}

.frame-option.active .frame-option-label {
  color: #e4fbff;
}

.bg-preview {
  max-width: 260px;
  max-height: 140px;
  object-fit: cover;
}

.compress-info {
  font-size: 12px;
  color: #6ee76e;
  opacity: 0.85;
  margin: 4px 0 0;
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
