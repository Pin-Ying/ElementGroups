<template>
  <div class="story-editor">
    <ImageCropper
      v-if="cropFile"
      :file="cropFile"
      @done="onCropDone"
      @skip="onCropSkip"
      @cancel="cropFile = null"
    />

    <div v-if="hasDraft" class="draft-notice">
      這個元素有未發布的草稿。
      <button class="draft-link" type="button" @click="loadDraft">載入草稿</button>
      <button class="draft-link" type="button" @click="loadPublished">改看已發布內容</button>
    </div>

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

    <!-- 開著 AI 面板時，寬螢幕改為編輯框與建議左右並排 -->
    <div class="editor-main" :class="{ 'editor-main--split': ai.enabled && aiPanelOpen }">
      <textarea class="textarea" v-model="storyText" :rows="rows" aria-label="故事內容"></textarea>

    <!-- AI 故事協助（只有後端設定了 API key 才會出現） -->
    <div v-if="ai.enabled && aiPanelOpen" class="ai-panel">
      <p class="ai-hint">
        會自動帶入這個元素的週期表資料
        <template v-if="storyText.trim()">，以及你目前已經寫的內容（AI 會延伸潤飾而不是整段重寫）</template>。
      </p>

      <label class="label ai-label">風格／方向（選填）</label>
      <input class="input" type="text" v-model="aiDirection" aria-label="風格或方向" />

      <label class="label ai-label">補充參考資料（選填）</label>
      <textarea class="textarea ai-reference" v-model="aiReference" rows="3" aria-label="補充參考資料"></textarea>

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
      </div>
    </div>
    </div>

    <label class="label">Image</label>
    <p class="field-hint">{{ uploadHint }}</p>
    <input class="input" type="file" accept="image/*" ref="imageInput" aria-label="元素圖片" @change="onImageFileChange" />

    <div class="img-compare">
      <div v-if="currentImgSrc" class="img-slot">
        <p class="preview-label">目前圖片</p>
        <img :src="currentImgSrc" class="img-preview" alt="" @error="e => e.target.style.display='none'" />
      </div>
      <div v-if="newImagePreviewUrl" class="img-slot img-slot--new">
        <p class="preview-label">新圖片（尚未儲存）</p>
        <img :src="newImagePreviewUrl" class="img-preview" alt="" />
        <p class="compress-info">{{ compressionSummary }}</p>
      </div>
    </div>

    <div class="editor-actions">
      <button class="button" type="button" :disabled="saving" @click="submit(false)">
        {{ saving ? 'Saving…' : '發布' }}
      </button>
      <button class="button secondary" type="button" :disabled="saving" @click="submit(true)">存成草稿</button>
      <slot name="extra-actions" />
    </div>
  </div>
</template>

<script>
// 元素故事的編輯器。後台與元素頁的 inline 編輯共用同一份，
// 避免兩邊各寫一套而功能長歪（例如一邊有壓縮與草稿、另一邊沒有）。
import { updateStory, suggestStory, getAiStatus, apiBase } from '../api'
import { compressImage, formatBytes, MAX_UPLOAD_BYTES, MAX_EDGE } from '../utils/imageCompress'
import { showToast } from '../store/toast'
import ImageCropper from './ImageCropper.vue'

