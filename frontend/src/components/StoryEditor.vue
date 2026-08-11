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

    <AiField
      label="Story"
      kind="element-story"
      v-model="storyText"
      :extra="{ symbol }"
      :rows="rows"
      multiline
    />

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
import { updateStory, apiBase } from '../api'
import AiField from './AiField.vue'
import { compressImage, formatBytes, MAX_UPLOAD_BYTES, MAX_EDGE } from '../utils/imageCompress'
import { showToast } from '../store/toast'
import ImageCropper from './ImageCropper.vue'

export default {
  components: { AiField, ImageCropper },
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
      newImagePreviewUrl: ''
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
  beforeUnmount() {
    this.revokePreview()
  },
  methods: {
    reset() {
      this.storyText = this.draft || this.story || ''
      this.draftText = this.draft || ''
      this.revokePreview()
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

.label {
  display: block;
  font-size: 13px;
  margin: 10px 0 4px;
  opacity: 0.75;
}

</style>
