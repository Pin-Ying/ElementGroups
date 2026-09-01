<template>
  <div class="box">
    <AdminBar title="CREATOR LINKS">
      <button class="button" type="button" :disabled="saving" @click="handleSave">
        {{ saving ? 'Saving…' : '儲存' }}
      </button>
    </AdminBar>
    <p class="desc">
      設定要對外顯示的社群連結，數量不限。<br>
      儲存後會出現在每一頁最下方的頁尾，以及 /links 頁面；網址留空的項目會被忽略。<br>
      /links 頁面的說明文字請到「頁面管理」編輯。
    </p>

    <form @submit.prevent="handleSave">
      <label class="label">頭像形狀</label>
      <div class="shape-picker">
        <button
          v-for="sh in AVATAR_SHAPES"
          :key="sh.key"
          class="shape-option"
          type="button"
          :class="{ active: meta.avatar_shape === sh.key }"
          @click="meta.avatar_shape = sh.key"
        >
          <i class="shape-demo" :class="'shape-demo--' + sh.key"></i>
          {{ sh.label }}
        </button>
      </div>

      <div v-if="!links.length" class="placeholder-text">
        尚未新增任何連結，點下方「＋ 新增連結」開始。
      </div>

      <div v-if="links.length" class="link-head">
        <span>平台</span>
        <span>顯示名稱</span>
        <span>網址</span>
      </div>

      <div v-for="(link, i) in links" :key="i" class="link-row">
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
          <button class="icon-button" type="button" title="下移" :disabled="i === links.length - 1" @click="moveLink(i, 1)">↓</button>
          <button class="icon-button danger" type="button" title="刪除" @click="removeLink(i)">✕</button>
        </div>

        <div class="link-extras">
          <div class="link-avatar">
            <span
              v-if="link.avatar"
              class="avatar-preview"
              :class="'avatar-preview--' + meta.avatar_shape"
            >
              <img :src="link.avatar" alt="" />
            </span>
            <span v-else class="avatar-empty">無頭像</span>
            <input
              class="input avatar-input"
              type="file"
              accept="image/*"
              :aria-label="link.label + ' 頭像'"
              @change="onAvatarChange($event, link)"
            />
            <button v-if="link.avatar" class="icon-button danger" type="button" title="移除頭像" @click="link.avatar = ''">✕</button>
          </div>

          <label class="link-color">
            顏色
            <input type="color" :value="link.color || platformInfo(link.platform).color" @input="link.color = $event.target.value" />
            <button v-if="link.color" class="reset-color" type="button" @click="link.color = ''">用平台預設</button>
          </label>
        </div>
      </div>

      <div class="link-actions">
        <button class="button secondary" type="button" @click="addLink">＋ 新增連結</button>
      </div>
    </form>
  </div>
</template>

<script>
// 後台的「社群連結」分頁（issue #29 的第一個拆分對象）。
//
// 選它當第一個，是因為相依最單純：三個自己的狀態、六個專用 method，不碰
// libraries、不碰 elementsState，也沒有跨分頁共用的東西。用它把「殼要提供
// 什麼」這件事確定下來，再照同樣的形狀搬其餘分頁。
//
// 資料自己載：原本 loadCreatorLinks() 掛在 AdminView 的 loadAll()，一進後台
// 就把十一個分頁的資料全撈一次。改成分頁自己在 mounted 時載，殼不必再持有
// 這裡的狀態。分頁用 v-if 渲染，切回來會重載——對這種小資料無所謂，而且能
// 確保看到的是最新的。
//
// 樣式只留這個分頁自己的排版。.box／.label／.desc／.icon-button 這些跨元件
// 共用的原語已經收進 assets/forms.css，照該檔開頭寫的分工原則。
import { getAdminCreatorLinks, updateCreatorLinks } from '../../api'
import { setCreatorLinks } from '../../store/creatorLinks'
import { showToast } from '../../store/toast'
import { PLATFORMS, platformInfo } from '../../utils/socialPlatforms'
import { compressImage } from '../../utils/imageCompress'
import AdminBar from '../AdminBar.vue'

const AVATAR_SHAPES = [
  { key: 'circle', label: '圓形' },
  { key: 'square', label: '方形' }
]