export default {
  components: { ImageCropper },
  props: {
    symbol: { type: String, required: true },
    story: { type: String, default: '' },
    draft: { type: String, default: '' },
    rows: { type: Number, default: 6 },
    // 不傳則用 API 的圖片端點
    imgSrc: { type: String, default: '' }
  },
  emits: ['saved', 'draft-saved'],
  data() {
    return {
      storyText: this.draft || this.story || '',
      draftText: this.draft || '',
      saving: false,
      cropFile: null,
      newImageBlob: null,
      newImageInfo: null,
      newImagePreviewUrl: '',
      ai: { enabled: false, used: 0, limit: 0 },
      aiPanelOpen: false,
      aiDirection: '',
      aiReference: '',
      aiSuggestion: '',
      aiLoading: false
    }
  },
  computed: {
    hasDraft() {
      return !!(this.draftText || '').trim()
    },
    currentImgSrc() {
      return this.imgSrc || `${apiBase}/elements/${this.symbol}/img`
    },
    uploadHint() {
      return `上傳前可裁切，並自動等比縮至長邊 ${MAX_EDGE}px；超過 ${formatBytes(MAX_UPLOAD_BYTES)} 的檔案不接受。`
    },
    compressionSummary() {
      const info = this.newImageInfo
      if (!info) return ''
      const saved = info.originalSize - info.compressedSize
      const pct = info.originalSize ? Math.round((saved / info.originalSize) * 100) : 0
      const size = `${formatBytes(info.originalSize)} → ${formatBytes(info.compressedSize)}`
      return saved > 0 ? `${size}（省下 ${pct}%）` : size
    }
  },
  watch: {
    // 後台切換元素時重設整個編輯狀態
    symbol() { this.reset() },
    story() { this.reset() },
    draft(v) { this.draftText = v || '' }
  },
  async created() {
    try {
      const res = await getAiStatus()
      this.ai = {
        enabled: !!res.data.enabled,
        used: res.data.used || 0,
        limit: res.data.limit || 0
      }
    } catch {
      this.ai = { enabled: false, used: 0, limit: 0 }
    }
  },
  beforeUnmount() {
    this.revokePreview()
  },
  methods: {
    reset() {
      this.storyText = this.draft || this.story || ''
      this.draftText = this.draft || ''
      this.revokePreview()
      this.aiDirection = ''
      this.aiReference = ''
      this.aiSuggestion = ''
      if (this.$refs.imageInput) this.$refs.imageInput.value = ''
    },
    revokePreview() {
      if (this.newImagePreviewUrl) {
        URL.revokeObjectURL(this.newImagePreviewUrl)
        this.newImagePreviewUrl = ''
      }
      this.newImageBlob = null
      this.newImageInfo = null
    },
    loadDraft() {
      this.storyText = this.draftText
      showToast('已載入草稿，按「發布」才會對外顯示', 'success')
    },
    loadPublished() {
      this.storyText = this.story || ''
    },
    onImageFileChange(e) {
      this.revokePreview()
      const file = e.target.files[0]
      e.target.value = ''
      if (!file) return
      if (!file.type.startsWith('image/')) {
        showToast('請選擇圖片檔', 'error')
        return
      }
      this.cropFile = file
    },
    async onCropDone({ blob }) {
      await this.acceptImage(new File([blob], 'cropped.jpg', { type: 'image/jpeg' }))
    },
    async onCropSkip() {
      await this.acceptImage(this.cropFile)
    },
    async acceptImage(file) {
      try {
        const result = await compressImage(file)
        this.newImageBlob = result.blob
        this.newImageInfo = result
        this.newImagePreviewUrl = URL.createObjectURL(result.blob)
      } catch (err) {
        showToast(err.message || '圖片處理失敗', 'error')
      } finally {
        this.cropFile = null
      }
    },
    async handleSuggest() {
      this.aiLoading = true
      try {
        const res = await suggestStory({
          symbol: this.symbol,
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
      showToast('已套用到編輯框，記得儲存', 'success')
    },
    async submit(asDraft) {
      const formData = new FormData()
      formData.append('symbol', this.symbol)
      formData.append('stroy', this.storyText)
      if (asDraft) {
        formData.append('draft', '1')
      } else if (this.newImageBlob) {
        formData.append('image', this.newImageBlob, `${this.symbol}.jpg`)
      }

      this.saving = true
      try {
        const res = await updateStory(formData)
        showToast(res.data.message || 'Saved!', 'success')

        if (asDraft) {
          this.draftText = this.storyText
          this.$emit('draft-saved', { symbol: this.symbol, story: this.storyText })
        } else {
          this.draftText = ''
          this.$emit('saved', {
            symbol: this.symbol,
            story: this.storyText,
            hasImage: !!this.newImageBlob
          })
          this.revokePreview()
        }
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
.story-editor { text-align: left; }

.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.editor-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 14px;
}

.img-compare {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  margin: 10px 0 4px;
}

.img-slot--new .img-preview { border-color: rgba(110, 231, 110, 0.55); }

.field-hint {
  font-size: 12px;
  opacity: 0.45;
  margin: 0 0 6px;
  line-height: 1.5;
}

.compress-info {
  font-size: 12px;
  color: #6ee76e;
  opacity: 0.85;
  margin: 4px 0 0;
}

.preview-label {
  font-size: 12px;
  opacity: 0.5;
  margin: 4px 0 2px;
}

.img-preview {
  max-width: 160px;
  max-height: 160px;
  border-radius: 6px;
  border: 1px solid rgba(228, 251, 255, 0.15);
  display: block;
  margin: 10px 0;
}

.textarea {
  width: 100%;
  min-height: 120px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(228, 251, 255, 0.15);
  border-radius: 6px;
  color: rgba(228, 251, 255, 0.9);
  padding: 8px 10px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
  display: block;
  margin: 4px 0 10px;
}

.input {
  display: block;
  width: 100%;
  margin: 4px 0 10px;
  box-sizing: border-box;
}

.draft-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin: 0 0 12px;
  padding: 9px 13px;
  border: 1px solid rgba(255, 196, 107, 0.35);
  border-radius: 7px;
  background: rgba(255, 196, 107, 0.08);
  font-size: 13px;
  color: rgba(255, 196, 107, 0.9);
}

.draft-link {
  border: none;
  background: none;
  padding: 0;
  font-family: inherit;
  font-size: 13px;
  color: #ffc46b;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.draft-link:hover { color: #fff; }

/* ── AI 協助 ── */
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

/* 寬螢幕時編輯框與 AI 建議並排，兩邊等高才好對照 */
.editor-main--split {
  display: grid;
  gap: 14px;
  align-items: start;
}

@media (min-width: 1000px) {
  .editor-main--split {
    grid-template-columns: 1fr 1fr;
  }

  .editor-main--split .textarea {
    height: 100%;
    min-height: 320px;
    margin-bottom: 0;
  }

  .editor-main--split .ai-panel {
    margin: 0;
    max-height: 520px;
    overflow-y: auto;
  }
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

.ai-label { font-size: 12px; opacity: 0.75; }
.ai-reference { min-height: 60px; }

.ai-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.ai-quota { font-size: 12px; opacity: 0.5; }

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

.label {
  display: block;
  font-size: 13px;
  margin: 10px 0 4px;
  opacity: 0.75;
}
</style>