export default {
  components: { AdminBar },
  data() {
    return {
      links: [],
      meta: { description: '', avatar_shape: 'circle' },
      saving: false,
      platforms: PLATFORMS,
      AVATAR_SHAPES
    }
  },
  mounted() {
    this.load()
  },
  methods: {
    platformInfo,
    async load() {
      try {
        const res = await getAdminCreatorLinks()
        this.links = (res.data.links || []).map(l => ({
          platform: l.platform || 'website',
          label: l.label || '',
          url: l.url || '',
          color: l.color || '',
          avatar: l.avatar || ''
        }))
        this.meta = {
          description: res.data.description || '',
          avatar_shape: res.data.avatar_shape || 'circle'
        }
      } catch (e) {
        console.error('Failed to load creator links:', e)
      }
    },
    addLink() {
      const used = new Set(this.links.map(l => l.platform))
      const next = PLATFORMS.find(p => !used.has(p.key)) || PLATFORMS[0]
      this.links.push({ platform: next.key, label: next.label, url: '', color: '', avatar: '' })
    },
    removeLink(i) {
      this.links.splice(i, 1)
    },
    moveLink(i, delta) {
      const target = i + delta
      if (target < 0 || target >= this.links.length) return
      const [item] = this.links.splice(i, 1)
      this.links.splice(target, 0, item)
    },
    onPlatformChange(link) {
      // 顯示名稱還是預設值時，跟著平台一起換；使用者自訂過就不動它
      const isDefaultLabel = PLATFORMS.some(p => p.label === link.label)
      if (!link.label || isDefaultLabel) link.label = platformInfo(link.platform).label
    },
    async onAvatarChange(e, link) {
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      try {
        // 頭像顯示尺寸很小，壓縮流程已足夠，不需要另外裁切
        const result = await compressImage(file)
        link.avatar = await new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result)
          reader.onerror = reject
          reader.readAsDataURL(result.blob)
        })
      } catch (err) {
        showToast(err.message || '頭像處理失敗', 'error')
      }
    },
    async handleSave() {
      const links = this.links
        .filter(l => (l.url || '').trim())
        .map(l => ({
          platform: l.platform,
          label: (l.label || '').trim() || platformInfo(l.platform).label,
          url: l.url.trim(),
          color: l.color || '',
          avatar: l.avatar || ''
        }))
      const payload = { ...this.meta, links }
      this.saving = true
      try {
        const res = await updateCreatorLinks(payload)
        showToast(res.data.message || 'Saved!', 'success')
        // 讓頁尾與 /links 立刻反映這次儲存的結果
        setCreatorLinks(payload)
      } catch (e) {
        showToast(e.response?.data?.message || 'Save failed', 'error')
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
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
  flex-wrap: wrap;
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

.link-extras {
  flex-basis: 100%;
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  padding-left: 2px;
}

.link-avatar {
  display: flex;
  align-items: center;
  gap: 7px;
}

.avatar-preview {
  display: block;
  width: 32px;
  height: 32px;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid rgba(228, 251, 255, 0.25);
}

.avatar-preview--circle { border-radius: 50%; }

.avatar-preview--square { border-radius: 6px; }

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border: none;
  border-radius: 0;
  display: block;
}

.avatar-empty {
  font-size: 11px;
  color: rgba(228, 251, 255, 0.3);
  width: 32px;
  text-align: center;
}

.avatar-input {
  margin: 0;
  font-size: 11px;
  max-width: 190px;
}

.link-color {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(228, 251, 255, 0.55);
}

.link-color input[type="color"] {
  width: 30px;
  height: 24px;
  padding: 0;
  border: 1px solid rgba(228, 251, 255, 0.25);
  border-radius: 5px;
  background: transparent;
  cursor: pointer;
}

.reset-color {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid rgba(228, 251, 255, 0.2);
  border-radius: 999px;
  background: transparent;
  color: rgba(228, 251, 255, 0.5);
  font-family: inherit;
  cursor: pointer;
}

.reset-color:hover {
  color: #e4fbff;
  border-color: rgba(228, 251, 255, 0.5);
}

.shape-picker {
  display: flex;
  gap: 8px;
  margin: 4px 0 14px;
}

.shape-option {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 14px;
  border: 1px solid rgba(228, 251, 255, 0.18);
  border-radius: 8px;
  background: transparent;
  color: rgba(228, 251, 255, 0.6);
  font-family: inherit;
  font-size: 13px;
  cursor: pointer;
}

.shape-option.active {
  border-color: #6ee76e;
  background: rgba(110, 231, 110, 0.1);
  color: #e4fbff;
}

.shape-demo {
  width: 16px;
  height: 16px;
  background: rgba(228, 251, 255, 0.45);
  display: inline-block;
}

.shape-demo--circle { border-radius: 50%; }

.shape-demo--square { border-radius: 4px; }

@media (max-width: 700px) {
  /* 單欄排列時欄位標題對不上，改在列內用 aria-label 辨識 */
  .link-row-fields {
    grid-template-columns: 1fr;
  }

  .link-head {
    display: none;
  }
}
</style>
